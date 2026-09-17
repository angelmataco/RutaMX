"""Cálculo de distancia, tiempo y costo de una ruta.

Usa la ruta real por carretera (OSRM) para distancia/tiempo y para la
geometría del camino, que es la que permite luego filtrar sugerencias por
cercanía real a la ruta (no en línea recta). Si OSRM no responde, cae a
una estimación en línea recta para que el flujo no se rompa.
"""

import math

import requests

from app.services import maps_service

VELOCIDAD_PROMEDIO_KMH = 80
COSTO_POR_KM = 4.5  # gasolina + casetas, estimado
COSTO_BASE_HOSPEDAJE = 600  # por cada parada intermedia estimada

OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"


def distancia_km(coord_a, coord_b):
    """Distancia en línea recta (km) entre dos coordenadas (lat, lon)."""
    return _distancia_haversine_km(coord_a, coord_b)


def _distancia_haversine_km(coord_a, coord_b):
    lat1, lon1 = coord_a
    lat2, lon2 = coord_b
    radio_tierra_km = 6371

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radio_tierra_km * c


def _ruta_real_osrm(coord_origen, coord_destino):
    """Consulta OSRM la ruta real por carretera entre dos coordenadas.

    Devuelve {distancia_km, tiempo_h, geometria} o None si el servicio no
    responde. `geometria` es la lista de puntos [lat, lon] del camino, en
    el mismo orden en que se recorre.
    """
    lon1, lat1 = coord_origen[1], coord_origen[0]
    lon2, lat2 = coord_destino[1], coord_destino[0]

    try:
        respuesta = requests.get(
            f"{OSRM_ROUTE_URL}/{lon1},{lat1};{lon2},{lat2}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=10,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
    except (requests.RequestException, ValueError):
        return None

    rutas = datos.get("routes") or []
    if not rutas:
        return None

    ruta = rutas[0]
    coordenadas_geojson = ruta["geometry"]["coordinates"]  # [[lon, lat], ...]
    geometria = [[lat, lon] for lon, lat in coordenadas_geojson]

    return {
        "distancia_km": round(ruta["distance"] / 1000, 1),
        "tiempo_h": round(ruta["duration"] / 3600, 2),
        "geometria": geometria,
    }


MAX_PUNTOS_CORREDOR = 300


def preparar_corredor(geometria):
    """Prepara la geometría de una ruta para búsquedas repetidas de
    cercanía (una vez por ruta, no una vez por destino candidato).

    Reduce la geometría a como máximo MAX_PUNTOS_CORREDOR puntos
    (OSRM puede devolver miles) y precalcula la distancia acumulada en
    cada uno. Devuelve (puntos, acumuladas).
    """
    paso = max(1, len(geometria) // MAX_PUNTOS_CORREDOR)
    puntos = geometria[::paso]
    if puntos[-1] != geometria[-1]:
        puntos.append(geometria[-1])

    acumuladas = [0.0]
    for i in range(1, len(puntos)):
        acumuladas.append(acumuladas[-1] + _distancia_haversine_km(puntos[i - 1], puntos[i]))

    return puntos, acumuladas


def distancia_a_corredor(corredor, punto):
    """Qué tan cerca está `punto` de un corredor ya preparado con
    `preparar_corredor`.

    Devuelve (distancia_perpendicular_km, distancia_acumulada_km): qué
    tan lejos está el punto de la carretera, y a qué avance sobre la
    ruta se encuentra el punto de la carretera más cercano.
    """
    puntos, acumuladas = corredor

    mejor_distancia = None
    mejor_acumulada = 0

    for coord_ruta, acumulada in zip(puntos, acumuladas):
        distancia = _distancia_haversine_km(coord_ruta, punto)
        if mejor_distancia is None or distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor_acumulada = acumulada

    return mejor_distancia, mejor_acumulada


def calcular_ruta(origen: str, destino: str, presupuesto: float = 0):
    """Calcula el resumen de un viaje entre origen y destino."""
    coord_origen = maps_service.obtener_coordenadas(origen)
    coord_destino = maps_service.obtener_coordenadas(destino)

    ruta_real = _ruta_real_osrm(coord_origen, coord_destino)

    if ruta_real:
        distancia_km = ruta_real["distancia_km"]
        tiempo_h = ruta_real["tiempo_h"]
        geometria = ruta_real["geometria"]
    else:
        # Respaldo: línea recta con un factor de ajuste, por si OSRM no responde.
        distancia_km = round(_distancia_haversine_km(coord_origen, coord_destino) * 1.2)
        tiempo_h = round(distancia_km / VELOCIDAD_PROMEDIO_KMH, 1)
        geometria = None

    paradas_estimadas = max(1, min(4, round(distancia_km / 250)))
    costo_estimado = round(distancia_km * COSTO_POR_KM + paradas_estimadas * COSTO_BASE_HOSPEDAJE)

    return {
        "origen": {"nombre": origen, "lat": coord_origen[0], "lon": coord_origen[1]},
        "destino": {"nombre": destino, "lat": coord_destino[0], "lon": coord_destino[1]},
        "distancia_km": distancia_km,
        "tiempo_h": tiempo_h,
        "costo_estimado": costo_estimado,
        "paradas_estimadas": paradas_estimadas,
        "presupuesto": presupuesto,
        "presupuesto_suficiente": bool(presupuesto) and presupuesto >= costo_estimado,
        "geometria": geometria,
    }
