import config
import glob
import flask
import os
import json

app = flask.Flask(__name__)

@app.route("/versions/")
def get_recommended_versions():
    return flask.jsonify({"versions" : config.recommended_versions})

@app.route("/results", methods=['GET', 'POST'])
def submit_result():
    if flask.request.method == "POST":
        pass
    else:
        # look in results directory
        results = {}
        for path in glob.glob(os.path.join(config.results_dir,'[!_]*.json')):
            # get name of file and path
            file_name, ext = os.path.splitext(os.path.basename(path))
            with open(path) as result_file:
                results[file_name] = json.load(result_file)
        return flask.jsonify({"results":results})

@app.route("/experiments/")
@app.route("/experiments/<name>")
def get_experiment_list(name=None):
    experiments = {}
    # look for experiments in experiments directory
    for path in glob.glob(os.path.join(config.experiments_dir,'[!_]*.py')):
        # get name of file and path
        file_name, ext = os.path.splitext(os.path.basename(path))
        experiments[file_name] = path

    if name == None:
        return flask.jsonify({"experiments" : experiments.keys()})

    if name in experiments:
        return "Experiment found"
    else:
        return "Experiment not found"

@app.route("/clients/")
@app.route("/clients/<name>")
def get_clients(name=None):
    clients = {}
    with open(config.clients_file) as clients_fh:
        clients = json.load(clients_fh)

    if name == None:
        return flask.jsonify(clients)

    if name in clients:
        return flask.jsonify(client[name])
    else:
        return "Client not found"

if __name__ == "__main__":
    app.run(debug=True)
