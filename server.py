import config
import flask

app = flask.Flask(__name__)

@app.route("/versions")
def get_recommended_versions():
    return flask.jsonify({"versions" : config.recommended_versions})

@app.route("/results", method=['POST']):
def submit_result():
    if request.method == "POST":
        pass

if __name__ == "__main__":
    app.run(debug=True)
