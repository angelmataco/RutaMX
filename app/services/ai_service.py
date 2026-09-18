"""Sugerencia de paradas/destinos según la ruta y los intereses del
usuario.

Las sugerencias salen de la tabla `destinos` (Supabase), filtradas por
cercanía real a la carretera entre origen y destino —no en línea recta—
usando la geometría que ya calcula `route_service` con OSRM. Si además
el usuario indicó cuántas horas máximo quiere manejar seguido, se
prioriza a los destinos que caen cerca de ese punto del camino, como
sugerencia de dónde parar a descansar.

LUGARES_DEMO se queda solo como respaldo por si la base de datos no
responde (ej. sin conexión), para que el flujo no se rompa.

Los destinos que no existían en la tabla se generan con IA en
`maps_service.obtener_coordenadas()` (ver `ia_destinos_service.py`) antes
de llegar aquí — por eso este módulo no necesita saber nada de eso, solo
consulta `destinos` como siempre.
"""

import random

from app.models import Destino
from app.services import maps_service, route_service

ETIQUETAS_TIPO = {
    "ciudad_principal": "Ciudad",
    "pueblo_magico": "Pueblo Mágico",
    "sitio_turistico": "Sitio turístico",
}

# Qué fracción de las horas máximas de manejo se usa como objetivo para
# sugerir dónde parar a descansar (8h máximo -> se sugiere cerca de 6.4h).
FACTOR_DESCANSO = 0.8

# Radios de búsqueda (km) alrededor de la carretera real: se prueba el
# más estricto primero y se va ampliando solo si no alcanza destinos.
RADIOS_CORREDOR_KM = [20, 60, 150]

# Si un destino está a menos de esto del origen o del destino, es
# básicamente el mismo lugar del que sales o a donde llegas: no tiene
# caso "sugerirlo" como parada en el camino.
RADIO_EXCLUSION_EXTREMOS_KM = 5

# Un destino a menos de esto (en horas de manejo real) del origen está
# prácticamente dentro de la ciudad de la que sales: no tiene caso
# "sugerirlo" como parada en el camino. Cerca del destino sí se permite
# sugerir (cuando ya llegaste, también quieres recomendaciones).
HORAS_MINIMAS_DESDE_ORIGEN = 1.0

# Qué tan cerca (en horas) del punto objetivo de descanso debe caer un
# destino para marcarlo como "buena parada para descansar".
TOLERANCIA_DESCANSO_HORAS = 1.0

LUGARES_DEMO = [
    {
        "id": "teotihuacan",
        "nombre": "Teotihuacán",
        "categoria": "Sitio cultural",
        "descripcion": "Pirámides monumentales, gastronomía local y arte, ideal para una parada de demostración.",
        "intereses": ["pueblos_magicos", "comida"],
    },
    {
        "id": "valle_de_bravo",
        "nombre": "Valle de Bravo",
        "categoria": "Naturaleza",
        "descripcion": "Bosque, lago y aire fresco para tomar un respiro tranquilo antes de seguir el camino.",
        "intereses": ["naturaleza", "descanso"],
    },
    {
        "id": "bernal",
        "nombre": "Bernal",
        "categoria": "Pueblo Mágico",
        "descripcion": "Un pueblo al pie de la Peña de Bernal, perfecto para una parada breve y panorámica.",
        "intereses": ["pueblos_magicos"],
    },
    {
        "id": "san_miguel_de_allende",
        "nombre": "San Miguel de Allende",
        "categoria": "Sitio cultural",
        "descripcion": "Arquitectura, mercados y calles para caminar con calma durante una escapada en carretera.",
        "intereses": ["pueblos_magicos", "comida"],
    },
    {
        "id": "playa_del_carmen",
        "nombre": "Playa del Carmen",
        "categoria": "Playa",
        "descripcion": "Costa caribeña con arena blanca, ideal para una parada de playa y descanso.",
        "intereses": ["playas", "descanso"],
    },
    {
        "id": "guanajuato",
        "nombre": "Guanajuato",
        "categoria": "Sitio cultural",
        "descripcion": "Callejones coloridos, historia y buena comida en una de las ciudades más fotogénicas del país.",
        "intereses": ["pueblos_magicos", "comida"],
    },
]


def _lugar_desde_destino(destino, horas_estimadas=None, horas_objetivo=None):
    lugar = {
        "id": destino.id,
        "nombre": destino.nombre,
        "categoria": ETIQUETAS_TIPO.get(destino.tipo, "Destino"),
        "descripcion": destino.descripcion,
        "lat": destino.lat,
        "lon": destino.lon,
    }
    if horas_estimadas is not None:
        lugar["horas_estimadas"] = round(horas_estimadas, 1)
        lugar["buena_para_descanso"] = (
            horas_objetivo is not None and abs(horas_estimadas - horas_objetivo) <= TOLERANCIA_DESCANSO_HORAS
        )
    return lugar


def _consulta_destinos(excluir_ids):
    consulta = Destino.query
    if excluir_ids:
        consulta = consulta.filter(~Destino.id.in_(excluir_ids))
    return consulta.all()


def _candidatos_en_el_corredor(ruta, limite, excluir_ids):
    """Filtra los destinos de la base que caen cerca de la carretera real
    de `ruta` (dict con "geometria", "distancia_km", "tiempo_h", y los
    puntos de "origen"/"destino").

    Excluye el origen y el destino del viaje (no tiene caso "sugerir"
    llegar al lugar de donde sales o a donde vas), y cualquier id en
    `excluir_ids` (destinos que el usuario ya vio o agregó). Empieza con
    un radio de búsqueda estricto y lo va ampliando solo si no alcanza
    para juntar al menos `limite` destinos.

    Devuelve una lista de (destino, horas_estimadas), o None si `ruta`
    no trae geometría (ej. OSRM no respondió al calcular la ruta).
    """
    geometria = ruta.get("geometria") if ruta else None
    if not geometria:
        return None

    corredor = route_service.preparar_corredor(geometria)
    distancia_total = ruta.get("distancia_km") or 0
    tiempo_total = ruta.get("tiempo_h") or 0
    punto_origen = (ruta["origen"]["lat"], ruta["origen"]["lon"])
    punto_destino = (ruta["destino"]["lat"], ruta["destino"]["lon"])

    calculados = []
    for destino in _consulta_destinos(excluir_ids):
        punto_destino_candidato = (destino.lat, destino.lon)

        # El punto exacto del destino no tiene caso "sugerirlo" (ya es a
        # donde vas), pero sí se permiten lugares cerca de él.
        if route_service.distancia_km(punto_destino_candidato, punto_destino) < RADIO_EXCLUSION_EXTREMOS_KM:
            continue

        distancia_perp, avance_km = route_service.distancia_a_corredor(corredor, punto_destino_candidato)
        horas_estimadas = (avance_km / distancia_total) * tiempo_total if distancia_total else 0

        # Descarta lo que está a menos de 1h de manejo real del origen
        # (básicamente dentro de la ciudad de la que sales).
        if horas_estimadas < HORAS_MINIMAS_DESDE_ORIGEN:
            continue

        calculados.append((destino, horas_estimadas, distancia_perp))

    for radio in RADIOS_CORREDOR_KM:
        candidatos = [(d, h) for d, h, dist in calculados if dist is not None and dist <= radio]
        if len(candidatos) >= limite:
            return candidatos

    # Ni con el radio más amplio alcanzó: se regresa lo que haya (puede
    # quedar corto, pero es mejor que nada).
    return [(d, h) for d, h, dist in calculados if dist is not None and dist <= RADIOS_CORREDOR_KM[-1]]


def _ordenar_candidatos(candidatos, intereses, horas_objetivo):
    """Ordena (destino, horas_estimadas) priorizando coincidencia de
    intereses y, si hay horas_objetivo, cercanía a ese punto del viaje.
    """
    random.shuffle(candidatos)  # para no repetir siempre el mismo orden entre empates

    def puntaje(item):
        destino, horas_estimadas = item
        coincide_interes = 0 if (intereses and intereses & set(destino.intereses or [])) else 1
        distancia_a_objetivo = abs(horas_estimadas - horas_objetivo) if horas_objetivo is not None else 0
        return (coincide_interes, distancia_a_objetivo)

    return sorted(candidatos, key=puntaje)


def _sugerir_desde_base(intereses, limite, ruta, horas_max, excluir_ids):
    candidatos = _candidatos_en_el_corredor(ruta, limite, excluir_ids) if ruta else None

    if candidatos is None:
        # No hay geometría de ruta (ej. faltó origen/destino, u OSRM no
        # respondió): se cae a sugerir de toda la base, sin filtro de
        # cercanía, para no dejar la sección vacía.
        destinos = _consulta_destinos(excluir_ids)
        if not destinos:
            return None
        candidatos = [(d, None) for d in destinos]

    if not candidatos:
        return []

    horas_objetivo = horas_max * FACTOR_DESCANSO if horas_max else None
    candidatos = _ordenar_candidatos(candidatos, intereses, horas_objetivo)

    return [
        _lugar_desde_destino(destino, horas_estimadas, horas_objetivo)
        for destino, horas_estimadas in candidatos[:limite]
    ]


def _sugerir_desde_demo(intereses, limite):
    candidatos = list(LUGARES_DEMO)
    random.shuffle(candidatos)

    if intereses:
        con_match = [l for l in candidatos if intereses & set(l["intereses"])]
        sin_match = [l for l in candidatos if l not in con_match]
        candidatos = con_match + sin_match

    resultado = []
    for lugar in candidatos[:limite]:
        lat, lon = maps_service.obtener_coordenadas(lugar["nombre"])
        resultado.append({**lugar, "lat": lat, "lon": lon})
    return resultado


def sugerir_paradas(intereses=None, limite=4, ruta=None, horas_max=None, excluir_ids=None):
    """Devuelve destinos sugeridos para la ruta actual.

    - `ruta`: resumen devuelto por route_service.calcular_ruta (usa su
      geometría real para sugerir solo lugares cerca del camino).
    - `horas_max`: horas máximas que el usuario quiere manejar seguido;
      si se da, se prioriza a los destinos cercanos al punto del viaje
      donde convendría parar a descansar.
    - `excluir_ids`: ids de destinos que ya se mostraron/agregaron y no
      deben repetirse (para "ver más recomendaciones").
    """
    intereses = set(intereses or [])
    excluir_ids = set(excluir_ids or [])

    try:
        resultado = _sugerir_desde_base(intereses, limite, ruta, horas_max, excluir_ids)
        if resultado is not None:
            return resultado
    except Exception as error:
        print(f"No se pudo consultar la base de destinos, usando catálogo de respaldo: {error}")

    return _sugerir_desde_demo(intereses, limite)
