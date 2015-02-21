import flask
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.sqlalchemy import SQLAlchemy
# local imports (from centinel-server package)
import config

app = flask.Flask("Centinel")
app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI


auth = HTTPBasicAuth()
db = SQLAlchemy(app);
