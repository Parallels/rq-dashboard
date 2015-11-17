from collections import Counter
from functools import wraps
from math import ceil

import arrow
from flask import Blueprint, current_app, render_template, url_for
from redis import Redis, from_url
from rq import Queue, Worker, pop_connection, push_connection
from rq_scheduler import Scheduler


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


def remove_none_values(input_dict):
    return {k: v for (k, v) in input_dict.items() if v is not None}


def serialize_date(dt):
    if dt is None:
        return None
    return arrow.get(dt).to('UTC').datetime.isoformat()


def serialize_job(job, scheduled_for=None):
    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        scheduled_for=serialize_date(scheduled_for) if scheduled_for else None,
        ended_at=serialize_date(job.ended_at),
        origin=job.origin,
        result=job._result,
        exc_info=job.exc_info,
        description=job.description)


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
