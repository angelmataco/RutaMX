"""Corrige los destinos del segundo/tercer lote (seed_destinos_v2.py) que
quedaron con una sola etiqueta de interés. Decide la segunda etiqueta
según palabras clave reales en la descripción de cada uno (no al azar),
siguiendo las mismas reglas que ya usamos antes: "cultura" es amplio,
"comida" solo si hay una razón concreta en el texto.

Uso:
    python scripts/fix_intereses_v3.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Destino, db
from sqlalchemy import func

REGLAS_NATURALEZA = [
    "cascada", "río", "rio ", "laguna", "lago", "bosque", "sierra", "montaña",
    "cañón", "parque nacional", "reserva", "desierto", "isla ", "volcán",
    "manantial", "humedal", "gruta", "cueva", "mirador", "senderismo",
    "avistamiento", "biosfera", "ballenas", "flamencos", "manglares",
    "arrecife", "snorkel", "buceo", "aves", "abismo", "cráter", "escalada",
]
REGLAS_PLAYAS = [
    "playa", "costa", "golfo", "caribe", "malecón", "surfistas", "bahía",
]
REGLAS_CULTURA = [
    "arqueológic", "maya", "zapoteca", "tolteca", "olmeca", "totonaca",
    "museo", "convento", "misión", "templo", "basílica", "santuario",
    "histór", "colonial", "porfiriana", "franciscan", "monumento",
    "capital", "carnaval", "feria", "tradición", "artesan", "textil",
    "patrimonio", "murales", "pirámide", "fuerte ", "mina ", "minero",
    "tlatoani", "zapata",
]
REGLAS_COMIDA = [
    "fresa", "limón", "mango", "naranja", "cítric", "uva", "aceituna",
    "café", "queso", "dulce", "cajeta", "azúcar", "caña", "aguas minerales",
    "mole", "cacao", "nuez", "nuecer",
]
REGLAS_DESCANSO = ["termal", "balneario", "aguas termales"]


def _segunda_etiqueta(descripcion, actual):
    texto = descripcion.lower()

    for reglas, etiqueta in (
        (REGLAS_DESCANSO, "descanso"),
        (REGLAS_PLAYAS, "playas"),
        (REGLAS_NATURALEZA, "naturaleza"),
        (REGLAS_CULTURA, "cultura"),
        (REGLAS_COMIDA, "comida"),
    ):
        if etiqueta in actual:
            continue
        if any(palabra in texto for palabra in reglas):
            return etiqueta

    # Nada coincidió: la mayoría de sitios (ruinas, monumentos, pueblos)
    # están de todos modos en algún entorno natural (sierra, desierto,
    # valle), así que "naturaleza" es más defendible que forzar "comida"
    # sin ninguna evidencia en el texto — eso era justo el problema que
    # ya habíamos corregido antes.
    return "naturaleza" if "cultura" in actual else "cultura"


def fix():
    app = create_app()

    with app.app_context():
        destinos = Destino.query.filter(func.array_length(Destino.intereses, 1) < 2).all()
        actualizados = 0

        for destino in destinos:
            actual = list(destino.intereses or [])
            nueva = _segunda_etiqueta(destino.descripcion, actual)
            if nueva not in actual:
                destino.intereses = actual + [nueva]
                actualizados += 1

        db.session.commit()
        print(f"Destinos corregidos: {actualizados}")


if __name__ == "__main__":
    fix()
