from flask import Blueprint
from flask import render_template
from rq import Queue
from .models import all_queues, all_workers


app = Blueprint('frontend', __name__)

@app.route('/', defaults={'queue_name': 'default'})
@app.route('/<queue_name>')
def overview(queue_name):
    return render_template('frontend/dashboard.html',
            workers=all_workers(),
            queue=Queue(queue_name),
            queues=all_queues())
