import importlib
import logging
import os
import sys
from urllib.parse import quote as urlquote, urlunparse

import click
from flask import Flask, Response, request

from . import default_settings
from .version import VERSION
from .web import blueprint, setup_rq_connection
from .web import config as service_config
from rq.serializers import JSONSerializer


def add_basic_auth(blueprint, username, password, realm="RQ Dashboard"):
    """Add HTTP Basic Auth to a blueprint.

    Note this is only for casual use!

    """

    @blueprint.before_request
    def basic_http_auth(*args, **kwargs):
        auth = request.authorization
        if auth is None or auth.password != password or auth.username != username:
            return Response(
                "Please login",
                401,
                {"WWW-Authenticate": 'Basic realm="{}"'.format(realm)},
            )


def make_flask_app(config, username, password, url_prefix, compatibility_mode=True):
    """Return Flask app with default configuration and registered blueprint."""
    app = Flask(__name__)

    # Start configuration with our built in defaults.
    app.config.from_object(default_settings)

    # Override with any settings in config file, if given.
    if config:
        app.config.from_object(importlib.import_module(config))

    # Override from a configuration file in the env variable, if present.
    if "RQ_DASHBOARD_SETTINGS" in os.environ:
        app.config.from_envvar("RQ_DASHBOARD_SETTINGS")

    # Optionally add basic auth to blueprint and register with app.
    if username:
        add_basic_auth(blueprint, username, password)
    app.register_blueprint(blueprint, url_prefix=url_prefix)

    return app


@click.command()
@click.option(
    "-b",
    "--bind",
    default="0.0.0.0",
    help="IP or hostname on which to bind HTTP server",
)
@click.option(
    "-p", "--port", default=9181, type=int, help="Port on which to bind HTTP server"
)
@click.option(
    "--url-prefix", default="", help="URL prefix e.g. for use behind a reverse proxy"
)
@click.option(
    "--username", default=None, help="HTTP Basic Auth username (not used if not set)"
)
@click.option("--password", default=None, help="HTTP Basic Auth password")
@click.option(
    "-c",
    "--config",
    default=None,
    help="Configuration file (Python module on search path)",
)
@click.option(
    "-H",
    "--redis-host",
    default=None,
    hidden=True,
    help="[DEPRECATED] IP address or hostname of Redis server. Use --redis-url instead",
)
@click.option(
    "-P",
    "--redis-port",
    default=None,
    type=int,
    hidden=True,
    help="[DEPRECATED] Port of Redis server. Use --redis-url instead",
)
@click.option(
    "--redis-password",
    default=None,
    hidden=True,
    help="[DEPRECATED] Password for Redis server. Use --redis-url instead",
)
@click.option(
    "-D",
    "--redis-database",
    default=None,
    type=int,
    hidden=True,
    help="[DEPRECATED] Database of Redis server, Use --redis-url instead",
)
@click.option(
    "-u",
    "--redis-url",
    default=[],
    multiple=True,
    help="Redis URL. Can be specified multiple times. Default: redis://127.0.0.1:6379",
)
@click.option(
    "--redis-sentinels",
    default=None,
    hidden=True,
    help="[DEPRECATED] List of redis sentinels. Use --redis-url instead",
)
@click.option(
    "--redis-master-name",
    default=None,
    hidden=True,
    help="[DEPRECATED] Name of redis master. Only needed when using sentinels. Use --redis-url instead",
)
@click.option(
    "--poll-interval",
    "--interval",
    "poll_interval",
    default=None,
    type=int,
    help="Refresh interval in ms",
)
@click.option(
    "--extra-path",
    default=["."],
    multiple=True,
    help="Append specified directories to sys.path",
)
@click.option(
    "--web-background",
    default=None,
    hidden=True,
    help="[DEPRECATED] Background of the web interface",
)
@click.option(
    "--delete-jobs",
    default=None,
    hidden=True,
    help="[DEPRECATED] Delete jobs instead of cancel",
)
@click.option("--debug/--normal", default=False, help="Enter DEBUG mode")
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="Enable verbose logging"
)
@click.option(
    "-j", "--json", is_flag=True, default=False, help="Enable JSONSerializer"
)
def run(
    bind,
    port,
    url_prefix,
    username,
    password,
    config,
    redis_host,
    redis_port,
    redis_password,
    redis_database,
    redis_url,
    redis_sentinels,
    redis_master_name,
    poll_interval,
    extra_path,
    web_background,
    debug,
    delete_jobs,
    verbose,
    json,
):
    """Run the RQ Dashboard Flask server.

    All configuration can be set on the command line or through environment
    variables of the form RQ_DASHBOARD_*. For example RQ_DASHBOARD_USERNAME.

    A subset of the configuration (the configuration parameters used by the
    underlying flask blueprint) can also be provided in a Python module
    referenced using --config, or with a .cfg file referenced by the
    RQ_DASHBOARD_SETTINGS environment variable.

    """
    if extra_path:
        sys.path += list(extra_path)

    click.echo("RQ Dashboard version {}".format(VERSION))
    app = make_flask_app(config, username, password, url_prefix)
    app.config["DEPRECATED_OPTIONS"] = []
    if redis_url:
        app.config["RQ_DASHBOARD_REDIS_URL"] = redis_url
    else:
        app.config["RQ_DASHBOARD_REDIS_URL"] = "redis://127.0.0.1:6379"
    if redis_host:
        app.config["DEPRECATED_OPTIONS"].append("--redis-host")
    if redis_port:
        app.config["DEPRECATED_OPTIONS"].append("--redis-port")
    if redis_password:
        app.config["DEPRECATED_OPTIONS"].append("--redis-password")
    if redis_database:
        app.config["DEPRECATED_OPTIONS"].append("--redis-database")
    if redis_sentinels:
        app.config["DEPRECATED_OPTIONS"].append("--redis-sentinels")
    if redis_master_name:
        app.config["DEPRECATED_OPTIONS"].append("--redis-master-name")
    if web_background:
        app.config["DEPRECATED_OPTIONS"].append("--web-background")
    if delete_jobs is not None:
        app.config["DEPRECATED_OPTIONS"].append("--delete-jobs")
    if poll_interval:
        app.config["RQ_DASHBOARD_POLL_INTERVAL"] = poll_interval
    # Conditionally disable Flask console messages
    # See: https://stackoverflow.com/questions/14888799
    log = logging.getLogger("werkzeug")
    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.ERROR)
        log.error(" * Running on {}:{}".format(bind, port))

    if app.config["DEPRECATED_OPTIONS"] and not redis_url:
        # redis+sentinel://[:password@]host:port[,host2:port2,...][/service_name[/db]][?param1=value1[&param2=value=2&...]]
        scheme = "redis+sentinel" if redis_sentinels else "redis"
        if redis_sentinels:
            netloc = redis_sentinels
        else:
            netloc = redis_host or "localhost"
            if redis_port:
                netloc = "%s:%s" % (netloc, redis_port)
        if redis_password:
            netloc = ":" + urlquote(redis_password) + "@" + netloc
        path = ""
        if redis_master_name:
            path += "/%s" % urlquote(redis_master_name)
        if redis_database:
            path += "/%s" % redis_database
        url = urlunparse((scheme, netloc, path, "", "", ""))
        log.error(
            "Use --redis-url=%s configuration option "
            "instead of specifying host, port and other parameters separately",
            url,
        )
        app.config["RQ_DASHBOARD_REDIS_URL"] = url
        
    if json:
        service_config.serializer = JSONSerializer

    setup_rq_connection(app)
    app.run(host=bind, port=port, debug=debug)


def main():
    run(auto_envvar_prefix="RQ_DASHBOARD")