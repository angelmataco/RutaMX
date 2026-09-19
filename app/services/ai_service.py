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
        "intereses": destino.intereses or [],
    }
    if horas_estimadas is not None:
        lugar["horas_estimadas"] = round(horas_estimadas, 1)
        lugar["buena_para_descanso"] = (
            horas_objetivo is not None and abs(horas_estimadas - horas_objetivo) <= TOLERANCIA_DESCANSO_HORAS
        )
    return lugar


def obtener_pool_con_horas(ruta, excluir_ids=None, limite=40):
    """Envoltorio público sobre `_candidatos_en_el_corredor` con un límite
    amplio — para tener de dónde elegir varios objetivos de parada (por
    propósito y hora) sin repetir destinos. Usado tanto por el chat de IA
    (`planificador_ia_service.py`) como por el reparto automático de
    paradas sin IA de aquí abajo.
    """
    if not ruta:
        return []
    candidatos = _candidatos_en_el_corredor(ruta, limite, set(excluir_ids or []))
    return candidatos or []


# Antes de esta hora del día no tiene caso proponer "descanso" (dormir) —
# todavía hay luz/actividad y se siente forzado.
HORA_LIMITE_DESCANSO_DE_DIA = 20.0

# Después de esta hora ya conviene priorizar una parada de descanso en
# vez de una visita, aunque el propósito original fuera otro.
HORA_LIMITE_NOCHE = 21.0


def _hora_del_reloj(hora_salida: str, horas_transcurridas: float):
    """`hora_salida` en formato "HH:MM" + horas transcurridas desde la
    salida -> hora del reloj real (0-24), o None si `hora_salida` no
    tiene un formato válido.
    """
    try:
        horas, minutos = hora_salida.split(":")
        salida = int(horas) + int(minutos) / 60
    except (ValueError, AttributeError, TypeError):
        return None
    return (salida + horas_transcurridas) % 24


def filtrar_objetivos_por_hora_del_dia(objetivos, hora_salida, intereses_usuario=None):
    """Ajusta el propósito de cada objetivo según la hora real del día en
    la que caería (no solo las horas transcurridas del viaje). Comparte
    esta lógica el chat de IA y el reparto automático sin IA — protege
    incluso si la IA propuso algo que no cuadra con la hora del día (ej.
    "dormir" a media tarde).

    Sin `hora_salida` no se puede calcular la hora real, así que se
    regresan los objetivos sin tocar.
    """
    if not hora_salida:
        return list(objetivos)

    interes_de_dia = (intereses_usuario or ["cultura"])[0]
    ajustados = []
    for objetivo in objetivos:
        hora_reloj = _hora_del_reloj(hora_salida, objetivo["hora_objetivo"])
        proposito = objetivo["proposito"]
        if hora_reloj is not None:
            if proposito == "descanso" and hora_reloj < HORA_LIMITE_DESCANSO_DE_DIA:
                proposito = interes_de_dia
            elif proposito != "descanso" and hora_reloj >= HORA_LIMITE_NOCHE:
                proposito = "descanso"
        ajustados.append({**objetivo, "proposito": proposito})
    return ajustados


def generar_objetivos_automaticos(tiempo_h, horas_max, hora_salida=None, intereses_usuario=None):
    """Versión sin IA de "decidir dónde conviene parar": si el usuario dio
    horas máximas de manejo seguido, propone una parada de comida en el
    primer tramo y de descanso en cada tramo siguiente, cada
    `horas_max` horas — después las ajusta con `filtrar_objetivos_por_hora_del_dia`
    igual que haría el chat de IA. Esto es lo que hace que el trabajo
    hecho para el chat también mejore las sugerencias del formulario
    manual, sin llamar a ningún proveedor de IA.
    """
    if not horas_max or not tiempo_h:
        return []

    objetivos = []
    hora = horas_max
    es_el_primero = True
    while hora < tiempo_h:
        objetivos.append({"proposito": "comida" if es_el_primero else "descanso", "hora_objetivo": round(hora, 1)})
        es_el_primero = False
        hora += horas_max

    return filtrar_objetivos_por_hora_del_dia(objetivos, hora_salida, intereses_usuario)


def asignar_paradas_a_objetivos(candidatos, objetivos):
    """Por cada objetivo (propósito + hora), elige el mejor candidato aún
    no usado: prioriza que su propósito esté entre los intereses del
    destino, y de ahí la cercanía en horas al objetivo. Nunca repite el
    mismo destino en dos objetivos de la misma lista — evita el problema
    de varios candidatos casi idénticos en tiempo/distancia. Si un
    objetivo se queda sin un candidato razonable, se omite (nunca fuerza
    un lugar que no encaja).

    `candidatos` es una lista de (Destino, horas_estimadas) como la que
    devuelve `obtener_pool_con_horas`. Devuelve una lista de lugares (con
    el mismo shape que `_lugar_desde_destino`) más `proposito` y
    `hora_objetivo`, ordenada por hora.
    """
    usados = set()
    resultado = []

    for objetivo in sorted(objetivos, key=lambda o: o["hora_objetivo"]):
        mejor = None
        mejor_puntaje = None
        for destino, horas_estimadas in candidatos:
            if destino.id in usados or horas_estimadas is None:
                continue
            coincide_proposito = 0 if objetivo["proposito"] in (destino.intereses or []) else 1
            distancia_hora = abs(horas_estimadas - objetivo["hora_objetivo"])
            puntaje = (coincide_proposito, distancia_hora)
            if mejor_puntaje is None or puntaje < mejor_puntaje:
                mejor_puntaje = puntaje
                mejor = (destino, horas_estimadas)

        if mejor is None:
            continue

        destino, horas_estimadas = mejor
        usados.add(destino.id)
        lugar = _lugar_desde_destino(destino, horas_estimadas)
        lugar["proposito"] = objetivo["proposito"]
        lugar["hora_objetivo"] = objetivo["hora_objetivo"]
        resultado.append(lugar)

    return resultado


def _sugerir_con_objetivos_automaticos(intereses, limite, ruta, horas_max, hora_salida, excluir_ids):
    """Usa `generar_objetivos_automaticos` + `asignar_paradas_a_objetivos`
    para dar las primeras paradas (una por propósito/hora, sin
    duplicados cercanos), y rellena el resto del cupo con las sugerencias
    normales ordenadas por interés. Devuelve `None` si no hay suficiente
    información para armar objetivos (así `sugerir_paradas` cae al
    comportamiento de siempre).
    """
    pool = obtener_pool_con_horas(ruta, excluir_ids, limite=max(limite, 20))
    if not pool:
        return None

    objetivos = generar_objetivos_automaticos(ruta.get("tiempo_h"), horas_max, hora_salida, list(intereses) or None)
    if not objetivos:
        return None

    asignadas = asignar_paradas_a_objetivos(pool, objetivos)
    if not asignadas:
        return None

    ids_usados = {lugar["id"] for lugar in asignadas}
    restantes = _ordenar_candidatos([(d, h) for d, h in pool if d.id not in ids_usados], intereses, None)
    relleno = [_lugar_desde_destino(d, h) for d, h in restantes[: max(0, limite - len(asignadas))]]
    return (asignadas + relleno)[:limite]


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


def sugerir_paradas(intereses=None, limite=4, ruta=None, horas_max=None, excluir_ids=None, hora_salida=None):
    """Devuelve destinos sugeridos para la ruta actual.

    - `ruta`: resumen devuelto por route_service.calcular_ruta (usa su
      geometría real para sugerir solo lugares cerca del camino).
    - `horas_max`: horas máximas que el usuario quiere manejar seguido;
      si se da, se prioriza a los destinos cercanos al punto del viaje
      donde convendría parar a descansar.
    - `hora_salida`: hora aproximada de salida ("HH:MM"), opcional. Con
      `horas_max` + `hora_salida` se reparten paradas por propósito y
      hora del día (comida/descanso, evitando proponer dormir de día) en
      vez de solo marcar un punto de descanso — mismo mecanismo que usa
      el chat de IA, sin necesitar ningún proveedor.
    - `excluir_ids`: ids de destinos que ya se mostraron/agregaron y no
      deben repetirse (para "ver más recomendaciones").
    """
    intereses = set(intereses or [])
    excluir_ids = set(excluir_ids or [])

    try:
        if ruta and horas_max and hora_salida:
            resultado = _sugerir_con_objetivos_automaticos(intereses, limite, ruta, horas_max, hora_salida, excluir_ids)
            if resultado:
                return resultado

        resultado = _sugerir_desde_base(intereses, limite, ruta, horas_max, excluir_ids)
        if resultado is not None:
            return resultado
    except Exception as error:
        print(f"No se pudo consultar la base de destinos, usando catálogo de respaldo: {error}")

    return _sugerir_desde_demo(intereses, limite)
