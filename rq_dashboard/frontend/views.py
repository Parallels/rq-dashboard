from flask import Blueprint
from flask import render_template
from rq import Queue


app = Blueprint('frontend', __name__)

@app.route('/')
def overview():
    return render_template('frontend/overview.html', tab='overview')

@app.route('/workers')
def workers():
    return render_template('frontend/workers.html', subtitle='Workers',
            tab='workers')

@app.route('/queue/<queue_name>')
def queue(queue_name):
    queue = Queue(queue_name)
    return render_template('frontend/queue.html', queue=queue,
            subtitle='Queue %s' % queue_name, tab='queue')

@app.route('/stats')
def stats():
    return render_template('skeletons/base.html', subtitle='Stats', tab='stats')
