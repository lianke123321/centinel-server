from datetime import datetime
import flask
import geoip2.errors
import geoip2.database
import glob
import json
import os
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
    # insert a hidden field into the form with the user's username
    # (this let's us keep state for the next time the client talks to
    # us)
    username = flask.request.args.get('username')
    if username is None:
        flask.abort(404)
    username = str(username)
    username_field = '<input type="hidden" name="username" value="replace-value">'
    # add the username to the username replacement string
    username_field = username_field.replace("replace-value", username)

    # replace the appropriate section of the page with the username
    # field
    with open('static/initial_informed_consent.html', 'r') as fileP:
        initial_page = fileP.read()
    replace_field = "<replace-with-hidden-username>"
    initial_page = initial_page.replace(replace_field, username_field)
    return initial_page

@app.route("/get_informed_consent_for_country")
def get_country_specific_consent():
    username = flask.request.args.get('username')
    country = flask.request.args.get('country')
    if username is None or country is None:
        flask.abort(404)
    username = str(username)

    username_field = '<input type="hidden" name="username" value="replace-value">'
    # add the username to the username replacement string
    username_field = username_field.replace("replace-value", username)

    country = str(country).upper()
    if country not in constants.freedom_house_lookup:
        flask.abort(404)

    with open('static/informed_consent.html', 'r') as fileP:
        page_content = fileP.read()

    # insert a hidden field to submit the userid for us
    replace_field = "<replace-with-hidden-username>"
    page_content = page_content.replace(replace_field, username_field)

    # get the content from freedom house and insert it into the report
    req = requests.get(constants.freedom_house_url(country))
    freedom_replacement = "<replace-this-with-freedom-house>"
    page_content = page_content.replace(freedom_replacement, req.content)

    flask.url_for('static', filename='economistDemocracyIndex.pdf')
    flask.url_for('static', filename='consent.js')

    # get the content from canada travel advisory and insert it into the report
    req = requests.get(constants.canada_url(country))
    canada_replacement = "<replace-this-with-canada>"
    page_content = page_content.replace(canada_replacement, req.content)

    return page_content

@app.route("/submit_consent")
def update_informed_consent():
    username = flask.request.args.get('username')
    if username is None:
        flask.abort(404)
    username = str(username)
    client = Client.query.filter_by(username=username).first()
    client.has_given_consent = True
    client.data_given_consent = datetime.now()
    db.session.commit()

@auth.verify_password
def verify_password(username, password):
    user = Client.query.filter_by(username=username).first()
    return user and user.verify_password(password)
