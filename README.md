Introduction
============

`rq-dashboard` is a general purpose, lightweight,
[Flask](https://flask.palletsprojects.com/)-based web front-end to monitor your
[RQ](http://python-rq.org/) queues, jobs, and workers in realtime.

[![Build Pull Request](https://github.com/Parallels/rq-dashboard/actions/workflows/pr.yaml/badge.svg)](https://github.com/Parallels/rq-dashboard/actions/workflows/pr.yaml)
[![Publish Release](https://github.com/Parallels/rq-dashboard/actions/workflows/publish.yaml/badge.svg)](https://github.com/Parallels/rq-dashboard/actions/workflows/publish.yaml)
[![Python
Support](https://img.shields.io/pypi/pyversions/rq-dashboard.svg)](https://pypi.python.org/pypi/rq-dashboard)
![PyPI Downloads](https://img.shields.io/pypi/dw/rq-dashboard)

Maturity notes
--------------

The RQ dashboard is currently being developed and is in beta stage.
How migrate to version 1.0 you can find [here](https://github.com/Parallels/rq-dashboard/wiki/How-to-migrate-to-1.0)

You can find help  in the discussion page in [github]([http](https://github.com/Parallels/rq-dashboard)) or join our [discord server](https://discord.gg/reuhvMFT)

Installing with Docker
----------------------

You can also run the dashboard inside of docker:

* copy the ```docker-compose.yml``` file from the root of the repository to ```docker-compose.override.yml``` and change the environment variables to your liking.
* run the following command:

  ``` {.console}
  $ docker-compose up
  ```

You can also find the official image on cjlapao/rq-dashboard:latest

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
  -u, --redis-url TEXT            Redis URL. Can be specified multiple times.
                                  Default: redis://127.0.0.1:6379
  --poll-interval, --interval INTEGER
                                  Refresh interval in ms
  --extra-path TEXT               Append specified directories to sys.path
  --disable-delete                Disable delete jobs, clean up registries
  --debug / --normal              Enter DEBUG mode
  -v, --verbose                   Enable verbose logging
  -j, --json                      Enable JSONSerializer
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
rq_dashboard.web.setup_rq_connection(app)
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

Consider using third-party project
[rq-dashboard-on-heroku](https://github.com/metabolize/rq-dashboard-on-heroku),
which installs rq-dashboard from PyPI and wraps in in
[Gunicorn](https://gunicorn.org) for deployment to Heroku.
rq-dashboard-on-heroku is maintained indepdently.

Running behind a Reverse Proxy
-------------------------------
You can run the dashboard as a `systemd` service in Linux or via a `suprevisor`
script and then use Apache or NGINX to direct traffic to the dashboard.

_This is for *non-production* functionality!_

Apache Reverse Proxy example:
```
ProxyPass /rq http://127.0.0.1:5001/rq
ProxyPassReverse /rq http://127.0.0.1:5001/rq
```

Systemd service example:
```
[Unit]
Description=Redis Queue Dashboard
[Install]

WantedBy=multi-user.target
[Service]
ExecStart=/bin/rq-dashboard -b 127.0.0.1 -p 5001 --url-prefix /rq -c rq_settings_dashboard --debug -v
StandardOutput=file:/var/log/redis/rq-dasbhoard.log
StandardError=file:/var/log/redis/rq-dashboard.log
User=redis-dash
Group=redis-dash
RemainAfterExit=yes
Type=simple
PermissionsStartOnly=false
PrivateTmp=no
```
* `--debug`,`-v` are optional -- they will write `stdout` to your specified files.
* `rq_settings_dashboard` is a Python file, with settings defined. You can use options that are available as environmental variables. (EX. `RQ_DASHBOARD_REDIS_PASSWORD = password`)


Running as Container in Docker Compose
--------------------------------------

Running the dashboard as an isolated service can be easier than embedding the
blueprint inside an existing Flask application. You can:

- update the UI independently of your main project—mount the repo into the
  container and a `git pull` refreshes the running dashboard;
- keep Python dependencies for the dashboard separate from the rest of your
  stack;
- front the dashboard with any reverse proxy (Caddy, Nginx, Traefik, etc.)
  without touching your core application code.

### Why `rq_dashboard/app.py` exists

The upstream project exposes only a Flask blueprint. The application factory in
`rq_dashboard/app.py` wraps that blueprint so that:

- Gunicorn (or any other WSGI server) can import a callable
  `rq_dashboard.app:create_app()` just like the rest of your services;
- static assets resolve under `/rq-dashboard/static`, which is required when
  the service sits behind a reverse proxy that adds a URL prefix;
- Redis credentials and other `RQ_DASHBOARD_*` settings are centralised so they
  can be supplied via environment variables.

Skip `app.py` and you lose the callable for Gunicorn and the static URLs break
as soon as the app is mounted anywhere other than `/`.

### Dockerfile

Build the image from a minimal Dockerfile that installs the published
requirements and Gunicorn. Copying only `requirements.txt` keeps the build
cache small while the bind mount supplies live source code:

```Dockerfile
# docker/Dockerfile.rq-dashboard
FROM python:3.8-slim

ENV PYTHONUNBUFFERED=1 \
    RQ_DASHBOARD_URL_PREFIX=/rq-dashboard

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        gcc \
        libc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /rq-dashboard

COPY rq-dashboard/requirements.txt /tmp/rq-dashboard-requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/rq-dashboard-requirements.txt \
    && pip3 install --no-cache-dir gunicorn

EXPOSE 9181
```

### Compose service

Add the dashboard as a standalone service that installs the local checkout in
editable mode and starts Gunicorn with the application factory. The example
below assumes the repository is mounted at `./rq-dashboard` relative to the
compose file and that a `redis` service already exists:

```yaml
  rq-dashboard:
    build:
      context: ..
      dockerfile: docker/Dockerfile.rq-dashboard
    container_name: rq-dashboard
    environment:
      RQ_DASHBOARD_REDIS_URL: redis://redis:6379/0
      RQ_DASHBOARD_URL_PREFIX: /rq-dashboard
      PIP_DISABLE_PIP_VERSION_CHECK: "1"
    volumes:
      - ../rq-dashboard:/rq-dashboard
    working_dir: /rq-dashboard
    command:
      - gunicorn
      - --bind
      - 0.0.0.0:9181
      - --workers
      - "2"
      - --threads
      - "2"
      - --timeout
      - "30"
      - --log-level
      - info
      - rq_dashboard.app:create_app()
    expose:
      - "9181"
    depends_on:
      redis:
        condition: service_started
```

- Mounting the source directory lets you update the dashboard with `git pull`
  and have the change reflected immediately.
- `RQ_DASHBOARD_URL_PREFIX` keeps URL generation aligned with the reverse
  proxy. When using Caddy/NGINX/Traefik, forward `X-Forwarded-Prefix` so the
  app recognises its mount point.
- The editable install happens at container startup. If you need faster boots,
  bake `pip install -e /rq-dashboard` (or `python setup.py develop`) into a
  custom image instead of doing it at runtime.

### Reverse proxy (Caddy example)

A reverse proxy should forward the original host, protocol, and URL prefix so
the dashboard emits correct links. A minimal Caddy stanza that publishes the
service under `/rq-dashboard/` looks like this:

```Caddyfile
handle /rq-dashboard* {
    reverse_proxy rq-dashboard:9181 {
        header_up X-Forwarded-Prefix /rq-dashboard
        header_up X-Forwarded-Proto {scheme}
        header_up Host {host}
    }
}
```

Mirror those headers if you are using Nginx, Traefik, or another proxy.

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
-   [Github stats](https://github.com/Parallels/rq-dashboard/graphs/traffic)
