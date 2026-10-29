"""Migración: agrega la columna usuario_id a rutas_guardadas.

`db.create_all()` crea tablas nuevas (como `usuarios`) pero no altera
tablas que ya existen — por eso esta migración aparte. Es seguro
correrla varias veces (usa IF NOT EXISTS).

Uso:
    python scripts/agregar_usuario_id.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text

from app import create_app
from app.models import db


def migrar():
    app = create_app()
    with app.app_context():
        db.session.execute(
            text(
                "ALTER TABLE rutas_guardadas "
                "ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id)"
            )
        )
        db.session.commit()
    print("Listo: rutas_guardadas.usuario_id existe.")


if __name__ == "__main__":
    migrar()
