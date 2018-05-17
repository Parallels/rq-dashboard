"""RQ Dashboard Flask Blueprint.

Uses the standard Flask configuration mechanism e.g. to set the connection
parameters to REDIS. To keep the documentation and defaults all in once place
the default settings must be loaded from ``rq_dashboard.default_settings``
e.g.  as done in ``cli.py``.

RQ Dashboard does not contain any built-in authentication mechanism because

    1. it is the responsbility of the wider hosting app rather than a
       particular blueprint, and

    2. there are numerous ways of adding security orthogonally.

As a quick-and-dirty convenience, the command line invocation in ``cli.py``
provides the option to require HTTP Basic Auth in a few lines of code.

"""
from functools import wraps
from math import ceil

import arrow
from redis import Redis, from_url
from redis.sentinel import Sentinel
from rq import (Queue, Worker, cancel_job, get_failed_queue, pop_connection,
                push_connection, requeue_job)
from rq.job import Job
from six import string_types

from flask import Blueprint, current_app, render_template, url_for

blueprint = Blueprint(
    'rq_dashboard',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.before_app_first_request
def setup_rq_connection():
    redis_url = current_app.config.get('REDIS_URL')
    redis_sentinels = current_app.config.get('REDIS_SENTINELS')
    if isinstance(redis_url, list):
        current_app.redis_conn = from_url(redis_url[0])
    elif isinstance(redis_url, string_types):
        current_app.redis_conn = from_url(redis_url)
    elif redis_sentinels:
        redis_master = current_app.config.get('REDIS_MASTER_NAME')
        password = current_app.config.get('REDIS_PASSWORD')
        db = current_app.config.get('REDIS_DB')
        sentinel_hosts = [tuple(sentinel.split(':', 1))
                          for sentinel in redis_sentinels.split(',')]

        sentinel = Sentinel(sentinel_hosts, db=db, password=password)
        current_app.redis_conn = sentinel.master_for(redis_master)
    else:
        current_app.redis_conn = Redis(
            host=current_app.config.get('REDIS_HOST'),
            port=current_app.config.get('REDIS_PORT'),
            password=current_app.config.get('REDIS_PASSWORD'),
            db=current_app.config.get('REDIS_DB')
        )


@blueprint.before_request
def push_rq_connection():
    push_connection(current_app.redis_conn)


@blueprint.teardown_request
def pop_rq_connection(exception=None):
    pop_connection()


def jsonify(f):
    @wraps(f)
    def _wrapped(*args, **kwargs):
        from flask import jsonify as flask_jsonify
        try:
            result_dict = f(*args, **kwargs)
        except Exception as e:
            result_dict = dict(status='error')
            if current_app.config['DEBUG']:
                result_dict['reason'] = str(e)
                from traceback import format_exc
                result_dict['exc_info'] = format_exc()
        return flask_jsonify(**result_dict)

    return _wrapped


def serialize_queues(queues):
    return [
        dict(
            name=q.name,
            count=q.count,
            url=url_for('.overview', queue_name=q.name))
        for q in queues
    ]


def serialize_date(dt):
    if dt is None:
        return None
    return arrow.get(dt).to('UTC').datetime.isoformat()


def serialize_job(job):
    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        ended_at=serialize_date(job.ended_at),
        origin=job.origin,
        result=job._result,
        exc_info=str(job.exc_info) if job.exc_info else None,
        description=job.description)


def remove_none_values(input_dict):
    return dict(((k, v) for k, v in input_dict.items() if v is not None))


def pagination_window(total_items, cur_page, per_page=5, window_size=10):
    all_pages = range(1, int(ceil(total_items / float(per_page))) + 1)
    result = all_pages
    if window_size >= 1:
        temp = min(
            len(all_pages) - window_size,
            (cur_page - 1) - int(ceil(window_size / 2.0))
        )
        pages_window_start = max(0, temp)
        pages_window_end = pages_window_start + window_size
        result = all_pages[pages_window_start:pages_window_end]
    return result


@blueprint.route('/', defaults={'queue_name': None, 'page': '1'})
@blueprint.route('/<queue_name>', defaults={'page': '1'})
@blueprint.route('/<queue_name>/<page>')
def overview(queue_name, page):
    if queue_name is None:
        # Show the failed queue by default if it contains any jobs
        failed = Queue('failed')
        if not failed.is_empty():
            queue = failed
        else:
            queue = Queue()
    else:
        queue = Queue(queue_name)

    return render_template(
        'rq_dashboard/dashboard.html',
        workers=Worker.all(),
        queue=queue,
        page=page,
        queues=Queue.all(),
        rq_url_prefix=url_for('.overview')
    )


@blueprint.route('/job/<job_id>/cancel', methods=['POST'])
@jsonify
def cancel_job_view(job_id):
    if current_app.config.get('DELETE_JOBS'):
        Job.fetch(job_id).delete()
    else:
        cancel_job(job_id)
    return dict(status='OK')


@blueprint.route('/job/<job_id>/requeue', methods=['POST'])
@jsonify
def requeue_job_view(job_id):
    requeue_job(job_id)
    return dict(status='OK')


@blueprint.route('/requeue-all', methods=['GET', 'POST'])
@jsonify
def requeue_all():
    fq = get_failed_queue()
    job_ids = fq.job_ids
    count = len(job_ids)
    for job_id in job_ids:
        requeue_job(job_id)
    return dict(status='OK', count=count)


@blueprint.route('/queue/<queue_name>/empty', methods=['POST'])
@jsonify
def empty_queue(queue_name):
    q = Queue(queue_name)
    q.empty()
    return dict(status='OK')


@blueprint.route('/queue/<queue_name>/compact', methods=['POST'])
@jsonify
def compact_queue(queue_name):
    q = Queue(queue_name)
    q.compact()
    return dict(status='OK')


@blueprint.route('/rq-instance/<instance_number>', methods=['POST'])
@jsonify
def change_rq_instance(instance_number):
    redis_url = current_app.config.get('REDIS_URL')
    if not isinstance(redis_url, list):
        return dict(status='Single RQ. Not Permitted.')
    if int(instance_number) >= len(redis_url):
        raise LookupError('Index exceeds RQ list. Not Permitted.')
    pop_connection()
    current_app.redis_conn = from_url(redis_url[int(instance_number)])
    push_rq_connection()
    return dict(status='OK')


@blueprint.route('/rq-instances.json')
@jsonify
def list_instances():
    return dict(rq_instances=current_app.config.get('REDIS_URL'))


@blueprint.route('/queues.json')
@jsonify
def list_queues():
    queues = serialize_queues(sorted(Queue.all()))
    return dict(queues=queues)


@blueprint.route('/jobs/<queue_name>/<page>.json')
@jsonify
def list_jobs(queue_name, page):
    current_page = int(page)
    queue = Queue(queue_name)
    per_page = 10
    total_items = queue.count
    pages_numbers_in_window = pagination_window(
        total_items, current_page, per_page)
    pages_in_window = [
        dict(number=p, url=url_for('.overview', queue_name=queue_name, page=p))
        for p in pages_numbers_in_window
    ]
    last_page = int(ceil(total_items / float(per_page)))

    prev_page = None
    if current_page > 1:
        prev_page = dict(url=url_for(
            '.overview', queue_name=queue_name, page=(current_page - 1)))

    next_page = None
    if current_page < last_page:
        next_page = dict(url=url_for(
            '.overview', queue_name=queue_name, page=(current_page + 1)))

    pagination = remove_none_values(
        dict(
            pages_in_window=pages_in_window,
            next_page=next_page,
            prev_page=prev_page
        )
    )

    offset = (current_page - 1) * per_page
    jobs = [serialize_job(job) for job in queue.get_jobs(offset, per_page)]
    return dict(name=queue.name, jobs=jobs, pagination=pagination)


def serialize_current_job(job):
    if job is None:
        return "idle"
    return dict(
        job_id=job.id,
        description=job.description,
        created_at=serialize_date(job.created_at)
    )


@blueprint.route('/workers.json')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = [
        dict(
            name=worker.name,
            queues=serialize_queue_names(worker),
            state=str(worker.get_state()),
            current_job=serialize_current_job(
                worker.get_current_job()),
        )
        for worker in Worker.all()
    ]
    return dict(workers=workers)


@blueprint.context_processor
def inject_interval():
    interval = current_app.config.get('RQ_POLL_INTERVAL')
    return dict(poll_interval=interval)
