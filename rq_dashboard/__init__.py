def init_app(app, url_prefix='/rq'):
    from .dashboard import dashboard
    app.register_blueprint(dashboard, url_prefix=url_prefix)
