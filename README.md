Introduction
============

`rq-dashboard` is a general purpose, lightweight,
[Flask](http://flask.pocoo.org/)-based web front-end to monitor your
[RQ](http://python-rq.org/) queues, jobs, and workers in realtime.

[![Build
Status](https://travis-ci.org/eoranged/rq-dashboard.svg?branch=master)](https://travis-ci.org/eoranged/rq-dashboard)
[![Python
Support](https://img.shields.io/pypi/pyversions/rq-dashboard.svg)](https://pypi.python.org/pypi/rq-dashboard)
![PyPI Downloads](https://img.shields.io/pypi/dw/rq-dashboard)

It looks like this
------------------

![image1](https://i.imgur.com/XGmoKQA.png)
![image2](https://i.imgur.com/nStM6H7.png?1)

Maturity notes
--------------

The RQ dashboard is currently being developed and is in beta stage.

Installing with Docker
----------------------

You can also run the dashboard inside of docker:

``` {.console}
$ docker pull eoranged/rq-dashboard
$ docker run -p 9181:9181 eoranged/rq-dashboard
```

and you can then run the image. You can pass additional options using
environment variables with prefix `RQ_DASHBOARD_*`:

    - RQ_DASHBOARD_REDIS_URL=redis://<redis:6379>
    - RQ_DASHBOARD_USERNAME=rq
    - RQ_DASHBOARD_PASSWORD=password

See more info on how to pass environment variables in [Docker documentation](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables--e---env---env-file)

Installing from PyPI
--------------------

``` {.console}
$ pip install rq-dashboard
```

Running the dashboard
---------------------

Run the dashboard standalone, like this:

``` {.console}
$ rq-dashboard
* Running on http://127.0.0.1:9181/
...
```

``` {.console}
$ rq-dashboard --help
Usage: rq-dashboard [OPTIONS]

  Run the RQ Dashboard Flask server.

  All configuration can be set on the command line or through environment
  variables of the form RQ_DASHBOARD_*. For example RQ_DASHBOARD_USERNAME.

  A subset of the configuration (the configuration parameters used by the
  underlying flask blueprint) can also be provided in a Python module
  referenced using --config, or with a .cfg file referenced by the
  RQ_DASHBOARD_SETTINGS environment variable.

Options:
  -b, --bind TEXT                 IP or hostname on which to bind HTTP server
  -p, --port INTEGER              Port on which to bind HTTP server
  --url-prefix TEXT               URL prefix e.g. for use behind a reverse
                                  proxy
  --username TEXT                 HTTP Basic Auth username (not used if not
                                  set)
  --password TEXT                 HTTP Basic Auth password
  -c, --config TEXT               Configuration file (Python module on search
                                  path)
  -H, --redis-host TEXT           IP address or hostname of Redis server
  -P, --redis-port INTEGER        Port of Redis server
  --redis-password TEXT           Password for Redis server
  -D, --redis-database INTEGER    Database of Redis server
  -u, --redis-url TEXT            Redis URL connection (overrides other
                                  individual settings)
  --redis-sentinels TEXT          List of redis sentinels. Each should be
                                  formatted: <host>:<port>
  --redis-master-name TEXT        Name of redis master. Only needed when using
                                  sentinels
  --poll-interval, --interval INTEGER
                                  Refresh interval in ms
  --extra-path TEXT               Append specified directories to sys.path
  --web-background TEXT           Background of the web interface
  --delete-jobs TEXT              Delete jobs instead of cancel
  --debug / --normal              Enter DEBUG mode
  -v, --verbose                   Enable verbose logging
  --help                          Show this message and exit.
```

Integrating the dashboard in your Flask app
-------------------------------------------

The dashboard can be integrated in to your own [Flask](http://flask.pocoo.org/) app by accessing the blueprint directly in the normal way, e.g.:

``` {.python}
from flask import Flask
import rq_dashboard

app = Flask(__name__)
app.config.from_object(rq_dashboard.default_settings)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()
```

If you start the Flask app on the default port, you can access the
dashboard at <http://localhost:5000/rq>. The `cli.py:main` entry point
provides a simple working example.

Running on Heroku
-----------------

Consider using
[rq-dashboard-on-heroku](https://github.com/metabolize/rq-dashboard-on-heroku),
which installs rq-dashboard from PyPI and wraps in in
[Gunicorn](https://gunicorn.org) for deployment to Heroku.
rq-dashboard-on-heroku is maintained indepdently.

Developing
----------

Develop in a virtualenv and make sure you have all the necessary build
time (and run time) dependencies with

    $ pip install -r requirements.txt

Develop in the normal way with

    $ python setup.py develop

Stats
-----

-   [PyPI stats](https://pypistats.org/packages/rq-dashboard)
-   [Github stats](https://github.com/eoranged/rq-dashboard/graphs/traffic)
