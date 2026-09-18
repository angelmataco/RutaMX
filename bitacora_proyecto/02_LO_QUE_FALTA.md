# Lo que falta — RutaMX

Última actualización: 2026-09-18

## Pendiente marcado en el código (TODOs reales)

- **Rutas guardadas sin usuario** (`app/models.py`): `RutaGuardada` no
  tiene columna `usuario_id`. Falta implementar login para que cada quien
  vea solo sus propias rutas. Hoy todas las rutas guardadas son públicas
  entre quien use la app.
- **Navegación en vivo** (`app/static/js/map.js`): comentario dejado para
  cuando se quiera agregar algo tipo Waze/Google Maps (seguimiento en
  tiempo real). No es prioridad para el proyecto escolar, pero quedó
  anotado.

## ✅ Ya implementado: destinos nuevos con IA (multi-proveedor)

Lo que estaba pendiente en la sección anterior de este archivo ya se hizo.
Cuando alguien escribe un origen/destino que no está en los 369 destinos
curados (ej. "Manuel Doblado", con o sin errores de ortografía),
`app/services/ia_destinos_service.py` le pide al proveedor de IA
configurado (`app/services/llm_provider.py`) que identifique el lugar
real, busque en internet los datos, y lo inserte en `destinos` con
`fuente="ia_generada"` — desde ahí funciona igual que los curados en
autocompletado, sugerencias y cálculo de ruta. Detalle completo del
porqué de cada decisión en `03_DECISIONES_Y_NOTAS.md`.

**Importante:** es multi-proveedor a propósito — Angel puede usar su key
de Claude, Roberto la que tenga (Gemini, ChatGPT, la que sea), y funciona
igual sin tocar código. Cada quien pone SU key en su `.env` local (nunca
se sube a git) — ver la sección "Conectar tu propia IA" en `README.md`.

**Lo que sigue pendiente de esto:**
- Nadie lo ha probado todavía con una API key real conectada (se probó
  sin ninguna key configurada, y confirmó que cae bien al comportamiento
  de antes sin romper nada — falta la prueba en vivo con IA de verdad
  generando un destino nuevo).
- Los nombres exactos de modelo para OpenAI (`gpt-5.1`) y Gemini
  (`gemini-3-pro`) en `llm_provider.py` son defaults razonables pero hay
  que confirmarlos contra la cuenta real de quien conecte esa key —los
  proveedores cambian nombres de modelo seguido.
- Las llamadas a la API de OpenAI y Gemini en `llm_provider.py` se
  escribieron con el patrón típico de cada SDK pero sin poder probarlas
  en vivo (solo se tiene documentación verificada de la API de Claude) —
  si alguien conecta esas keys y falla la llamada, revisar la forma
  exacta contra la documentación vigente de cada proveedor.

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
