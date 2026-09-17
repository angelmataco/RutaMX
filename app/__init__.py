import os

from flask import Flask

from config import config_by_name


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    try:
        app.config.from_pyfile("config.py", silent=True)
    except FileNotFoundError:
        pass

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", app.config.get("SUPABASE_DB_URL"))
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    from app.models import db

    db.init_app(app)

    from app.routes import main_bp

    app.register_blueprint(main_bp)

    return app
