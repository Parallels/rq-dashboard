Introduction
============

``rq-dashboard`` is a general purpose, lightweight, `Flask`_-based web
front-end to monitor your `RQ`_ queues, jobs, and workers in realtime.

|Build Status|
|Python Support|

It looks like this
------------------

|image1|
|image2|

Installing
----------

.. code:: console

    $ pip install rq-dashboard


Running the dashboard
---------------------

Run the dashboard standalone, like this:

.. code:: console

    $ rq-dashboard
    * Running on http://127.0.0.1:9181/
    ...


.. code:: console

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
      -b, --bind TEXT               IP or hostname on which to bind HTTP server
      -p, --port INTEGER            Port on which to bind HTTP server
      --url-prefix TEXT             URL prefix e.g. for use behind a reverse proxy
      --username TEXT               HTTP Basic Auth username (not used if not set)
      --password TEXT               HTTP Basic Auth password
      -c, --config TEXT             Configuration file (Python module on search
                                    path)
      -H, --redis-host TEXT         IP address or hostname of Redis server
      -P, --redis-port INTEGER      Port of Redis server
      --redis-password TEXT         Password for Redis server
      -D, --redis-database INTEGER  Database of Redis server
      -u, --redis-url TEXT          Redis URL connection (overrides other
                                    individual settings)
      --redis-sentinels TEXT        List of redis sentinels. Each should be
                                    formatted: <host>:<port>
      --redis-master-name TEXT      Name of redis master. Only needed when using
                                    sentinels
      --interval INTEGER            Refresh interval in ms
      --extra-path TEXT             Append specified directories to sys.path
      --web-background TEXT         Background of the web interface
      --delete-jobs TEXT            Delete jobs instead of cancel
      --debug / --normal            Enter DEBUG mode
      --help                        Show this message and exit.


Integrating the dashboard in your Flask app
-------------------------------------------

The dashboard can be integrated in to your own `Flask`_ app by accessing the
blueprint directly in the normal way, e.g.:

.. code:: python

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


If you start the Flask app on the default port, you can access the dashboard at http://localhost:5000/rq. The ``cli.py:main`` entry point provides a simple working example.


Developing
----------

We use piptools_ to keep our development dependencies up to date

::

    $ pip install --upgrade pip
    $ pip install git+https://github.com/nvie/pip-tools.git@future

Now make changes to the ``requirements.in`` file, and resolve all the
2nd-level dependencies into ``requirements.txt`` like so:

::

    $ pip-compile --annotate requirements.in


Develop in a virtualenv and make sure you have all the necessary build time (and
run time) dependencies with

::

    $ pip install -r requirements.txt


Develop in the normal way with

::

    $ python setup.py develop


Maturity notes
--------------

The RQ dashboard is currently being developed and is in beta stage.


Docker
------

You can also run the dashboard inside of docker, simply build the image with

::

    $ make image

and you can then run the image, possibly modifying it with the following environment
variables from their default values

* REDIS_URL=redis://redis
* USERNAME=rq
* PASSWORD=password


.. _piptools: https://github.com/nvie/pip-tools
.. _Flask: http://flask.pocoo.org/
.. _RQ: http://python-rq.org/

.. |Build Status| image:: https://travis-ci.org/eoranged/rq-dashboard.svg?branch=master
   :target: https://travis-ci.org/eoranged/rq-dashboard
.. |Python Support| image:: https://img.shields.io/pypi/pyversions/rq-dashboard.svg
   :target: https://pypi.python.org/pypi/rq-dashboard

.. |image1| image:: https://i.imgur.com/XGmoKQA.png?1
   :target: https://i.imgur.com/XGmoKQA.png
   :width: 47%
.. |image2| image:: https://i.imgur.com/nStM6H7.png?1
   :target: https://i.imgur.com/nStM6H7.png
   :width: 47%
