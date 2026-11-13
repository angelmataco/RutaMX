"""Migración: agrega a rutas_guardadas las siete columnas del catálogo.

Columnas autorizadas por Angel el 2026-11-03: descripcion, duracion_dias,
categoria, region, visibilidad, ruta_origen_id y autor_id. Todas son opcionales
o con valor por defecto ('privada'), así las filas anteriores siguen válidas y
v1 no se entera. Es segura de correr varias veces (IF NOT EXISTS) y corre en una
sola transacción: si una sentencia falla se revierte todo.

NO se ha ejecutado contra la base real. La corre Angel, con respaldo previo y
después de probarla en una copia (ver bitácora). Mientras no se ejecute, el
catálogo responde «migración pendiente» y el resto de la app sigue igual.

Uso:
    python base_datos/migraciones/agregar_columnas_catalogo.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import text

from base_datos.catalogo_valores import VISIBILIDADES

COLUMNAS = (
    "ADD COLUMN IF NOT EXISTS descripcion TEXT",
    "ADD COLUMN IF NOT EXISTS duracion_dias INTEGER CHECK (duracion_dias > 0)",
    "ADD COLUMN IF NOT EXISTS categoria TEXT",
    "ADD COLUMN IF NOT EXISTS region TEXT",
    "ADD COLUMN IF NOT EXISTS visibilidad TEXT NOT NULL DEFAULT 'privada' "
    "CHECK (visibilidad IN (" + ", ".join(f"'{v}'" for v in VISIBILIDADES) + "))",
    "ADD COLUMN IF NOT EXISTS ruta_origen_id INTEGER REFERENCES rutas_guardadas(id) ON DELETE SET NULL",
    "ADD COLUMN IF NOT EXISTS autor_id INTEGER REFERENCES usuarios(id)",
)

SENTENCIAS = tuple(f"ALTER TABLE rutas_guardadas {c}" for c in COLUMNAS) + (
    "CREATE INDEX IF NOT EXISTS ix_rutas_guardadas_visibilidad ON rutas_guardadas (visibilidad)",
)


class ErrorMigracion(Exception):
    """La migración falló y se revirtió completa."""


def aplicar(sesion):
    """Ejecuta todas las sentencias en una transacción de `sesion`."""
    try:
        for sentencia in SENTENCIAS:
            sesion.execute(text(sentencia))
        sesion.commit()
    except Exception as error:
        sesion.rollback()
        raise ErrorMigracion("La migración del catálogo falló y se revirtió.") from error


def migrar():
    from base_datos.conexion import crear_app_minima
    from base_datos.modelos import db

    app = crear_app_minima()
    with app.app_context():
        aplicar(db.session)
    print("Listo: rutas_guardadas tiene las columnas del catálogo.")


def principal():
    """Corre la migración y devuelve el código de salida (0 bien, 1 error)."""
    try:
        migrar()
    except ErrorMigracion as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(principal())
