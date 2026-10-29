"""Segunda pasada de corrección de `intereses`.

Reglas nuevas (pedidas por el equipo):
- Cada destino debe tener al menos 2 etiquetas.
- "comida" ya NO es una etiqueta de relleno: solo se usa donde hay un
  platillo, bebida o tradición gastronómica específica y reconocida
  (ej. cajeta en Celaya, fresa en Irapuato, mole en Oaxaca), no solo
  porque "toda ciudad tiene restaurantes".
- "cultura" se usa de forma amplia: casi cualquier ciudad o pueblo tiene
  algo que ver (centro histórico, museo, arquitectura, sitio arqueológico).

Uso:
    python scripts/fix_intereses_v2.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Destino, Estado, db

# (nombre, estado) -> nueva lista de intereses (reemplaza por completo)
CORRECCIONES = {
    ("Aguascalientes", "Aguascalientes"): ["cultura", "comida"],
    ("Mexicali", "Baja California"): ["comida", "cultura"],
    ("Tijuana", "Baja California"): ["comida", "cultura"],
    ("Tecate", "Baja California"): ["comida", "naturaleza"],
    ("Todos Santos", "Baja California Sur"): ["playas", "descanso", "cultura"],
    ("Ciudad del Carmen", "Campeche"): ["playas", "naturaleza"],
    ("Tapachula", "Chiapas"): ["comida", "cultura"],
    ("Tuxtla Gutiérrez", "Chiapas"): ["naturaleza", "cultura"],
    ("San Cristóbal de las Casas", "Chiapas"): ["cultura", "naturaleza"],
    ("Chihuahua", "Chihuahua"): ["naturaleza", "cultura"],
    ("Ciudad Juárez", "Chihuahua"): ["cultura", "comida"],
    ("Creel", "Chihuahua"): ["naturaleza", "cultura"],
    ("Centro Histórico de la Ciudad de México", "Ciudad de México"): ["cultura", "comida"],
    ("Saltillo", "Coahuila"): ["cultura", "comida"],
    ("Torreón", "Coahuila"): ["cultura", "comida"],
    ("Cuatro Ciénegas", "Coahuila"): ["naturaleza", "cultura"],
    ("Parras", "Coahuila"): ["comida", "cultura"],
    ("Colima", "Colima"): ["naturaleza", "cultura"],
    ("Comala", "Colima"): ["comida", "cultura"],
    ("Durango", "Durango"): ["cultura", "comida"],
    ("Mapimí", "Durango"): ["naturaleza", "cultura"],
    ("Celaya", "Guanajuato"): ["comida", "cultura"],
    ("Guanajuato", "Guanajuato"): ["cultura", "comida"],
    ("Irapuato", "Guanajuato"): ["comida", "cultura"],
    ("León", "Guanajuato"): ["cultura", "comida"],
    ("San Miguel de Allende", "Guanajuato"): ["cultura", "comida"],
    ("Centro Histórico de León", "Guanajuato"): ["cultura", "comida"],
    ("Zona Piel y Calzado de León", "Guanajuato"): ["cultura", "comida"],
    ("Chilpancingo", "Guerrero"): ["cultura", "comida"],
    ("Taxco", "Guerrero"): ["cultura", "naturaleza"],
    ("Pachuca", "Hidalgo"): ["cultura", "comida"],
    ("Huasca de Ocampo", "Hidalgo"): ["naturaleza", "cultura"],
    ("Mineral del Chico", "Hidalgo"): ["naturaleza", "cultura"],
    ("Zapopan", "Jalisco"): ["cultura", "comida"],
    ("Lagos de Moreno", "Jalisco"): ["cultura", "comida"],
    ("Tequila", "Jalisco"): ["comida", "cultura"],
    ("Centro Histórico de Guadalajara", "Jalisco"): ["cultura", "comida"],
    ("Toluca", "México"): ["naturaleza", "comida"],
    ("Tepotzotlán", "México"): ["cultura", "naturaleza"],
    ("Valle de Bravo", "México"): ["naturaleza", "descanso", "cultura"],
    ("Cuitzeo", "Michoacán"): ["naturaleza", "cultura"],
    ("Tlalpujahua", "Michoacán"): ["cultura", "naturaleza"],
    ("Cuernavaca", "Morelos"): ["descanso", "cultura"],
    ("Tepoztlán", "Morelos"): ["naturaleza", "cultura"],
    ("Tlayacapan", "Morelos"): ["cultura", "naturaleza"],
    ("Tepic", "Nayarit"): ["cultura", "naturaleza"],
    ("Jala", "Nayarit"): ["naturaleza", "cultura"],
    ("Santiago", "Nuevo León"): ["naturaleza", "descanso", "cultura"],
    ("Chignahuapan", "Puebla"): ["cultura", "naturaleza"],
    ("Cuetzalan", "Puebla"): ["naturaleza", "cultura"],
    ("Querétaro", "Querétaro"): ["cultura", "comida"],
    ("Bernal", "Querétaro"): ["cultura", "naturaleza"],
    ("Tequisquiapan", "Querétaro"): ["descanso", "comida", "cultura"],
    ("Chetumal", "Quintana Roo"): ["playas", "cultura"],
    ("San Luis Potosí", "San Luis Potosí"): ["cultura", "comida"],
    ("Real de Catorce", "San Luis Potosí"): ["naturaleza", "cultura"],
    ("Culiacán", "Sinaloa"): ["cultura", "comida"],
    ("Los Mochis", "Sinaloa"): ["cultura", "naturaleza"],
    ("Mazatlán", "Sinaloa"): ["playas", "descanso", "cultura"],
    ("Cosalá", "Sinaloa"): ["cultura", "naturaleza"],
    ("Ciudad Obregón", "Sonora"): ["cultura", "naturaleza"],
    ("Hermosillo", "Sonora"): ["cultura", "comida"],
    ("Álamos", "Sonora"): ["cultura", "naturaleza"],
    ("Villahermosa", "Tabasco"): ["naturaleza", "cultura"],
    ("Tapijulapa", "Tabasco"): ["naturaleza", "cultura"],
    ("Ciudad Victoria", "Tamaulipas"): ["cultura", "naturaleza"],
    ("Reynosa", "Tamaulipas"): ["cultura", "comida"],
    ("Tampico", "Tamaulipas"): ["playas", "cultura"],
    ("Tlaxcala de Xicohténcatl", "Tlaxcala"): ["cultura", "naturaleza"],
    ("Huamantla", "Tlaxcala"): ["cultura", "comida"],
    ("Orizaba", "Veracruz"): ["naturaleza", "cultura"],
    ("Xalapa", "Veracruz"): ["naturaleza", "comida", "cultura"],
    ("Izamal", "Yucatán"): ["cultura", "comida"],
    ("Valladolid", "Yucatán"): ["cultura", "naturaleza"],
    ("Chichén Itzá", "Yucatán"): ["cultura", "naturaleza"],
    ("Zacatecas", "Zacatecas"): ["cultura", "comida"],
    ("Jerez", "Zacatecas"): ["cultura", "comida"],
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
            print("No encontrados:")
            for item in no_encontrados:
                print(f"  - {item}")


if __name__ == "__main__":
    fix()
