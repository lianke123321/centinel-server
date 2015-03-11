from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
import flask
import geoip2.errors
import geoip2.database
import glob
import hashlib
import json
import os
import random
import re
import requests
import string
import tarfile
from werkzeug import secure_filename


from centinel.models import Client, Role
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

def generate_typeable_handle(length = 8):
    """Generate a random typeable (a-z, 1-9) string for consent URL."""
    return "".join([random.choice(string.digits + 
                    string.ascii_lowercase) for _ in range(length)])

def update_client_info(username, ip):
    """Update client's information upon contact.
    This information includes their IP address,
    time when last seen, and country.

    Params:

    username-   username of the client who contaced.
    ip-         IP address of the client

    """
    client = Client.query.filter_by(username=username).first()
    if client is None:
        # this should never happen
        return
    # aggregate the ip to /24
    client.last_ip = ".".join(ip.split(".")[:3]) + ".0/24"
    client.last_seen = datetime.now()
    client.country = get_country_from_ip(ip)
    db.session.commit()

@app.errorhandler(404)
def not_found(error):
    return flask.make_response(flask.jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return flask.make_response(flask.jsonify({'error': 'Bad request'}), 400)

@app.errorhandler(418)
def no_consent(error):
    return flask.make_response(flask.jsonify({'error': 'Consent not given'}),
                               418)

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
    update_client_info(flask.request.authorization.username,
                       flask.request.remote_addr)
    # abort if there is no result file
    if not flask.request.files:
        flask.abort(400)

    # make sure the informed consent has been given before we proceed
    username = flask.request.authorization.username
    client = Client.query.filter_by(username=username).first()
    if not client.has_given_consent:
        flask.abort(418)

    # TODO: overwrite file if exists?
    result_file = flask.request.files['result']
    client_dir = username

    # we assume that the directory was created when the user
    # registered
    file_name = secure_filename(result_file.filename)
    file_path = os.path.join(config.results_dir, client_dir, file_name)

    result_file.save(file_path)

    return flask.jsonify({"status": "success"}), 201

@app.route("/results")
@auth.login_required
def get_results():
    update_client_info(flask.request.authorization.username,
                       flask.request.remote_addr)
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

def get_user_specific_content(folder, filename=None, json_var=None):
    """Perform the functionality of get_experiments and get_inputs_files

    Params:

    filename- the name of the file to retrieve or None to fetch the
        hashes of all the files
    folder- the directory that the user's directory is contained in
    json_var- the name of the json variable to return containing the
    list of hashes

    """
    update_client_info(flask.request.authorization.username,
                       flask.request.remote_addr)
    username = flask.request.authorization.username

    # make sure the informed consent has been given before we proceed
    client = Client.query.filter_by(username=username).first()
    if not client.has_given_consent:
        flask.abort(418)

    # all of the scheduler files are combined together here.
    # this is run every time the experiment list or "scheduler.info"
    # is requested.
    if (json_var == "experiments" and 
        (filename is None or filename == "scheduler.info")):
        global_scheduler_filename = os.path.join(config.experiments_dir,
                                                 "global", "scheduler.info")
        country_scheduler_filename = os.path.join(config.experiments_dir,
                                                  client.country, "scheduler.info")
        client_scheduler_filename = os.path.join(config.experiments_dir,
                                                 username, "scheduler.info")

        freqs = {}
        if os.path.exists(global_scheduler_filename):
            with open(global_scheduler_filename, 'r') as file_p:
                freqs.update(json.load(file_p))
        if os.path.exists(country_scheduler_filename):
            with open(country_scheduler_filename, 'r') as file_p:
                freqs.update(json.load(file_p))
        if os.path.exists(client_scheduler_filename):
            with open(client_scheduler_filename, 'r') as file_p:
                freqs.update(json.load(file_p))

        with open(client_scheduler_filename, 'w') as file_p:
            json.dump(freqs, file_p)

    files = {}

    # include global baseline content
    global_dir = os.path.join(folder, "global")
    if os.path.exists(global_dir):
        for path in glob.glob(os.path.join(global_dir, "*")):
            file_name = os.path.basename(path)
            # avoid sending the global scheduler here
            # the only scheduler file sent must be the unified scheduler
            # in the client's experiments dir.
            if file_name == "scheduler.info":
                continue
            files[file_name] = path
    else:
        print ("Global baseline folder \"%s\" "
               "doesn't exist!" %(global_dir))

    # include country-specific baseline content
    country_specific_dir = os.path.join(folder, client.country)
    if os.path.exists(country_specific_dir):
        # if baseline experiments exist for this country (==folder exists),
        # sync up all of the files in that dir.
        for path in glob.glob(os.path.join(country_specific_dir, "*")):
            file_name = os.path.basename(path)
            # avoid sending the country-specific scheduler here
            # the only scheduler file sent must be the unified scheduler
            # in the client's experiments dir.
            if file_name == "scheduler.info":
                continue
            files[file_name] = path
    else:
        print ("Country baseline folder %s "
               "doesn't exist!" %(country_specific_dir))

    user_dir = os.path.join(folder, username, '*')
    for path in glob.glob(user_dir):
        file_name = os.path.basename(path)
        files[file_name] = path

    if filename is None:
        for filename in files:
            with open(files[filename], 'r') as file_p:
                hash_val = hashlib.md5(file_p.read()).digest()
                files[filename] = urlsafe_b64encode(hash_val)

        return flask.jsonify({json_var: files})

    # this should never happen, but better be safe
    if '..' in filename or filename.startswith('/'):
        flask.abort(404)

    if filename in files:
        # send requested experiment file
        return flask.send_file(files[filename])
    else:
        # not found
        flask.abort(404)



@app.route("/experiments")
@app.route("/experiments/<name>")
@auth.login_required
def get_experiments(name=None):
    update_client_info(flask.request.authorization.username,
                       flask.request.remote_addr)
    return get_user_specific_content(config.experiments_dir, filename=name,
                                     json_var="experiments")

@app.route("/input_files")
@app.route("/input_files/<name>")
@auth.login_required
def get_inputs(name=None):
    update_client_info(flask.request.authorization.username,
                       flask.request.remote_addr)
    return get_user_specific_content(config.inputs_dir, filename=name,
                                     json_var="inputs")

@app.route("/clients")
def get_system_status():
    """This is a list of clients and the countries from which they last
    connected and when. This does not require authentication as it
    doesn't reveal anything important (e.g. IP address, username, etc.).
    The list is shuffled each time so that numbers are randomly assigned.

    """
    clients = Client.query.all()
    random.shuffle(clients)
    results = []
    number = 0
    for client in clients:
        info = {}
        info['num'] = number
        info['country'] = client.country
        if client.last_seen is not None:
            info['last_seen'] = str( client.last_seen.date() )
        else:
            continue
        info['is_vpn']    = client.is_vpn
        results.append(info)
        number += 1
    return flask.jsonify({ "clients" : results })

@app.route("/client_details")
@auth.login_required
def get_clients():
    """This is a list of clients that is fully detailed.
    This requires both authentication and admin-level access.

    """
    update_client_info(flask.request.authorization.username,
                       flask.request.remote_addr)
    # ensure that the client has the admin role
    username = flask.request.authorization.username
    user = Client.query.filter_by(username=username).first()
    admin = Role.query.filter_by(name='admin').first()
    if user not in admin.users:
        return unauthorized()

    results = []
    clients = Client.query.all()
    for client in clients:
        info = {}
        info['username']  = client.username
        info['handle']    = client.typeable_handle
        info['country']   = client.country
        info['registered_date'] = client.registered_date
        info['last_seen'] = client.last_seen
        info['last_ip']   = client.last_ip
        info['is_vpn']    = client.is_vpn
        info['has_given_consent'] = client.has_given_consent
        info['date_given_consent'] = client.date_given_consent
        results.append(info)
    return flask.jsonify({ "clients" : results })

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
    client_json['registered_date'] = datetime.now()
    client_json['has_given_consent'] = False
    client_json['is_vpn'] = False
    client_json['roles'] = ['client']

    if not username or not password:
        flask.abort(400)

    client = Client.query.filter_by(username=username).first()
    if client is not None:
        flask.abort(400)

    # create a typeable handle to put in the consent form URL
    typeable_handle = generate_typeable_handle(length = 8)
    client = Client.query.filter_by(typeable_handle=typeable_handle).first()
    # if there is a collision, generate another one
    while client is not None:
        typeable_handle = generate_typeable_handle(length = 8)
        client = Client.query.filter_by(typeable_handle=typeable_handle).first()
    client_json['typeable_handle'] = typeable_handle

    user = Client(**client_json)
    db.session.add(user)
    db.session.commit()

    os.makedirs(os.path.join(config.results_dir, username))
    os.makedirs(os.path.join(config.experiments_dir, username))
    os.makedirs(os.path.join(config.inputs_dir, username))

    return flask.jsonify({"status": "success", "typeable_handle" : typeable_handle}), 201

@app.route("/geolocate/")
@app.route("/geolocate/<custom_ip>")
def geolocate(custom_ip=None):
    if custom_ip is not None:
        ip = custom_ip
    else:
        ip = flask.request.remote_addr

    try:
        # aggregate ip to the /24
        ip_aggr = ".".join(ip.split(".")[:3]) + ".0/24"
        country = get_country_from_ip(ip)
    except Exception as exp:
        return flask.jsonify({"ip": ip_aggr,
                              "error": str(exp)})
    return flask.jsonify({"ip": ip_aggr, "country": country})

def display_consent_page(username, path, freedom_url=''):
    # insert a hidden field into the form with the user's username
    with open(path, 'r') as file_p:
        initial_page = file_p.read()
    initial_page = initial_page.decode('utf-8')
    replace_field = u'replace-with-username-value'
    initial_page = initial_page.replace(replace_field,
                                        urlsafe_b64encode(username))
    replace_field = u'replace-with-human-readable-username-value'
    initial_page = initial_page.replace(replace_field, (username))
    freedom_replacement = u'replace-this-with-freedom-house'
    initial_page = initial_page.replace(freedom_replacement,
                                        u'static/' + freedom_url)
    return initial_page

@app.route("/consent/<typeable_handle>")
def get_initial_informed_consent_with_handle(typeable_handle):
    if typeable_handle is None:
        flask.abort(404)
    client = Client.query.filter_by(typeable_handle=typeable_handle).first()
    if client is None:
        flask.abort(404)
    if client.has_given_consent:
        return "Consent already given."
    username = client.username
    return display_consent_page(username,
                                'static/initial_informed_consent.html')

@app.route("/get_initial_consent")
def get_initial_informed_consent():
    username = flask.request.args.get('username')
    if username is None:
        flask.abort(404)
    username = urlsafe_b64decode(str(username))
    client = Client.query.filter_by(username=username).first()
    if client is None:
        flask.abort(404)
    if client.has_given_consent:
        return "Consent already given."
    return display_consent_page(username,
                                'static/initial_informed_consent.html')

@app.route("/get_informed_consent_for_country")
def get_country_specific_consent():
    username = flask.request.args.get('username')
    country = flask.request.args.get('country')
    if username is None or country is None:
        flask.abort(404)
    username = urlsafe_b64decode(str(username))
    client = Client.query.filter_by(username=username).first()
    if client is None:
        flask.abort(404)
    if client.has_given_consent:
        return "Consent already given."
    country = str(country).upper()
    if country not in constants.freedom_house_lookup:
        flask.abort(404)

    # if we don't already have the content from freedom house, fetch
    # it, then host it locally and insert it into the report
    freedom_url = "".join(["freedom_house_", country, ".html"])
    filename = os.path.join("static", freedom_url)
    # get the content from freedom house if we don't already have it
    get_page_and_strip_bad_content(constants.freedom_house_url(country),
                                   filename)

    page_path = 'static/informed_consent.html'
    page_content = display_consent_page(username, page_path, freedom_url)

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
    with open(filename, 'w') as file_p:
        file_p.write(page)

@app.route("/submit_consent")
def update_informed_consent():
    username = flask.request.args.get('username')
    if username is None:
        flask.abort(404)
    username = urlsafe_b64decode(str(username))
    client = Client.query.filter_by(username=username).first()
    if client is None:
        flask.abort(404)
    if client.has_given_consent:
        return "Consent already given."
    client.has_given_consent = True
    client.date_given_consent = datetime.now().date()
    db.session.commit()
    response = ("Success! Thanks for registering; you are ready to start "
                "sending us censorship measurement results.")
    return response

@auth.verify_password
def verify_password(username, password):
    user = Client.query.filter_by(username=username).first()
    return user and user.verify_password(password)
