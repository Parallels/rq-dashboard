from flask import Flask
from rq import use_redis


app = Flask(__name__)

# Override config
app.config['DEBUG'] = True

# Globally setup RQ
use_redis()

# Modules/blueprints
from . import init_app
init_app(app, '')  # register it under '/'
