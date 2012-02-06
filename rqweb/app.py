from flask import Flask
from redis import Redis
from rq import conn

app = Flask(__name__)
redis_conn = Redis()

# Override config
app.config['DEBUG'] = True
app.config['REDIS_CONNECTION'] = redis_conn

# Globally setup RQ
conn.push(redis_conn)

# Modules/blueprints
import api.views, frontend.views
app.register_blueprint(api.views.app, url_prefix='/api')
app.register_blueprint(frontend.views.app)
