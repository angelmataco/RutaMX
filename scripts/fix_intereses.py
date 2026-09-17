"""Corrige la columna `intereses` de `destinos`.

Al sembrar los datos, "comida" se usó como etiqueta genérica de relleno en
varios lugares que en realidad son turísticos/culturales (centros
históricos, sitios arqueológicos, pueblos mineros, artesanía) sin una base
gastronómica real. Este script alinea cada etiqueta con lo que el lugar es
realmente conocido, y agrega una categoría nueva, "cultura", para todo lo
que es sitio histórico/arqueológico/artesanal y no encajaba bien en las
5 categorías originales (naturaleza, playas, pueblos_magicos, comida,
descanso).

Uso:
    python scripts/fix_intereses.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Destino, Estado, db

# (nombre, estado) -> nueva lista de intereses
CORRECCIONES = {
    # Capitales / ciudades principales
    ("Aguascalientes", "Aguascalientes"): ["cultura"],
    ("San Francisco de Campeche", "Campeche"): ["cultura", "playas"],
    ("Chihuahua", "Chihuahua"): ["naturaleza"],
    ("Ciudad de México", "Ciudad de México"): ["comida", "cultura"],
    ("Saltillo", "Coahuila"): ["cultura"],
    ("Durango", "Durango"): ["cultura"],
    ("Guanajuato", "Guanajuato"): ["cultura"],
    ("León", "Guanajuato"): ["cultura"],
    ("Chilpancingo", "Guerrero"): ["cultura"],
    ("Pachuca", "Hidalgo"): ["cultura"],
    ("Guadalajara", "Jalisco"): ["comida", "cultura"],
    ("Morelia", "Michoacán"): ["cultura", "comida"],
    ("Tepic", "Nayarit"): ["cultura"],
    ("Monterrey", "Nuevo León"): ["cultura", "comida"],
    ("Oaxaca de Juárez", "Oaxaca"): ["comida", "cultura"],
    ("Puebla de Zaragoza", "Puebla"): ["comida", "cultura"],
    ("Querétaro", "Querétaro"): ["cultura"],
    ("San Luis Potosí", "San Luis Potosí"): ["cultura"],
    ("Culiacán", "Sinaloa"): ["cultura"],
    ("Hermosillo", "Sonora"): ["cultura"],
    ("Ciudad Victoria", "Tamaulipas"): ["cultura"],
    ("Tlaxcala de Xicohténcatl", "Tlaxcala"): ["cultura"],
    ("Veracruz", "Veracruz"): ["playas", "comida", "cultura"],
    ("Mérida", "Yucatán"): ["cultura", "comida"],
    ("Zacatecas", "Zacatecas"): ["cultura"],

    # Pueblos mágicos
    ("San Miguel de Allende", "Guanajuato"): ["cultura"],
    ("San Cristóbal de las Casas", "Chiapas"): ["cultura"],
    ("Pátzcuaro", "Michoacán"): ["cultura", "naturaleza"],
    ("Taxco", "Guerrero"): ["cultura"],
    ("Izamal", "Yucatán"): ["cultura"],
    ("Valladolid", "Yucatán"): ["cultura"],
    ("Dolores Hidalgo", "Guanajuato"): ["cultura", "comida"],
    ("Álamos", "Sonora"): ["cultura"],
    ("Xilitla", "San Luis Potosí"): ["naturaleza", "cultura"],
    ("Loreto", "Baja California Sur"): ["playas", "naturaleza", "cultura"],
    ("Palizada", "Campeche"): ["naturaleza", "cultura"],
    ("Chiapa de Corzo", "Chiapas"): ["naturaleza", "cultura"],
    ("Palenque", "Chiapas"): ["naturaleza", "cultura"],
    ("Comitán", "Chiapas"): ["naturaleza", "cultura"],
    ("Batopilas", "Chihuahua"): ["naturaleza", "cultura"],
    ("Yuriria", "Guanajuato"): ["naturaleza", "cultura"],
    ("Real del Monte", "Hidalgo"): ["comida", "cultura"],
    ("Lagos de Moreno", "Jalisco"): ["cultura"],
    ("Malinalco", "México"): ["naturaleza", "cultura"],
    ("Tepotzotlán", "México"): ["cultura"],
    ("Tlalpujahua", "Michoacán"): ["cultura"],
    ("Tlayacapan", "Morelos"): ["cultura"],
    ("Chignahuapan", "Puebla"): ["cultura"],
    ("Zacatlán", "Puebla"): ["naturaleza", "comida", "cultura"],
    ("Tulum", "Quintana Roo"): ["playas", "naturaleza", "cultura"],
    ("Cosalá", "Sinaloa"): ["cultura"],
    ("El Fuerte", "Sinaloa"): ["naturaleza", "cultura"],
    ("Tula", "Tamaulipas"): ["comida", "cultura"],
    ("Huamantla", "Tlaxcala"): ["cultura"],
    ("Papantla", "Veracruz"): ["comida", "cultura"],
    ("Jerez", "Zacatecas"): ["cultura"],
    ("Sombrerete", "Zacatecas"): ["naturaleza", "cultura"],

    # Ciudades adicionales
    ("Ciudad Juárez", "Chihuahua"): ["cultura"],
    ("Torreón", "Coahuila"): ["cultura"],
    ("Zapopan", "Jalisco"): ["comida", "cultura"],
    ("Los Mochis", "Sinaloa"): ["cultura"],
    ("Ciudad Obregón", "Sonora"): ["cultura"],
    ("Reynosa", "Tamaulipas"): ["cultura"],
    ("Córdoba", "Veracruz"): ["comida", "cultura"],

    # Sitios turísticos (el caso que detectó Angel: León y similares)
    ("Centro Histórico de León", "Guanajuato"): ["cultura"],
    ("Zona Piel y Calzado de León", "Guanajuato"): ["cultura"],
    ("Centro Histórico de la Ciudad de México", "Ciudad de México"): ["cultura"],
    ("Coyoacán", "Ciudad de México"): ["cultura", "comida"],
    ("Xochimilco", "Ciudad de México"): ["naturaleza", "cultura"],
    ("Chichén Itzá", "Yucatán"): ["cultura"],
    ("Centro Histórico de Guadalajara", "Jalisco"): ["cultura"],
}


def fix():
    app = create_app()

    with app.app_context():
        actualizados = 0
        no_encontrados = []

        for (nombre, estado_nombre), nuevos_intereses in CORRECCIONES.items():
            destino = (
                Destino.query.join(Estado)
                .filter(Destino.nombre == nombre, Estado.nombre == estado_nombre)
                .first()
            )
            if not destino:
                no_encontrados.append(f"{nombre} ({estado_nombre})")
                continue

            if destino.intereses != nuevos_intereses:
                destino.intereses = nuevos_intereses
                actualizados += 1

        db.session.commit()
        print(f"Destinos actualizados: {actualizados}")
        if no_encontrados:
            print("No encontrados (revisar nombre/estado):")
            for item in no_encontrados:
                print(f"  - {item}")


if __name__ == "__main__":
    fix()
