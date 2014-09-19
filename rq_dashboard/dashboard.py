from redis import Redis
from redis import from_url
from rq import push_connection, pop_connection
from functools import wraps
import times
from flask import Blueprint
from flask import current_app, url_for, abort
from flask import render_template
from rq import Queue, Worker
from rq import cancel_job, requeue_job
from rq import get_failed_queue
from math import ceil


dashboard = Blueprint('rq_dashboard', __name__,
        template_folder='templates',
        static_folder='static',
        )


@dashboard.before_request
def authentication_hook():
    """ Allow the parent app to authenticate user's access to the dashboard
        with it's own auth_handler method that must return True or False
    """
    auth_handler = current_app.extensions['rq-dashboard'].auth_handler
    if auth_handler and not auth_handler():
        abort(401)


@dashboard.before_app_first_request
def setup_rq_connection():
    if current_app.config.get('REDIS_URL'):
        current_app.redis_conn = from_url(current_app.config.get('REDIS_URL'))
    else:
        current_app.redis_conn = Redis(host=current_app.config.get('REDIS_HOST', 'localhost'),
                       port=current_app.config.get('REDIS_PORT', 6379),
                       password=current_app.config.get('REDIS_PASSWORD', None),
                       db=current_app.config.get('REDIS_DB', 0))


@dashboard.before_request
def push_rq_connection():
    push_connection(current_app.redis_conn)


@dashboard.teardown_request
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


def remove_none_values(input_dict):
    return dict([ (k,v) for k,v in input_dict.items() if v is not None ])


def pagination_window(total_items, cur_page, per_page=5, window_size=10):
    all_pages = range(1, int(ceil(total_items / float(per_page))) + 1)
    results = all_pages
    if (window_size >= 1):
        pages_window_start = int(max(0, min(len(all_pages) - window_size, (cur_page-1) - ceil(window_size / 2.0))))
        pages_window_end = int(pages_window_start + window_size)
        result = all_pages[pages_window_start:pages_window_end]
    return result


@dashboard.route('/', defaults={'queue_name': None, 'page': '1'})
@dashboard.route('/<queue_name>', defaults={'page': '1'})
@dashboard.route('/<queue_name>/<page>')
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

    return render_template('rq_dashboard/dashboard.html',
            workers=Worker.all(),
            queue=queue,
            page=page,
            queues=Queue.all(),
            rq_url_prefix=url_for('.overview'))


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


@dashboard.route('/jobs/<queue_name>/<page>.json')
@jsonify
def list_jobs(queue_name, page):
    current_page = int(page)
    queue = Queue(queue_name)
    per_page = 5
    total_items = queue.count
    pages_numbers_in_window = pagination_window(total_items, current_page, per_page)
    pages_in_window = [ dict(number=p, url=url_for('.overview',
        queue_name=queue_name, page=p)) for p in pages_numbers_in_window ]
    last_page = int(ceil(total_items / float(per_page)))

    prev_page = None
    if current_page > 1:
        prev_page = dict(url=url_for('.overview', queue_name=queue_name, page=(current_page-1)))

    next_page = None
    if current_page < last_page:
        next_page = dict(url=url_for('.overview', queue_name=queue_name, page=(current_page+1)))

    pagination = remove_none_values(
        dict(pages_in_window=pages_in_window,
            next_page=next_page,
            prev_page=prev_page))

    offset = (current_page - 1) * per_page
    jobs = [serialize_job(job) for job in queue.get_jobs(offset, per_page)]
    return dict(name=queue.name, jobs=jobs, pagination=pagination)


@dashboard.route('/workers.json')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = [dict(name=worker.name, queues=serialize_queue_names(worker),
        state=worker.get_state()) for worker in Worker.all()]
    return dict(workers=workers)

@dashboard.context_processor
def inject_interval():
    interval = current_app.config.get('RQ_POLL_INTERVAL', 2500)
    return dict(poll_interval=interval)
