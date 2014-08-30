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
        results = []
        for path in glob.glob(os.path.join(config.results_dir,'[!_]*.json')):
            results.append(path)
        return flask.jsonify({"result_files":results})

@app.route("/experiments/")
@app.route("/experiments/<name>")
def get_experiment_list(name=None):
    experiments = {}

    for path in glob.glob(os.path.join(config.experiments_dir,'[!_]*.py')):
        # get name of file and path
        file_name, ext = os.path.splitext(os.path.basename(path))
        experiments[file_name] = path

    if name in experiments:
        return "Experiment found"
    else:
        return flask.jsonify({"experiments" : experiments.keys()})

@app.route("/clients/")
@app.route("/clients/<name>")
def get_clients(name=None):
    clients = {}
    with open(config.clients_file) as clients_fh:
        clients = json.load(clients_fh)

    if name not in clients:
        return flask.jsonify(clients)
    else:
        return flask.jsonify(client[name])
        
    
if __name__ == "__main__":
    app.run(debug=True)
