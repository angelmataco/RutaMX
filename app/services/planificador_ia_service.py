"""Orquesta un turno del chat "Planear con IA".

No decide nada por su cuenta: le pregunta a `llm_provider` qué falta o
qué objetivos de parada propone, y usa `route_service`/`ai_service` (los
mismos que ya arman el flujo manual) para convertir esos objetivos en
lugares reales verificados. La IA nunca elige el lugar exacto — solo
propósito + momento del viaje.
"""

from app.services import ai_service, llm_provider, route_service


def procesar_turno(mensajes: list[dict]) -> dict:
    """Procesa un turno del chat de planeación.

    `mensajes` es el historial completo `[{"role": "user"|"assistant",
    "content": str}]`. Devuelve uno de:
    - `{"tipo": "pregunta", "mensaje": str, "opciones_respuesta": [str]}`
    - `{"tipo": "opciones", "opciones": [{"titulo", "resumen", "paradas"}]}`
    - `{"tipo": "error", "mensaje": str}`
    """
    if not llm_provider.hay_proveedor_configurado():
        return {"tipo": "error", "mensaje": "No hay ninguna IA conectada en este servidor."}

    slots = llm_provider.extraer_slots_viaje(mensajes)
    if not slots:
        return {"tipo": "error", "mensaje": "No se pudo procesar tu mensaje. Intenta de nuevo."}

    if not slots.get("listo"):
        return {
            "tipo": "pregunta",
            "mensaje": slots.get("pregunta_siguiente") or "¿Puedes contarme más sobre tu viaje?",
            "opciones_respuesta": slots.get("opciones_respuesta") or [],
        }

    origen = (slots.get("origen") or "").strip()
    destino = (slots.get("destino") or "").strip()
    if not origen or not destino:
        return {"tipo": "error", "mensaje": "No logré identificar el origen y destino de tu viaje."}

    try:
        ruta = route_service.calcular_ruta(origen, destino)
    except Exception as error:
        print(f"No se pudo calcular la ruta para el chat de IA: {error}")
        return {"tipo": "error", "mensaje": "No se pudo calcular la ruta para ese origen/destino."}

    pool = ai_service.obtener_pool_con_horas(ruta)

    contexto = {
        "origen": origen,
        "destino": destino,
        "personas": slots.get("personas"),
        "tiempo_h": ruta.get("tiempo_h"),
        "distancia_km": ruta.get("distancia_km"),
        "horas_max": slots.get("horas_max"),
        "hora_salida": slots.get("hora_salida"),
        "intereses": slots.get("intereses"),
    }
    propuesta = llm_provider.generar_opciones_objetivos(contexto)
    if not propuesta or not propuesta.get("opciones"):
        return {"tipo": "error", "mensaje": "La IA no pudo proponer un itinerario para este viaje."}

    resumen_publico = {clave: valor for clave, valor in ruta.items() if clave != "geometria"}
    hora_salida = slots.get("hora_salida")
    intereses_usuario = slots.get("intereses")

    opciones = []
    for opcion in propuesta["opciones"][:2]:
        objetivos = ai_service.filtrar_objetivos_por_hora_del_dia(
            opcion.get("objetivos") or [], hora_salida, intereses_usuario
        )
        paradas = ai_service.asignar_paradas_a_objetivos(pool, objetivos)
        if not paradas:
            continue
        opciones.append({"titulo": opcion.get("titulo") or "Opción de itinerario", "resumen": resumen_publico, "paradas": paradas})

    if not opciones:
        return {"tipo": "error", "mensaje": "No se encontraron paradas reales que encajen con este viaje."}

    return {"tipo": "opciones", "opciones": opciones}
