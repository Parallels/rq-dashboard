#!/usr/bin/env python
import sys
import optparse
from ..app import app


def main():
    parser = optparse.OptionParser("usage: %prog [options]")
    parser.add_option('-b', '--bind', dest='bind_addr',
                      metavar='ADDR',
                      help='IP addr or hostname to bind to')
    parser.add_option('-p', '--port', dest='port', type='int',
                      metavar='PORT',
                      help='port to bind to')
    parser.add_option('-H', '--redis-host', dest='redis_host',
                      metavar='ADDR',
                      help='IP addr or hostname of Redis server')
    parser.add_option('-P', '--redis-port', dest='redis_port', type='int',
                      metavar='PORT',
                      help='port of Redis server')
    (options, args) = parser.parse_args()

    # Populate app.config from options, defaulting to app.config's original
    # values, if specified, finally defaulting to something sensible.
    app.config['BIND_ADDR'] = options.bind_addr or app.config.get('BIND_ADDR', '0.0.0.0')
    app.config['PORT'] = options.port or app.config.get('PORT', 9181)

    # Override app.config from options if specified.  Otherwise leave untouched,
    # so the client can use its own defauls if app.config has no values.
    if options.redis_host:
        app.config['REDIS_HOST'] = options.redis_host
    if options.redis_port:
        app.config['REDIS_PORT'] = options.redis_port

    if len(args) > 0:
        parser.print_help()
        sys.exit(2)

    app.run(host=app.config['BIND_ADDR'], port=app.config['PORT'])

if __name__ == '__main__':
    main()
