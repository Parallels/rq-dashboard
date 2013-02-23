# Modules/blueprints
from .dashboard import dashboard


class RQDashboard(object):
    def __init__(self, app=None, url_prefix='/rq', **kwargs):
        self.url_prefix = url_prefix
        if app is not None:
            self.init_app(app, **kwargs)
        else:
            self.app = None

    def init_app(self, app, **kwargs):
        """Initializes the Flask-Gravata extension for the specified application.

        :param app: The application.
        """

        if not hasattr(app, 'extensions'):
            app.extensions = {}

        if self.app is not None:
            raise Exception('RQ-dashboard is already associated with an application.')

        self.app = app
        app.extensions['rq-dashboard'] = self

        app.register_blueprint(dashboard, url_prefix=self.url_prefix)


