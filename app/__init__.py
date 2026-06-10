import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import BadRequest

from .config import DevelopmentConfig, ProductionConfig, TestingConfig

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)


def _select_config_class():
    env = os.environ.get("FLASK_ENV", "production").strip().lower()
    if env in {"development", "dev"}:
        return DevelopmentConfig
    if env == "testing":
        return TestingConfig
    return ProductionConfig


def create_app(config_class=None):
    config_class = config_class or _select_config_class()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = "main.login"
    login_manager.login_message_category = "warning"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    from .routes import main_bp

    app.register_blueprint(main_bp)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=(self)"
        return response

    @app.errorhandler(400)
    def bad_request(error):
        if isinstance(error, BadRequest) and "CSRF" in str(error.description):
            return "Bad request: invalid or missing CSRF token.", 400
        return "Bad request.", 400

    @app.errorhandler(403)
    def forbidden(_error):
        return "Forbidden.", 403

    with app.app_context():
        db.create_all()
        from .schema import ensure_schema

        ensure_schema()
        from .seed import seed_database

        seed_database()

    return app
