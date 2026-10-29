"""Verifica y corrige las coordenadas de todos los destinos contra un
geocodificador real (Nominatim / OpenStreetMap), en vez de confiar en
coordenadas puestas a mano.

Por cada destino:
  1. Consulta Nominatim con "<nombre>, <estado>, México".
  2. Si encuentra un resultado y el salto respecto a la coordenada actual
     es razonable (<= 50 km, mismo lugar), actualiza lat/lon.
  3. Si el salto es grande o no hay resultado, NO se toca el dato: se
     reporta para revisión manual (puede ser un nombre ambiguo, o un
     lugar como "Centro Histórico de X" que no es un punto oficial en
     el mapa y necesita una coordenada elegida a mano).

Respeta la política de uso de Nominatim (máx. 1 solicitud/segundo,
User-Agent identificable).

Uso:
    python scripts/verify_coordenadas.py
"""

import math
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import Destino, Estado, db
from app.services.maps_service import geocodificar

UMBRAL_KM = 50


def _distancia_km(lat1, lon1, lat2, lon2):
    radio_tierra_km = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return radio_tierra_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def verificar():
    app = create_app()

    with app.app_context():
        destinos = db.session.query(Destino, Estado.nombre).join(Estado).order_by(Destino.id).all()

        actualizados = []
        revisar = []
        sin_resultado = []

        for destino, estado_nombre in destinos:
            resultado = geocodificar(destino.nombre, f"{estado_nombre}, México")
            time.sleep(1.1)  # política de uso justo de Nominatim: máx. 1 req/seg

            if not resultado:
                sin_resultado.append(f"{destino.nombre} ({estado_nombre})")
                continue

            lat_nueva, lon_nueva, nombre_encontrado = resultado
            salto_km = _distancia_km(destino.lat, destino.lon, lat_nueva, lon_nueva)

            if salto_km <= UMBRAL_KM:
                if salto_km > 0.5:  # solo contar como "actualizado" si de verdad cambió algo notable
                    actualizados.append(
                        f"{destino.nombre} ({estado_nombre}): movido {salto_km:.1f} km "
                        f"-> ({lat_nueva:.4f}, {lon_nueva:.4f})"
                    )
                destino.lat = lat_nueva
                destino.lon = lon_nueva
            else:
                revisar.append(
                    f"{destino.nombre} ({estado_nombre}): Nominatim encontró algo a {salto_km:.0f} km "
                    f"de distancia ('{nombre_encontrado}'). NO se aplicó, revisar a mano."
                )

        db.session.commit()

        print(f"Destinos verificados: {len(destinos)}")
        print(f"Coordenadas ajustadas (>0.5 km de diferencia): {len(actualizados)}")
        for linea in actualizados:
            print(f"  - {linea}")

        print(f"\nSin resultado en Nominatim (se dejaron igual): {len(sin_resultado)}")
        for linea in sin_resultado:
            print(f"  - {linea}")

        print(f"\nPara revisar a mano (salto > {UMBRAL_KM} km, posible nombre ambiguo): {len(revisar)}")
        for linea in revisar:
            print(f"  - {linea}")


if __name__ == "__main__":
    verificar()
