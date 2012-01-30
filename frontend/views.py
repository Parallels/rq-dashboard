from flask import Blueprint
from flask import render_template


app = Blueprint('frontend', __name__)

@app.route('/')
def index():
    return render_template('base.html')
