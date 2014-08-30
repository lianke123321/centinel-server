import config
import glob
import flask
import os
import json

from werkzeug import secure_filename

app = flask.Flask("Centinel")

@app.errorhandler(404)
def not_found(error):
    return flask.make_response(flask.jsonify({'error': 'Not found'}), 404)

@app.route("/versions")
def get_recommended_versions():
    return flask.jsonify({"versions" : config.recommended_versions})

@app.route("/results", methods=['POST'])
def submit_result():
    # abort if there is no result file
    if not flask.request.files:
        flask.abort(400)

    #XXX: overwrite file if exists?
    result_file = flask.request.files['result']
    file_name = secure_filename(result_file.filename)
    file_path = os.path.join(config.results_dir, file_name)
    result_file.save(file_path)

    return flask.jsonify({"status" : "success"}), 201

@app.route("/results")
def get_results():
    results = {}

    #XXX: cache the list of results?
    # look in results directory
    for path in glob.glob(os.path.join(config.results_dir,'[!_]*.json')):
        # get name of file and path
        file_name, ext = os.path.splitext(os.path.basename(path))
        # read the result file
        with open(path) as result_file:
            try:
                results[file_name] = json.load(result_file)
            except Exception, e:
                print "Couldn't open file - %s" % (path)

    return flask.jsonify({"results" : results})

@app.route("/experiments")
@app.route("/experiments/<name>")
def get_experiments(name=None):
    experiments = {}

    # look for experiments in experiments directory
    for path in glob.glob(os.path.join(config.experiments_dir,'[!_]*.py')):
        # get name of file and path
        file_name, ext = os.path.splitext(os.path.basename(path))
        # read the result file
        with open(path) as experiment_file:
            experiments[file_name] = experiment_file.read()

    # send all the experiment files
    if name == None:
        return flask.jsonify({"experiments" : experiments})

    if name in experiments:
        # send requested experiment file
        #XXX: Don't send a python file in JSON
        return flask.jsonify({"experiments" : experiments[name]})
    else:
        # not found
        flask.abort(404)

@app.route("/clients")
@app.route("/clients/<name>")
def get_clients(name=None):
    clients = {}

    with open(config.clients_file) as clients_fh:
        clients = json.load(clients_fh)

    # send all the client details
    if name == None:
        return flask.jsonify(clients)

    if name in clients:
        # send requested client details
        return flask.jsonify(client[name])
    else:
        # not found
        flask.abort(404)

@app.route("/log", methods=["POST"])
def submit_log():
    pass

if __name__ == "__main__":
    app.run(debug=True)
