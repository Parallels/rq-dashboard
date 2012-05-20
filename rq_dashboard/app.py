from flask import Flask
from rq_dashboard import RQDashboard


app = Flask(__name__)

# Override config
app.config['DEBUG'] = True

RQDashboard(app, '')
