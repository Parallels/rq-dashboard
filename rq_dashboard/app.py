"""
Application factory so RQ Dashboard can run under Gunicorn with a URL prefix.

The upstream project exposes a Flask blueprint. This module wraps the
blueprint with a fully configured Flask application that mirrors the CLI
behaviour while honouring environment variables that we use inside Docker.
"""
import os
from pathlib import Path
from typing import Optional

from rq.serializers import JSONSerializer

from .cli import make_flask_app
from .web import config as service_config
from .web import setup_rq_connection

_TRUTHY = {"1", "true", "yes", "on", "t", "y"}


def _normalize_prefix(raw_prefix: Optional[str]) -> str:
    """Return a normalised URL prefix suitable for blueprint registration."""
    if not raw_prefix:
        return ""
    prefix = raw_prefix.strip()
    if not prefix:
        return ""
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    # Avoid returning "/" because Flask treats that as no prefix.
    prefix = prefix.rstrip("/")
    return prefix or ""


def _str_to_bool(value: str) -> bool:
    return value.lower() in _TRUTHY


def _apply_environment_config(app, url_prefix: str) -> None:
    """Overlay configuration derived from environment variables."""
    redis_url = os.environ.get("RQ_DASHBOARD_REDIS_URL") or os.environ.get("REDIS_URL")
    if redis_url:
        app.config["RQ_DASHBOARD_REDIS_URL"] = redis_url
    elif app.config.get("RQ_DASHBOARD_REDIS_URL") is None:
        app.config["RQ_DASHBOARD_REDIS_URL"] = "redis://redis:6379/0"

    disable_delete_env = os.environ.get("RQ_DASHBOARD_DISABLE_DELETE")
    if disable_delete_env is not None:
        app.config["RQ_DASHBOARD_DISABLE_DELETE"] = _str_to_bool(disable_delete_env)

    poll_interval_env = os.environ.get("RQ_DASHBOARD_POLL_INTERVAL")
    if poll_interval_env:
        try:
            app.config["RQ_DASHBOARD_POLL_INTERVAL"] = int(poll_interval_env)
        except ValueError:
            pass

    if _str_to_bool(os.environ.get("RQ_DASHBOARD_JSON_SERIALIZER", "false")):
        service_config.serializer = JSONSerializer

    # Honour any other RQ_DASHBOARD_* values so new settings flow through
    # without additional code changes.
    for key, value in os.environ.items():
        if key.startswith("RQ_DASHBOARD_"):
            if key in {
                "RQ_DASHBOARD_REDIS_URL",
                "RQ_DASHBOARD_DISABLE_DELETE",
                "RQ_DASHBOARD_POLL_INTERVAL",
                "RQ_DASHBOARD_JSON_SERIALIZER",
                "RQ_DASHBOARD_URL_PREFIX",
                "RQ_DASHBOARD_USERNAME",
                "RQ_DASHBOARD_PASSWORD",
                "RQ_DASHBOARD_CONFIG",
            }:
                continue
            app.config[key] = value

    app.config["APPLICATION_ROOT"] = url_prefix or "/"
    app.config.setdefault("PREFERRED_URL_SCHEME", os.environ.get("PREFERRED_URL_SCHEME", "http"))


def create_app():
    """Create and configure a Flask app instance for the dashboard."""
    url_prefix = _normalize_prefix(os.environ.get("RQ_DASHBOARD_URL_PREFIX", "/rq-dashboard"))
    username = os.environ.get("RQ_DASHBOARD_USERNAME")
    password = os.environ.get("RQ_DASHBOARD_PASSWORD")
    config_module = os.environ.get("RQ_DASHBOARD_CONFIG")

    app = make_flask_app(config_module, username, password, url_prefix)

    static_root = Path(__file__).resolve().parent / "static"
    app.static_folder = str(static_root)
    app.static_url_path = f"{url_prefix}/static" if url_prefix else "/static"

    _apply_environment_config(app, url_prefix)
    setup_rq_connection(app)

    return app
