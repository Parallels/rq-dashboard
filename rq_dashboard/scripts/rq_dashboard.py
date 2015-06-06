from __future__ import absolute_import
from flask import Flask, Response, request
import optparse
import os
import pkg_resources
import rq_dashboard
import sys


def get_version(package='rq_dashboard'):
    return pkg_resources.get_distribution(package).version


def get_options():
    parser = optparse.OptionParser("usage: %prog [options]")
    # Command line hosting parameters
    parser.add_option('-b', '--bind', dest='bind_addr',
                      metavar='ADDR', default='0.0.0.0',
                      help='IP addr or hostname to bind to')
    parser.add_option('-p', '--port', dest='port', type='int',
                      metavar='PORT', default=9181,
                      help='port to bind to')
    parser.add_option('--url-prefix', dest='url_prefix', default='',
                      metavar='URL_PREFIX',
                      help='url prefix e.g. for hosting behind reverse proxy')
    parser.add_option('--username', dest='username', default=None,
                      metavar='USERNAME',
                      help='HTTP Basic Auth username')
    parser.add_option('--password', dest='password', default=None,
                      metavar='PASSWORD',
                      help='HTTP Basic Auth password')

    # Built in RQ Dashboard parameters.
    parser.add_option('-H', '--redis-host', dest='redis_host',
                      metavar='ADDR',
                      help='IP addr or hostname of Redis server')
    parser.add_option('-P', '--redis-port', dest='redis_port', type='int',
                      metavar='REDIS_PORT',
                      help='port of Redis server')
    parser.add_option('--redis-password', dest='redis_password',
                      metavar='PASSWORD',
                      help='password for Redis server')
    parser.add_option('-D', '--redis-database', dest='redis_database',
                      type='int', metavar='DB',
                      help='database of Redis server')
    parser.add_option('-u', '--redis_url', dest='redis_url_connection',
                      metavar='REDIS_URL',
                      help='redis url connection')
    parser.add_option('--interval', dest='poll_interval', type='int',
                      metavar='POLL_INTERVAL',
                      help='refresh interval in ms')
    (options, args) = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(2)
    return options


def configure_app(app, options):
    # Start configuration with our defaults.
    app.config.from_object(rq_dashboard.default_settings)

    # Override from a configuration file if given in the env variable.
    if 'RQ_DASHBOARD_SETTINGS' in os.environ:
        app.config.from_envvar('RQ_DASHBOARD_SETTINGS')

    # Lastly, override with any command line arguments, if given.
    if options.redis_url_connection:
        app.config['REDIS_URL'] = options.redis_url_connection
    if options.redis_host:
        app.config['REDIS_HOST'] = options.redis_host
    if options.redis_port:
        app.config['REDIS_PORT'] = options.redis_port
    if options.redis_password:
        app.config['REDIS_PASSWORD'] = options.redis_password
    if options.redis_database:
        app.config['REDIS_DB'] = options.redis_database
    if options.poll_interval:
        app.config['RQ_POLL_INTERVAL'] = options.poll_interval


def add_basic_auth(blueprint, options):
    """Add HTTP Basic Auth if it has been configured.

    Note this is only for casual use!

    """
    if options.username and options.password:
        @blueprint.before_request
        def basic_http_auth(*args, **kwargs):
            auth = request.authorization
            if (
                    auth is None
                    or auth.password != options.password
                    or auth.username != options.username):
                return Response(
                    'Please login',
                    401,
                    {'WWW-Authenticate': 'Basic realm="RQ Dashboard"'})


def main():
    """Command line entry point defined in setup.py."""
    print('RQ Dashboard version {}'.format(get_version()))
    options = get_options()
    app = Flask(__name__)
    configure_app(app, options)
    add_basic_auth(rq_dashboard.blueprint.blueprint, options)
    app.register_blueprint(
        rq_dashboard.blueprint.blueprint, url_prefix=options.url_prefix)
    app.run(host=options.bind_addr, port=options.port)
