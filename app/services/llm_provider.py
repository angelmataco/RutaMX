"""Capa que conecta con "la IA que cada quien tenga configurada".

No sabe nada de destinos ni de la base de datos — solo manda una
instrucción de texto a un proveedor de LLM (Claude, OpenAI o Gemini,
detectado automáticamente por qué API key está en el entorno) y devuelve
un dict ya parseado. `ia_destinos_service.py` es quien sabe qué hacer con
ese dict.

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

# Modelo por default de cada proveedor. Se puede sobreescribir con la
# variable de entorno IA_MODELO si alguien quiere usar otro.
MODELOS_DEFAULT = {
    "anthropic": "claude-opus-5",
    # Nombres de modelo cambian seguido en estos dos proveedores — quien
    # conecte la key debe confirmar el nombre vigente en su cuenta.
    "openai": "gpt-5.1",
    "gemini": "gemini-3-pro",
}


def _plantilla_prompt(nombre_escrito: str) -> str:
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


def _modelo_configurado(proveedor: str) -> str:
    return os.environ.get("IA_MODELO") or MODELOS_DEFAULT[proveedor]


def completar_plantilla_destino(nombre_escrito_por_usuario: str) -> dict | None:
    """Le pide al proveedor de IA configurado que identifique el lugar y
    llene la plantilla de un destino. Devuelve el dict ya parseado, o
    `None` si no hay ningún proveedor configurado, la IA no encontró el
    lugar, o hubo un error de red/API (nunca lanza excepción hacia arriba
    — quien llama debe poder seguir con su flujo normal sin esto).
    """
    proveedor = _proveedor_configurado()
    if not proveedor:
        return None

    prompt = _plantilla_prompt(nombre_escrito_por_usuario)
    modelo = _modelo_configurado(proveedor)

    try:
        if proveedor == "anthropic":
            resultado = _completar_con_anthropic(prompt, modelo)
        elif proveedor == "openai":
            resultado = _completar_con_openai(prompt, modelo)
        else:
            resultado = _completar_con_gemini(prompt, modelo)
    except Exception as error:
        print(f"No se pudo generar el destino con {proveedor}: {error}")
        return None

    if not resultado or not resultado.get("encontrado"):
        return None
    return resultado


def _completar_con_anthropic(prompt: str, modelo: str) -> dict | None:
    import anthropic

    client = anthropic.Anthropic()
    respuesta = client.messages.create(
        model=modelo,
        max_tokens=1024,
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}],
        output_config={"format": {"type": "json_schema", "schema": JSON_SCHEMA_DESTINO}},
        messages=[{"role": "user", "content": prompt}],
    )
    if respuesta.stop_reason == "refusal":
        return None

    for bloque in respuesta.content:
        if bloque.type == "text":
            return json.loads(bloque.text)
    return None


def _completar_con_openai(prompt: str, modelo: str) -> dict | None:
    # SDK/forma de llamada de OpenAI cambian seguido — verificar contra la
    # documentación vigente de la Responses API al momento de conectar
    # esta key por primera vez.
    import openai

    client = openai.OpenAI()
    respuesta = client.responses.create(
        model=modelo,
        input=prompt,
        tools=[{"type": "web_search"}],
        text={
            "format": {
                "type": "json_schema",
                "name": "destino",
                "schema": JSON_SCHEMA_DESTINO,
            }
        },
    )
    return json.loads(respuesta.output_text)


def _completar_con_gemini(prompt: str, modelo: str) -> dict | None:
    # SDK/forma de llamada de Gemini cambian seguido — verificar contra la
    # documentación vigente de google-genai al momento de conectar esta
    # key por primera vez.
    from google import genai
    from google.genai import types

    client = genai.Client()
    respuesta = client.models.generate_content(
        model=modelo,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_mime_type="application/json",
            response_schema=JSON_SCHEMA_DESTINO,
        ),
    )
    return json.loads(respuesta.text)
