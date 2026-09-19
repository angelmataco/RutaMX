"""Enlaces de Google Maps para empezar el road trip en el teléfono.

No usa la API de Google (no necesita key): es solo una URL con origen,
destino y paradas que la app de Google Maps abre lista para "Iniciar".
"""

from urllib.parse import quote, urlencode

# Google Maps acepta como máximo 9 paradas intermedias por enlace.
MAX_PARADAS_POR_TRAMO = 9
BASE_URL = "https://www.google.com/maps/dir/?"


def _punto(nombre, lat, lon):
    """Coordenadas si las hay (exactas); si no, el nombre como texto."""
    if lat is not None and lon is not None:
        return f"{lat},{lon}"
    return nombre or ""


def _enlace(puntos):
    parametros = {
        "api": 1,
        "origin": puntos[0],
        "destination": puntos[-1],
        "travelmode": "driving",
    }
    intermedios = puntos[1:-1]
    if intermedios:
        parametros["waypoints"] = "|".join(intermedios)
    return BASE_URL + urlencode(parametros, quote_via=quote)


def enlaces_google_maps(datos):
    """Devuelve una lista de enlaces (uno por tramo de hasta 9 paradas).

    `datos` trae origen/destino (texto), resumen (con origen/destino
    {nombre, lat, lon}) y paradas [{nombre, lat, lon}] en orden.
    Cada tramo arranca donde terminó el anterior.
    """
    resumen = datos.get("resumen") or {}
    o = resumen.get("origen") or {}
    d = resumen.get("destino") or {}

    puntos = [_punto(datos.get("origen") or o.get("nombre"), o.get("lat"), o.get("lon"))]
    for parada in datos.get("paradas") or []:
        puntos.append(_punto(parada.get("nombre"), parada.get("lat"), parada.get("lon")))
    puntos.append(_punto(datos.get("destino") or d.get("nombre"), d.get("lat"), d.get("lon")))

    enlaces = []
    inicio = 0
    while True:
        fin = min(inicio + MAX_PARADAS_POR_TRAMO + 1, len(puntos) - 1)
        enlaces.append(_enlace(puntos[inicio : fin + 1]))
        if fin >= len(puntos) - 1:
            return enlaces
        inicio = fin
