# Modules/blueprints
from .dashboard import dashboard


class RQDashboard(object):

    def __init__(self, app=None, url_prefix='/rq', auth_handler=None):
        self.url_prefix = url_prefix
        if app is not None:
            self.app = app
            self.init_app(app)
        else:
            self.app = None
        if auth_handler is None:
            self.auth_handler = self.basic_auth
        self.redis_conn = None

    def basic_auth(self, username, password):
        return (self.app.config.get('AUTH_USER', None) == username and
                self.app.config.get('AUTH_PASS', None) == password)

    def init_app(self, app):
        """Initializes the RQ-Dashboard for the specified application."""
        app.register_blueprint(dashboard, url_prefix=self.url_prefix)
        app.extensions['rq-dashboard'] = self
