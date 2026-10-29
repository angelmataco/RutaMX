"""Llena población (Censo INEGI 2020) para las ciudades del segundo lote
que aparecen en la lista de ciudades mexicanas >100k habitantes ya
investigada (misma fuente que fix_poblacion.py). Solo se llenan las que
tienen una cifra oficial verificable; el resto se queda en NULL a
propósito.

Uso:
    python scripts/fix_poblacion_v2.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Destino, Estado, db

# (nombre, estado) -> población (Censo INEGI 2020, ciudades > 100k)
POBLACION_V2 = {
    ("Delicias", "Chihuahua"): 128548,
    ("Ciudad Acuña", "Coahuila"): 160225,
    ("Navojoa", "Sonora"): 120926,
    ("Tehuacán", "Puebla"): 293825,
    ("Tulancingo", "Hidalgo"): 106163,
    ("Nuevo Laredo", "Tamaulipas"): 416055,
    ("Matamoros", "Tamaulipas"): 510739,
    ("Iguala", "Guerrero"): 132854,
    ("Zamora de Hidalgo", "Michoacán"): 154546,
}


def fix():
    app = create_app()

    with app.app_context():
        actualizados = 0
        no_encontrados = []

        for (nombre, estado_nombre), poblacion in POBLACION_V2.items():
            destino = (
                Destino.query.join(Estado)
                .filter(Destino.nombre == nombre, Estado.nombre == estado_nombre)
                .first()
            )
            if not destino:
                no_encontrados.append(f"{nombre} ({estado_nombre})")
                continue

            if destino.poblacion != poblacion:
                destino.poblacion = poblacion
                actualizados += 1

        db.session.commit()
        print(f"Destinos con población actualizada: {actualizados}")
        if no_encontrados:
            print("No encontrados:")
            for item in no_encontrados:
                print(f"  - {item}")


if __name__ == "__main__":
    fix()
