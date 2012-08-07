#!/usr/bin/env python
import optparse
from ..app import app


def main():
    parser = optparse.OptionParser("usage: %prog [options]")
    parser.add_option('-l', '--listen', dest='host',
                      metavar='IP', help='IP to listen on')
    parser.add_option('-p', '--port', dest='port', type='int',
                      metavar='PORT', help='port to listen on')
    parser.add_option('-s', '--redis-server', dest='redis_host',
                      metavar='IP', help='IP of redis server')
    parser.add_option('--redis-port', dest='redis_port', type='int',
                      metavar='PORT', help='port of redis server')
    (options, args) = parser.parse_args()

    # populate app.config from options, defaulting to app.config's original
    # values, if specified, finally defaulting to something sensible.
    app.config['HOST'] = options.host or app.config.get('HOST', '0.0.0.0')
    app.config['PORT'] = options.port or app.config.get('PORT', 9181)

    # override app.config from options if specified.  Otherwise leave untouched,
    # so the client can use its own defauls if app.config has no values.
    if options.redis_host: app.config['REDIS_HOST'] = options.redis_host
    if options.redis_port: app.config['REDIS_PORT'] = options.redis_port

    app.run(host=app.config['HOST'], port=app.config['PORT'])

if __name__ == '__main__':
    main()
