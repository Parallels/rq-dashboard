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
from math import ceil

from flask import Blueprint, current_app, render_template, url_for
from redis import Redis, from_url
from rq import (Queue, Worker, cancel_job, get_failed_queue, pop_connection,
                push_connection, requeue_job)

from .utils import (jsonify, remove_none_values, pagination_window,
                    serialize_queues, serialize_job)

blueprint = Blueprint(
    'rq_dashboard',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.before_app_first_request
def setup_rq_connection():
    redis_url = current_app.config.get('REDIS_URL')
    if redis_url:
        current_app.redis_conn = from_url(redis_url)
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
    per_page = 5
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


@blueprint.route('/workers.json')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = [
        dict(
            name=worker.name,
            queues=serialize_queue_names(worker),
            state=worker.get_state()
        )
        for worker in Worker.all()
    ]
    return dict(workers=workers)


@blueprint.context_processor
def inject_interval():
    interval = current_app.config.get('RQ_POLL_INTERVAL')
    return dict(poll_interval=interval)
