"""Sugerencia de paradas/destinos según la ruta y los intereses del
usuario.

Las sugerencias salen de la tabla `destinos` (Supabase), filtradas por
cercanía real a la carretera entre origen y destino —no en línea recta—
usando la geometría que ya calcula `route_service` con OSRM. Si además
hay geometría de ruta, las sugerencias se reparten solas por "lapsos" de
tiempo a lo largo del camino (ver `lapsos_de_la_ruta`), sin que el
usuario tenga que decir cada cuántas horas quiere parar.

LUGARES_DEMO se queda solo como respaldo por si la base de datos no
responde (ej. sin conexión), para que el flujo no se rompa.

Los destinos que no existían en la tabla se generan con IA en
`maps_service.obtener_coordenadas()` (ver `ia_destinos_service.py`) antes
de llegar aquí — por eso este módulo no necesita saber nada de eso, solo
consulta `destinos` como siempre.
"""

import random
import re

from app.models import Destino
from app.services import gasto_service, maps_service, route_service

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

# Ventana en la que se recomienda: desde 30 min después de salir (antes
# de eso sigues básicamente en la ciudad de la que sales) hasta 20 min
# antes de llegar (después ya casi estás en el destino).
HORAS_MINIMAS_DESDE_ORIGEN = 0.5
HORAS_MINIMAS_ANTES_DE_LLEGAR = 20 / 60

# El tramo de la ventana se divide en lapsos de más o menos esta duración
# (un viaje de 6 h -> 2 lapsos; uno de 12 h -> 4). Sustituye a la vieja
# pregunta "horas máximas de manejo seguido": la app lo decide sola.
LAPSO_OBJETIVO_H = 3.0

# Un lugar distinguido (estrella / Michelin...) solo pasa al frente si la ruta
# pasa cerca: a lo más este desvío (km) desde la carretera. Más lejos sigue
# pudiendo aparecer, pero sin prioridad.
RADIO_PRIORIDAD_KM = 40

# Cuántos lugares se ven por página en "Descubre en el camino" (debe coincidir con
# MOSTRAR_SUGERENCIAS en main.js) y cuántos distinguidos (★) se ponen al frente como
# máximo, para que ninguna ruta se llene de puras estrellas.
TAMANO_PAGINA_SUGERENCIAS = 5
MAX_DISTINGUIDOS_AL_FRENTE = 2

# Un tramo no puede ser más corto que esto (limita cuántos tramos se pueden pedir).
LAPSO_MINIMO_H = 0.5

# Horarios en los que un tramo pide "lugar para comer". El desayuno no se
# sugiere: se supone que se desayuna antes de salir.
VENTANAS_DE_COMIDA_SUGERIDA = [(13.0, 16.0), (19.0, 21.5)]
# Un tramo que termina a partir de esta hora (o que cruza la noche) pide un
# lugar para pasar la noche.
HORA_TRAMO_DE_DESCANSO = 20.0

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


def _dato(obj, clave):
    """Lee un campo de un destino (objeto) o de un lugar ya armado (dict)."""
    return obj.get(clave) if isinstance(obj, dict) else getattr(obj, clave, None)


def prestigio(obj):
    """Qué tan distinguido es un lugar por su reconocimiento público (0 = ninguno).

    REGLA (Angel): los lugares con estrella, o mencionados por Michelin u otra
    organización, tienen preferencia en las recomendaciones, siempre que la ruta
    pase cerca (los candidatos ya vienen filtrados por cercanía a la carretera).
    Sirve igual para destinos y, en el futuro, para restaurantes y hoteles: basta
    con que tengan `gastronomia_destacada` y `reconocimiento_gastronomico`.
    Más puntos = más distinguido: estrella Michelin > UNESCO / 50 Best > Bib Gourmand.
    """
    if not _dato(obj, "gastronomia_destacada"):
        return 0
    texto = _dato(obj, "reconocimiento_gastronomico") or ""
    puntos = 1
    if re.search(r"unesco", texto, re.I):
        puntos += 2
    if re.search(r"2 estrellas|dos estrellas", texto, re.I):
        puntos += 4
    elif re.search(r"estrella", texto, re.I):
        puntos += 3
    if re.search(r"bib gourmand", texto, re.I):
        puntos += 1
    if re.search(r"50 best", texto, re.I):
        puntos += 2
    return puntos


def prioridad(obj):
    """`prestigio` pero solo si la ruta pasa cerca (a `RADIO_PRIORIDAD_KM` o menos).
    Si no se conoce la distancia se asume que sí está cerca."""
    distancia = _dato(obj, "distancia_a_ruta_km")
    if distancia is not None and distancia > RADIO_PRIORIDAD_KM:
        return 0
    return prestigio(obj)


def _linea_de_tiempo(lugares, tamano_pagina=None):
    """Ordena las sugerencias como una línea de tiempo del viaje:
    1) al frente van los lugares distinguidos (estrella / Michelin...) cercanos a
       la ruta, sin importar la hora, pero **como máximo `MAX_DISTINGUIDOS_AL_FRENTE`**
       (los más distinguidos; a igual puntaje, el más cercano al inicio), para que
       una ruta no se llene de puras estrellas;
    2) después todo lo demás en orden de camino (a 1 h, luego a 2 h, luego a 3 h y
       media…). Los distinguidos que sobran conservan su ★ pero entran a la línea de
       tiempo por su hora, y **nunca dentro de la primera página**.
    Así el usuario ve rápido qué tiene disponible en las primeras horas."""
    tamano_pagina = tamano_pagina or TAMANO_PAGINA_SUGERENCIAS

    def horas(lugar):
        valor = lugar.get("horas_estimadas")
        return valor if valor is not None else 0

    distinguidos = sorted((l for l in lugares if prioridad(l) > 0), key=lambda l: (-prioridad(l), horas(l)))
    al_frente = distinguidos[:MAX_DISTINGUIDOS_AL_FRENTE]
    sobrantes = distinguidos[MAX_DISTINGUIDOS_AL_FRENTE:]
    comunes = sorted((l for l in lugares if prioridad(l) == 0), key=horas)

    # La primera página: los distinguidos del frente + los primeros comunes por hora.
    huecos = max(0, tamano_pagina - len(al_frente))
    primera_pagina = al_frente + comunes[:huecos]
    # El resto de la línea de tiempo (comunes que siguen + distinguidos sobrantes), por hora.
    resto = sorted(comunes[huecos:] + sobrantes, key=horas)
    return primera_pagina + resto


def _elegir_con_distinguidos(lugares, limite):
    """Los primeros `limite` de `lugares` (ya ordenados por relevancia), pero
    sin dejar fuera a ningún distinguido cercano a la ruta."""
    elegidos = lugares[:limite]
    ids = {l["id"] for l in elegidos}
    faltan = [l for l in lugares[limite:] if prioridad(l) > 0 and l["id"] not in ids]
    return elegidos + faltan


def lapsos_de_la_ruta(tiempo_h, tramos=None, hora_salida=None, propositos=None):
    """Divide el viaje en lapsos de tiempo, de 30 min después de salir a
    20 min antes de llegar. Por defecto salen de ~3 h cada uno; si el
    usuario pide `tramos` (ej. 3), la ventana se divide en esa cantidad de
    partes iguales.

    Cada lapso trae sus horas de camino (`desde_h`, `hasta_h`), la hora del
    reloj (`reloj_desde`, `reloj_hasta`, `dia`, `cruza_noche`) según
    `hora_salida` (08:00 si no se conoce), y su propósito:
    - `proposito`: "comida", "turismo" o "descanso" (dormir);
    - `personalizado`: True si lo eligió el usuario en `propositos`
      ({indice: proposito}); si no, lo decide solo según la hora;
    - `permite_dormir`: dormir solo aplica si el tramo termina después de
      las 20:00 o cruza la noche.
    Devuelve una lista vacía si el viaje es demasiado corto (o no se conoce
    su duración) para tener una ventana.
    """
    if not tiempo_h:
        return []
    inicio = HORAS_MINIMAS_DESDE_ORIGEN
    fin = tiempo_h - HORAS_MINIMAS_ANTES_DE_LLEGAR
    if fin <= inicio:
        return []

    maximo = max(1, int((fin - inicio) / LAPSO_MINIMO_H))
    if tramos:
        cuantos = max(1, min(int(tramos), maximo))
    else:
        cuantos = max(1, min(round((fin - inicio) / LAPSO_OBJETIVO_H), maximo))
    ancho = (fin - inicio) / cuantos
    propositos = propositos or {}

    lapsos = []
    for i in range(cuantos):
        desde, hasta = inicio + i * ancho, inicio + (i + 1) * ancho
        hora_desde, dia_desde = gasto_service.momento_de_llegada(desde, hora_salida)
        hora_hasta, dia_hasta = gasto_service.momento_de_llegada(hasta, hora_salida)
        lapso = {
            "indice": i,
            "desde_h": round(desde, 2),
            "hasta_h": round(hasta, 2),
            "reloj_desde": gasto_service.formato_hora(hora_desde),
            "reloj_hasta": gasto_service.formato_hora(hora_hasta),
            "dia": dia_desde,
            "cruza_noche": dia_hasta > dia_desde,
            "_hora_desde": hora_desde,
            "_hora_hasta": hora_hasta,
        }
        lapso["permite_dormir"] = lapso["cruza_noche"] or hora_hasta >= HORA_TRAMO_DE_DESCANSO
        pedido = propositos.get(i)
        if pedido in ("comida", "turismo") or (pedido == "descanso" and lapso["permite_dormir"]):
            lapso["proposito"], lapso["personalizado"] = pedido, True
        else:
            lapso["proposito"], lapso["personalizado"] = _proposito_automatico(lapso), False
        lapsos.append(lapso)
    return lapsos


def _proposito_automatico(lapso):
    """Qué conviene recomendar en un tramo según la hora del reloj:
    "descanso" (dónde pasar la noche) solo si el tramo termina después de
    las 20:00 o cruza la noche; "comida" si cae en horario de comer; y si
    no, "turismo"."""
    if lapso["permite_dormir"]:
        return "descanso"
    for ini, fin in VENTANAS_DE_COMIDA_SUGERIDA:
        traslape = min(lapso["_hora_hasta"], fin) - max(lapso["_hora_desde"], ini)
        if traslape >= 1.0:
            return "comida"
    return "turismo"


def _intereses_de_turismo(intereses_usuario):
    """Los intereses del usuario que son de "turismo" (sin comida ni descanso)."""
    return [i for i in (intereses_usuario or []) if i not in ("comida", "descanso")]


def _coincide_proposito(intereses_destino, tipo_destino, proposito):
    """¿Este lugar sirve para ese propósito? Comer: lugares de comida.
    Descansar: lugares de descanso o ciudades grandes (donde hay dónde
    dormir). Otro (un interés, ej. "playas"): el lugar tiene ese interés."""
    if proposito == "descanso":
        return "descanso" in intereses_destino or tipo_destino == "ciudad_principal"
    return proposito in intereses_destino


def _encaja_con_lo_pedido(destino, proposito, intereses_usuario):
    """Filtro estricto para un tramo que el usuario personalizó: si pidió
    comer, solo lugares donde se puede comer; si pidió dormir, solo dónde
    dormir; si pidió turismo, lugares con sus intereses (o cualquiera, si
    no marcó ninguno)."""
    intereses = destino.intereses or []
    if proposito in ("comida", "descanso"):
        return _coincide_proposito(intereses, destino.tipo, proposito)
    turismo = _intereses_de_turismo(intereses_usuario)
    return not turismo or bool(set(turismo) & set(intereses))


def _indice_de_lapso(lapsos, horas_estimadas):
    for lapso in lapsos:
        if lapso["desde_h"] <= horas_estimadas <= lapso["hasta_h"]:
            return lapso["indice"]
    return None


def _lugar_desde_destino(destino, horas_estimadas=None, horas_objetivo=None):
    lugar = {
        "id": destino.id,
        "nombre": destino.nombre,
        "categoria": ETIQUETAS_TIPO.get(destino.tipo, "Destino"),
        "descripcion": destino.descripcion,
        "lat": destino.lat,
        "lon": destino.lon,
        "intereses": destino.intereses or [],
        # Gastronomía reconocida (UNESCO / Guía Michelin): se muestra con una estrellita
        # y en los tramos de "comer" va primero.
        "distancia_a_ruta_km": getattr(destino, "distancia_a_ruta_km", None),
        "gastronomia_destacada": bool(getattr(destino, "gastronomia_destacada", False)),
        "reconocimiento_gastronomico": getattr(destino, "reconocimiento_gastronomico", None),
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


def generar_objetivos_por_lapsos(lapsos, intereses_usuario=None):
    """Un objetivo de parada por lapso, en la mitad del lapso, con el
    propósito de ese tramo. Los tramos que el usuario personalizó son
    estrictos (`estricto`): solo se acepta un lugar que encaje con lo pedido."""
    objetivos = []
    for lapso in lapsos:
        turismo = _intereses_de_turismo(intereses_usuario)
        proposito = lapso["proposito"]
        if proposito == "turismo":
            proposito = turismo[0] if turismo else "cultura"
        objetivos.append(
            {
                "proposito": proposito,
                "hora_objetivo": round((lapso["desde_h"] + lapso["hasta_h"]) / 2, 2),
                "ventana": (lapso["desde_h"], lapso["hasta_h"]),
                "estricto": lapso["personalizado"],
                "indice": lapso["indice"],
                "tipo_pedido": lapso["proposito"],
            }
        )
    return objetivos


HORAS_TOLERANCIA_OBJETIVO_IA = 1.5


def preparar_objetivos_ia(objetivos, tiempo_h, hora_salida=None, intereses_usuario=None):
    """Aplica las reglas de la app a los objetivos que propuso la IA (no se
    confía en que el modelo las respete):
    - solo entre 30 min después de salir y 20 min antes de llegar;
    - "descanso" (dormir) solo si de verdad hay noche en ese punto del viaje
      (se llega después de las 20:00 o se cruza la noche); si no, se cambia
      por un interés de turismo;
    - "comida" y "descanso" son estrictos: solo lugares donde se puede comer
      o dormir, dentro de ±1.5 h del punto pedido.
    Sin hora de salida se supone 08:00.
    """
    salida = hora_salida or "08:00"
    turismo = _intereses_de_turismo(intereses_usuario)
    interes_de_dia = turismo[0] if turismo else "cultura"
    minimo = HORAS_MINIMAS_DESDE_ORIGEN
    maximo = (tiempo_h - HORAS_MINIMAS_ANTES_DE_LLEGAR) if tiempo_h else None

    listos = []
    for objetivo in objetivos:
        try:
            hora = float(objetivo["hora_objetivo"])
        except (KeyError, TypeError, ValueError):
            continue
        if hora < minimo or (maximo is not None and hora > maximo):
            continue

        proposito = objetivo.get("proposito")
        if proposito == "descanso":
            reloj, _ = gasto_service.momento_de_llegada(hora, salida)
            _, dia_antes = gasto_service.momento_de_llegada(hora - HORAS_TOLERANCIA_OBJETIVO_IA, salida)
            _, dia_despues = gasto_service.momento_de_llegada(hora + HORAS_TOLERANCIA_OBJETIVO_IA, salida)
            hay_noche = reloj >= HORA_TRAMO_DE_DESCANSO or dia_despues > dia_antes
            if not hay_noche:
                proposito = interes_de_dia

        estricto = proposito in ("comida", "descanso")
        listos.append(
            {
                "proposito": proposito,
                "hora_objetivo": round(hora, 2),
                "ventana": (
                    max(minimo, hora - HORAS_TOLERANCIA_OBJETIVO_IA),
                    min(maximo, hora + HORAS_TOLERANCIA_OBJETIVO_IA) if maximo is not None else hora + HORAS_TOLERANCIA_OBJETIVO_IA,
                ),
                "estricto": estricto,
                "encaja": lambda destino, p=proposito: _coincide_proposito(destino.intereses or [], destino.tipo, p),
            }
        )
    return listos


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
        ventana = objetivo.get("ventana")
        for destino, horas_estimadas in candidatos:
            if destino.id in usados or horas_estimadas is None:
                continue
            # Un objetivo con ventana (tramo) solo acepta lugares dentro de ese tramo.
            if ventana and not (ventana[0] <= horas_estimadas <= ventana[1]):
                continue
            # Un tramo personalizado por el usuario es estricto.
            if objetivo.get("estricto") and not objetivo["encaja"](destino):
                continue
            coincide_proposito = 0 if _coincide_proposito(destino.intereses or [], destino.tipo, objetivo["proposito"]) else 1
            distancia_hora = abs(horas_estimadas - objetivo["hora_objetivo"])
            # Entre los que encajan, primero el más distinguido (estrella / Michelin...).
            puntaje = (coincide_proposito, -prioridad(destino), distancia_hora)
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


def _sugerir_por_lapsos(intereses, limite, ruta, hora_salida, excluir_ids, lapso=None, tramos=None, propositos=None):
    """Sugerencias repartidas por lapsos de tiempo a lo largo de la ruta.

    Cada tramo tiene un propósito: el que eligió el usuario, o si lo dejó
    en automático el que toca según la hora del reloj (comida en horario
    de comer, dormir solo si el tramo termina después de las 20:00 o cruza
    la noche, turismo el resto).

    - Tramo personalizado: SOLO lugares que encajan con lo pedido (si pidió
      comer, solo donde se puede comer).
    - Tramo automático: de todo, con prioridad al propósito de la hora
      (y nunca se propone dormir donde no aplica).
    - `lapso=None` ("todo el camino"): primero la mejor parada de cada
      tramo y después se rellena turnando entre tramos.
    - `lapso=N`: solo lugares de ese tramo.
    - `tramos=N`: en cuántos tramos dividir el viaje (por defecto, solo).
    Cada lugar trae `lapso`, `hora_llegada` y, si encaja con lo que pide su
    tramo, `proposito`. Devuelve `None` si no se puede (sin geometría, viaje
    muy corto...) para caer al comportamiento de siempre.
    """
    lapsos = lapsos_de_la_ruta(ruta.get("tiempo_h"), tramos, hora_salida, propositos)
    if not lapsos:
        return None
    pool = obtener_pool_con_horas(ruta, excluir_ids, limite=max(limite, 40))
    if not pool:
        return None

    intereses_lista = list(intereses)
    objetivos = generar_objetivos_por_lapsos(lapsos, intereses_lista)
    por_indice = {o["indice"]: o for o in objetivos}
    for o in objetivos:
        o["encaja"] = lambda destino, tipo=o["tipo_pedido"]: _encaja_con_lo_pedido(destino, tipo, intereses_lista)

    def acepta(destino, indice):
        """En un tramo personalizado solo entran lugares que encajan."""
        o = por_indice.get(indice)
        return not (o and o["estricto"]) or o["encaja"](destino)

    def armar(destino, horas):
        lugar = _lugar_desde_destino(destino, horas)
        indice = _indice_de_lapso(lapsos, horas)
        lugar["lapso"] = indice
        lugar["hora_llegada"] = gasto_service.formato_hora(gasto_service.hora_de_llegada(horas, hora_salida))
        objetivo = por_indice.get(indice)
        if objetivo and objetivo["tipo_pedido"] != "turismo":
            if _coincide_proposito(destino.intereses or [], destino.tipo, objetivo["proposito"]):
                lugar["proposito"] = objetivo["proposito"]
        return lugar

    if lapso is not None:
        objetivo = por_indice.get(lapso)
        if not objetivo:
            return None
        elegido = next(l for l in lapsos if l["indice"] == lapso)
        dentro = [(d, h) for d, h in pool if elegido["desde_h"] <= h <= elegido["hasta_h"] and acepta(d, lapso)]
        random.shuffle(dentro)
        dentro.sort(
            key=lambda item: (
                -prioridad(item[0]),  # los distinguidos (y cercanos a la ruta) van primero
                0 if _coincide_proposito(item[0].intereses or [], item[0].tipo, objetivo["proposito"]) else 1,
                0 if (intereses and intereses & set(item[0].intereses or [])) else 1,
                -(item[0].poblacion or 0) if objetivo["proposito"] == "descanso" else 0,
            )
        )
        return _linea_de_tiempo([armar(d, h) for d, h in dentro[:limite]])

    asignadas = []
    for lugar in asignar_paradas_a_objetivos(pool, objetivos):
        destino = next(d for d, _ in pool if d.id == lugar["id"])
        asignadas.append(armar(destino, lugar["horas_estimadas"]))

    ids_usados = {lugar["id"] for lugar in asignadas}
    por_lapso = {l["indice"]: [] for l in lapsos}
    for d, h in _ordenar_candidatos([(d, h) for d, h in pool if d.id not in ids_usados], intereses, None):
        indice = _indice_de_lapso(lapsos, h)
        if indice is not None and acepta(d, indice):
            por_lapso[indice].append(armar(d, h))

    relleno = []
    while any(por_lapso.values()):
        for indice in por_lapso:  # una por lapso en cada vuelta
            if por_lapso[indice]:
                relleno.append(por_lapso[indice].pop(0))
    return _linea_de_tiempo(_elegir_con_distinguidos(asignadas + relleno, limite))


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

        # Solo se recomienda dentro de la ventana: desde 30 min después de
        # salir hasta 20 min antes de llegar.
        if horas_estimadas < HORAS_MINIMAS_DESDE_ORIGEN:
            continue
        if tiempo_total and horas_estimadas > tiempo_total - HORAS_MINIMAS_ANTES_DE_LLEGAR:
            continue

        destino.distancia_a_ruta_km = round(distancia_perp, 1) if distancia_perp is not None else None
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


def sugerir_paradas(intereses=None, limite=4, ruta=None, horas_max=None, excluir_ids=None, hora_salida=None, lapso=None, tramos=None, propositos=None):
    """Devuelve destinos sugeridos para la ruta actual.

    - `ruta`: resumen devuelto por route_service.calcular_ruta (usa su
      geometría real para sugerir solo lugares cerca del camino).
    - `horas_max`: ya no lo pide el formulario (la app reparte sola las
      sugerencias por lapsos de tiempo); solo se conserva por si alguien
      lo manda, y se usa en el respaldo sin geometría de ruta.
    - `hora_salida`: hora aproximada de salida ("HH:MM"), opcional. Ajusta
      el propósito de cada parada a la hora real del día (comida/descanso,
      evitando proponer dormir de día) — mismo mecanismo que usa el chat
      de IA, sin necesitar ningún proveedor.
    - `lapso`: índice de un lapso (ver `lapsos_de_la_ruta`) para ver solo
      las sugerencias de ese tramo del viaje.
    - `tramos`: en cuántos tramos dividir el viaje (por defecto, automático).
    - `propositos`: {indice de tramo: "comida"|"turismo"|"descanso"} para los
      tramos que el usuario personalizó; los demás quedan en automático.
    - `excluir_ids`: ids de destinos que ya se mostraron/agregaron y no
      deben repetirse (para "ver más recomendaciones").
    """
    intereses = set(intereses or [])
    excluir_ids = set(excluir_ids or [])

    try:
        if ruta and ruta.get("geometria"):
            resultado = _sugerir_por_lapsos(intereses, limite, ruta, hora_salida, excluir_ids, lapso, tramos, propositos)
            if resultado is not None:
                return resultado

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
