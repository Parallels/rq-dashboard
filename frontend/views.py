from flask import Blueprint
from flask import render_template


app = Blueprint('frontend', __name__)

@app.route('/')
def overview():
    return render_template('frontend/overview.html', tab='overview')

@app.route('/workers')
def workers():
    return render_template('frontend/workers.html', subtitle='Workers',
            tab='workers')

@app.route('/queues')
def queues():
    return render_template('frontend/queues.html', subtitle='Queues',
            tab='queues')

@app.route('/stats')
def stats():
    return render_template('skeletons/base.html', subtitle='Stats', tab='stats')
