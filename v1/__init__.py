import os

from dotenv import load_dotenv
from flask import Flask

from config import config_by_name

load_dotenv()


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    try:
        app.config.from_pyfile("config.py", silent=True)
    except FileNotFoundError:
        pass

    from base_datos.conexion import iniciar_base_datos

    iniciar_base_datos(app)

    from v1.routes import main_bp

    app.register_blueprint(main_bp)

    return app
