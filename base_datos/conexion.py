"""Conexión a la base de datos de RutaMX (Postgres en Supabase vía SQLAlchemy).

Es compartida por v1 y v2: este paquete no importa nada de ninguna de las dos
versiones. `db` es el objeto único de SQLAlchemy; `iniciar_base_datos` lo
enlaza a una app de Flask, y `crear_app_minima` arma una app solo con la base
de datos para los scripts y migraciones, sin depender de v1.
"""

import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

db = SQLAlchemy()


def iniciar_base_datos(app):
    """Configura la URL de la base y enlaza `db` a la app dada."""
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", app.config.get("SUPABASE_DB_URL"))
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)


def crear_app_minima():
    """App de Flask solo con la base de datos (para scripts y migraciones)."""
    load_dotenv()
    app = Flask(
        "base_datos",
        instance_path=os.path.join(RAIZ, "instance"),
        instance_relative_config=True,
    )
    app.config.from_pyfile("config.py", silent=True)
    iniciar_base_datos(app)
    return app
