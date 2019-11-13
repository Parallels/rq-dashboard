from __future__ import absolute_import

import importlib
import logging
import os
import sys

import click
from flask import Flask, Response, request

from . import default_settings
from .version import VERSION
from .web import blueprint


def add_basic_auth(blueprint, username, password, realm='RQ Dashboard'):
    """Add HTTP Basic Auth to a blueprint.

    Note this is only for casual use!

    """
    @blueprint.before_request
    def basic_http_auth(*args, **kwargs):
        auth = request.authorization
        if (auth is None or auth.password != password or
                auth.username != username):
            return Response(
                'Please login',
                401,
                {'WWW-Authenticate': 'Basic realm="{}"'.format(realm)})


def make_flask_app(config, username, password, url_prefix,
                   compatibility_mode=True):
    """Return Flask app with default configuration and registered blueprint."""
    app = Flask(__name__)

    # Start configuration with our built in defaults.
    app.config.from_object(default_settings)

    # Override with any settings in config file, if given.
    if config:
        app.config.from_object(importlib.import_module(config))

    # Override from a configuration file in the env variable, if present.
    if 'RQ_DASHBOARD_SETTINGS' in os.environ:
        app.config.from_envvar('RQ_DASHBOARD_SETTINGS')

    # Optionally add basic auth to blueprint and register with app.
    if username:
        add_basic_auth(blueprint, username, password)
    app.register_blueprint(blueprint, url_prefix=url_prefix)

    return app


@click.command()
@click.option(
    '-b', '--bind', default='0.0.0.0',
    help='IP or hostname on which to bind HTTP server')
@click.option(
    '-p', '--port', default=9181, type=int,
    help='Port on which to bind HTTP server')
@click.option(
    '--url-prefix', default='',
    help='URL prefix e.g. for use behind a reverse proxy')
@click.option(
    '--username', default=None,
    help='HTTP Basic Auth username (not used if not set)')
@click.option(
    '--password', default=None,
    help='HTTP Basic Auth password')
@click.option(
    '-c', '--config', default=None,
    help='Configuration file (Python module on search path)')
@click.option(
    '-H', '--redis-host', default=None,
    help='IP address or hostname of Redis server')
@click.option(
    '-P', '--redis-port', default=None, type=int,
    help='Port of Redis server')
@click.option(
    '--redis-password', default=None,
    help='Password for Redis server')
@click.option(
    '-D', '--redis-database', default=None, type=int,
    help='Database of Redis server')
@click.option(
    '-u', '--redis-url', default=None,
    help='Redis URL connection (overrides other individual settings)')
@click.option(
    '--redis-sentinels', default=None,
    help='List of redis sentinels. Each should be formatted: <host>:<port>')
@click.option(
    '--redis-master-name', default=None,
    help='Name of redis master. Only needed when using sentinels')
@click.option(
    '--poll-interval', '--interval', 'poll_interval', default=None, type=int,
    help='Refresh interval in ms')
@click.option(
    '--extra-path', default='.', multiple=True,
    help='Append specified directories to sys.path')
@click.option(
    '--web-background', default='black',
    help='Background of the web interface')
@click.option(
    '--delete-jobs', default=False, help='Delete jobs instead of cancel')
@click.option(
    '--debug/--normal', default=False, help='Enter DEBUG mode')
@click.option(
    '-v', '--verbose', is_flag=True, default=False, help='Enable verbose logging')
def run(
        bind, port, url_prefix, username, password,
        config,
        redis_host, redis_port, redis_password, redis_database, redis_url,
        redis_sentinels, redis_master_name,
        poll_interval, extra_path, web_background, debug, delete_jobs,
        verbose):
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

    click.echo('RQ Dashboard version {}'.format(VERSION))
    app = make_flask_app(config, username, password, url_prefix)
    if redis_url:
        app.config['RQ_DASHBOARD_REDIS_URL'] = redis_url
    if redis_host:
        app.config['RQ_DASHBOARD_REDIS_HOST'] = redis_host
    if redis_port:
        app.config['RQ_DASHBOARD_REDIS_PORT'] = redis_port
    if redis_password:
        app.config['RQ_DASHBOARD_REDIS_PASSWORD'] = redis_password
    if redis_database:
        app.config['RQ_DASHBOARD_REDIS_DB'] = redis_database
    if redis_sentinels:
        app.config['RQ_DASHBOARD_REDIS_SENTINELS'] = redis_sentinels
    if redis_master_name:
        app.config['RQ_DASHBOARD_REDIS_MASTER_NAME'] = redis_master_name
    if poll_interval:
        app.config['RQ_DASHBOARD_POLL_INTERVAL'] = poll_interval
    if web_background:
        app.config["RQ_DASHBOARD_WEB_BACKGROUND"] = web_background
    if delete_jobs:
        app.config["RQ_DASHBOARD_DELETE_JOBS"] = delete_jobs
    # Conditionally disable Flask console messages
    # See: https://stackoverflow.com/questions/14888799
    log = logging.getLogger('werkzeug')
    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.ERROR)
        log.error(" * Running on {}:{}".format(bind, port))

    app.run(host=bind, port=port, debug=debug)


def main():
    run(auto_envvar_prefix='RQ_DASHBOARD')
