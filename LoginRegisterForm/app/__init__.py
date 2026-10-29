import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, request
from .extensions import db


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_prefixed_env()

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("FLASK_SECRET_KEY is not set")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("FLASK_SQLALCHEMY_DATABASE_URI is not set")

    app.config.update(
        SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV_NAME") == "production",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
    )

    db.init_app(app)

    from .auth import auth_bp
    from .main import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.after_request
    def no_cache_for_auth_pages(response):
        if request.endpoint in ('auth.login', 'main.dashboard'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    with app.app_context():
        from . import models
        db.create_all()

    return app