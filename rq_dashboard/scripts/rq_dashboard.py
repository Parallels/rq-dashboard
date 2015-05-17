#!/usr/bin/env python
from __future__ import absolute_import
from flask import Flask
import optparse
import os
import rq_dashboard
import sys
from ..version import VERSION


def main():
    app = Flask(__name__)
    options = get_options()
    configure_app(app, options)
    run_app(app)


def get_options():
    parser = optparse.OptionParser("usage: %prog [options]")
    parser.add_option('-b', '--bind', dest='bind_addr',
                      metavar='ADDR', default='0.0.0.0',
                      help='IP addr or hostname to bind to')
    parser.add_option('-p', '--port', dest='port', type='int',
                      metavar='PORT', default=9181,
                      help='port to bind to')
    parser.add_option('-H', '--redis-host', dest='redis_host',
                      metavar='ADDR',
                      help='IP addr or hostname of Redis server')
    parser.add_option('-P', '--redis-port', dest='redis_port', type='int',
                      metavar='PORT',
                      help='port of Redis server')
    parser.add_option('--redis-password', dest='redis_password',
                      metavar='PASSWORD',
                      help='password for Redis server')
    parser.add_option('-D', '--redis-database', dest='redis_database', type='int',
                      metavar='DB',
                      help='database of Redis server')
    parser.add_option('-u', '--redis_url', dest='redis_url_connection',
                      metavar='REDIS_URL',
                      help='redis url connection')
    parser.add_option('--interval', dest='poll_interval', type='int',
                      metavar='POLL_INTERVAL',
                      help='refresh interval')
    parser.add_option('--url-prefix', dest='url_prefix',
                      metavar='URL_PREFIX',
                      help='url prefix e.g. for hosting behind reverse proxy')
    (options, args) = parser.parse_args()
    if len(args) > 0:
        parser.print_help()
        sys.exit(2)
    return options


def configure_app(app, options):
    # Start configuration from a configuration file, if given.
    if os.getenv('RQ_DASHBOARD_SETTINGS'):
        app.config.from_envvar('RQ_DASHBOARD_SETTINGS')

    # Override with any command line arguments, if given.
    if options.bind_addr:
        app.config['BIND_ADDR'] = options.bind_addr
    if options.port:
        app.config['PORT'] = options.port
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
    if options.url_prefix:
        app.config['URL_PREFIX'] = options.url_prefix
    app.config['REDIS_URL'] = options.redis_url_connection or None


def run_app(app):
    print('RQ Dashboard, version %s' % VERSION)
    rq_dashboard.RQDashboard(app, url_prefix=app.config.get('URL_PREFIX', ''))
    app.run(host=app.config['BIND_ADDR'], port=app.config['PORT'])


if __name__ == '__main__':
    main()

