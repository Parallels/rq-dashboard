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

You can either run the dashboard standalone, like this:

.. code:: console

    $ rq-dashboard
    * Running on http://127.0.0.1:9181/
    ...


Integrating the dashboard in your Flask app
-------------------------------------------

Or you can integrate the dashboard in your own `Flask`_ app by accessing the
blueprint directly in the normal way, e.g.:

.. code:: python

    from flask import Flask
    import rq_dashboard

    app = Flask(__name__)
    app.config.from_object('rq_dashboard.default_settings')
    app.register_blueprint(rq_dashboard.blueprint.blueprint)

    @app.route("/")
    def hello():
        return "Hello World!"

    if __name__ == "__main__":
        app.run()


The ``scripts/rq_dashboard.py.main`` entry point provides a simple working
example.


Adding dependencies
-------------------

We use pip-tools to keep our development dependencies up to date

::

    $ pip install --upgrade pip
    $ pip install git+https://github.com/nvie/pip-tools.git@future

Now make changes to the ``requirements.in`` file, and resolve all the
2nd-level dependencies into ``requirements.txt`` like so:

::

    $ pip-compile --annotate requirements.in


Making a release
----------------

The development environment assumes you are in a virtualenv and have pulled in
the necessary build time (and run time) dependencies with

::

    $ pip install -r requirements.txt


See the pip_docs_on_requirements_ and in particular the setup_vs_requirements_
article by Donald Stufft.

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

See ``fab -l`` for more options.


Maturity notes
--------------

The RQ dashboard is currently being developed and is in beta stage.


.. _Flask: http://flask.pocoo.org/
.. _RQ: http://python-rq.org/
.. _pip_docs_on_requirements: http://pip.readthedocs.org/en/stable/user_guide.html#requirements-files
.. _setup_vs_requirements: https://caremad.io/2013/07/setup-vs-requirement

.. |Can I Use Python 3?| image:: https://caniusepython3.com/project/rq-dashboard.svg
   :target: https://caniusepython3.com/project/rq-dashboard
.. |image1| image:: https://cloud.github.com/downloads/nvie/rq-dashboard/scrot_high.png
.. |image2| image:: https://cloud.github.com/downloads/nvie/rq-dashboard/scrot_failed.png
