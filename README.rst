WANTED: PROJECT MAINTAINER
==========================

This project is slowly becoming outdated, and I lack the time and
interest to further maintain it. I know this project is used by many
people, and so I’m looking for a maintainer / collaborator that can help
maintain this project, review pull requests, implement new features,
etc. Please let me know if you’re interested!

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

You can either run the dashboard standalone, like this…

.. code:: console

    $ rq-dashboard
    * Running on http://127.0.0.1:9181/
    * Restarting with reloader
    ...

Integrating the dashboard in your Flask app
-------------------------------------------

...or you can integrate the dashboard in your own `Flask`_ app, like this:

.. code:: python

    from flask import Flask
    from rq_dashboard import RQDashboard


    app = Flask(__name__)
    RQDashboard(app)

    @app.route("/")
    def hello():
        return "Hello World!"

    if __name__ == "__main__":
        app.run()

This will register the dashboard on the ``/rq`` URL root in your Flask
app. To use a different URL root, use the following:

.. code:: python

    RQDashboard(app, url_prefix='/some/other/url')

Maturity notes
--------------

The RQ dashboard is currently being developed and is in beta stage.

.. _Flask: http://flask.pocoo.org/
.. _RQ: http://python-rq.org/

.. |Can I Use Python 3?| image:: https://caniusepython3.com/project/rq-dashboard.svg
   :target: https://caniusepython3.com/project/rq-dashboard
.. |image1| image:: https://cloud.github.com/downloads/nvie/rq-dashboard/scrot_high.png
.. |image2| image:: https://cloud.github.com/downloads/nvie/rq-dashboard/scrot_failed.png
