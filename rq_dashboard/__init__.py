# Modules/blueprints
from .dashboard import dashboard


class RQDashboard(object):
    def __init__(self, app, url_prefix='/rq'):
        self.init_app(app, url_prefix)

    def init_app(self, app, url_prefix='/rq'):
        app.register_blueprint(dashboard, url_prefix=url_prefix)
