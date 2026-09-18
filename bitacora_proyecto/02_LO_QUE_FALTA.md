# Lo que falta — RutaMX

Última actualización: 2026-09-18

## Pendiente marcado en el código (TODOs reales)

- **Rutas guardadas sin usuario** (`app/models.py`): `RutaGuardada` no
  tiene columna `usuario_id`. Falta implementar login para que cada quien
  vea solo sus propias rutas. Hoy todas las rutas guardadas son públicas
  entre quien use la app.
- **Fallback con IA para destinos que no están en la base**
  (`app/services/ai_service.py`): si alguien pide una ruta hacia un pueblo
  chico que no está en los 369 destinos curados, hoy no se genera nada
  nuevo. La idea (ya escrita en el código como plan) es que una IA genere
  la sugerencia con la misma plantilla (nombre, tipo, coordenadas vía
  geocoding, descripción, intereses) y la guarde en la tabla marcada como
  `fuente="ia_generada"`.
- **Navegación en vivo** (`app/static/js/map.js`): comentario dejado para
  cuando se quiera agregar algo tipo Waze/Google Maps (seguimiento en
  tiempo real). No es prioridad para el proyecto escolar, pero quedó
  anotado.

## Lo siguiente que se habló de hacer (según la última conversación)

- **Conectar la API de Claude**: es el paso que sigue según lo platicado.
  El uso más natural es justo el fallback de destinos con IA de arriba —
  cuando no hay resultados en la base, llamarla para generar la
  sugerencia. Dónde conseguir la key: **console.anthropic.com** → API
  Keys (cuenta de Anthropic, no la de Supabase). Se instala con
  `pip install anthropic` y se guarda como variable de entorno
  `ANTHROPIC_API_KEY` (mismo patrón que ya usan con
  `instance/config.py` para la de Supabase, que tampoco se sube a git).
  Modelo recomendado: `claude-opus-5`.
  **Este plan todavía no se ha ejecutado** — falta:
  1. Decidir/confirmar el alcance exacto (solo fallback de destinos, o
     también un cuadro de ayuda conversacional — la idea del "AI de
     ayuda" mencionada abajo).
  2. Agregar `anthropic` a `requirements.txt`.
  3. Escribir la función que llama a Claude y guarda el resultado en
     `destinos` con `fuente="ia_generada"`.
  4. Probar en vivo con un destino real que no esté en la base.

## Ideas guardadas para después (todavía sin planear a detalle)

- **"IA de ayuda"**: un cuadro/asistente conversacional dentro de la app
  para ayudar al usuario a planear su viaje. Angel dijo explícitamente
  "solo guárdalo como idea" — no se ha diseñado ni empezado.

## Cosas que valdría la pena revisar pronto (no urgentes, no pedidas aún)

- Roberto ya tiene el link de GitHub y probablemente empiece a hacer
  cambios — vale la pena acordar quién actualiza esta carpeta y con qué
  frecuencia hacen `git pull` antes de tocar el mismo archivo, para no
  pisarse cambios.
- El grafo de conocimiento (`graphify-out/`) reportó 14 nodos "aislados"
  (poco conectados) y algunas relaciones marcadas como INFERRED que
  valdría la pena confirmar si son correctas — no es bloqueante, solo
  queda anotado por si se quiere revisar la arquitectura más a fondo.
