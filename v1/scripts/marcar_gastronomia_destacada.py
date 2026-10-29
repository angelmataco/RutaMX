"""Marca los destinos con gastronomía destacada según fuentes públicas
verificables, y agrega los que falten en la base.

Criterio (solo esto, nada a ojo; la ciudad de cada restaurante debe estar
confirmada en la fuente):
  - UNESCO: Ciudad Creativa de la Gastronomía (en México: Ensenada 2015 y
    Mérida 2019).
  - Guía Michelin México 2026: la localidad tiene al menos un restaurante
    con estrella o con Bib Gourmand (lista completa de Bib Gourmand con
    ciudad: https://en.wikipedia.org/wiki/List_of_Michelin_Bib_Gourmand_restaurants_in_Mexico ;
    estrellas: https://en.wikipedia.org/wiki/List_of_Michelin-starred_restaurants_in_Mexico).
  - Latin America's 50 Best Restaurants 2025 (lugares 1-100), con la ciudad
    confirmada (Forbes México).
No se usa la lista de "restaurantes recomendados" de Michelin (133) ni la
UNESCO de cocina tradicional (patrimonio inmaterial) porque no dan una
ciudad por restaurante.

Por cada lugar reconocido:
  1. Agrega, si no existen, las columnas `gastronomia_destacada` y
     `reconocimiento_gastronomico` (migración segura de repetir).
  2. Marca el destino, guarda el motivo con su fuente y se asegura de que
     tenga la etiqueta "comida" (las demás etiquetas no se tocan).
  3. Si el lugar no está en la base, lo agrega con coordenadas reales de
     Nominatim (regla del proyecto: no inventar datos).

Es seguro repetirlo. Uso:
    python scripts/marcar_gastronomia_destacada.py
"""

import os
import sys
import time
import unicodedata

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text

from app import create_app
from app.models import Destino, Estado, db
from app.services.maps_service import geocodificar

UNESCO = "https://www.unesco.org/en/creative-cities"
MICHELIN = "https://guide.michelin.com/mx/es"

# (nombre en la base, estado, motivo). Fuentes: lista de restaurantes con
# estrella Michelin en México (2026), Guía Michelin México 2026 (Bib Gourmand,
# Excélsior) y la red de Ciudades Creativas de la UNESCO.
RECONOCIDOS = [
    ("Ciudad de México", "Ciudad de México",
     "Guía Michelin México 2026: Pujol y Quintonil (2 estrellas), 9 restaurantes con 1 estrella y 27 Bib Gourmand. "
     "Latin America's 50 Best 2025: Quintonil (#7), Máximo (#30), Rosetta (#39), Pujol, Sud 777, Em, Nicos"),
    ("Guadalajara", "Jalisco",
     "Guía Michelin México 2026: Alcalde y Xokol (1 estrella) y 2 Bib Gourmand (PalReal, Tacos y gorditas Elvira). "
     "Latin America's 50 Best 2025: Alcalde (#15)"),
    ("Puerto Vallarta", "Jalisco", "Guía Michelin México 2026: Bib Gourmand ICÚ"),
    ("Ensenada", "Baja California",
     "UNESCO Ciudad Creativa de la Gastronomía (2015). Guía Michelin México 2026: Olivea Farm to Table (1 estrella) y "
     "5 Bib Gourmand (Casa Marcelo, Fauna, Humo y Sal, La Concheria, Sabina). Latin America's 50 Best 2025: Fauna (#18)"),
    ("Valle de Guadalupe", "Baja California",
     "Guía Michelin México 2026: Animalón, Conchas de Piedra, Damiana y Lunario (1 estrella) y Bib Gourmand "
     "(La Cocina de Doña Esthela, Villa Torél). Latin America's 50 Best 2025: Villa Torél (#17) y Lunario (#90)"),
    ("Tijuana", "Baja California", "Guía Michelin México 2026: Bib Gourmand Carmelita Molino y Cocina"),
    ("Mérida", "Yucatán",
     "UNESCO Ciudad Creativa de la Gastronomía (2019). Guía Michelin México 2026: Huniik y La Barra de Huniik "
     "(1 estrella) y 2 Bib Gourmand (Pancho Maíz, Taquerías Kisín). Latin America's 50 Best 2025: Huniik (#32)"),
    ("Playa del Carmen", "Quintana Roo",
     "Guía Michelin México 2026: HA' (1 estrella) y Bib Gourmand Axiote Cocina de México"),
    ("Tulum", "Quintana Roo",
     "Guía Michelin México 2026: Bib Gourmand Cetli y Mestixa. Latin America's 50 Best 2025: Arca (#22)"),
    ("Los Cabos", "Baja California Sur", "Guía Michelin México 2026: Cocina de Autor Los Cabos (1 estrella)"),
    ("San José del Cabo", "Baja California Sur", "Guía Michelin México 2026: Bib Gourmand Flora's Field Kitchen"),
    ("Oaxaca de Juárez", "Oaxaca",
     "Guía Michelin México 2026: Los Danzantes Oaxaca y Levadura de Olla (1 estrella) y 5 Bib Gourmand "
     "(La Olla, Labo Fermento, Las Quince Letras, Tierra del Sol, Xaok)"),
    ("Monterrey", "Nuevo León",
     "Guía Michelin México 2026: KOLI Cocina de Origen (1 estrella) y Bib Gourmand Tacos Doña Mary La Gritona. "
     "Latin America's 50 Best 2025: Cara de Vaca (#54)"),
    ("San Pedro Garza García", "Nuevo León",
     "Guía Michelin México 2026: Pangea (1 estrella) y Bib Gourmand El Bambi's Café"),
    ("Puebla de Zaragoza", "Puebla",
     "Guía Michelin México 2026: 7 Bib Gourmand (Cultivo, El Güero Marinero, Jacinto y Yo, Los Camellos, Moyuelo, "
     "Casareyna, Semitas Beto)"),
    ("Atlixco", "Puebla", "Guía Michelin México 2026: Bib Gourmand Vica"),
    # --- lugares que no estaban en la base ---
    ("Chocholá", "Yucatán", "Guía Michelin México 2026: Ixi'im (1 estrella, Estrella Verde)"),
    ("Cabo San Lucas", "Baja California Sur", "Guía Michelin México 2026: Bib Gourmand Metate"),
    ("Puerto Morelos", "Quintana Roo",
     "Guía Michelin México 2026: Bib Gourmand Punta Corcho. Latin America's 50 Best 2025: Le Chique (#58)"),
    ("Tixkokob", "Yucatán", "Guía Michelin México 2026: Bib Gourmand Pueblo Pibil"),
    ("El Pescadero", "Baja California Sur", "Guía Michelin México 2026: Bib Gourmand Cocina de Campo by Agricole"),
]

# Lugares que no estaban en la base y se agregan (coordenadas de Nominatim).
NUEVOS = {
    "Chocholá": {
        "tipo": "sitio_turistico",
        "busqueda": "Chocholá, Yucatán",
        "descripcion": "Pueblo yucateco cercano a Mérida, sede del restaurante Ixi'im, con estrella Michelin.",
        "intereses": ["comida"],
    },
    "Cabo San Lucas": {
        "tipo": "ciudad_principal",
        "busqueda": "Cabo San Lucas, Baja California Sur",
        "descripcion": "Ciudad turística en el extremo sur de la península de Baja California, en el municipio de Los Cabos.",
        "intereses": ["comida", "playas"],
    },
    "Puerto Morelos": {
        "tipo": "sitio_turistico",
        "busqueda": "Puerto Morelos, Quintana Roo",
        "descripcion": "Puerto pesquero y destino de playa en la Riviera Maya, con arrecife de coral frente a la costa.",
        "intereses": ["comida", "playas"],
    },
    "Tixkokob": {
        "tipo": "sitio_turistico",
        "busqueda": "Tixkokob, Yucatán",
        "descripcion": "Pueblo yucateco cercano a Mérida, sede del restaurante Pueblo Pibil, reconocido por la Guía Michelin.",
        "intereses": ["comida"],
    },
    "El Pescadero": {
        "tipo": "sitio_turistico",
        "busqueda": "El Pescadero, Baja California Sur",
        "descripcion": "Poblado agrícola entre Cabo San Lucas y Todos Santos, sede de Cocina de Campo by Agricole, reconocida por la Guía Michelin.",
        "intereses": ["comida"],
    },
}


def _n(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def migrar():
    db.session.execute(text("ALTER TABLE destinos ADD COLUMN IF NOT EXISTS gastronomia_destacada BOOLEAN NOT NULL DEFAULT FALSE"))
    db.session.execute(text("ALTER TABLE destinos ADD COLUMN IF NOT EXISTS reconocimiento_gastronomico TEXT"))
    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        migrar()
        marcados, agregados, sin_encontrar = [], [], []

        for nombre, estado_nombre, motivo in RECONOCIDOS:
            estado = Estado.query.filter_by(nombre=estado_nombre).first()
            destino = next(
                (d for d in Destino.query.filter_by(estado_id=estado.id).all() if _n(d.nombre) == _n(nombre)), None
            )

            if destino is None and nombre in NUEVOS:
                datos = NUEVOS[nombre]
                geo = geocodificar(datos["busqueda"])
                time.sleep(1)  # política de uso de Nominatim
                if not geo:
                    sin_encontrar.append(nombre)
                    continue
                lat, lon, encontrado = geo
                destino = Destino(
                    nombre=nombre, estado_id=estado.id, tipo=datos["tipo"], lat=lat, lon=lon,
                    descripcion=datos["descripcion"], intereses=datos["intereses"], fuente="curada",
                )
                db.session.add(destino)
                agregados.append((nombre, lat, lon, encontrado))
            elif destino is None:
                sin_encontrar.append(nombre)
                continue

            destino.gastronomia_destacada = True
            destino.reconocimiento_gastronomico = motivo
            if "comida" not in (destino.intereses or []):
                destino.intereses = list(destino.intereses or []) + ["comida"]  # solo se agrega, no se quita nada
            marcados.append(destino.nombre)

        db.session.commit()

    print(f"Marcados como gastronomía destacada ({len(marcados)}): {', '.join(marcados)}")
    for nombre, lat, lon, encontrado in agregados:
        print(f"Agregado: {nombre} ({lat:.4f}, {lon:.4f}) — Nominatim: {encontrado}")
    if sin_encontrar:
        print(f"NO se pudieron marcar/agregar: {', '.join(sin_encontrar)}")


if __name__ == "__main__":
    main()
