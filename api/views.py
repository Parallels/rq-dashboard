from flask import Blueprint
from . import jsonify
from rq import Queue, Worker


app = Blueprint('api', __name__)

def serialize_queues(queues):
    return [dict(name=q.name, count=q.count) for q in queues]

@app.route('/queues')
@jsonify
def list_queues():
    queues = serialize_queues(sorted(Queue.all()))
    return dict(queues=queues)

@app.route('/workers')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = [dict(name=worker.name, queues=serialize_queue_names(worker),
        state=worker.state) for worker in Worker.all()]
    return dict(workers=workers)
