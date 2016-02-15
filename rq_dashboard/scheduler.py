from collections import Counter
from math import ceil

from flask import Blueprint, current_app, render_template, url_for
from redis import Redis, from_url
from rq import Queue, pop_connection, push_connection
from rq_scheduler import Scheduler

from .utils import (jsonify, remove_none_values, pagination_window,
                    serialize_job)


blueprint = Blueprint(
    'rq_scheduler_dashboard',
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


@blueprint.context_processor
def inject_interval():
    interval = current_app.config.get('RQ_POLL_INTERVAL')
    return dict(poll_interval=interval)


@blueprint.route('/', defaults={'queue_name': None, 'page': '1'})
@blueprint.route('/<queue_name>', defaults={'page': '1'})
@blueprint.route('/<queue_name>/<page>')
def overview(queue_name, page):
    queue = Queue()
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
        'rq_dashboard/scheduler_dashboard.html',
        queue=queue,
        page=page,
        queues=Queue.all(),
        rq_url_prefix=url_for('.overview')
    )


@blueprint.route('/jobs/<queue_name>/<page>.json')
@jsonify
def list_jobs(queue_name, page):
    current_page = int(page)

    scheduler = Scheduler(queue_name)
    jobs = scheduler.get_jobs(with_times=True)
    if queue_name:
        jobs = filter(lambda (job, _): job.origin == queue_name, jobs)

    per_page = 5
    total_items = len(jobs)
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

    # scheduler.get_jobs(with_times=True)]
    offset = (current_page - 1) * per_page
    job_page = jobs[offset:offset+per_page]
    job_page = [serialize_job(job, at) for (job, at) in job_page]
    return dict(name=queue_name, jobs=job_page, pagination=pagination)


@blueprint.route('/queues.json')
@jsonify
def list_queues():
    queues = Counter(job.origin for job in Scheduler().get_jobs())
    return dict(
        queues=[
            dict(
                name=queue_name,
                count=count,
                url=url_for('.overview', queue_name=queue_name),
            )
            for queue_name, count in queues.items()
        ]
    )


@blueprint.route('/status.json')
@jsonify
def scheduler_status():
    scheduler = Scheduler()
    return dict(
        running=(
            scheduler.connection.exists(scheduler.scheduler_key) and
            not scheduler.connection.hexists(scheduler.scheduler_key, 'death')
        )
    )


@blueprint.route('/job/<job_id>/cancel', methods=['POST'])
@jsonify
def cancel_job_view(job_id):
    scheduler = Scheduler()
    scheduler.cancel(job_id)
    return dict(status='OK')


@blueprint.route('/<queue_name>/cancel-all', methods=['GET', 'POST'])
@jsonify
def cancel_all(queue_name):
    scheduler = Scheduler()
    for job in scheduler.get_jobs():
        if job.origin == queue_name:
            scheduler.cancel(job)

    return dict(status='OK')
