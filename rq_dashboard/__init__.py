# Modules/blueprints
from .dashboard import dashboard


class RQDashboard(object):
    def __init__(self, app=None, url_prefix='/rq'):
        self.url_prefix = url_prefix
        if app is not None:
            self.app = app
            self.init_app(app)
        else:
            self.app = None

    def init_app(self, app):
        """Initializes the RQ-Dashboard for the specified application."""
        if self.app is not None:
            raise Exception('RQ-dashboard is already associated with an application.')

        app.register_blueprint(dashboard, url_prefix=self.url_prefix)
