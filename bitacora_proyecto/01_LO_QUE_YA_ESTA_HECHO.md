# Lo que ya está hecho — RutaMX

Última actualización: 2026-09-19

RutaMX es una app web para planear road trips por México. Flujo completo
funcionando de punta a punta: formulario → cálculo de ruta → mapa →
sugerencias de paradas → armar itinerario → guardar → descargar PDF.

## Mapa y ruta

- Mapa con Leaflet + OpenStreetMap.
- Ruta real por carretera (no línea recta) con Leaflet Routing Machine +
  OSRM (servidor demo gratuito, sin API key).
- Distancia, tiempo y gasto máximo recomendado calculados con la ruta real de OSRM;
  si OSRM no responde, cae a una estimación en línea recta para que no se
  rompa el flujo.
- **Geocoding real arreglado**: antes el cálculo de ruta solo reconocía 18
  ciudades hardcodeadas y cualquier otra (ej. León, Los Cabos) caía en la
  misma coordenada de respaldo, dando un mapa en blanco. Ahora resuelve en
  orden: tabla `destinos` (369 lugares) → Nominatim (geocoding real) →
  catálogo de 18 ciudades → respaldo.
- Mapa agrandado (llena toda su tarjeta, sin espacio en blanco).

## Cuentas de usuario (nombre + apellido + PIN, sin correo)

- Registro e inicio de sesión con nombre + apellido + PIN de 4 dígitos —
  sin correo, decisión explícita para este proyecto escolar (ver
  `03_DECISIONES_Y_NOTAS.md`).
- `app/services/auth_service.py` hashea el PIN (nunca se guarda en texto
  plano) y detecta nombre+apellido duplicados sin importar acentos o
  mayúsculas.
- Sesión con la cookie firmada que ya trae Flask — no se instaló ninguna
  librería nueva (nada de Flask-Login).
- Endpoints: `POST /api/auth/registro`, `POST /api/auth/login`,
  `POST /api/auth/logout`, `GET /api/auth/yo`.
- Solo **guardar** una ruta (`POST /api/rutas`) requiere sesión iniciada;
  calcular rutas y pedir sugerencias sigue abierto sin cuenta.
  `GET /api/rutas` ahora filtra por dueño — cada quien ve solo sus
  propias rutas guardadas.
- Modal de login/registro en el navbar (elemento `<dialog>` nativo de
  HTML, sin librerías extra) — si intentas guardar una ruta sin sesión,
  se abre solo en vez de fallar con un error confuso.
- Probado en vivo: registro → guardar ruta → cerrar sesión (ya no
  aparece en el selector) → volver a iniciar sesión (reaparece).

## Destinos nuevos generados con IA (multi-proveedor)

- Cuando alguien escribe un origen/destino que no está en los 369
  destinos curados (ej. "Manuel Doblado", con o sin errores de
  ortografía), `app/services/ia_destinos_service.py` le pide a la IA
  configurada que identifique el lugar real, busque en internet los datos
  necesarios (estado, tipo, descripción, intereses, población) y lo
  inserte en `destinos` con `fuente="ia_generada"`.
- Las coordenadas nunca se toman de lo que "sepa" la IA — siempre se
  verifican con `geocodificar()` (Nominatim), igual que los 369 curados.
- Pasa **una sola vez por lugar**: la siguiente vez que alguien lo
  escriba, ya está en la tabla y no se vuelve a llamar a la IA.
- Desde que se inserta, funciona exactamente igual que los curados:
  aparece en el autocompletado, en sugerencias de paradas para rutas
  futuras que pasen cerca, y en el cálculo de rutas.
- **Multi-proveedor de verdad**: `app/services/llm_provider.py` detecta
  solo con qué variable de entorno esté configurada
  (`ANTHROPIC_API_KEY` → `OPENAI_API_KEY` → `GEMINI_API_KEY`) cuál usar —
  Angel puede tener la de Claude, Roberto la que tenga, sin tocar código.
  Sin ninguna key configurada, la app sigue funcionando igual que antes
  (cae a Nominatim directo, solo que ese lugar no se guarda para
  siempre).

## Campos del formulario sin teclado (selector de hora tipo rueda + burbujas)

- **Hora de salida**: ya no es el `<input type="time">` nativo (en
  escritorio obliga a escribir con teclado) — ahora es un botón que abre
  un selector tipo rueda (como el de iOS) con **dos** columnas, hora
  (00-23) y minuto (00-59), en **formato 24 horas** (sin AM/PM — pedido
  explícito), cada una con scroll-snap. Construido con HTML/CSS nativos
  (`<dialog>` + `scroll-snap-type`), sin ninguna librería. Guarda el
  valor en el mismo formato `HH:MM` de siempre, así que no hizo falta
  tocar `form.js` ni `main.js`.
- **Presupuesto** (hoy ya no existe, ver "Gasto máximo recomendado") y **Horas máximas de manejo**: en vez de una lista
  plana de `<datalist>` (se veía sosa), ahora son una fila de "burbujas"
  deslizable — mismo estilo que los chips de "¿Qué buscas?" — con montos
  predefinidos (presupuesto: $1,000, $3,000, $5,000, $7,000, $9,000; horas:
  1 a 16) más una burbuja "Otro" que revela un campo normal para escribir
  un valor exacto distinto.
- `app/static/js/time_picker.js` y `app/static/js/bubble_picker.js`
  (nuevos) manejan cada uno.

## "Planear con IA" — chat que arma el itinerario completo

- Botón "🤖 Planear con IA" en el formulario principal — abre un panel de
  chat grande y centrado, efecto vidrio esmerilado (`<dialog>` nativo +
  `backdrop-filter: blur`), sin librerías nuevas.
- El usuario describe su viaje en lenguaje natural; la IA hace máximo 5
  preguntas de seguimiento, cada una con hasta 3 respuestas rápidas
  sugeridas + botón "Otro" para texto libre.
- Al final propone **dos itinerarios genuinamente distintos** (cantidad,
  propósito y horario de cada parada los decide la IA según ese viaje —
  no hay plantilla fija de "2 paradas vs 1 combinada").
- **La IA nunca elige el lugar exacto** — solo decide propósito de parada
  (comida/descanso/cultura/etc.) + a qué hora del viaje conviene. La
  asignación a un destino real de la tabla (`ai_service.asignar_paradas_a_objetivos`)
  siempre es un algoritmo determinista que nunca repite el mismo lugar en
  dos objetivos.
- **Hora de salida** (campo nuevo, opcional): con eso se calcula la hora
  real del reloj de cada parada — no propone "dormir" en pleno día ni
  solo visitas cortas ya entrada la noche
  (`ai_service.filtrar_objetivos_por_hora_del_dia`).
- **Funciona también sin usar el botón de IA**: si en el formulario
  manual pones horas máximas de manejo + hora de salida,
  `sugerir_paradas()` usa el mismo motor de reparto por propósito/hora
  (con una fórmula fija en vez de una conversación) — probado en vivo,
  CDMX→Oaxaca con horas_max=4 + hora_salida=08:00 devolvió una parada de
  comida a la hora correcta.
- Endpoints nuevos: `GET /api/ia/disponible` (oculta el botón si nadie
  tiene una key conectada), `POST /api/ia/planear`.
- `llm_provider.py` se generalizó a un dispatcher compartido — las
  mismas 3 funciones por proveedor (Claude/OpenAI/Gemini) ahora sirven
  tanto para generar destinos nuevos como para el chat, sin duplicar
  código de detección de proveedor.

## Base de datos de destinos (Supabase / Postgres)

- Catálogo de los 32 estados con 369 destinos verificados: mínimo 8
  ciudades/pueblos mágicos y mínimo 3 sitios turísticos por estado.
- Cada destino tiene nombre, estado, tipo, coordenadas verificadas contra
  Nominatim, descripción e intereses asociados.
- Rutas guardadas también viven en Supabase (tabla `rutas_guardadas`), ya
  no se pierden al reiniciar el servidor.

## Sugerencias de paradas (IA / lógica de ruta)

- Filtra destinos por cercanía real a la carretera (usando la geometría de
  OSRM), no en línea recta.
- Si el usuario indica horas máximas de manejo seguido, prioriza destinos
  cerca de ese punto del viaje como sugerencia de descanso.
- Se descartan destinos a menos de 1 hora real de manejo del origen (están
  prácticamente en la misma ciudad de la que sales); ya NO se descartan
  los que están cerca del destino (ahí sí tiene sentido sugerir cosas).
- "Ver más recomendaciones" trae tandas de 16 en vez de 8.
- Sin filtros de interés marcados da recomendaciones generales; si luego
  seleccionas uno o más filtros y vuelves a dar "Planea mi ruta", se
  filtran de acuerdo a eso.
- Si cambias los filtros y vuelves a calcular la ruta (mismo origen y
  destino), las paradas que ya habías agregado al itinerario **ya no se
  borran** — antes sí se perdían.

## Autocompletado de Origen/Destino

- Dropdown propio en JS (no el `<datalist>` nativo del navegador) para los
  campos Origen y Destino, alimentado por los 369 destinos de la base.
- Ignora acentos y mayúsculas (escribir "leon" sí encuentra "León").
- Se puede aceptar la sugerencia resaltada con **Tab** (y de paso sigue
  moviendo el foco al siguiente campo) o con **Enter**.
- Flechas arriba/abajo para navegar entre sugerencias, Escape para cerrar.

## Itinerario y guardado

- Armar itinerario agregando/quitando/reordenando paradas sugeridas.
- La parada de ORIGEN tiene un color distinto (dorado claro) al de
  DESTINO (terracota) y a las paradas normales (verde), para diferenciarlas
  a simple vista.
- "Guarda tu plan" (guardar ruta + selector de rutas guardadas) vive junto
  a "Resumen de aventura" en la sección de itinerario — antes estaba en la
  sección del mapa, donde no encajaba bien.
- Descarga de itinerario en PDF con el branding de la app (ReportLab,
  backend).

## Formulario sin valores precargados

- Origen, Destino y Nombre de la ruta no traen texto real
  precargado: los tres primeros usan `placeholder` (ejemplo en gris que
  desaparece al escribir) y el presupuesto arranca sin burbuja elegida
  (antes traía 6500). Origen/Destino siguen con `required`; nombre vacío
  cae a "origen a destino" y presupuesto vacío se trata como 0.
  Archivo: `app/templates/partials/hero.html`.

## Navegación con Google Maps (enlace + QR)

- Botón "📍 Abrir en Google Maps" en la tarjeta de resumen del itinerario,
  y sección "Empieza tu viaje" en el PDF con un QR y un enlace tocable.
  Escanear el QR (o tocar el botón en el celular) abre la ruta completa en
  la app de Google Maps lista para "Iniciar". No usa la API de Google: es
  solo una URL (`google.com/maps/dir/?api=1&origin=…&waypoints=…`), sin
  key ni costo. El mapa de la web sigue siendo Leaflet/OSRM.
- Usa coordenadas cuando las hay (más exacto) y el nombre si no.
- Google admite máx. 9 paradas por enlace: si hay más, se divide en tramos
  (cada uno arranca donde terminó el anterior) y el PDF pone un QR por
  tramo. Google puede recalcular el camino entre paradas.
- Archivos: `app/services/navegacion_service.py`, endpoint
  `POST /api/itinerario/enlaces`, `pdf_service.py`, `main.js`. El QR usa
  reportlab (sin dependencias nuevas). 4 tests nuevos (53 en total).

## Ajustes de diseño del resumen del viaje

- La tarjeta "Resumen del viaje" ya llena su recuadro (las 4 cifras se
  estiran a la altura del mapa; antes quedaba todo arriba y vacío abajo).
- Las duraciones se muestran como "9 h 30 min" / "45 min" en vez de
  "9.5 h": resumen, tarjetas de paradas, chat de IA y PDF. Función
  compartida `formatoDuracion()` en `static/js/formato.js` (y su gemela
  `formato_duracion()` en `pdf_service.py`, deben dar lo mismo).

- **"🗂️ Mis rutas guardadas"**: botón junto a "Planear con IA" en la tarjeta
  del inicio. Abre una ventana flotante con las rutas del usuario como
  burbujas (nombre, origen → destino, km · duración · paradas). Sin sesión
  muestra "Aún no has iniciado sesión" con botones Iniciar sesión / Crear
  cuenta, y al entrar se abre la ventana de rutas sola. Con sesión y sin
  rutas, un aviso. Tocar una burbuja restaura la ruta (formulario, mapa,
  resumen, itinerario y sugerencias). Antes el selector de "rutas
  guardadas" no cargaba nada al elegir una; ahora sí funciona. "Guardar
  ruta actual" se queda abajo en "Guarda tu plan". Código en `main.js`.
- Las 4 cifras del resumen del viaje van centradas en su recuadro.

## Ventanas flotantes: la página de atrás se congela

- Mientras haya cualquier `<dialog>` abierto (Planear con IA, Mis rutas
  guardadas, login/registro, selector de hora) la página principal no se
  mueve al hacer scroll; solo se desplaza la ventana. Es una regla general
  en `styles.css` (`html:has(dialog[open]) { overflow: hidden }`), así que
  las ventanas futuras la heredan solas. Ver regla en `AGENTS.md`.

## Chat "Planear con IA": efecto de escritura

- El saludo inicial se escribe letra por letra la primera vez que se abre
  el chat (las siguientes veces la conversación se conserva sin
  re-animar). Cada respuesta de la IA también se escribe poco a poco
  (~20 ms por letra, máx. ~2.5 s por mensaje) con cursor parpadeante, y
  mientras el servidor responde salen tres puntitos "pensando". Las
  respuestas rápidas y las opciones aparecen al terminar de escribir. Se
  respeta `prefers-reduced-motion` (sin animación). Código en
  `planificador_ia.js`.

## Gasto máximo recomendado (reemplaza al campo "Presupuesto")

- Se quitó el campo de presupuesto: ahora la app calcula cuánto conviene
  gastar como máximo, por el viaje completo. Código en
  `app/services/gasto_service.py` (constantes arriba, fáciles de afinar).
- **Siempre incluye:** gasolina (km ÷ rendimiento × precio del litro;
  default 13 km/l y $25.5/l), casetas (ver abajo) e imprevistos ($500 en
  viajes de ≤4 h, subiendo linealmente hasta $2,000 a las 20 h o más).
- **Solo si aplica:** comidas ($150 × personas) y hospedaje ($600 por
  noche). De cada parada del itinerario el sistema **deduce solo** si es
  para comer o dormir (`clasificar_parada`): comida si el lugar es de
  comida, nació como "comida" o se llega en horario de desayuno (7:30–10),
  comida (13–16) o cena (19–21:30); hospedaje si se llega a las 20:00 o
  después. Para no contar de más, solo cuenta una comida por cada 3 h de
  camino y una noche por cada 8 h. Cada parada del itinerario muestra la
  etiqueta "🍽️ Comer · 13:10" / "🛏️ Dormir · 21:00". Las paradas guardan su
  `horas_estimadas` (hora de camino) para poder calcular la hora de
  llegada. Las noches se **deducen solas** simulando el viaje día por día
  con la hora de salida (default 08:00): no se maneja pasadas las 21:00 y
  se retoma a las 07:00. Ej.: 8 h saliendo a las 08:00 = 0 noches; 10 h
  saliendo a las 17:00 = 1 noche; León → Cabo San Lucas = 3 noches.
- **Casetas:** si hay una IA conectada se le pide el estimado del
  trayecto (con búsqueda web, resultado en caché, validado: se descarta
  si es negativo o > $5/km); si no, o si falla, promedio de $1.1/km.
  Cada caseta cuesta distinto, así que es un promedio, y el resumen lo
  dice ("Casetas (promedio)" / "(estimado IA)").
- **Formulario:** selector de "¿Cuántas personas van?" (burbujas 1–8,
  vacío = 1). El botón pequeño "⚙️ Ajustes de gasto" vive en el
  **Resumen del viaje**, debajo del desglose, y abre una ventana con
  "Aplicar cambios" (recalcula el gasto) y ✕ (deshace): coche
  (Compacto 15 / Mediano 13 / SUV 11 km/l), gasolina (Magna $23.8 /
  Premium $29), y paradas para comer / noches de hospedaje manuales (vacío
  = automático). Si nadie toca nada, todo funciona con los valores típicos.
- El resumen muestra el total y un desglose (gasolina, casetas, comidas,
  hospedaje, imprevistos) con una línea de "Incluye…". El desglose y los
  ajustes se guardan dentro de `resumen` de cada ruta guardada y se
  restauran al abrirla; el PDF trae el mismo desglose. El gasto se
  recalcula en el servidor (`POST /api/gasto`) cada vez que cambian la
  distancia real o las paradas. La columna `presupuesto` de la base ya no
  se usa (queda sin borrar para no romper rutas viejas).
- 15 tests nuevos (`tests/test_gasto_service.py` y `/api/gasto`); las
  pruebas apagan la estimación de casetas por IA (`tests/conftest.py`)
  para no gastar tokens.

## Autollenado y formulario del inicio (rediseño)

- **Autollenado de Origen/Destino:** primero salen los nombres que
  EMPIEZAN con lo escrito (se filtra letra por letra, con las ciudades
  importantes primero); y cuando lo escrito ya es una palabra completa se
  agregan también los nombres que la contienen. Ej.: "l" → León, Los
  Mochis, La Paz…; "leo" → León; "leon" → León, Centro Histórico de León,
  Zona Piel y Calzado de León; "mexico" → Ciudad de México, Centro
  Histórico de la Ciudad de México. El orden lo da `/api/destinos/nombres`
  (ciudad principal → pueblo mágico → sitio turístico, y por población);
  un nombre exacto sube al primer lugar. Sin acentos ni mayúsculas.
  Código: `initAutocompletado` y `contienePalabraCompleta` en `main.js`.
- **Tarjeta ancha** (máx. 980 px, antes 620). Origen | Destino y Nombre de
  la ruta | Hora de salida van en pares; "¿Qué buscas?" y "¿Cuántas
  personas van?" ocupan cada uno **su propia fila a todo el ancho** (así no se ven pegadas unas con otras). Abajo, centrados:
  "Planea mi ruta", los dos botones y el botón pequeño de ajustes. Con
  menos de 900 px pasa a una sola columna. La Hora de salida subió junto
  al nombre para que los pares queden simétricos.
- **Una sola forma para todas las opciones:** las casillas de personas y los chips de "¿Qué buscas?" son rectángulos redondeados de la
  misma altura (antes unas eran círculos y otras rectángulos). Los 6 chips
  reparten todo el ancho. En teléfono: chips en 3 columnas y personas en
  2 filas de 4. Estilos al final de `styles.css`.
- **Personas:** 8 casillas que llenan todo el ancho (sin "Otro"; máximo 8). `bubble_picker.js` acepta selectores sin botón "Otro".
- **Ajustes de gasto:** dejó de ser un desplegable dentro del formulario.
  Ahora es un botón pequeño y discreto ("⚙️ Ajustes de gasto") centrado
  bajo los botones principales, que abre una ventana flotante (`<dialog>`)
  con coche, gasolina, comidas y noches. Muestra "· N" cuando hay ajustes
  activos.

## Sugerencias por lapsos de tiempo (reemplaza "Horas máximas de manejo")

- Se quitó la pregunta "Horas máximas de manejo seguido": la app lo decide
  sola. `ai_service.lapsos_de_la_ruta(tiempo_h)` divide el viaje en
  **lapsos de ~3 h**, desde **30 min después de salir hasta 20 min antes
  de llegar** (6 h → 2 lapsos, 12 h → 4, 50 h → 16). Solo se recomiendan
  lugares dentro de esa ventana (antes: a más de 1 h del origen y sin
  límite cerca del destino).
- "Descubre en el camino" tiene una fila de botones: **Todo el camino** y
  **Tramo N · desde – hasta** (ej. "Tramo 2 · 2 h 59 min – 5 h 28 min").
  En "Todo el camino" sale primero la mejor parada de cada lapso (comida en
  el primero, descanso en los demás, ajustado a la hora del día si hay hora
  de salida) y luego se rellena turnando entre lapsos; en un tramo solo
  salen lugares de ese tramo. Las tarjetas dicen "🍽️ Buen lugar para
  comer" o "😴 Buen punto para parar a descansar" cuando aplica.
- Backend: `_sugerir_por_lapsos`, `generar_objetivos_por_lapsos`;
  `/api/sugerencias` acepta `lapso` y devuelve `lapsos`. El chat de "Planear
  con IA" no cambia (sigue conversando sus propias horas). Si la ruta no
  tiene geometría (OSRM caído) cae al comportamiento de antes.
- 5 tests nuevos (75 en total).

## Todo fluye: el gasto se recalcula al cambiar cualquier variable

- El gasto se recalcula solo al: agregar/quitar/mover paradas, cambiar
  personas, cambiar la hora de salida, o aplicar "Ajustes de gasto"
  (`recalcularGasto` en `main.js`; evento `ajustes-gasto-aplicados`). Los
  ajustes vigentes se guardan con la ruta. Cambiar la hora de salida
  también refresca las sugerencias.
- Arreglo: antes una parada solo contaba como comida si el lugar tenía la
  etiqueta "comida" en la base (los pueblos mágicos no), y no se miraba la
  hora de llegada.

## Tramos: elegir cuántos, hora del reloj y recomendaciones según la hora

- **Cuántos tramos:** en "Descubre en el camino" hay un selector
  "Dividir el viaje en: Automático · 2 · 3 · 4 · 5 · 6". Automático = ~3 h
  por tramo; si se elige un número, la ventana (30 min después de salir a
  20 min antes de llegar) se divide en esa cantidad de partes iguales (nunca
  tramos de menos de 30 min). Parámetro `tramos` de `/api/sugerencias`.
- **Hora del reloj:** cada tramo se muestra con su horario ("Tramo 2 ·
  19:09 – 20:48"), con "Día N" si el viaje dura varios días y 🌙 si el
  tramo cruza la noche. Usa la hora de salida; sin ella supone 08:00 y lo
  avisa. Las tarjetas dicen "llegas 19:34". Cambiar la hora de salida
  refresca todo.
- **Qué se recomienda según la hora** (`_proposito_del_lapso` en
  `ai_service.py`): tramo que termina de noche (≥20:00) o cruza la noche →
  🛏️ lugar para pasar la noche (ciudades grandes o con interés "descanso");
  tramo que cae en horario de comer (13–16 o 19–21:30, al menos 1 h de
  traslape) → 🍽️ lugar de comida; el resto → turismo según los intereses.
  El botón del tramo lleva el icono 🍽️/🛏️. En un tramo se muestran primero
  los lugares que encajan con su propósito. Consistente con el gasto: ahí
  las paradas también se clasifican solas por hora de llegada.
- 5 tests nuevos (83 → 87 aprox.; ver `pytest -q`).

## Elegir para qué es cada tramo (y reglas de qué se recomienda)

- Al tocar un tramo aparece la fila "¿Qué buscas en el tramo N?":
  **Automático · 🍽️ Comer · 🏞️ Turismo · 🛏️ Dormir**. Todo arranca en
  Automático (la app decide por la hora del reloj); elegir algo es un solo
  toque. El botón del tramo muestra el icono y cambia de color si se
  personalizó. Cambiar el número de tramos o empezar otro viaje reinicia lo
  elegido. Parámetro `propositos=0:comida,2:descanso` en `/api/sugerencias`.
- **Tramo personalizado = estricto:** si se pide comer, SOLO lugares donde
  se puede comer (los que tienen el interés "comida"); dormir, solo ciudades
  o lugares de descanso; turismo, los intereses de "¿Qué buscas?" (o
  cualquiera si no marcó). Si no hay ninguno, lo dice ("No encontramos
  lugares para comer en este tramo…").
- **Tramo automático:** de todo, con prioridad al propósito de la hora
  (comida en horario de comer). **Dormir solo aplica si el tramo termina
  después de las 20:00 o cruza la noche** (`permite_dormir`); si no, la
  opción "Dormir" ni se ofrece ni se propone.
- Código: `lapsos_de_la_ruta`, `_proposito_automatico`,
  `_encaja_con_lo_pedido`, `_sugerir_por_lapsos` en `ai_service.py`.

## "Planear con IA" al día con todas las reglas nuevas

- **Preguntas:** ya no pregunta por horas máximas de manejo ni presupuesto
  (la app lo calcula sola). Prioriza preguntar hora de salida (decide cuándo
  comer y si hay noche), luego personas e intereses. El saludo lo menciona.
- **Prompt de objetivos:** la IA recibe los tramos con su hora del reloj y
  las reglas: paradas solo entre 30 min después de salir y 20 min antes de
  llegar; "descanso" = dormir, solo si se pasa de las 8 pm o se cruza la
  noche; "comida" cerca de horarios de comer; sin dos paradas a menos de
  ~1.5 h.
- **Las reglas se hacen cumplir en el servidor** (`preparar_objetivos_ia`),
  no se confía en el modelo: descarta objetivos fuera de la ventana, cambia
  "dormir" de día por turismo, y hace estrictos comida y dormir (solo
  lugares que encajan, dentro de ±1.5 h del punto pedido).
- **Gasto y formulario:** cada opción calcula su propio gasto (con las
  personas y la hora de salida de la conversación) y muestra "gasto máx. ≈
  $X". Al elegir una opción, el formulario se llena (origen, destino,
  nombre, personas, hora de salida, intereses) y se recargan tramos y
  sugerencias con esos datos.

## Calidad / pruebas

- 100 tests automatizados (`pytest -q`), cubren cálculo de ruta, geocoding,
  sugerencias, guardado de rutas, generación de PDF, generación de
  destinos con IA (con el proveedor mockeado, sin gastar tokens reales),
  cuentas de usuario (registro, login, aislamiento entre cuentas), y el
  chat de planeación con IA (asignación de objetivos, filtro de hora del
  día, orquestación del chat — todo con el proveedor mockeado).
- Grafo de conocimiento del proyecto generado con graphify
  (`graphify-out/`), se actualiza con `/graphify update`.

## Commits recientes (los últimos 7, de la sesión más reciente)

1. Selector de hora tipo rueda + montos predefinidos en presupuesto/horas
   máximas — ver sección de arriba.
2. "Planear con IA" — chat que arma el itinerario, con reparto
   inteligente de paradas reutilizable sin IA — ver sección de arriba.
3. Cuentas de usuario (nombre + apellido + PIN de 4 dígitos, sin correo) —
   ver sección de arriba.
4. Destinos nuevos generados con IA (multi-proveedor: Claude/OpenAI/Gemini)
   cuando el lugar no está en la base — ver sección de arriba.
5. Autocompletado propio con Tab/Enter y sin distinguir acentos.
6. Arreglo: las paradas ya no se borran al cambiar solo los filtros.
7. Arreglo raíz del geocoding (tabla + Nominatim) + mapa más grande + tandas
   de 16 + colores de origen/destino + reubicación de "Guarda tu plan".
