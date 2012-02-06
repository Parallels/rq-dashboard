from flask import Blueprint
from flask import render_template
from rq import Queue
from .models import all_queues, all_workers


app = Blueprint('frontend', __name__)

@app.route('/')
def overview():
    return render_template('frontend/overview.html',
            workers=all_workers(),
            queue=Queue(),
            queues=all_queues())

@app.route('/stats')
def stats():
    return render_template('skeletons/base.html', subtitle='Stats', tab='stats')
