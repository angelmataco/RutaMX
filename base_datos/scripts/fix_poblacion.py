"""Llena la columna `poblacion` con cifras verificadas del Censo de
Población y Vivienda 2020 (INEGI) — el último censo completo publicado
por ciudad/municipio. El Censo 2030 todavía no existe y la Encuesta
Intercensal 2025 no publica cifras por localidad, así que usar "2025"
implicaría inventar números; 2020 es lo más reciente que se puede
verificar de verdad.

Solo se llenan los destinos donde encontramos una cifra confiable. Los
demás (pueblos mágicos pequeños, sitios turísticos dentro de una ciudad)
se quedan en NULL a propósito, en vez de inventar un número.

Uso:
    python scripts/fix_poblacion.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Destino, Estado, db

# (nombre, estado) -> población (Censo INEGI 2020)
POBLACION = {
    ("Aguascalientes", "Aguascalientes"): 863893,
    ("Mexicali", "Baja California"): 854186,
    ("Tijuana", "Baja California"): 1810645,
    ("Ensenada", "Baja California"): 330652,
    ("La Paz", "Baja California Sur"): 250141,
    ("San Francisco de Campeche", "Campeche"): 249623,
    ("Ciudad del Carmen", "Campeche"): 191238,
    ("Tuxtla Gutiérrez", "Chiapas"): 578830,
    ("Tapachula", "Chiapas"): 217550,
    ("San Cristóbal de las Casas", "Chiapas"): 183509,
    ("Comitán", "Chiapas"): 113479,
    ("Chihuahua", "Chihuahua"): 925762,
    ("Ciudad Juárez", "Chihuahua"): 1501551,
    ("Ciudad de México", "Ciudad de México"): 9209944,
    ("Saltillo", "Coahuila"): 864431,
    ("Torreón", "Coahuila"): 690193,
    ("Colima", "Colima"): 146965,
    ("Manzanillo", "Colima"): 159853,
    ("Durango", "Durango"): 616068,
    ("León", "Guanajuato"): 1579803,
    ("Irapuato", "Guanajuato"): 452090,
    ("Celaya", "Guanajuato"): 378143,
    ("Chilpancingo", "Guerrero"): 225728,
    ("Acapulco", "Guerrero"): 658609,
    ("Pachuca", "Hidalgo"): 297848,
    ("Guadalajara", "Jalisco"): 1385621,
    ("Zapopan", "Jalisco"): 1257547,
    ("Puerto Vallarta", "Jalisco"): 224166,
    ("Lagos de Moreno", "Jalisco"): 111569,
    ("Toluca", "México"): 223876,
    ("Morelia", "Michoacán"): 743275,
    ("Uruapan", "Michoacán"): 299523,
    ("Cuernavaca", "Morelos"): 341029,
    ("Tepic", "Nayarit"): 371387,
    ("Monterrey", "Nuevo León"): 1142952,
    ("Oaxaca de Juárez", "Oaxaca"): 258913,
    ("Puebla de Zaragoza", "Puebla"): 1542232,
    ("Querétaro", "Querétaro"): 794789,
    ("Chetumal", "Quintana Roo"): 169028,
    ("Cancún", "Quintana Roo"): 888797,
    ("Playa del Carmen", "Quintana Roo"): 304942,
    ("San Luis Potosí", "San Luis Potosí"): 845941,
    ("Culiacán", "Sinaloa"): 808416,
    ("Mazatlán", "Sinaloa"): 441975,
    ("Los Mochis", "Sinaloa"): 298009,
    ("Hermosillo", "Sonora"): 855563,
    ("Ciudad Obregón", "Sonora"): 329404,
    ("Villahermosa", "Tabasco"): 340060,
    ("Ciudad Victoria", "Tamaulipas"): 332100,
    ("Reynosa", "Tamaulipas"): 691557,
    ("Tampico", "Tamaulipas"): 297373,
    ("Xalapa", "Veracruz"): 443063,
    ("Veracruz", "Veracruz"): 405952,
    ("Córdoba", "Veracruz"): 139075,
    ("Orizaba", "Veracruz"): 120500,
    ("Mérida", "Yucatán"): 921771,
    ("Zacatecas", "Zacatecas"): 138444,
}


def fix():
    app = create_app()

    with app.app_context():
        actualizados = 0
        no_encontrados = []

        for (nombre, estado_nombre), poblacion in POBLACION.items():
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
