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
    `paradas`: las del itinerario; cada una con `intereses`. Las que
    tienen "comida" cuentan como una comida.
    """
    ajustes = ajustes or {}
    paradas = paradas or []

    personas = int(_numero_o_none(ajustes.get("personas"), 1) or 1)
    rendimiento = RENDIMIENTOS_KML.get(ajustes.get("tipo_coche"), RENDIMIENTO_DEFAULT_KML)
    precio_litro = PRECIOS_LITRO.get(ajustes.get("gasolina"), PRECIO_LITRO_DEFAULT)

    comidas_auto = sum(1 for p in paradas if "comida" in (p.get("intereses") or []))
    comidas_manual = _numero_o_none(ajustes.get("comidas"))
    comidas = int(comidas_manual) if comidas_manual is not None else comidas_auto

    # Cada parada para comer también alarga el viaje.
    tiempo_con_paradas = float(tiempo_h) + comidas * HORAS_POR_PARADA_DE_COMIDA
    noches_manual = _numero_o_none(ajustes.get("noches"))
    noches = int(noches_manual) if noches_manual is not None else noches_estimadas(
        tiempo_con_paradas, ajustes.get("hora_salida")
    )

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
        "personas": personas,
        "rendimiento_kml": rendimiento,
        "precio_litro": precio_litro,
    }
