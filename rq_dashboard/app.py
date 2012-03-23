from flask import Flask
from redis import Redis
from rq import use_connection


app = Flask(__name__)

# Override config
app.config['DEBUG'] = True

# Globally setup RQ
use_connection(Redis())

# Modules/blueprints
from . import init_app
init_app(app, '')  # register it under '/'
