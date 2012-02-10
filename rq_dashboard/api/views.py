import times
from flask import Blueprint
from . import jsonify
from rq import Queue, Worker


app = Blueprint('api', __name__)

def serialize_queues(queues):
    return [dict(name=q.name, count=q.count) for q in queues]

def serialize_date(dt):
    if dt is None:
        return None
    return times.format(dt, 'Europe/Amsterdam')

def serialize_job(job):
    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        ended_at=serialize_date(job.ended_at),
        origin=job.origin,
        result=job.result,
        exc_info=job.exc_info,
        description=job.description)


@app.route('/queues')
@jsonify
def list_queues():
    queues = serialize_queues(sorted(Queue.all()))
    return dict(queues=queues)


@app.route('/jobs/<queue_name>')
@jsonify
def list_jobs(queue_name):
    queue = Queue(queue_name)
    jobs = [serialize_job(job) for job in queue.jobs]
    return dict(name=queue.name, jobs=jobs)


@app.route('/workers')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = [dict(name=worker.name, queues=serialize_queue_names(worker),
        state=worker.state) for worker in Worker.all()]
    return dict(workers=workers)
