# Lo que falta — RutaMX

Última actualización: 2026-09-19

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

## ✅ Ya implementado: cuentas de usuario (nombre + apellido + PIN)

Cada quien inicia sesión con nombre + apellido + PIN de 4 dígitos (sin
correo — decisión explícita para este proyecto escolar, ver
`03_DECISIONES_Y_NOTAS.md`). `app/services/auth_service.py` maneja
registro/login; la sesión usa la cookie firmada que ya trae Flask (nada
nuevo que instalar). Solo **guardar** una ruta requiere sesión — calcular
rutas y pedir sugerencias sigue abierto sin cuenta.

`RutaGuardada` ahora tiene `usuario_id` (migración en
`scripts/agregar_usuario_id.py`, correrla una vez después de
`db.create_all()`) y `/api/rutas` (GET y POST) filtra/exige sesión.

**Lo que sigue pendiente de esto:**
- No hay "recuperar PIN" (sin correo no hay a dónde mandarlo) — si
  alguien lo olvida, se resetea a mano desde la base. Aceptado a
  propósito para el alcance escolar.
- Nombre + apellido debe ser único por cuenta — si dos personas reales
  se llaman exactamente igual, la segunda no puede registrarse con ese
  nombre. No es problema real para el grupo de prueba (Angel, Roberto).
- El modal de login/registro usa el elemento `<dialog>` nativo de HTML —
  funciona en todos los navegadores modernos, pero si alguien prueba en
  un navegador muy viejo podría no abrir.

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

## ✅ Ya implementado: "Planear con IA" (chat + reparto inteligente de paradas)

Lo que antes estaba en "ideas guardadas" como "IA de ayuda" ya se
implementó, con bastante más diseño del que se anotó originalmente.
Botón "🤖 Planear con IA" en el formulario principal, abre un panel de
chat grande y centrado (efecto vidrio esmerilado con `<dialog>` nativo).
El usuario describe su viaje en lenguaje natural, la IA hace como máximo
5 preguntas de seguimiento (con hasta 3 respuestas rápidas sugeridas +
"Otro" para texto libre) y entrega **dos itinerarios distintos** para
elegir.

Piezas nuevas:
- `app/services/llm_provider.py` — se generalizó (dispatcher compartido
  `_llamar_proveedor`) y ganó `extraer_slots_viaje()` (interpreta la
  conversación) y `generar_opciones_objetivos()` (propone 2 conjuntos de
  objetivos: propósito + hora, sin elegir lugar).
- `app/services/ai_service.py` — nuevas funciones deterministas:
  `asignar_paradas_a_objetivos()` (reparte objetivos entre lugares reales
  sin repetir), `filtrar_objetivos_por_hora_del_dia()` (no propone
  "dormir" de día ni "visita corta" ya entrada la noche),
  `generar_objetivos_automaticos()` (la versión **sin IA**, con fórmula
  fija en vez de conversación).
- `app/services/planificador_ia_service.py` (nuevo) — orquesta cada turno
  del chat.
- Endpoints `GET /api/ia/disponible` y `POST /api/ia/planear`.
- **La IA nunca elige el lugar exacto** — solo decide propósito + hora;
  la asignación a un destino real siempre es el mismo algoritmo
  determinista, verificado, sin inventar nada.

**La pieza más importante para el proyecto sin usar el botón de IA:**
`sugerir_paradas()` ahora, si le das `horas_max` **y** `hora_salida`
(campo nuevo, opcional, en el formulario), reparte las sugerencias por
propósito y hora usando exactamente el mismo motor
(`asignar_paradas_a_objetivos` + `filtrar_objetivos_por_hora_del_dia`)
que el chat, solo que los objetivos los genera una fórmula en vez de una
conversación. **Probado en vivo**: CDMX→Oaxaca con horas_max=4 y
hora_salida=08:00 devolvió Tehuacán marcado `proposito: "comida"` a la
hora correcta — funciona sin tocar la IA.

**Lo que sigue pendiente de esto:**
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

## ✅ Ya implementado: campos sin teclado (hora tipo rueda 24h + burbujas)

Presupuesto, horas máximas de manejo, y hora de salida ya no obligan a
escribir con teclado (pedido explícito de Angel). El selector de hora es
de 2 columnas en formato 24h (sin AM/PM); presupuesto/horas usan
"burbujas" (mismo estilo que los chips de intereses) en vez de una lista
plana. Ver `01_LO_QUE_YA_ESTA_HECHO.md` y `03_DECISIONES_Y_NOTAS.md` para
el detalle, incluyendo dos bugs reales de CSS que se encontraron y
corrigieron en el camino (el recuadro tapando los números por un problema
de `z-index`, y la fila de burbujas desbordando la página por un
`min-width` de flexbox). Sin pendientes conocidos.

## Cosas que valdría la pena revisar pronto (no urgentes, no pedidas aún)

- Roberto ya tiene el link de GitHub y probablemente empiece a hacer
  cambios — vale la pena acordar quién actualiza esta carpeta y con qué
  frecuencia hacen `git pull` antes de tocar el mismo archivo, para no
  pisarse cambios.
- El grafo de conocimiento (`graphify-out/`) reportó 14 nodos "aislados"
  (poco conectados) y algunas relaciones marcadas como INFERRED que
  valdría la pena confirmar si son correctas — no es bloqueante, solo
  queda anotado por si se quiere revisar la arquitectura más a fondo.
