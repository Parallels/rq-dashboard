Introduction
============

``rq-dashboard`` is a general purpose, lightweight, `Flask`_-based web
front-end to monitor your `RQ`_ queues, jobs, and workers in realtime.

|Can I Use Python 3?|


It looks like this
------------------

|image1| |image2|


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
    RQ Dashboard version 0.3.5
    Usage: rq-dashboard [options]

    Options:
      -h, --help            show this help message and exit
      -b ADDR, --bind=ADDR  IP addr or hostname to bind to
      -p PORT, --port=PORT  port to bind to
      --url-prefix=URL_PREFIX
                            url prefix e.g. for hosting behind reverse proxy
      --username=USERNAME   HTTP Basic Auth username
      --password=PASSWORD   HTTP Basic Auth password
      -c CONFIG_FILE, --config=CONFIG_FILE
                            configuration file
      -H ADDR, --redis-host=ADDR
                            IP addr or hostname of Redis server
      -P REDIS_PORT, --redis-port=REDIS_PORT
                            port of Redis server
      --redis-password=PASSWORD
                            password for Redis server
      -D DB, --redis-database=DB
                            database of Redis server
      -u REDIS_URL, --redis_url=REDIS_URL
                            redis url connection
      --interval=POLL_INTERVAL
                            refresh interval in ms


Integrating the dashboard in your Flask app
-------------------------------------------

The dashboard can be integrated in to your own `Flask`_ app by accessing the
blueprint directly in the normal way, e.g.:

.. code:: python

    from flask import Flask
    import rq_dashboard

    app = Flask(__name__)
    app.config.from_object(rq_dashboard.default_settings)
    app.register_blueprint(rq_dashboard.blueprint.blueprint)

    @app.route("/")
    def hello():
        return "Hello World!"

    if __name__ == "__main__":
        app.run()


The ``scripts/rq_dashboard.py:main`` entry point provides a simple working
example.


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


Then use Fabric to perform various development tasks. For example, to tag, build
and upload to testpypi

::

    $ git tag 0.3.5   # no 'v' prefix or anything
    $ fab build
    $ fab upload

This requires write access to both the GitHub repo and to the PyPI test site.

See ``fab -l`` for more options and ``fab -d <subcommand>`` for details.


Maturity notes
--------------

The RQ dashboard is currently being developed and is in beta stage.


.. _piptools: https://github.com/nvie/pip-tools
.. _Flask: http://flask.pocoo.org/
.. _RQ: http://python-rq.org/

.. |Can I Use Python 3?| image:: https://caniusepython3.com/project/rq-dashboard.svg
   :target: https://caniusepython3.com/project/rq-dashboard
.. |image1| image:: https://cloud.github.com/downloads/nvie/rq-dashboard/scrot_high.png
.. |image2| image:: https://cloud.github.com/downloads/nvie/rq-dashboard/scrot_failed.png
