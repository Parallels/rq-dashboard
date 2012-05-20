from flask import Flask


app = Flask(__name__)

# Override config
app.config['DEBUG'] = True

# Modules/blueprints
from . import init_app
init_app(app, '')  # register it under '/'
