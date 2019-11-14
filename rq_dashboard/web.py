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
import os
import re
from functools import wraps
from math import ceil

import arrow
from flask import (Blueprint, current_app, make_response, render_template,
                   send_from_directory, url_for)
from redis import Redis, from_url
from redis.sentinel import Sentinel
from rq import VERSION as rq_version
from rq import (Queue, Worker, cancel_job, pop_connection, push_connection,
                requeue_job)
from rq.job import Job
from rq.registry import (DeferredJobRegistry, FailedJobRegistry,
                         FinishedJobRegistry, StartedJobRegistry)
from six import string_types

from .legacy_config import upgrade_config
from .version import VERSION as rq_dashboard_version

blueprint = Blueprint(
    'rq_dashboard',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.before_app_first_request
def setup_rq_connection():
    # It's the only place where we can safely define default value for web background
    # since It is used in template
    current_app.config.setdefault('RQ_DASHBOARD_WEB_BACKGROUND', 'black')
    # we need to do It here instead of cli, since It may be embeded
    upgrade_config(current_app)
    # Getting Redis connection parameters for RQ
    redis_url = current_app.config.get('RQ_DASHBOARD_REDIS_URL')
    redis_sentinels = current_app.config.get('RQ_DASHBOARD_REDIS_SENTINELS')
    if isinstance(redis_url, list):
        current_app.redis_conn = from_url(redis_url[0])
    elif isinstance(redis_url, string_types):
        current_app.redis_conn = from_url(redis_url)
    elif redis_sentinels:
        redis_master = current_app.config.get('RQ_DASHBOARD_REDIS_MASTER_NAME')
        password = current_app.config.get('RQ_DASHBOARD_REDIS_PASSWORD')
        db = current_app.config.get('RQ_DASHBOARD_REDIS_DB')
        sentinel_hosts = [tuple(sentinel.split(':', 1))
                          for sentinel in redis_sentinels.split(',')]

        sentinel = Sentinel(sentinel_hosts, db=db, password=password)
        current_app.redis_conn = sentinel.master_for(redis_master)
    else:
        current_app.redis_conn = Redis(
            host=current_app.config.get('RQ_DASHBOARD_REDIS_HOST', 'localhost'),
            port=current_app.config.get('RQ_DASHBOARD_REDIS_PORT', 6379),
            password=current_app.config.get('RQ_DASHBOARD_REDIS_PASSWORD'),
            db=current_app.config.get('RQ_DASHBOARD_REDIS_DB', 0),
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
        result_dict = f(*args, **kwargs)
        return flask_jsonify(**result_dict), {'Cache-Control': 'no-store'}

    return _wrapped


def serialize_queues(queues):
    return [
        dict(
            name=q.name,
            count=q.count,
            queued_url=url_for('.jobs_overview', queue_name=q.name),
            failed_job_registry_count=FailedJobRegistry(q.name).count,
            failed_url=url_for('.jobs_overview', queue_name=q.name, registry_name='failed'),
            started_job_registry_count=StartedJobRegistry(q.name).count,
            started_url=url_for('.jobs_overview', queue_name=q.name, registry_name='started'),
            deferred_job_registry_count=DeferredJobRegistry(q.name).count,
            deferred_url=url_for('.jobs_overview', queue_name=q.name, registry_name='deferred'),
            finished_job_registry_count=FinishedJobRegistry(q.name).count,
            finished_url=url_for('.jobs_overview', queue_name=q.name, registry_name='finished'),
        )
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


def pagination_window(total_items, cur_page, per_page, window_size=10):
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


@blueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(blueprint.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def get_queue_registry_jobs_count(queue_name, registry_name, offset, per_page):
    queue = Queue(queue_name)
    if registry_name != 'queued':
        if per_page >= 0:
            per_page = offset + (per_page - 1)

        if registry_name == 'failed':
            current_queue = FailedJobRegistry(queue_name)
        elif registry_name == 'deferred':
            current_queue = DeferredJobRegistry(queue_name)
        elif registry_name == 'started':
            current_queue = StartedJobRegistry(queue_name)
        elif registry_name == 'finished':
            current_queue = FinishedJobRegistry(queue_name)
    else:
        current_queue = queue
    total_items = current_queue.count

    job_ids = current_queue.get_job_ids(offset, per_page)
    current_queue_jobs = [queue.fetch_job(job_id) for job_id in job_ids]
    jobs = [serialize_job(job) for job in current_queue_jobs]

    return(total_items, jobs)


@blueprint.route('/')
@blueprint.route('/view')
@blueprint.route('/view/queues')
def queues_overview():
    r = make_response(render_template(
        'rq_dashboard/queues.html',
        queues=Queue.all(),
        rq_url_prefix='/',
        rq_dashboard_version=rq_dashboard_version,
        rq_version=rq_version,
        active_tab='queues',
    ))
    r.headers.set('Cache-Control', 'no-store')
    return r


@blueprint.route('/view/workers')
def workers_overview():
    r = make_response(render_template(
        'rq_dashboard/workers.html',
        workers=Worker.all(),
        rq_url_prefix='/',
        rq_dashboard_version=rq_dashboard_version,
        rq_version=rq_version,
        active_tab='workers',
    ))
    r.headers.set('Cache-Control', 'no-store')
    return r


@blueprint.route('/view/jobs', defaults={'queue_name': None, 'registry_name': 'queued', 'per_page': '8', 'page': '1'})
@blueprint.route('/view/jobs/<queue_name>', defaults={'registry_name': 'queued', 'per_page': '8', 'page': '1'})
@blueprint.route('/view/jobs/<queue_name>/<registry_name>', defaults={'per_page': '8', 'page': '1'})
@blueprint.route('/view/jobs/<queue_name>/<registry_name>/<int:per_page>', defaults={'page': '1'})
@blueprint.route('/view/jobs/<queue_name>/<registry_name>/<int:per_page>/<int:page>')
def jobs_overview(queue_name, registry_name, per_page, page):
    if queue_name is None:
        queue = Queue()
    else:
        queue = Queue(queue_name)
    r = make_response(render_template(
        'rq_dashboard/jobs.html',
        queues=Queue.all(),
        queue=queue,
        per_page=per_page,
        page=page,
        registry_name=registry_name,
        rq_url_prefix='/',
        rq_dashboard_version=rq_dashboard_version,
        rq_version=rq_version,
        active_tab='jobs',
    ))
    r.headers.set('Cache-Control', 'no-store')
    return r


@blueprint.route('/job/<job_id>/cancel', methods=['POST'])
@jsonify
def cancel_job_view(job_id):
    job = Job.fetch(job_id)
    if job.is_queued:
        if current_app.config.get('RQ_DASHBOARD_DELETE_JOBS', False):
            job.delete()
        else:
            cancel_job(job_id)
    else:
        job.delete()
    return dict(status='OK')


@blueprint.route('/job/<job_id>/requeue', methods=['POST'])
@jsonify
def requeue_job_view(job_id):
    requeue_job(job_id, connection=current_app.redis_conn)
    return dict(status='OK')


@blueprint.route('/requeue/<queue_name>', methods=['GET', 'POST'])
@jsonify
def requeue_all(queue_name):
    fq = Queue(queue_name).failed_job_registry
    job_ids = fq.get_job_ids()
    count = len(job_ids)
    for job_id in job_ids:
        requeue_job(job_id, connection=current_app.redis_conn)
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
    redis_url = current_app.config.get('RQ_DASHBOARD_REDIS_URL')
    if not isinstance(redis_url, list):
        return dict(status='Single RQ. Not Permitted.')
    if int(instance_number) >= len(redis_url):
        raise LookupError('Index exceeds RQ list. Not Permitted.')
    pop_connection()
    current_app.redis_conn = from_url(redis_url[int(instance_number)])
    push_rq_connection()
    return dict(status='OK')


@blueprint.route('/data/rq-instances.json')
@jsonify
def list_instances():
    redis_url = current_app.config.get('RQ_DASHBOARD_REDIS_URL')
    if isinstance(redis_url, list):
        return dict(
            rq_instances=[re.sub(r'://:[^@]*@', '://:***@', x) for x in redis_url],
        )
    elif isinstance(redis_url, string_types):
        return dict(
            rq_instances=[re.sub(r'://:[^@]*@', '://:***@', redis_url)],
        )
    else:
        # TODO handle case when configuration is not in form of URL
        return dict(rq_instances=[])


@blueprint.route('/data/queues.json')
@jsonify
def list_queues():
    queues = serialize_queues(sorted(Queue.all()))
    return dict(queues=queues)


@blueprint.route('/data/jobs/<queue_name>/<registry_name>/<per_page>/<page>.json')
@jsonify
def list_jobs(queue_name, registry_name, per_page, page):
    current_page = int(page)
    per_page = int(per_page)
    offset = (current_page - 1) * per_page
    total_items, jobs = get_queue_registry_jobs_count(queue_name, registry_name, offset, per_page)

    pages_numbers_in_window = pagination_window(
        total_items, current_page, per_page)
    pages_in_window = [
        dict(number=p, url=url_for('.jobs_overview', queue_name=queue_name,
             registry_name=registry_name, per_page=per_page, page=p))
        for p in pages_numbers_in_window
    ]
    last_page = int(ceil(total_items / float(per_page)))

    prev_page = None
    if current_page > 1:
        prev_page = dict(url=url_for(
            '.jobs_overview', queue_name=queue_name,
            registry_name=registry_name, per_page=per_page, page=(current_page - 1)))

    next_page = None
    if current_page < last_page:
        next_page = dict(url=url_for(
            '.jobs_overview', queue_name=queue_name,
            registry_name=registry_name, per_page=per_page, page=(current_page + 1)))

    first_page_link = dict(url=url_for('.jobs_overview', queue_name=queue_name,
                                       registry_name=registry_name, per_page=per_page, page=1))
    last_page_link = dict(url=url_for('.jobs_overview', queue_name=queue_name,
                                      registry_name=registry_name, per_page=per_page, page=last_page))

    pagination = remove_none_values(
        dict(
            current_page=current_page,
            num_pages=last_page,
            pages_in_window=pages_in_window,
            next_page=next_page,
            prev_page=prev_page,
            first_page=first_page_link,
            last_page=last_page_link,
        )
    )

    return dict(name=queue_name, registry_name=registry_name, jobs=jobs, pagination=pagination)


def serialize_current_job(job):
    if job is None:
        return "idle"
    return dict(
        job_id=job.id,
        description=job.description,
        created_at=serialize_date(job.created_at)
    )


@blueprint.route('/data/workers.json')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]
    workers = sorted((
        dict(
            name=worker.name,
            queues=serialize_queue_names(worker),
            state=str(worker.get_state()),
            current_job=serialize_current_job(worker.get_current_job()),
            version=getattr(worker, 'version', ''),
            python_version=getattr(worker, 'python_version', '')
        )
        for worker in Worker.all()),
        key=lambda w: (w['state'], w['queues'], w['name']))
    return dict(workers=workers)


@blueprint.context_processor
def inject_interval():
    interval = current_app.config.get('RQ_DASHBOARD_POLL_INTERVAL', 2500)
    return dict(poll_interval=interval)
