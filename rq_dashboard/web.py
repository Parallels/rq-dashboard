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
import json
import os
import re
from functools import wraps
from math import ceil

import arrow
from flask import (
    Blueprint,
    current_app,
    make_response,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from redis.exceptions import ConnectionError as RedisConnectionError
from redis_sentinel_url import connect as from_url
from rq import (
    VERSION as rq_version,
    Queue,
    Worker,
    requeue_job,
)
from rq.exceptions import NoSuchJobError
from rq.job import Job
from rq.registry import (
    DeferredJobRegistry,
    FailedJobRegistry,
    FinishedJobRegistry,
    StartedJobRegistry,
    ScheduledJobRegistry,
    CanceledJobRegistry,

)
from six import string_types

from .legacy_config import upgrade_config
from .version import VERSION as rq_dashboard_version

from rq.serializers import DefaultSerializer


blueprint = Blueprint(
    "rq_dashboard", __name__, template_folder="templates", static_folder="static",
)

class Config:
    serializer = DefaultSerializer

config: Config = Config()

# @blueprint.before_app_first_request
def setup_rq_connection(current_app):
    # we need to do It here instead of cli, since It may be embeded
    upgrade_config(current_app)
    # Getting Redis connection parameters for RQ
    redis_url = current_app.config.get("RQ_DASHBOARD_REDIS_URL")
    if isinstance(redis_url, string_types):
        current_app.config["RQ_DASHBOARD_REDIS_URL"] = (redis_url,)
        _, current_app.redis_conn = from_url((redis_url,)[0])
    elif isinstance(redis_url, (tuple, list)):
        _, current_app.redis_conn = from_url(redis_url[0])
    else:
        raise RuntimeError("No Redis configuration!")


@blueprint.before_request
def push_rq_connection():
    new_instance_number = request.view_args.get("instance_number")
    if new_instance_number is not None:
        redis_url = current_app.config.get("RQ_DASHBOARD_REDIS_URL")
        if new_instance_number < len(redis_url):
            _, new_instance = from_url(redis_url[new_instance_number])
        else:
            raise LookupError("Index exceeds RQ list. Not Permitted.")
    else:
        new_instance = current_app.redis_conn
    
    current_app.redis_conn = new_instance





def jsonify(f):
    @wraps(f)
    def _wrapped(*args, **kwargs):
        from flask import jsonify as flask_jsonify

        result_dict = f(*args, **kwargs)
        return flask_jsonify(**result_dict), {"Cache-Control": "no-store"}

    return _wrapped

def check_delete_enable(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_app.config.get("RQ_DASHBOARD_DISABLE_DELETE"):
            return dict(status="DISABLED")
        return f(*args, **kwargs)
    return wrapper

def serialize_queues(instance_number, queues):
    return [
        dict(
            name=q.name,
            count=q.count,
            queued_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="queued",
                per_page="8",
                order="asc",
                page="1",
            ),
            failed_job_registry_count=FailedJobRegistry(q.name, connection=q.connection).count,
            failed_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="failed",
                per_page="8",
                order="asc",
                page="1",
            ),
            started_job_registry_count=StartedJobRegistry(q.name, connection=q.connection).count,
            started_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="started",
                per_page="8",
                order="asc",
                page="1",
            ),
            deferred_job_registry_count=DeferredJobRegistry(q.name, connection=q.connection).count,
            deferred_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="deferred",
                per_page="8",
                order="asc",
                page="1",
            ),
            finished_job_registry_count=FinishedJobRegistry(q.name, connection=q.connection).count,
            finished_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="finished",
                per_page="8",
                order="asc",
                page="1",
            ),
            canceled_job_registry_count=CanceledJobRegistry(q.name, connection=q.connection).count,
            canceled_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="canceled",
                per_page="8",
                order="asc",
                page="1",
            ),
            scheduled_job_registry_count=ScheduledJobRegistry(q.name, connection=q.connection).count,
            scheduled_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="scheduled",
                per_page="8",
                order="asc",
                page="1",
            ),
        )
        for q in queues
    ]


def serialize_date(dt):
    if dt is None:
        return None
    return arrow.get(dt).to("UTC").datetime.isoformat()


def serialize_job(job: Job):
    latest_result = job.latest_result()
    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        ended_at=serialize_date(job.ended_at),
        exc_info=latest_result.exc_string if latest_result else None,
        description=job.description,
    )


def serialize_current_job(job):
    if job is None:
        return "idle"
    return dict(
        job_id=job.id,
        description=job.description,
        created_at=serialize_date(job.created_at),
        call_string=job.get_call_string(),
    )


def remove_none_values(input_dict):
    return dict(((k, v) for k, v in input_dict.items() if v is not None))


def pagination_window(total_items, cur_page, per_page, window_size=10):
    all_pages = range(1, int(ceil(total_items / float(per_page))) + 1)
    result = all_pages
    if window_size >= 1:
        temp = min(
            len(all_pages) - window_size, (cur_page - 1) - int(ceil(window_size / 2.0))
        )
        pages_window_start = max(0, temp)
        pages_window_end = pages_window_start + window_size
        result = all_pages[pages_window_start:pages_window_end]
    return result


@blueprint.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(blueprint.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


def get_queue_registry_jobs_count(queue_name, registry_name, offset, per_page, order, connection):
    queue = Queue(queue_name, serializer=config.serializer, connection=connection)
    if registry_name != "queued":
        if per_page >= 0:
            per_page = offset + (per_page - 1)

        if registry_name == "failed":
            current_queue = FailedJobRegistry(queue_name, connection=connection)
        elif registry_name == "deferred":
            current_queue = DeferredJobRegistry(queue_name, connection=connection)
        elif registry_name == "started":
            current_queue = StartedJobRegistry(queue_name, connection=connection)
        elif registry_name == "finished":
            current_queue = FinishedJobRegistry(queue_name, connection=connection)
        elif registry_name == "scheduled":
            current_queue = ScheduledJobRegistry(queue_name, connection=connection)
        elif registry_name == "canceled":
            current_queue = CanceledJobRegistry(queue_name, connection=connection)
    else:
        current_queue = queue
    total_items = current_queue.count


    if order == 'dsc':
        end = total_items - offset
        start = max(0, end - per_page)
    else:
        start = offset
        end = start + per_page

    job_ids = current_queue.get_job_ids(start, end)
    if order == 'dsc':
        job_ids.reverse()

    current_queue_jobs = [queue.fetch_job(job_id) for job_id in job_ids]
    jobs = [serialize_job(job) for job in current_queue_jobs if job]

    return (total_items, jobs)


def escape_format_instance_list(url_list):
    if isinstance(url_list, (list, tuple)):
        url_list = [re.sub(r":\/\/[^@]*@", "://***:***@", x) for x in url_list]
    elif isinstance(url_list, string_types):
        url_list = [re.sub(r":\/\/[^@]*@", "://***:***@", url_list)]
    return url_list


@blueprint.route("/", defaults={"instance_number": 0})
@blueprint.route("/<int:instance_number>/")
@blueprint.route("/<int:instance_number>/view")
@blueprint.route("/<int:instance_number>/view/queues")
def queues_overview(instance_number):
    try:
        r = make_response(
            render_template(
                "rq_dashboard/queues.html",
                current_instance=instance_number,
                instance_list=escape_format_instance_list(current_app.config.get("RQ_DASHBOARD_REDIS_URL")),
                queues=Queue.all(connection=current_app.redis_conn),
                rq_url_prefix=url_for(".queues_overview"),
                rq_dashboard_version=rq_dashboard_version,
                rq_version=rq_version,
                active_tab="queues",
                deprecation_options_usage=current_app.config.get(
                    "DEPRECATED_OPTIONS", False
                ),
            )
        )
    except RedisConnectionError:
        r = make_response(
            "<h1>Connection Error</h1>"
        )
    r.headers.set("Cache-Control", "no-store")
    return r


@blueprint.route("/<int:instance_number>/view/workers")
def workers_overview(instance_number):
    r = make_response(
        render_template(
            "rq_dashboard/workers.html",
            current_instance=instance_number,
            instance_list=escape_format_instance_list(current_app.config.get("RQ_DASHBOARD_REDIS_URL")),
            workers=Worker.all(connection=current_app.redis_conn),
            rq_url_prefix=url_for(".queues_overview"),
            rq_dashboard_version=rq_dashboard_version,
            rq_version=rq_version,
            active_tab="workers",
            deprecation_options_usage=current_app.config.get(
                "DEPRECATED_OPTIONS", False
            ),
        )
    )
    r.headers.set("Cache-Control", "no-store")
    return r


@blueprint.route(
    "/<int:instance_number>/view/jobs",
    defaults={
        "queue_name": None,
        "registry_name": "queued",
        "per_page": "8",
        "order": "asc",
        "page": "1",
    },
)
@blueprint.route(
    "/<int:instance_number>/view/jobs/<queue_name>/<registry_name>/<int:per_page>/<order>/<int:page>"
)
def jobs_overview(instance_number, queue_name, registry_name, per_page, order, page):
    if queue_name is None:
        queue = Queue(serializer=config.serializer, connection=current_app.redis_conn)
    else:
        queue = Queue(queue_name, serializer=config.serializer, connection=current_app.redis_conn)
    r = make_response(
        render_template(
            "rq_dashboard/jobs.html",
            current_instance=instance_number,
            instance_list=escape_format_instance_list(current_app.config.get("RQ_DASHBOARD_REDIS_URL")),
            queues=Queue.all(connection=current_app.redis_conn),
            queue=queue,
            per_page=per_page,
            order=order,
            page=page,
            registry_name=registry_name,
            rq_url_prefix=url_for(".queues_overview"),
            rq_dashboard_version=rq_dashboard_version,
            rq_version=rq_version,
            active_tab="jobs",
            deprecation_options_usage=current_app.config.get(
                "DEPRECATED_OPTIONS", False
            ),
            enable_delete=not current_app.config.get("RQ_DASHBOARD_DISABLE_DELETE"),
        )
    )
    r.headers.set("Cache-Control", "no-store")
    return r


@blueprint.route("/<int:instance_number>/view/job/<job_id>")
def job_view(instance_number, job_id):
    job = Job.fetch(job_id, connection=current_app.redis_conn)
    r = make_response(
        render_template(
            "rq_dashboard/job.html",
            current_instance=instance_number,
            instance_list=escape_format_instance_list(current_app.config.get("RQ_DASHBOARD_REDIS_URL")),
            id=job.id,
            rq_url_prefix=url_for(".queues_overview"),
            rq_dashboard_version=rq_dashboard_version,
            rq_version=rq_version,
            deprecation_options_usage=current_app.config.get(
                "DEPRECATED_OPTIONS", False
            ),
            enable_delete=not current_app.config.get("RQ_DASHBOARD_DISABLE_DELETE"),
        )
    )
    r.headers.set("Cache-Control", "no-store")
    return r


@blueprint.route("/job/<job_id>/delete", methods=["POST"])
@check_delete_enable
@jsonify
def delete_job_view(job_id, registry=None):
    try:
        job = Job.fetch(job_id, connection=current_app.redis_conn)
        job.delete()
    except NoSuchJobError:
        if registry:
            registry.remove(job_id)
        return dict(status="ERROR")

    return dict(status="OK")


@blueprint.route("/job/<job_id>/requeue", methods=["POST"])
@jsonify
def requeue_job_view(job_id):
    requeue_job(job_id, connection=current_app.redis_conn)
    return dict(status="OK")


@blueprint.route("/requeue/<queue_name>", methods=["GET", "POST"])
@jsonify
def requeue_all(queue_name):
    fq = Queue(queue_name, serializer=config.serializer, connection=current_app.redis_conn).failed_job_registry
    job_ids = fq.get_job_ids()
    count = len(job_ids)
    for job_id in job_ids:
        requeue_job(job_id, connection=current_app.redis_conn)
    return dict(status="OK", count=count)


@blueprint.route("/queue/<queue_name>/<registry_name>/empty", methods=["POST"])
@check_delete_enable
@jsonify
def empty_queue(queue_name, registry_name):
    if registry_name == "queued":
        q = Queue(queue_name, serializer=config.serializer, connection=current_app.redis_conn)
        q.empty()
    elif registry_name == "failed":
        registry = FailedJobRegistry(queue_name, connection=current_app.redis_conn)
        for id in registry.get_job_ids():
            delete_job_view(id, registry)
    elif registry_name == "deferred":
        registry = DeferredJobRegistry(queue_name, connection=current_app.redis_conn)
        for id in registry.get_job_ids():
            delete_job_view(id, registry)
    elif registry_name == "started":
        registry = StartedJobRegistry(queue_name, connection=current_app.redis_conn)
        for id in registry.get_job_ids():
            delete_job_view(id, registry)
    elif registry_name == "finished":
        registry = FinishedJobRegistry(queue_name, connection=current_app.redis_conn)
        for id in registry.get_job_ids():
            delete_job_view(id, registry)
    elif registry_name == "canceled":
        registry = CanceledJobRegistry(queue_name, connection=current_app.redis_conn)
        for id in registry.get_job_ids():
            delete_job_view(id, registry)
    elif registry_name == "scheduled":
        registry = ScheduledJobRegistry(queue_name, connection=current_app.redis_conn)
        for id in registry.get_job_ids():
            delete_job_view(id, registry)

    return dict(status="OK")


@blueprint.route("/queue/<queue_name>/compact", methods=["POST"])
@jsonify
def compact_queue(queue_name):
    q = Queue(queue_name, serializer=config.serializer, connection=current_app.redis_conn)
    q.compact()
    return dict(status="OK")


@blueprint.route("/<int:instance_number>/data/queues.json")
@jsonify
def list_queues(instance_number):
    queues = serialize_queues(instance_number, sorted(Queue.all(connection=current_app.redis_conn)))
    return dict(queues=queues)


@blueprint.route(
    "/<int:instance_number>/data/jobs/<queue_name>/<registry_name>/<per_page>/<order>/<page>.json"
)
@jsonify
def list_jobs(instance_number, queue_name, registry_name, per_page, order, page):
    current_page = int(page)
    per_page = int(per_page)
    offset = (current_page - 1) * per_page

    total_items, jobs = get_queue_registry_jobs_count(
        queue_name, registry_name, offset, per_page, order, current_app.redis_conn
    )

    pages_numbers_in_window = pagination_window(total_items, current_page, per_page)
    pages_in_window = [
        dict(
            number=p,
            url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=queue_name,
                registry_name=registry_name,
                per_page=per_page,
                order=order,
                page=p,
            ),
        )
        for p in pages_numbers_in_window
    ]
    last_page = int(ceil(total_items / float(per_page)))

    prev_page = None
    if current_page > 1:
        prev_page = dict(
            url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=queue_name,
                registry_name=registry_name,
                per_page=per_page,
                order=order,
                page=(current_page - 1),
            )
        )

    next_page = None
    if current_page < last_page:
        next_page = dict(
            url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=queue_name,
                registry_name=registry_name,
                per_page=per_page,
                order=order,
                page=(current_page + 1),
            )
        )

    first_page_link = dict(
        url=url_for(
            ".jobs_overview",
            instance_number=instance_number,
            queue_name=queue_name,
            registry_name=registry_name,
            per_page=per_page,
            order=order,
            page=1,
        )
    )
    last_page_link = dict(
        url=url_for(
            ".jobs_overview",
            instance_number=instance_number,
            queue_name=queue_name,
            registry_name=registry_name,
            per_page=per_page,
            order=order,
            page=last_page,
        )
    )

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

    return dict(
        name=queue_name, registry_name=registry_name, jobs=jobs, pagination=pagination
    )


@blueprint.route("/<int:instance_number>/data/job/<job_id>.json")
@jsonify
def job_info(instance_number, job_id):
    job = Job.fetch(job_id, serializer=config.serializer, connection=current_app.redis_conn)
    latest_result = job.latest_result()
    result = dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        ended_at=serialize_date(job.ended_at),
        origin=job.origin,
        status=job.get_status(),
        result=job.return_value(),
        exc_info=latest_result.exc_string if latest_result else None,
        description=job.description,
        metadata=json.dumps(job.get_meta()),
    )
    dep_ids = [di.decode("utf-8").split(':')[-1].strip() for di in job.dependency_ids]
    if len(dep_ids) > 0:
        result["depends_on"] = dep_ids
        status = []
        for dep_id in dep_ids:
            try:
                _ = Job.fetch(dep_id, serializer=config.serializer)
                status.append('active')
            except NoSuchJobError:
                status.append('expired')
        result["depends_on_status"] = status
    return result


@blueprint.route("/<int:instance_number>/data/workers.json")
@jsonify
def list_workers(instance_number):
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = sorted(
        (
            dict(
                name=worker.name,
                pid=worker.pid,
                queues=serialize_queue_names(worker),
                state=str(worker.get_state()),
                current_job=serialize_current_job(worker.get_current_job()),
                last_heartbeat=worker.last_heartbeat,
                birth_date=worker.birth_date,
                successful_job_count=worker.successful_job_count,
                failed_job_count=worker.failed_job_count,
                total_working_time=worker.total_working_time,
                version=getattr(worker, "version", ""),
                python_version=getattr(worker, "python_version", ""),
            )
            for worker in Worker.all(connection=current_app.redis_conn)
        ),
        key=lambda w: (w["state"], w["queues"], w["name"]),
    )
    return dict(workers=workers)


@blueprint.context_processor
def inject_interval():
    interval = current_app.config.get("RQ_DASHBOARD_POLL_INTERVAL", 2500)
    return dict(poll_interval=interval)