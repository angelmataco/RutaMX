"""Integración con la API/librería de mapas.

CIUDADES_DEMO sigue siendo el catálogo rápido que usa `obtener_coordenadas`
como último respaldo. `geocodificar()` de aquí abajo sí consulta un
servicio real (Nominatim/OpenStreetMap) y es lo que debe usar cualquier
proceso que AGREGUE destinos nuevos a la base de datos (scripts de carga,
y `ia_destinos_service.py` cuando la IA genera un lugar nuevo), para que
las coordenadas guardadas sean exactas y no aproximadas a mano.
"""

import unicodedata

import requests

from app.models import Destino

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim exige un User-Agent identificable (política de uso justo).
USER_AGENT = "RutaMX-App/1.0 (proyecto escolar DASV; contacto: equipo RutaMX)"

CIUDADES_DEMO = {
    "ciudad de mexico": (19.4326, -99.1332),
    "cdmx": (19.4326, -99.1332),
    "puebla": (19.0414, -98.2063),
    "tehuacan": (18.4636, -97.3928),
    "oaxaca de juarez": (17.0732, -96.7266),
    "oaxaca": (17.0732, -96.7266),
    "valle de bravo": (19.1947, -100.1319),
    "queretaro": (20.5888, -100.3899),
    "bernal": (20.7458, -99.9439),
    "san miguel de allende": (20.9153, -100.7436),
    "guadalajara": (20.6597, -103.3496),
    "monterrey": (25.6866, -100.3161),
    "teotihuacan": (19.6925, -98.8438),
    "cancun": (21.1619, -86.8515),
    "merida": (20.9674, -89.5926),
    "guanajuato": (21.0190, -101.2574),
    "veracruz": (19.1738, -96.1342),
    "acapulco": (16.8531, -99.8237),
    "tulum": (20.2114, -87.4654),
    "playa del carmen": (20.6296, -87.0739),
}

# Coordenada aproximada del centro de México, usada como respaldo cuando
# no reconocemos el nombre de la ciudad en el catálogo demo.
COORDENADA_RESPALDO = (23.6345, -102.5528)


def _normalizar(texto: str) -> str:
    texto = texto.strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return texto


def _buscar_en_destinos(clave: str):
    """Busca un destino de la base (369 lugares curados) por nombre
    normalizado, exacto o parcial. Devuelve (lat, lon) o None.
    """
    if not clave:
        return None

    for destino in Destino.query.all():
        if _normalizar(destino.nombre) == clave:
            return destino.lat, destino.lon

    for destino in Destino.query.all():
        nombre_normalizado = _normalizar(destino.nombre)
        if clave in nombre_normalizado or nombre_normalizado in clave:
            return destino.lat, destino.lon

    return None


def obtener_coordenadas(nombre_ciudad: str):
    """Devuelve (lat, lon) para un lugar, resolviendo en este orden:

    1. La tabla `destinos` (369 lugares curados, ya geocodificados).
    2. Generar el destino con IA (si hay un proveedor configurado) y
       guardarlo en la tabla — así queda disponible para siempre en
       autocompletado/sugerencias, no solo para esta petición.
    3. Nominatim (`geocodificar`), para cualquier lugar real de México
       que no esté en la base y que la IA no haya podido generar.
    4. El catálogo demo (`CIUDADES_DEMO`), como respaldo rápido.
    5. `COORDENADA_RESPALDO`, si todo lo anterior falla.
    """
    clave = _normalizar(nombre_ciudad or "")

    try:
        encontrado = _buscar_en_destinos(clave)
        if encontrado:
            return encontrado
    except Exception as error:
        print(f"No se pudo consultar la tabla de destinos para geocodificar: {error}")

    try:
        # Import perezoso: ia_destinos_service importa este módulo, así
        # que importarlo arriba del archivo crearía un import circular.
        from app.services import ia_destinos_service

        destino_generado = ia_destinos_service.generar_destino_con_ia(nombre_ciudad)
        if destino_generado:
            return destino_generado.lat, destino_generado.lon
    except Exception as error:
        print(f"No se pudo generar el destino con IA: {error}")

    resultado_geocodificado = geocodificar(nombre_ciudad)
    if resultado_geocodificado:
        lat, lon, _ = resultado_geocodificado
        return lat, lon

    if clave in CIUDADES_DEMO:
        return CIUDADES_DEMO[clave]

    for nombre, coords in CIUDADES_DEMO.items():
        if clave and (clave in nombre or nombre in clave):
            return coords

    return COORDENADA_RESPALDO


def geocodificar(nombre_lugar: str, contexto: str = "México"):
    """Consulta Nominatim (OpenStreetMap) para obtener coordenadas reales
    de un lugar por nombre — desde una ciudad hasta un restaurante
    puntual, siempre que exista en OpenStreetMap.

    Devuelve (lat, lon, nombre_encontrado) o None si no hay un resultado
    confiable. `nombre_encontrado` es el nombre oficial que devolvió el
    geocodificador, útil para confirmar que sí encontró el lugar correcto
    antes de guardarlo.
    """
    consulta = f"{nombre_lugar}, {contexto}" if contexto else nombre_lugar

    try:
        respuesta = requests.get(
            NOMINATIM_URL,
            params={"q": consulta, "format": "json", "limit": 1, "countrycodes": "mx"},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        respuesta.raise_for_status()
        resultados = respuesta.json()
    except (requests.RequestException, ValueError):
        return None

    if not resultados:
        return None

    resultado = resultados[0]
    return float(resultado["lat"]), float(resultado["lon"]), resultado.get("display_name", "")
