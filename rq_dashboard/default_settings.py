"""Default Flask app configuration.

Intended to be loaded with::

    app.config.from_object(rq_dashboard.default_settings)

and then overridden as required.

"""
#: If set the RQ_DASHBOARD_REDIS_URL takes precedence over RQ_DASHBOARD_REDIS_HOST, RQ_DASHBOARD_REDIS_PORT, etc
RQ_DASHBOARD_REDIS_URL = None

RQ_DASHBOARD_REDIS_HOST = 'localhost'
RQ_DASHBOARD_REDIS_PORT = 6379
RQ_DASHBOARD_REDIS_PASSWORD = None
RQ_DASHBOARD_REDIS_DB = 0

RQ_DASHBOARD_POLL_INTERVAL = 2500  #: Web interface poll period for updates in ms
DEBUG = False
RQ_DASHBOARD_WEB_BACKGROUND = "black"
RQ_DASHBOARD_DELETE_JOBS = False

RQ_DASHBOARD_JOB_SORT_ORDER = '-age'
