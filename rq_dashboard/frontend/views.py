from flask import Blueprint
from flask import render_template
from rq import Queue
from .models import all_queues, all_workers


app = Blueprint('frontend', __name__)


@app.route('/', defaults={'queue_name': None})
@app.route('/<queue_name>')
def overview(queue_name):
    if queue_name is None:
        # Show the failed queue by default if it contains any jobs
        failed = Queue('failed')
        if not failed.is_empty():
            queue = failed
        else:
            queue = Queue()
    else:
        queue = Queue(queue_name)
    return render_template('frontend/dashboard.html',
            workers=all_workers(),
            queue=queue,
            queues=all_queues())
