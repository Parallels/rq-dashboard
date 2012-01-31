from flask import Blueprint
from . import jsonify
from rq import Queue


app = Blueprint('api', __name__)

@app.route('/queues')
@jsonify
def list_queues():
    import random
    queues = [dict(name=q.name, count=random.randint(0, 59)) for q in sorted(Queue.all())]
    return dict(queues=queues)
