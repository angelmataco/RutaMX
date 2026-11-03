"""Entorno aislado para probar `base_datos` (T-03).

Las pruebas de integración usan SOLO la base indicada en la variable
`RUTAMX_TEST_DB_URL` (un PostgreSQL desechable en este equipo). Nunca se carga
el `.env` ni `instance/config.py`, y nunca se usa Supabase como respaldo:

- Si la variable falta o está vacía, las pruebas de integración se OMITEN con
  un aviso claro (no cuentan como evidencia de persistencia ni de atomicidad).
- Si apunta a un servidor que no es local, o a una base cuyo nombre no termina
  en `_prueba` o `_test`, la corrida se detiene (las pruebas borran tablas).
- Si está definida y la conexión falla, la prueba falla (no se oculta).

Los datos son ficticios. Ejemplo de la variable (sin contraseña real):
    RUTAMX_TEST_DB_URL=postgresql://rutamx_test@127.0.0.1:54329/rutamx_prueba
"""

import os
from urllib.parse import urlparse

import pytest
from flask import Flask
from sqlalchemy import text

from base_datos.conexion import db, iniciar_base_datos

HOSTS_LOCALES = {"127.0.0.1", "localhost", "::1"}
SUFIJOS_BASE_DESECHABLE = ("_prueba", "_test")


def _url_de_prueba():
    return os.environ.get("RUTAMX_TEST_DB_URL", "").strip()


@pytest.fixture(scope="session")
def app_prueba():
    """App de Flask mínima con la base desechable, sin configuración real."""
    url = _url_de_prueba()
    if not url:
        pytest.skip(
            "OMITIDA: falta RUTAMX_TEST_DB_URL (PostgreSQL desechable). "
            "Sin ella no hay evidencia de persistencia ni de atomicidad."
        )
    host = urlparse(url).hostname
    if host not in HOSTS_LOCALES:
        pytest.exit(
            f"RUTAMX_TEST_DB_URL apunta a '{host}', que no es local. "
            "Las pruebas solo usan una base desechable en este equipo.",
            returncode=1,
        )

    nombre_base = urlparse(url).path.lstrip("/")
    if not nombre_base.endswith(SUFIJOS_BASE_DESECHABLE):
        pytest.exit(
            f"La base '{nombre_base}' no parece desechable: su nombre debe terminar "
            f"en {' o '.join(SUFIJOS_BASE_DESECHABLE)}. Las pruebas borran tablas.",
            returncode=1,
        )

    # Importar el modelo registra las tablas en `db`.
    import base_datos.modelos  # noqa: F401

    app = Flask("pruebas_base_datos")
    app.config["SQLALCHEMY_DATABASE_URI"] = url
    iniciar_base_datos(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def bd(app_prueba):
    """Contexto de app con las tablas de rutas y usuarios vacías."""
    with app_prueba.app_context():
        db.session.execute(
            text("TRUNCATE rutas_guardadas, usuarios RESTART IDENTITY CASCADE")
        )
        db.session.commit()
        yield db
        db.session.rollback()
        db.session.remove()


@pytest.fixture()
def crear_usuario(bd):
    """Fábrica de usuarios ficticios (clave y PIN inventados)."""
    from base_datos.modelos import Usuario

    contador = {"n": 0}

    def _crear(nombre="Persona"):
        contador["n"] += 1
        usuario = Usuario(
            nombre=nombre,
            apellido=f"Ficticio{contador['n']}",
            clave_normalizada=f"{nombre.lower()}ficticio{contador['n']}",
            pin_hash="hash-ficticio",
        )
        bd.session.add(usuario)
        bd.session.commit()
        return usuario.id

    return _crear
