import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, redirect, url_for, session, g, jsonify, request
from authlib.integrations.flask_client import OAuth

from rq_dashboard.web import blueprint as rq_dashboard_blueprint

OIDC_CLIENT_ID = os.environ.get('OIDC_CLIENT_ID')
OIDC_CLIENT_SECRET = os.environ.get('OIDC_CLIENT_SECRET')
OIDC_SERVER_METADATA_URL = os.environ.get('OIDC_SERVER_METADATA_URL')

if not all([OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_SERVER_METADATA_URL]):
    raise RuntimeError(
        "Ошибка: OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, и OIDC_SERVER_METADATA_URL "
        "должны быть установлены как переменные окружения."
    )

app = Flask(__name__)

app.config['RQ_DASHBOARD_REDIS_URL'] = [os.environ.get('RQ_REDIS_URL')]

oauth = OAuth(app)


oauth.register(
    name='oidc_provider',
    client_id=OIDC_CLIENT_ID,
    client_secret=OIDC_CLIENT_SECRET,
    server_metadata_url=OIDC_SERVER_METADATA_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)


@app.route('/login')
def login():
    redirect_uri = url_for('auth_callback', _external=True)
    return oauth.oidc_provider.authorize_redirect(redirect_uri)


@app.route('/auth-callback')
def auth_callback():
    try:
        token = oauth.oidc_provider.authorize_access_token()
        session['user'] = token.get('userinfo')
        return redirect(url_for('rq_dashboard.queues_overview'))

    except Exception as e:
        return f"Ошибка аутентификации: {e}", 400


@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('rq_dashboard.queues_overview'))
    return redirect(url_for('login'))


def require_auth():
    if 'user' not in session:
        return redirect(url_for('login'))
    g.user = session.get('user')


rq_dashboard_blueprint.before_request(require_auth)
app.register_blueprint(rq_dashboard_blueprint, url_prefix="/dashboard")

# --- 5. Запуск приложения ---
if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')