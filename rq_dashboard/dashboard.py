from redis import Redis
from redis import from_url
from rq import push_connection
from functools import wraps
import times
from flask import Blueprint
from flask import current_app, url_for, abort
from flask import render_template
from rq import Queue, Worker
from rq.queue import FailedQueue
from rq.job import Job
from rq.exceptions import InvalidJobOperationError
from rq import cancel_job, requeue_job
from rq import get_failed_queue
from math import ceil
import re
from ast import literal_eval


dashboard = Blueprint('rq_dashboard', __name__,
        template_folder='templates',
        static_folder='static',
        )


class RqTimeoutQueue(FailedQueue):
    def __init__(self, connection=None):
        Queue.__init__(self, 'timeout', connection=connection)


@dashboard.before_request
def authentication_hook():
    """ Allow the parent app to authenticate user's access to the dashboard
        with it's own auth_handler method that must return True or False
    """
    if current_app.auth_handler and not current_app.auth_handler():
        abort(401)

@dashboard.before_app_first_request
def setup_rq_connection():
    if current_app.config.get('REDIS_URL'):
        redis_conn = from_url(current_app.config.get('REDIS_URL'))
    else:
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
    extra = parse_job(job)

    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        ended_at=serialize_date(job.ended_at),
        started_at=serialize_date(job.meta.get("started_at", None)),
        origin=job.origin,
        result=job._result,
        exc_info=job.exc_info,
        description=job.description,
        meta=job.meta,
        status=job._status,
        name=extra["name"],
        args=extra["args"])


def remove_none_values(input_dict):
    return dict([ (k,v) for k,v in input_dict.iteritems() if v is not None ])


def pagination_window(total_items, cur_page, per_page=5, window_size=10):
    all_pages = range(1, int(ceil(total_items / float(per_page))) + 1)
    results = all_pages
    if (window_size >= 1):
        pages_window_start = int(max(0, min(len(all_pages) - window_size, (cur_page-1) - ceil(window_size / 2.0))))
        pages_window_end = int(pages_window_start + window_size)
        result = all_pages[pages_window_start:pages_window_end]
    return result


def parse_job(job):
  match = re.match(r"start\(u?'([a-zA-Z_\.]+)', (.*)", job.description)
  if match:
    return {"name": match.group(1), "args": match.group(2)}
  else:
    return {"name": job.description, "args": ""}


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
            queues=Queue.all())


@dashboard.route('/job/<job_id>', methods=['GET'])
def job_view(job_id):

    return render_template('rq_dashboard/job.html',
                           job_id=job_id)


@dashboard.route('/job/<job_id>/data.json', methods=['GET'])
@jsonify
def get_one_job(job_id):
    job = Job.fetch(job_id)
    return serialize_job(job)


@dashboard.route('/job/<job_id>/cancel', methods=['POST'])
@jsonify
def cancel_job_view(job_id):
    cancel_job(job_id)
    return dict(status='OK')


@dashboard.route('/job/<job_id>/requeue', methods=['POST'])
@jsonify
def requeue_job_view(job_id):

    # Just try both failed queues... don't care about efficiency for single job retries
    timeout_queue = RqTimeoutQueue()
    failed_queue = get_failed_queue()

    try:
        failed_queue.requeue(job_id)
    except:
        pass
    try:
        timeout_queue.requeue(job_id)
    except:
        pass

    return dict(status='OK')


@dashboard.route('/empty-all-queues', methods=['POST'])
@jsonify
def empty_all_queues():
    for queue in Queue.all():
        queue.empty()
    return dict(status='OK')


@dashboard.route('/queue/<queue_name>/empty', methods=['POST'])
@jsonify
def empty_queue(queue_name):
    q = Queue(queue_name)
    q.empty()
    return dict(status='OK')


@dashboard.route('/queue/<queue_name>/requeue-all', methods=['POST'])
@jsonify
def requeue_queue(queue_name):
    if queue_name == "timeout":
        fq = RqTimeoutQueue()
    else:
        fq = FailedQueue()
    job_ids = fq.job_ids
    count = len(job_ids)
    for job_id in job_ids:
        try:
            fq.requeue(job_id)
        except InvalidJobOperationError:
            print "Job ID %s wasn't on a failed queue?" % job_id
    return dict(status='OK', count=count)


@dashboard.route("/queue/<queue_name>/cancel-all", methods=["POST"])
@jsonify
def cancel_all(queue_name):
  queue = Queue(queue_name)
  count = 0
  for job_id in queue.get_job_ids():
    if Job.exists(job_id, queue.connection):
      cancel_job(job_id)
      count += 1

  return dict(status='OK', count=count)


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
    per_page = current_app.config.get('RQ_DASHBOARD_JOBS_PER_PAGE', 5)
    total_items = queue.count
    pages_numbers_in_window = pagination_window(total_items, current_page, per_page)
    pages_in_window = [dict(number=p, url=url_for('.overview',
                       queue_name=queue_name, page=p)) for p in pages_numbers_in_window]
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
        state=worker.state) for worker in Worker.all()]
    return dict(workers=workers)


@dashboard.context_processor
def inject_config():

    if current_app.config.get('RQ_DASHBOARD_GROUP_WORKERS', False):
        group_workers = "true"
    else:
        group_workers = "false"

    return dict(
        poll_interval=current_app.config.get('RQ_POLL_INTERVAL', 2500),
        show_results=current_app.config.get('RQ_DASHBOARD_SHOW_RESULTS', False),
        show_logs=current_app.config.get('RQ_DASHBOARD_SHOW_LOGS', False),
        heroku_workers=current_app.config.get('RQ_DASHBOARD_HEROKU_WORKERS', False),
        group_workers=group_workers,
        base_url=url_for('.overview')
    )
