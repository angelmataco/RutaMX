"""Capa que conecta con "la IA que cada quien tenga configurada".

No sabe nada de destinos, rutas ni del chat de planeación — solo manda
una instrucción de texto (con un JSON Schema de salida) a un proveedor de
LLM (Claude, OpenAI o Gemini, detectado automáticamente por qué API key
está en el entorno) y devuelve un dict ya parseado. Cada módulo que use
esto (`ia_destinos_service.py`, `planificador_ia_service.py`) arma su
propio prompt/schema y le pide al dispatcher compartido que lo ejecute.

Cada persona del equipo conecta SU propia API key en su `.env` local
(nunca se sube a git) — no todos tienen por qué usar el mismo proveedor.
"""

import json
import os

# Mismo schema para los tres proveedores, así el resultado no depende de
# cuál esté conectado — solo cambia quién lo ejecuta.
CAMPOS_DESTINO = {
    "encontrado": "bool — true solo si identificaste un lugar real de México con confianza razonable",
    "nombre": "string — nombre oficial del lugar, ya corregido si el usuario tenía errores de escritura",
    "estado": "string — nombre oficial del estado de México al que pertenece",
    "tipo": "string — una de: ciudad_principal, pueblo_magico, sitio_turistico",
    "descripcion": "string — 1-2 líneas, tono turístico/informativo",
    "intereses": "array de string — subconjunto de: naturaleza, playas, pueblos_magicos, comida, descanso, cultura",
    "poblacion": "integer o null — población aproximada si la encuentras",
}

JSON_SCHEMA_DESTINO = {
    "type": "object",
    "properties": {
        "encontrado": {"type": "boolean"},
        "nombre": {"type": "string"},
        "estado": {"type": "string"},
        "tipo": {"type": "string", "enum": ["ciudad_principal", "pueblo_magico", "sitio_turistico"]},
        "descripcion": {"type": "string"},
        "intereses": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["naturaleza", "playas", "pueblos_magicos", "comida", "descanso", "cultura"],
            },
        },
        "poblacion": {"type": ["integer", "null"]},
    },
    "required": ["encontrado", "nombre", "estado", "tipo", "descripcion", "intereses", "poblacion"],
    "additionalProperties": False,
}

INTERESES_VALIDOS = ["naturaleza", "playas", "pueblos_magicos", "comida", "descanso", "cultura"]

JSON_SCHEMA_SLOTS_VIAJE = {
    "type": "object",
    "properties": {
        "listo": {"type": "boolean"},
        "pregunta_siguiente": {"type": ["string", "null"]},
        "opciones_respuesta": {
            "type": ["array", "null"],
            "items": {"type": "string"},
            "maxItems": 3,
        },
        "origen": {"type": ["string", "null"]},
        "destino": {"type": ["string", "null"]},
        "personas": {"type": ["integer", "null"]},
        "horas_max": {"type": ["number", "null"]},
        "hora_salida": {"type": ["string", "null"]},
        "intereses": {"type": ["array", "null"], "items": {"type": "string", "enum": INTERESES_VALIDOS}},
    },
    "required": [
        "listo", "pregunta_siguiente", "opciones_respuesta", "origen", "destino",
        "personas", "horas_max", "hora_salida", "intereses",
    ],
    "additionalProperties": False,
}

JSON_SCHEMA_OPCIONES_OBJETIVOS = {
    "type": "object",
    "properties": {
        "opciones": {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "items": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string"},
                    "objetivos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "proposito": {"type": "string", "enum": INTERESES_VALIDOS},
                                "hora_objetivo": {"type": "number"},
                            },
                            "required": ["proposito", "hora_objetivo"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["titulo", "objetivos"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["opciones"],
    "additionalProperties": False,
}

# Modelo por default de cada proveedor. Se puede sobreescribir con la
# variable de entorno IA_MODELO si alguien quiere usar otro.
MODELOS_DEFAULT = {
    "anthropic": "claude-opus-5",
    # Nombres de modelo cambian seguido en estos dos proveedores — quien
    # conecte la key debe confirmar el nombre vigente en su cuenta.
    "openai": "gpt-5.1",
    "gemini": "gemini-3-pro",
}

MAX_PREGUNTAS_CHAT = 5


def _proveedor_configurado() -> str | None:
    forzado = os.environ.get("IA_PROVEEDOR", "").strip().lower()
    if forzado in MODELOS_DEFAULT:
        return forzado

    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    return None


def hay_proveedor_configurado() -> bool:
    return _proveedor_configurado() is not None


def _modelo_configurado(proveedor: str) -> str:
    return os.environ.get("IA_MODELO") or MODELOS_DEFAULT[proveedor]


def _llamar_proveedor(prompt: str, schema: dict, usar_busqueda_web: bool = False) -> dict | None:
    """Dispatcher compartido: detecta el proveedor configurado y le pide
    que responda `prompt` ajustándose a `schema` (JSON Schema). Devuelve
    el dict ya parseado, o `None` si no hay proveedor, o hubo un error de
    red/API/parseo (nunca lanza excepción hacia arriba — quien llama debe
    poder seguir con su flujo normal sin esto).
    """
    proveedor = _proveedor_configurado()
    if not proveedor:
        return None

    modelo = _modelo_configurado(proveedor)

    try:
        if proveedor == "anthropic":
            return _completar_con_anthropic(prompt, modelo, schema, usar_busqueda_web)
        if proveedor == "openai":
            return _completar_con_openai(prompt, modelo, schema, usar_busqueda_web)
        return _completar_con_gemini(prompt, modelo, schema, usar_busqueda_web)
    except Exception as error:
        print(f"No se pudo completar la solicitud con {proveedor}: {error}")
        return None


def _plantilla_prompt_destino(nombre_escrito: str) -> str:
    campos_desc = "\n".join(f"- {campo}: {descripcion}" for campo, descripcion in CAMPOS_DESTINO.items())
    return (
        f'El usuario escribió "{nombre_escrito}" buscando un lugar en México '
        "(puede tener errores de ortografía). Identifica el lugar real al que "
        "se refiere, confírmalo con una búsqueda web, y devuelve estos campos "
        f"exactos:\n{campos_desc}\n\n"
        "Si NO puedes identificar un lugar real de México con confianza "
        'razonable, responde con "encontrado": false y deja los demás campos '
        "vacíos. No inventes datos — si no lo encuentras en la búsqueda, no lo "
        "adivines."
    )


def completar_plantilla_destino(nombre_escrito_por_usuario: str) -> dict | None:
    """Le pide al proveedor de IA configurado que identifique el lugar y
    llene la plantilla de un destino (con búsqueda web real). Devuelve el
    dict ya parseado, o `None` si no hay proveedor, no se encontró el
    lugar, o hubo un error.
    """
    resultado = _llamar_proveedor(
        _plantilla_prompt_destino(nombre_escrito_por_usuario), JSON_SCHEMA_DESTINO, usar_busqueda_web=True
    )
    if not resultado or not resultado.get("encontrado"):
        return None
    return resultado


def _prompt_slots_viaje(mensajes: list[dict]) -> str:
    preguntas_ia_hechas = sum(1 for m in mensajes if m.get("role") == "assistant")
    transcript = "\n".join(f'{m.get("role")}: {m.get("content")}' for m in mensajes)
    return (
        "Eres el asistente de planeación de road trips de RutaMX. Lee esta "
        f"conversación con el usuario y extrae lo que ya sabes del viaje:\n\n{transcript}\n\n"
        "Campos a extraer: origen, destino, personas (cuántas van), "
        "horas_max (cuántas horas máximo quieren manejar seguido antes de "
        "parar), hora_salida (formato HH:MM, hora aproximada en que saldrían), "
        f"intereses (subconjunto de {INTERESES_VALIDOS}).\n\n"
        f"Ya le has hecho {preguntas_ia_hechas} pregunta(s) de seguimiento en "
        f"esta conversación. El máximo permitido es {MAX_PREGUNTAS_CHAT} — si "
        f"ya llegaste a {MAX_PREGUNTAS_CHAT} o más, NO preguntes otra vez: "
        "da tu mejor estimado razonable con lo que ya tengas y marca "
        '"listo": true (origen y destino son los únicos campos '
        "verdaderamente indispensables; el resto puedes asumirlo con "
        "sentido común si no se dijo).\n\n"
        f"Si todavía puedes preguntar (menos de {MAX_PREGUNTAS_CHAT} "
        "preguntas hechas) y falta un dato importante para armar un buen "
        'itinerario, pon "listo": false y escribe UNA sola pregunta breve y '
        'natural en "pregunta_siguiente" (nunca preguntes más de una cosa a '
        "la vez). Junto con la pregunta, propón hasta 3 respuestas rápidas "
        'concretas y relevantes a ESA pregunta en "opciones_respuesta" (ej. '
        'si preguntas la hora de salida en un viaje corto: "8-10am", '
        '"12-2pm", "5-7pm" — el usuario siempre puede escribir su propia '
        "respuesta también, así que no hace falta cubrir todos los "
        "casos).\n\n"
        'Si ya tienes todo lo necesario, pon "listo": true, '
        '"pregunta_siguiente": null, "opciones_respuesta": null.'
    )


def extraer_slots_viaje(mensajes: list[dict]) -> dict | None:
    """Lee el historial del chat de planeación y extrae los datos del
    viaje que ya se conocen, o la siguiente pregunta a hacer (con hasta 3
    respuestas rápidas sugeridas). Devuelve `None` si no hay proveedor
    configurado o hubo un error.
    """
    return _llamar_proveedor(_prompt_slots_viaje(mensajes), JSON_SCHEMA_SLOTS_VIAJE, usar_busqueda_web=False)


def _prompt_opciones_objetivos(contexto: dict) -> str:
    return (
        "Vas a proponer objetivos de parada para un road trip real por "
        f"México. Datos del viaje:\n"
        f"- Origen: {contexto.get('origen')}\n"
        f"- Destino: {contexto.get('destino')}\n"
        f"- Personas: {contexto.get('personas') or 'no especificado'}\n"
        f"- Duración total estimada: {contexto.get('tiempo_h')} horas ({contexto.get('distancia_km')} km)\n"
        f"- Horas máximas de manejo seguido antes de parar: {contexto.get('horas_max') or 'no especificado'}\n"
        f"- Hora de salida: {contexto.get('hora_salida') or 'no especificada'}\n"
        f"- Intereses mencionados: {contexto.get('intereses') or 'ninguno en particular'}\n\n"
        "Propón EXACTAMENTE 2 opciones de itinerario, genuinamente "
        "distintas entre sí (no una plantilla fija — la cantidad, el "
        "propósito y el horario de cada parada los decides tú según ESTE "
        "viaje en particular; un viaje corto puede terminar con una sola "
        "parada en ambas opciones, uno largo con varias). Cada opción es "
        "una lista de objetivos: {proposito, hora_objetivo}. "
        f"proposito debe ser uno de: {INTERESES_VALIDOS}. hora_objetivo es "
        "cuántas horas después de salir conviene esa parada (número, puede "
        "tener decimales).\n\n"
        "No elijas el lugar exacto — eso lo hace otro sistema con datos "
        "reales verificados. Solo decide propósito + momento del viaje. "
        "Dale a cada opción un título corto (3-6 palabras) que describa su "
        'estilo (ej. "Ruta directa con una parada", "Explora el camino").'
    )


def generar_opciones_objetivos(contexto: dict) -> dict | None:
    """A partir de los datos ya extraídos del viaje + el resumen real de
    la ruta, genera 2 conjuntos distintos de objetivos de parada
    (propósito + hora aproximada, sin elegir el lugar). Devuelve `None`
    si no hay proveedor configurado o hubo un error.
    """
    return _llamar_proveedor(
        _prompt_opciones_objetivos(contexto), JSON_SCHEMA_OPCIONES_OBJETIVOS, usar_busqueda_web=False
    )


JSON_SCHEMA_CASETAS = {
    "type": "object",
    "properties": {"casetas_mxn": {"type": ["number", "null"]}},
    "required": ["casetas_mxn"],
    "additionalProperties": False,
}


def estimar_casetas(origen: str, destino: str, distancia_km: float) -> float | None:
    """Pide a la IA el costo total aproximado de casetas (MXN, auto
    particular) del trayecto. Devuelve `None` si no hay proveedor o falla;
    quien llama valida el número y cae al promedio por km."""
    prompt = (
        f"Estima el costo TOTAL en pesos mexicanos de las casetas de peaje para un automóvil "
        f"particular (sin remolque) en el viaje por carretera de {origen} a {destino} "
        f"(unos {round(distancia_km)} km), por la ruta más común y con las tarifas vigentes. "
        f"Suma todas las casetas del trayecto. Si el trayecto casi no tiene casetas, responde un "
        f"monto bajo. Responde solo con el JSON pedido; usa null si no puedes estimarlo."
    )
    datos = _llamar_proveedor(prompt, JSON_SCHEMA_CASETAS, usar_busqueda_web=True)
    return (datos or {}).get("casetas_mxn")


def _completar_con_anthropic(prompt: str, modelo: str, schema: dict, usar_busqueda_web: bool) -> dict | None:
    import anthropic

    client = anthropic.Anthropic()
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}] if usar_busqueda_web else None
    respuesta = client.messages.create(
        model=modelo,
        max_tokens=1024,
        tools=tools,
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}],
    )
    if respuesta.stop_reason == "refusal":
        return None

    for bloque in respuesta.content:
        if bloque.type == "text":
            return json.loads(bloque.text)
    return None


def _completar_con_openai(prompt: str, modelo: str, schema: dict, usar_busqueda_web: bool) -> dict | None:
    # SDK/forma de llamada de OpenAI cambian seguido — verificar contra la
    # documentación vigente de la Responses API al momento de conectar
    # esta key por primera vez.
    import openai

    client = openai.OpenAI()
    tools = [{"type": "web_search"}] if usar_busqueda_web else None
    respuesta = client.responses.create(
        model=modelo,
        input=prompt,
        tools=tools,
        text={"format": {"type": "json_schema", "name": "respuesta", "schema": schema}},
    )
    return json.loads(respuesta.output_text)


def _completar_con_gemini(prompt: str, modelo: str, schema: dict, usar_busqueda_web: bool) -> dict | None:
    # SDK/forma de llamada de Gemini cambian seguido — verificar contra la
    # documentación vigente de google-genai al momento de conectar esta
    # key por primera vez.
    from google import genai
    from google.genai import types

    client = genai.Client()
    tools = [types.Tool(google_search=types.GoogleSearch())] if usar_busqueda_web else None
    respuesta = client.models.generate_content(
        model=modelo,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=tools,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    return json.loads(respuesta.text)
