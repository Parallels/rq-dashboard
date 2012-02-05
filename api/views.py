import times
from flask import Blueprint
from . import jsonify
from rq import Queue, Worker
from rq.job import Job
from rq.exceptions import UnpickleError


app = Blueprint('api', __name__)

def serialize_queues(queues):
    return [dict(name=q.name, count=q.count) for q in queues]

def serialize_date(dt):
    return times.format(dt, 'Europe/Amsterdam')

def serialize_job(job):
    return dict(
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        origin=job.origin,
        exc_info=job.exc_info,
        description=job.call_string)


@app.route('/queues')
@jsonify
def list_queues():
    queues = serialize_queues(sorted(Queue.all()))
    return dict(queues=queues)


@app.route('/jobs/<queue_name>')
@jsonify
def list_jobs(queue_name):
    queue = Queue(queue_name)
    messages = queue.messages
    jobs = []
    for msg in messages:
        try:
            job = Job.unpickle(msg)
            jobs.append(serialize_job(job))
        except UnpickleError as e:
            jobs.append(dict(
                error='Unknown or unreadable job.',
                exc_info=unicode(e)
                ))

    return dict(name=queue.name, jobs=jobs)


@app.route('/workers')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = [dict(name=worker.name, queues=serialize_queue_names(worker),
        state=worker.state) for worker in Worker.all()]
    return dict(workers=workers)
