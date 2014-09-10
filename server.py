import os
import glob
import flask
import json

import config

from werkzeug import secure_filename
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context

app = flask.Flask("Centinel")
auth = HTTPBasicAuth()
db = SQLAlchemy(app)


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(36), index=True) #uuid length=36
    password_hash = db.Column(db.String(64))

    def __init__(self, username, password):
        self.username = username
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

@app.errorhandler(404)
def not_found(error):
    return flask.make_response(flask.jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return flask.make_response(flask.jsonify({'error': 'Bad request'}), 400)

@auth.error_handler
def unauthorized():
    return flask.make_response(flask.jsonify({'error': 'Unauthorized access'}), 401)

@app.route("/version")
def get_recommended_version():
    return flask.jsonify({"version" : config.recommended_version})

@app.route("/results", methods=['POST'])
@auth.login_required
def submit_result():
    # abort if there is no result file
    if not flask.request.files:
        flask.abort(400)

    #XXX: overwrite file if exists?
    result_file = flask.request.files['result']
    client_dir = flask.request.authorization.username

    # we assume that the directory was created when the user
    # registered
    file_name = secure_filename(result_file.filename)
    file_path = os.path.join(config.results_dir, client_dir, file_name)

    result_file.save(file_path)

    return flask.jsonify({"status" : "success"}), 201

@app.route("/results")
@auth.login_required
def get_results():
    results = {}

    #XXX: cache the list of results?
    #XXX: let the admin query any results file here?
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

    return flask.jsonify({"results" : results})

@app.route("/experiments")
@app.route("/experiments/<name>")
def get_experiments(name=None):
    experiments = {}

    #XXX: create an option to pull down all?
    # look in experiments directory for each user
    username = flask.request.authorization.username
    user_dir = os.path.join(config.experiments_dir, username, '[!_]*.py')
    for path in glob.glob(user_dir):
        file_name, _ = os.path.splitext(os.path.basename(path))
        experiments[file_name] = path

    # send all the experiment file names
    if name == None:
        return flask.jsonify({"experiments" : experiments.keys()})

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
    #XXX: ensure that only the admin can make this call
    clients = Client.query.all()
    return flask.jsonify(clients=[client.username for client in clients])

@app.route("/log", methods=["POST"])
@auth.login_required
def submit_log():
    # abort if there is no log file
    if not flask.request.files:
        flask.abort(400)

    #XXX: overwrite file if exists?
    result_file = flask.request.files['log']
    client_dir = flask.request.authorization.username

    # we assume that the directory was created when the user
    # registered
    file_name = secure_filename(result_file.filename)
    file_path = os.path.join(config.log_dir, client_dir, file_name)

    result_file.save(file_path)

    return flask.jsonify({"status" : "success"}), 201

@app.route("/register", methods=["POST"])
def register():
    #XXX: use a captcha to prevent spam?
    if not flask.request.json:
        flask.abort(404)

    username = flask.request.json.get('username')
    password = flask.request.json.get('password')

    if not username or not password:
        flask.abort(400)

    client = Client.query.filter_by(username=username).first()

    if client is not None:
        flask.abort(400)

    user = Client(username=username, password=password)
    db.session.add(user)
    db.session.commit()

    os.makedirs(os.path.join(config.results_dir, username))
    os.makedirs(os.path.join(config.experiments_dir, username))
    os.makedirs(os.path.join(config.log_dir, username))

    return flask.jsonify({"status" : "success"}), 201

@auth.verify_password
def verify_password(username, password):
    user = Client.query.filter_by(username=username).first()
    return user and user.verify_password(password)

if __name__ == "__main__":
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % (config.sqlite_db)
    if not os.path.exists(config.sqlite_db):
        db.create_all()
    app.run(debug=True)
