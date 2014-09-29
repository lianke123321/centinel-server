from base64 import b64decode, b64encode
from datetime import datetime
import flask
import geoip2.errors
import geoip2.database
import glob
import json
import os
import re
import requests
from werkzeug import secure_filename

from centinel.models import Client
import config
from centinel import constants

import centinel
app = centinel.app
db = centinel.db
auth = centinel.auth

try:
    reader = geoip2.database.Reader(config.maxmind_db)
except (geoip2.database.maxminddb.InvalidDatabaseError, IOError):
    print ("You appear to have an error in your geolocation database.\n"
           "Your database is either corrupt or does not exist\n"
           "until you download a new copy, geolocation functionality\n"
           "will be disabled")
    reader = None


def get_country_from_ip(ip):
    """Return the country for the given ip"""
    try:
        return reader.country(ip).country.iso_code
    # if we have disabled geoip support, reader should be None, so the
    # exception should be triggered
    except (geoip2.errors.AddressNotFoundError,
            geoip2.errors.GeoIP2Error, AttributeError):
        return '--'

@app.errorhandler(404)
def not_found(error):
    return flask.make_response(flask.jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return flask.make_response(flask.jsonify({'error': 'Bad request'}), 400)

@auth.error_handler
def unauthorized():
    json_resp = flask.jsonify({'error': 'Unauthorized access'})
    return flask.make_response(json_resp, 401)

@app.route("/version")
def get_recommended_version():
    return flask.jsonify({"version": config.recommended_version})

@app.route("/results", methods=['POST'])
@auth.login_required
def submit_result():
    # abort if there is no result file
    if not flask.request.files:
        flask.abort(400)

    # TODO: overwrite file if exists?
    result_file = flask.request.files['result']
    client_dir = flask.request.authorization.username

    # we assume that the directory was created when the user
    # registered
    file_name = secure_filename(result_file.filename)
    file_path = os.path.join(config.results_dir, client_dir, file_name)

    result_file.save(file_path)

    return flask.jsonify({"status": "success"}), 201

@app.route("/results")
@auth.login_required
def get_results():
    results = {}

    # TODO: cache the list of results?
    # TODO: let the admin query any results file here?
    # look in results directory for the user's results (we assume this
    # directory was created when the user registered)
    username = flask.request.authorization.username
    user_dir = os.path.join(config.results_dir, username, '[!_]*.json')
    for path in glob.glob(user_dir):
        file_name, ext = os.path.splitext(os.path.basename(path))
        with open(path) as result_file:
            try:
                results[file_name] = json.load(result_file)
            except Exception, e:
                print "Couldn't open file - %s - %s" % (path, str(e))

    return flask.jsonify({"results": results})

@app.route("/experiments")
@app.route("/experiments/<name>")
@auth.login_required
def get_experiments(name=None):
    experiments = {}

    # TODO: create an option to pull down all?
    # look in experiments directory for each user
    username = flask.request.authorization.username
    user_dir = os.path.join(config.experiments_dir, username, '[!_]*.py')
    for path in glob.glob(user_dir):
        file_name, _ = os.path.splitext(os.path.basename(path))
        experiments[file_name] = path

    # send all the experiment file names
    if name is None:
        return flask.jsonify({"experiments": experiments.keys()})

    # this should never happen, but better be safe
    if '..' in name or name.startswith('/'):
        flask.abort(404)

    if name in experiments:
        # send requested experiment file
        return flask.send_file(experiments[name])
    else:
        # not found
        flask.abort(404)

@app.route("/clients")
@auth.login_required
def get_clients():
    # TODO: ensure that only the admin can make this call
    clients = Client.query.all()
    return flask.jsonify(clients=[client.username for client in clients])


@app.route("/register", methods=["POST"])
def register():
    # TODO: use a captcha to prevent spam?
    if not flask.request.json:
        flask.abort(404)

    ip = flask.request.remote_addr

    # parse the info we need out of the json
    client_json = flask.request.get_json()
    username = client_json.get('username')
    password = client_json.get('password')
    # if the user didn't specify which country they were coming from,
    # pull it from geolocation on their ip
    country = client_json.get('country')
    if country is None or (len(country) != 2):
        client_json['country'] = get_country_from_ip(ip)
    client_json['ip'] = ip
    client_json['last_seen'] = datetime.now()
    client_json['roles'] = ['client']

    if not username or not password:
        flask.abort(400)

    client = Client.query.filter_by(username=username).first()
    if client is not None:
        flask.abort(400)

    user = Client(**client_json)
    db.session.add(user)
    db.session.commit()

    os.makedirs(os.path.join(config.results_dir, username))
    os.makedirs(os.path.join(config.experiments_dir, username))

    return flask.jsonify({"status": "success"}), 201

@app.route("/geolocation")
def geolocate_client():
    # get the ip and aggregate to the /24
    ip = flask.request.remote_addr
    ip_aggr = ".".join(ip.split(".")[:3]) + ".0/24"
    country = get_country_from_ip(ip)
    return flask.jsonify({"ip": ip_aggr, "country": country})

@app.route("/get_initial_consent")
def get_initial_informed_consent():
    username = b64decode(flask.request.args.get('username'))
    password = b64decode(flask.request.args.get('password'))
    if username is None or password is None:
        flask.abort(404)
    username, password = str(username), str(password)
    if not verify_password(username, password):
        flask.abort(404)

    # insert a hidden field into the form with the user's username and
    # password
    with open('static/initial_informed_consent.html', 'r') as fileP:
        initial_page = fileP.read()
    initial_page = initial_page.replace("replace-with-username-value",
                                        b64encode(username))
    initial_page = initial_page.replace("replace-with-password-value",
                                        b64encode(password))
    return initial_page

@app.route("/get_informed_consent_for_country")
def get_country_specific_consent():
    username = b64decode(flask.request.args.get('username'))
    password = b64decode(flask.request.args.get('password'))
    country = flask.request.args.get('country')
    if username is None or country is None or password is None:
        flask.abort(404)
    username, password = str(username), str(password)
    if not verify_password(username, password):
        flask.abort(404)
    country = str(country).upper()
    if country not in constants.freedom_house_lookup:
        flask.abort(404)

    with open('static/informed_consent.html', 'r') as fileP:
        page_content = fileP.read()

    # insert the username and password into hidden fields
    replace_field = "replace-with-username-value"
    page_content = page_content.replace(replace_field, (b64encode(username)))
    replace_field = "replace-with-password-value"
    page_content = page_content.replace(replace_field, (b64encode(password)))
    replace_field = "replace-with-human-readable-username-value"
    page_content = page_content.replace(replace_field, (username))

    # if we don't already have the content from freedom house, fetch
    # it, then host it locally and insert it into the report
    freedom_url = "".join(["freedom_house_", country, ".html"])
    filename = os.path.join("static", freedom_url)
    # get the content from freedom house if we don't already have it
    get_page_and_strip_bad_content(constants.freedom_house_url(country),
                                   filename)
    freedom_replacement = "replace-this-with-freedom-house"
    page_content = page_content.replace(freedom_replacement,
                                        "static/" + freedom_url)

    flask.url_for('static', filename=freedom_url)
    flask.url_for('static', filename='economistDemocracyIndex.pdf')
    flask.url_for('static', filename='consent.js')

    return page_content

def get_page_and_strip_bad_content(url, filename):
    """Get the given page, strip out all requests back to the original
    domain (identified via src tags), and write out the page

    Note: this will break stuff, but that is better than letting the
    domain know where and who our clients are

    Note: we expect the content to be fairly static, so we don't
    refetch it if we already have it

    """
    # if os.path.exists(filename):
    #     return
    req = requests.get(url)
    # replace external links with a blank reference (sucks for the
    # rendering engine to figure out, but hey, they get paid to work
    # that out)
    replace_src = 'src\s*=\s*"\s*\S+\s*"'
    page = re.sub(replace_src, "", req.content)
    replace_href = 'href\s*=\s*"\s*\S+\s*"'
    page = re.sub(replace_href, "", page)
    replace_script = '<\s*script\s*>[\s\S]*</\s*script\s*>'
    page = re.sub(replace_script, "", page)
    with open(filename, 'w') as fileP:
        fileP.write(page)

@app.route("/submit_consent")
def update_informed_consent():
    username = b64decode(flask.request.args.get('username'))
    password = b64decode(flask.request.args.get('password'))
    if username is None or password is None:
        flask.abort(404)
    username, password = str(username), str(password)
    if not verify_password(username, password):
        flask.abort(404)
    client = Client.query.filter_by(username=username).first()
    client.has_given_consent = True
    client.date_given_consent = datetime.now()
    db.session.commit()
    response = ("Success! Thanks for registering; you are ready to start "
                "sending us censorship measurement results.")
    return response

@auth.verify_password
def verify_password(username, password):
    user = Client.query.filter_by(username=username).first()
    return user and user.verify_password(password)
