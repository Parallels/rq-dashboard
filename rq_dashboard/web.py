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
    pop_connection,
    push_connection,
    requeue_job,
)
from rq.job import Job
from rq.registry import (
    DeferredJobRegistry,
    FailedJobRegistry,
    FinishedJobRegistry,
    StartedJobRegistry,
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
    push_connection(new_instance)
    current_app.redis_conn = new_instance


@blueprint.teardown_request
def pop_rq_connection(exception=None):
    pop_connection()


def jsonify(f):
    @wraps(f)
    def _wrapped(*args, **kwargs):
        from flask import jsonify as flask_jsonify

        result_dict = f(*args, **kwargs)
        return flask_jsonify(**result_dict), {"Cache-Control": "no-store"}

    return _wrapped


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
                page="1",
            ),
            failed_job_registry_count=FailedJobRegistry(q.name).count,
            failed_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="failed",
                per_page="8",
                page="1",
            ),
            started_job_registry_count=StartedJobRegistry(q.name).count,
            started_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="started",
                per_page="8",
                page="1",
            ),
            deferred_job_registry_count=DeferredJobRegistry(q.name).count,
            deferred_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="deferred",
                per_page="8",
                page="1",
            ),
            finished_job_registry_count=FinishedJobRegistry(q.name).count,
            finished_url=url_for(
                ".jobs_overview",
                instance_number=instance_number,
                queue_name=q.name,
                registry_name="finished",
                per_page="8",
                page="1",
            ),
        )
        for q in queues
    ]


def serialize_date(dt):
    if dt is None:
        return None
    return arrow.get(dt).to("UTC").datetime.isoformat()


def serialize_job(job):
    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        ended_at=serialize_date(job.ended_at),
        exc_info=str(job.exc_info) if job.exc_info else None,
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


def get_queue_registry_jobs_count(queue_name, registry_name, offset, per_page):
    queue = Queue(queue_name, serializer=config.serializer)
    if registry_name != "queued":
        if per_page >= 0:
            per_page = offset + (per_page - 1)

        if registry_name == "failed":
            current_queue = FailedJobRegistry(queue_name)
        elif registry_name == "deferred":
            current_queue = DeferredJobRegistry(queue_name)
        elif registry_name == "started":
            current_queue = StartedJobRegistry(queue_name)
        elif registry_name == "finished":
            current_queue = FinishedJobRegistry(queue_name)
    else:
        current_queue = queue
    total_items = current_queue.count

    job_ids = current_queue.get_job_ids(offset, per_page)
    current_queue_jobs = [queue.fetch_job(job_id) for job_id in job_ids]
    jobs = [serialize_job(job) for job in current_queue_jobs if job]

    return (total_items, jobs)


def escape_format_instance_list(url_list):
    if isinstance(url_list, (list, tuple)):
        url_list = [re.sub(r"://:[^@]*@", "://:***@", x) for x in url_list]
    elif isinstance(url_list, string_types):
        url_list = [re.sub(r"://:[^@]*@", "://:***@", url_list)]
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
                queues=Queue.all(),
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
            workers=Worker.all(),
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
        "page": "1",
    },
)
@blueprint.route(
    "/<int:instance_number>/view/jobs/<queue_name>/<registry_name>/<int:per_page>/<int:page>"
)
def jobs_overview(instance_number, queue_name, registry_name, per_page, page):
    if queue_name is None:
        queue = Queue(serializer=config.serializer)
    else:
        queue = Queue(queue_name, serializer=config.serializer)
    r = make_response(
        render_template(
            "rq_dashboard/jobs.html",
            current_instance=instance_number,
            instance_list=escape_format_instance_list(current_app.config.get("RQ_DASHBOARD_REDIS_URL")),
            queues=Queue.all(),
            queue=queue,
            per_page=per_page,
            page=page,
            registry_name=registry_name,
            rq_url_prefix=url_for(".queues_overview"),
            rq_dashboard_version=rq_dashboard_version,
            rq_version=rq_version,
            active_tab="jobs",
            deprecation_options_usage=current_app.config.get(
                "DEPRECATED_OPTIONS", False
            ),
        )
    )
    r.headers.set("Cache-Control", "no-store")
    return r


@blueprint.route("/<int:instance_number>/view/job/<job_id>")
def job_view(instance_number, job_id):
    job = Job.fetch(job_id)
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
        )
    )
    r.headers.set("Cache-Control", "no-store")
    return r


@blueprint.route("/job/<job_id>/delete", methods=["POST"])
@jsonify
def delete_job_view(job_id):
    job = Job.fetch(job_id)
    job.delete()
    return dict(status="OK")


@blueprint.route("/job/<job_id>/requeue", methods=["POST"])
@jsonify
def requeue_job_view(job_id):
    requeue_job(job_id, connection=current_app.redis_conn)
    return dict(status="OK")


@blueprint.route("/requeue/<queue_name>", methods=["GET", "POST"])
@jsonify
def requeue_all(queue_name):
    fq = Queue(queue_name, serializer=config.serializer).failed_job_registry
    job_ids = fq.get_job_ids()
    count = len(job_ids)
    for job_id in job_ids:
        requeue_job(job_id, connection=current_app.redis_conn)
    return dict(status="OK", count=count)


@blueprint.route("/queue/<queue_name>/<registry_name>/empty", methods=["POST"])
@jsonify
def empty_queue(queue_name, registry_name):
    if registry_name == "queued":
        q = Queue(queue_name, serializer=config.serializer)
        q.empty()
    elif registry_name == "failed":
        ids = FailedJobRegistry(queue_name).get_job_ids()
        for id in ids:
            delete_job_view(id)
    elif registry_name == "deferred":
        ids = DeferredJobRegistry(queue_name).get_job_ids()
        for id in ids:
            delete_job_view(id)
    elif registry_name == "started":
        ids = StartedJobRegistry(queue_name).get_job_ids()
        for id in ids:
            delete_job_view(id)
    elif registry_name == "finished":
        ids = FinishedJobRegistry(queue_name).get_job_ids()
        for id in ids:
            delete_job_view(id)
    return dict(status="OK")


@blueprint.route("/queue/<queue_name>/compact", methods=["POST"])
@jsonify
def compact_queue(queue_name):
    q = Queue(queue_name, serializer=config.serializer)
    q.compact()
    return dict(status="OK")


@blueprint.route("/<int:instance_number>/data/queues.json")
@jsonify
def list_queues(instance_number):
    queues = serialize_queues(instance_number, sorted(Queue.all()))
    return dict(queues=queues)


@blueprint.route(
    "/<int:instance_number>/data/jobs/<queue_name>/<registry_name>/<per_page>/<page>.json"
)
@jsonify
def list_jobs(instance_number, queue_name, registry_name, per_page, page):
    current_page = int(page)
    per_page = int(per_page)
    offset = (current_page - 1) * per_page
    total_items, jobs = get_queue_registry_jobs_count(
        queue_name, registry_name, offset, per_page
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
    job = Job.fetch(job_id, serializer=config.serializer)
    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        ended_at=serialize_date(job.ended_at),
        origin=job.origin,
        status=job.get_status(),
        result=job._result,
        exc_info=str(job.exc_info) if job.exc_info else None,
        description=job.description,
    )


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
            for worker in Worker.all()
        ),
        key=lambda w: (w["state"], w["queues"], w["name"]),
    )
    return dict(workers=workers)


@blueprint.context_processor
def inject_interval():
    interval = current_app.config.get("RQ_DASHBOARD_POLL_INTERVAL", 2500)
    return dict(poll_interval=interval)