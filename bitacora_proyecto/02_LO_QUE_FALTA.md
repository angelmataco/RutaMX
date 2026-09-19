# Lo que falta — RutaMX

Última actualización: 2026-09-19

Este archivo es solo lo que **todavía no está hecho**. En cuanto algo se
termina, se mueve a `01_LO_QUE_YA_ESTA_HECHO.md` (con su explicación) y
se borra de aquí — nunca queda un "✅ Ya implementado" aquí adentro. Ver
la regla completa en `AGENTS.md`.

## Pendiente para la próxima sesión (pedido explícito de Angel)

- **Origen/Destino: quitar el valor precargado, dejar solo placeholder**
  (`app/templates/partials/hero.html`). Hoy los campos `hero-origen` /
  `hero-destino` tienen `value="Ciudad de México"` / `value="Oaxaca de
  Juárez"` — texto real que hay que borrar a mano. Angel quiere que sea
  `placeholder` (ejemplo en gris que desaparece solo al escribir/dar
  clic), no un valor que haya que seleccionar y sobreescribir. Al
  quitarle el `value`, revisar: (a) `form.js` → `leerValores()` leerá
  `origen`/`destino` vacíos si el usuario no escribe nada — el atributo
  `required` que ya tienen ambos inputs debería bastar para impedir el
  submit vacío, pero confirmarlo en vivo; (b) el campo "Nombre de la
  ruta" trae de default "Escapada CDMX a Oaxaca", que hace referencia a
  esas mismas dos ciudades — decidir si también cambia o se deja como
  ejemplo aparte.

## Pendiente marcado en el código (TODOs reales)

- **Navegación en vivo** (`app/static/js/map.js`): comentario dejado para
  cuando se quiera agregar algo tipo Waze/Google Maps (seguimiento en
  tiempo real). No es prioridad para el proyecto escolar, pero quedó
  anotado.

## Pendientes sueltos de funcionalidad ya implementada

Estos NO son features sin hacer — son detalles/riesgos que quedaron
abiertos dentro de features que ya están terminadas y documentadas en
`01_LO_QUE_YA_ESTA_HECHO.md`. Se listan aquí porque siguen siendo trabajo
real por hacer, no porque la feature esté incompleta.

**De cuentas de usuario:**
- No hay "recuperar PIN" (sin correo no hay a dónde mandarlo) — si
  alguien lo olvida, se resetea a mano desde la base. Aceptado a
  propósito para el alcance escolar.
- Nombre + apellido debe ser único por cuenta — si dos personas reales
  se llaman exactamente igual, la segunda no puede registrarse con ese
  nombre. No es problema real para el grupo de prueba (Angel, Roberto).

**De destinos nuevos con IA:**
- Nadie lo ha probado todavía con una API key real conectada (se probó
  sin ninguna key configurada, y confirmó que cae bien al comportamiento
  de antes sin romper nada — falta la prueba en vivo con IA de verdad
  generando un destino nuevo).
- Los nombres exactos de modelo para OpenAI (`gpt-5.1`) y Gemini
  (`gemini-3-pro`) en `llm_provider.py` son defaults razonables pero hay
  que confirmarlos contra la cuenta real de quien conecte esa key — los
  proveedores cambian nombres de modelo seguido.
- Las llamadas a la API de OpenAI y Gemini en `llm_provider.py` se
  escribieron con el patrón típico de cada SDK pero sin poder probarlas
  en vivo (solo se tiene documentación verificada de la API de Claude) —
  si alguien conecta esas keys y falla la llamada, revisar la forma
  exacta contra la documentación vigente de cada proveedor.

**De "Planear con IA":**
- **El chat en sí no se ha podido probar de punta a punta con una IA
  real todavía.** Se probó con una key presente en el entorno de
  desarrollo, pero resultó inválida para uso directo del SDK (error 401
  "API key is invalid") — el manejo de error funcionó perfecto (mensaje
  claro al usuario, no rompe nada), pero falta la prueba real con una key
  de Anthropic/OpenAI/Gemini genuina para confirmar que el chat completo
  (preguntas, quick-replies, las dos opciones finales) funciona de
  extremo a extremo.
- El campo "personas" se captura en la conversación pero no se guarda en
  ningún lado (ni en `RutaGuardada` ni en `Destino`) — hoy solo influye
  en el razonamiento de la IA sobre qué proponer, no se persiste.
- Los tests de `planificador_ia_service.py` y de la asignación de
  objetivos están con el proveedor mockeado (correcto para no gastar
  tokens en cada `pytest`), pero por lo mismo no prueban el prompt real
  contra un modelo de verdad — si el modelo devuelve algo fuera de lo
  esperado en producción, revisar primero el prompt en `llm_provider.py`.

## Ideas guardadas para después (todavía sin planear a detalle)

_(vacío por ahora)_

## Cosas que valdría la pena revisar pronto (no urgentes, no pedidas aún)

- Roberto ya tiene el link de GitHub y probablemente empiece a hacer
  cambios — vale la pena acordar quién actualiza esta carpeta y con qué
  frecuencia hacen `git pull` antes de tocar el mismo archivo, para no
  pisarse cambios.
- El grafo de conocimiento (`graphify-out/`) reportó 14 nodos "aislados"
  (poco conectados) y algunas relaciones marcadas como INFERRED que
  valdría la pena confirmar si son correctas — no es bloqueante, solo
  queda anotado por si se quiere revisar la arquitectura más a fondo.
