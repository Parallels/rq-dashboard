from flask import Blueprint
from . import jsonify
from rq import Queue


app = Blueprint('api', __name__)

@app.route('/queues')
@jsonify
def list_queues():
    queues = [dict(name=q.name, count=q.count) for q in Queue.all()]
    return dict(queues=queues)
