from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('default_config')
app.config.from_envvar('DROP_SETTINGS', silent=True)
db = SQLAlchemy(app)
config = app.config
