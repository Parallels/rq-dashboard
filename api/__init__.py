from functools import wraps
from flask import current_app


def jsonify(f):
    @wraps(f)
    def _wrapped(*args, **kwargs):
        from flask import jsonify as flask_jsonify
        try:
            result_dict = f(*args, **kwargs)
        except Exception as e:
            result_dict = dict(status='error')
            if current_app.config['DEBUG']:
                result_dict['reason'] = e.message
                from traceback import format_exc
                result_dict['exc_info'] = format_exc(e)
        return flask_jsonify(**result_dict)
    return _wrapped

