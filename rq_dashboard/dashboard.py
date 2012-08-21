from redis import Redis
from rq import push_connection
from functools import wraps
import times
from flask import Blueprint
from flask import current_app, url_for
from flask import render_template
from rq import Queue, Worker
from rq import cancel_job, requeue_job
from rq import get_failed_queue


dashboard = Blueprint('rq_dashboard', __name__,
        template_folder='templates',
        static_folder='static',
        )


@dashboard.before_app_first_request
def setup_rq_connection():
    redis_conn = Redis(host=current_app.config.get('REDIS_HOST', 'localhost'),
                       port=current_app.config.get('REDIS_PORT', 6379),
                       password=current_app.config.get('REDIS_PASSWORD', None),
                       db=current_app.config.get('REDIS_DB', 0))
    push_connection(redis_conn)


def jsonify(f):
    @wraps(f)
    def _wrapped(*args, **kwargs):
        from flask import jsonify as flask_jsonify
        try:
            result_dict = f(*args, **kwargs)
        except Exception as e:
            result_dict = dict(status='error')
            if current_app.config['DEBUG']:
                result_dict['reason'] = e.message
                from traceback import format_exc
                result_dict['exc_info'] = format_exc(e)
        return flask_jsonify(**result_dict)
    return _wrapped


def serialize_queues(queues):
    return [dict(name=q.name, count=q.count, url=url_for('.overview',
        queue_name=q.name)) for q in queues]


def serialize_date(dt):
    if dt is None:
        return None
    return times.format(dt, 'UTC')


def serialize_job(job):
    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        ended_at=serialize_date(job.ended_at),
        origin=job.origin,
        result=job._result,
        exc_info=job.exc_info,
        description=job.description)


@dashboard.route('/', defaults={'queue_name': None})
@dashboard.route('/<queue_name>')
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

    return render_template('rq_dashboard/dashboard.html',
            workers=Worker.all(),
            queue=queue,
            queues=Queue.all())


@dashboard.route('/job/<job_id>/cancel', methods=['POST'])
@jsonify
def cancel_job_view(job_id):
    cancel_job(job_id)
    return dict(status='OK')


@dashboard.route('/job/<job_id>/requeue', methods=['POST'])
@jsonify
def requeue_job_view(job_id):
    requeue_job(job_id)
    return dict(status='OK')


@dashboard.route('/requeue-all', methods=['GET', 'POST'])
@jsonify
def requeue_all():
    fq = get_failed_queue()
    job_ids = fq.job_ids
    count = len(job_ids)
    for job_id in job_ids:
        requeue_job(job_id)
    return dict(status='OK', count=count)


@dashboard.route('/queue/<queue_name>/empty', methods=['POST'])
@jsonify
def empty_queue(queue_name):
    q = Queue(queue_name)
    q.empty()
    return dict(status='OK')


@dashboard.route('/queue/<queue_name>/compact', methods=['POST'])
@jsonify
def compact_queue(queue_name):
    q = Queue(queue_name)
    q.compact()
    return dict(status='OK')


@dashboard.route('/queues.json')
@jsonify
def list_queues():
    queues = serialize_queues(sorted(Queue.all()))
    return dict(queues=queues)


@dashboard.route('/jobs/<queue_name>.json')
@jsonify
def list_jobs(queue_name):
    queue = Queue(queue_name)
    jobs = [serialize_job(job) for job in queue.jobs]
    return dict(name=queue.name, jobs=jobs)


@dashboard.route('/workers.json')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = [dict(name=worker.name, queues=serialize_queue_names(worker),
        state=worker.state) for worker in Worker.all()]
    return dict(workers=workers)
