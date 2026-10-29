"""Gasto máximo recomendado de un viaje.

Suma gasolina + casetas + imprevistos, y solo si aplica: comidas (paradas
de comida) y hospedaje (noches). Todo es un estimado para un auto
particular, por el viaje completo. Las constantes están arriba para
poder afinarlas sin tocar la lógica.
"""

from app.services import llm_provider

# --- Gasolina ---
RENDIMIENTO_DEFAULT_KML = 13  # término medio entre autos de ~11 y ~15 km/l
RENDIMIENTOS_KML = {"compacto": 15, "mediano": 13, "suv": 11}
# Magna ~ $23.8/l (promedio nacional, sep 2026). La Premium cuesta ~$5-6
# más. Sin elegir tipo se usa un punto medio.
PRECIO_LITRO_DEFAULT = 25.5
PRECIOS_LITRO = {"magna": 23.8, "premium": 29.0}

# --- Casetas ---
# Respaldo cuando no hay IA conectada: ~$1.5/km en tramos de cuota
# (rango típico $1-2/km en autopistas troncales para auto) por ~70% del
# trayecto que suele ir por cuota ≈ $1.1/km sobre la distancia total.
# Es un promedio: cada caseta cuesta distinto.
CASETAS_POR_KM_RESPALDO = 1.1

# --- Comida y hospedaje (solo si aplican) ---
COSTO_COMIDA_POR_PERSONA = 150
COSTO_NOCHE_HOSPEDAJE = 600  # por noche, por el grupo (una habitación)
HORAS_POR_PARADA_DE_COMIDA = 0.75

# Un día de manejo razonable: no se maneja pasadas las 21:00; al día
# siguiente se retoma a las 07:00.
HORA_SALIDA_DEFAULT = 8.0
HORA_FIN_MANEJO = 21.0
HORA_INICIO_MANEJO = 7.0

# --- Imprevistos (snacks, propinas, un desvío...) ---
IMPREVISTOS_MIN = 500
IMPREVISTOS_MAX = 2000
IMPREVISTOS_HORAS_MIN = 4  # viajes de hasta 4 h -> mínimo
IMPREVISTOS_HORAS_MAX = 20  # viajes de 20 h o más -> máximo

# Ventanas del día en las que una parada cuenta como comida (desayuno,
# comida, cena) y hora a partir de la cual se duerme ahí.
VENTANAS_DE_COMIDA = [(7.5, 10.0), (13.0, 16.0), (19.0, 21.5)]
HORA_LLEGADA_PARA_DORMIR = 20.0

# Nadie come tres veces en hora y media ni duerme dos veces en una tarde:
# entre una comida y la siguiente deben pasar al menos estas horas de
# camino, y entre una noche y la siguiente también.
HORAS_ENTRE_COMIDAS = 3.0
HORAS_ENTRE_NOCHES = 8.0

_cache_casetas_ia = {}


def _hora_a_decimal(hora_salida):
    """'17:30' -> 17.5. Devuelve la hora de salida por default si viene
    vacía o inválida."""
    try:
        horas, minutos = str(hora_salida).split(":")[:2]
        valor = int(horas) + int(minutos) / 60
        if 0 <= valor < 24:
            return valor
    except (ValueError, TypeError):
        pass
    return HORA_SALIDA_DEFAULT


def noches_estimadas(tiempo_h, hora_salida=None):
    """Cuántas noches hay que dormir en el camino: se simula el viaje día
    por día. Un viaje de 8 h que sale a las 08:00 llega a las 16:00 (0
    noches); uno de 10 h que sale a las 17:00 pasa de las 21:00 (1)."""
    hora = _hora_a_decimal(hora_salida)
    restante = float(tiempo_h)
    noches = 0
    while True:
        disponible = max(0.0, HORA_FIN_MANEJO - hora)
        if restante <= disponible:
            return noches
        restante -= disponible
        noches += 1
        hora = HORA_INICIO_MANEJO


def momento_de_llegada(horas_manejo, hora_salida=None):
    """(hora del reloj, número de día) al que se llega tras `horas_manejo`
    de manejo, con las mismas reglas de día que `noches_estimadas`: cada
    noche dormida suma un día."""
    hora = _hora_a_decimal(hora_salida)
    restante = float(horas_manejo)
    dia = 1
    while True:
        disponible = max(0.0, HORA_FIN_MANEJO - hora)
        if restante <= disponible:
            return hora + restante, dia
        restante -= disponible
        hora = HORA_INICIO_MANEJO
        dia += 1


def hora_de_llegada(horas_manejo, hora_salida=None):
    """Solo la hora del reloj (0-24) de `momento_de_llegada`."""
    return momento_de_llegada(horas_manejo, hora_salida)[0]


def formato_hora(hora_decimal):
    minutos = round((hora_decimal % 24) * 60)
    return f"{minutos // 60 % 24:02d}:{minutos % 60:02d}"


def clasificar_parada(parada, hora_salida=None):
    """Deduce solo qué se hace en una parada del itinerario:
    - comida: el lugar es de comida, la parada nació como "comida", o se
      llega en horario de desayuno/comida/cena;
    - hospedaje: se llega de noche (a partir de las 20:00).
    Sin `horas_estimadas` (dato de la ruta) solo se puede saber por el
    tipo de lugar."""
    intereses = parada.get("intereses") or []
    es_comida = "comida" in intereses or parada.get("proposito") == "comida"
    es_hospedaje = False
    hora_llegada = None

    horas = _numero_o_none(parada.get("horas_estimadas"))
    if horas is not None:
        llegada = hora_de_llegada(horas, hora_salida)
        hora_llegada = formato_hora(llegada)
        es_comida = es_comida or any(desde <= llegada <= hasta for desde, hasta in VENTANAS_DE_COMIDA)
        es_hospedaje = llegada >= HORA_LLEGADA_PARA_DORMIR

    return {
        "nombre": parada.get("nombre"),
        "comida": es_comida,
        "hospedaje": es_hospedaje,
        "hora_llegada": hora_llegada,
    }


def _espaciar(detalle, paradas, clave, horas_minimas):
    """Si varias paradas seguidas se clasificaron igual (ej. tres "comida"
    en la misma mañana), solo cuenta la primera de cada `horas_minimas`."""
    def horas(i):
        return _numero_o_none(paradas[i].get("horas_estimadas"))

    ultima = None
    for i in sorted((i for i in range(len(detalle)) if horas(i) is not None), key=horas):
        if not detalle[i][clave]:
            continue
        if ultima is not None and horas(i) - ultima < horas_minimas:
            detalle[i][clave] = False
        else:
            ultima = horas(i)


def imprevistos(tiempo_h):
    """$500 en viajes cortos, subiendo poco a poco hasta $2,000."""
    avance = (float(tiempo_h) - IMPREVISTOS_HORAS_MIN) / (IMPREVISTOS_HORAS_MAX - IMPREVISTOS_HORAS_MIN)
    avance = min(1.0, max(0.0, avance))
    return round(IMPREVISTOS_MIN + avance * (IMPREVISTOS_MAX - IMPREVISTOS_MIN))


def estimar_casetas(origen, destino, distancia_km):
    """Costo de casetas del viaje: (monto_mxn, fuente).

    Si hay una IA conectada, se le pide el estimado para ese trayecto
    (con búsqueda web); si no, o si falla, se usa el promedio por km.
    """
    respaldo = round(distancia_km * CASETAS_POR_KM_RESPALDO)
    if not llm_provider.hay_proveedor_configurado():
        return respaldo, "estimado"

    clave = (origen.strip().lower(), destino.strip().lower())
    if clave not in _cache_casetas_ia:
        monto_ia = llm_provider.estimar_casetas(origen, destino, distancia_km)
        if monto_ia is not None:  # los fallos no se guardan: se reintenta la próxima vez
            _cache_casetas_ia[clave] = monto_ia

    monto = _cache_casetas_ia.get(clave)
    # Descarta respuestas absurdas (negativas o de más de $5/km).
    if isinstance(monto, (int, float)) and 0 <= monto <= distancia_km * 5:
        return round(monto), "ia"
    return respaldo, "estimado"


def _numero_o_none(valor, minimo=0):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if numero >= minimo else None


def calcular_gasto(distancia_km, tiempo_h, ajustes=None, paradas=None, casetas_por_km=None):
    """Desglose del gasto máximo recomendado.

    `ajustes` (todo opcional): personas, hora_salida, tipo_coche
    (compacto/mediano/suv), gasolina (magna/premium), comidas y noches
    (si se mandan, reemplazan el cálculo automático).
    `paradas`: las del itinerario; de cada una se deduce sola si es para
    comer o para dormir (ver `clasificar_parada`) y se suma al gasto.
    """
    ajustes = ajustes or {}
    paradas = paradas or []

    personas = int(_numero_o_none(ajustes.get("personas"), 1) or 1)
    rendimiento = RENDIMIENTOS_KML.get(ajustes.get("tipo_coche"), RENDIMIENTO_DEFAULT_KML)
    precio_litro = PRECIOS_LITRO.get(ajustes.get("gasolina"), PRECIO_LITRO_DEFAULT)

    detalle = [clasificar_parada(p, ajustes.get("hora_salida")) for p in paradas]
    _espaciar(detalle, paradas, "comida", HORAS_ENTRE_COMIDAS)
    _espaciar(detalle, paradas, "hospedaje", HORAS_ENTRE_NOCHES)
    comidas_auto = sum(1 for d in detalle if d["comida"])
    comidas_manual = _numero_o_none(ajustes.get("comidas"))
    comidas = int(comidas_manual) if comidas_manual is not None else comidas_auto

    # Cada parada para comer también alarga el viaje.
    tiempo_con_paradas = float(tiempo_h) + comidas * HORAS_POR_PARADA_DE_COMIDA
    noches_manual = _numero_o_none(ajustes.get("noches"))
    noches_auto = max(
        noches_estimadas(tiempo_con_paradas, ajustes.get("hora_salida")),
        sum(1 for d in detalle if d["hospedaje"]),
    )
    noches = int(noches_manual) if noches_manual is not None else noches_auto

    gasolina = distancia_km / rendimiento * precio_litro
    casetas = distancia_km * (CASETAS_POR_KM_RESPALDO if casetas_por_km is None else casetas_por_km)
    costo_comidas = comidas * COSTO_COMIDA_POR_PERSONA * personas
    hospedaje = noches * COSTO_NOCHE_HOSPEDAJE
    extra = imprevistos(tiempo_h)

    return {
        "gasolina": round(gasolina),
        "casetas": round(casetas),
        "comidas": round(costo_comidas),
        "hospedaje": round(hospedaje),
        "imprevistos": extra,
        "total": round(gasolina + casetas + costo_comidas + hospedaje + extra),
        "num_comidas": comidas,
        "num_noches": noches,
        "comidas_automatico": comidas_manual is None,
        "noches_automatico": noches_manual is None,
        "paradas_detalle": detalle,
        "personas": personas,
        "rendimiento_kml": rendimiento,
        "precio_litro": precio_litro,
    }
