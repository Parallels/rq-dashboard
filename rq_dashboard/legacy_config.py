import warnings

LEGACY_CONFIG_OPTIONS = {
    'REDIS_URL': 'RQ_DASHBOARD_REDIS_URL',
    'REDIS_HOST': 'RQ_DASHBOARD_REDIS_HOST',
    'REDIS_PORT': 'RQ_DASHBOARD_REDIS_PORT',
    'REDIS_PASSWORD': 'RQ_DASHBOARD_REDIS_PASSWORD',
    'REDIS_DB': 'RQ_DASHBOARD_REDIS_DB',
    'REDIS_SENTINELS': 'RQ_DASHBOARD_REDIS_SENTINELS',
    'REDIS_MASTER_NAME': 'RQ_DASHBOARD_REDIS_MASTER_NAME',
    'RQ_POLL_INTERVAL': 'RQ_DASHBOARD_POLL_INTERVAL',
    'WEB_BACKGROUND': 'RQ_DASHBOARD_WEB_BACKGROUND',
    'DELETE_JOBS': 'RQ_DASHBOARD_DELETE_JOBS',
}

warning_template = "Configuration option {old_name} is depricated and will be removed in future versions. "\
                   "Please use {new_name} instead."


def upgrade_config(app):
    """
    Updates old configuration options with new ones throwing warnings to those who haven't upgraded yet.
    """
    for old_name, new_name in LEGACY_CONFIG_OPTIONS.items():
        if old_name in app.config:
            warnings.warn(warning_template.format(old_name=old_name, new_name=new_name), UserWarning)
            app.config[new_name] = app.config[old_name]
