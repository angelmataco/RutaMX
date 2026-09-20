# Lo que ya está hecho — RutaMX

Última actualización: 2026-09-20

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
- **Avatar de sesión con Blobatar** (blobatar.dev, MIT): con sesión iniciada, el botón
  "Iniciar sesión" del navbar se cambia por el monito (sin círculo alrededor); al picarlo se
  despliega una ventana de perfil con el monito grande, nombre + apellido y "Cerrar sesión"
  (se cierra con clic fuera, Esc, otro clic en el avatar o al encogerse el navbar). El monito sale
  de `nombre + apellido`: es siempre el mismo para la misma cuenta y no se guarda nada en la base.
  - **Navbar:** siempre respira, parpadea y mira de reojo (poquito). Con el mouse a menos de
    220 px sus ojos lo siguen (`--mo-track-travel` 6.5px). Al picarle se enoja (rosado-rojo, ceño
    fruncido) 1.4 s y, al terminar, se queda quieto (animaciones en pausa) mientras la ventana de
    perfil esté abierta.
  - **Ventana de perfil:** tiene su propio monito: sigue al mouse siempre (aunque esté lejos) con
    los ojos mucho más exagerados (12px) y se enoja con cada clic sobre él, uno a la vez (si ya
    está enojado, el clic no hace nada). Al cerrarla, el del navbar vuelve a su vida normal.
  - Probado con 14 nombres distintos (siluetas, acentos y ñ): enojo, quietud, seguimiento y
    cierre; y con una sesión simulada (al probarlo no había cuentas reales en la base).
  - Archivos: lógica en `app/static/js/avatar.js` (`RutaAvatar`); `auth.js` (`pintarAvatar`,
    `alternarMenu`, `cerrarMenu`); `partials/navbar.html`; estilos `.navbar__avatar/.navbar__menu`
    en `styles.css`. Copias de blobatar 2.7 (sin dependencias, no se editan) en
    `app/static/js/vendor/` (`blobatar.js` = dist/internal.js, `blobatar-gaze.js` = gaze.js,
    `blobatar-expresiones.js` = expression.js) y `app/static/css/blobatar-motion.css` /
    `blobatar-gaze.css` (enlazados en `base.html`). Angel guarda el paquete completo fuera del repo,
    con un `LEEME.md`, para reutilizarlo en otros proyectos.

## Navbar fijo que se encoge y tope suave entre secciones

- **Navbar fijo** (`position: fixed`, `navbar.js` + bloque final de `styles.css`): al bajar más de
  48 px se encoge a ~53 px (51 en celular) con fondo translúcido y desenfoque; quedan el
  logo y "RutaMX" (centrados en el primer tercio de la pantalla) y, en el segundo tercio, la
  **píldora de progreso** (ver abajo). Los botones de navegación y el avatar solo están en el navbar
  completo; si la ventana de perfil estaba abierta, se cierra al encogerse. En celular queda solo
  el logo (sin el nombre) junto a la píldora. Al subir de 16 px vuelve a su tamaño completo y la
  píldora desaparece.
  Un espaciador (`.navbar-espacio`) conserva la altura completa en el flujo, así el contenido
  no salta al encogerse. Queda por encima del mapa, la píldora y el grid reveal; las ventanas
  `<dialog>` lo tapan como al resto de la página. `scroll-padding-top` evita que los enlaces del
  navbar dejen el título de la sección tapado.
- **Tope suave entre secciones** (`tope.js` + `.section` en `styles.css`): al dejar de deslizar a
  menos de ~70 px (8 % de la altura de la ventana) del inicio de una sección, o de arriba de todo,
  la página se acomoda sola con un desplazamiento corto. Lejos de esos puntos el scroll es libre
  (también dentro de secciones altas). Cada sección llena al menos la pantalla bajo el navbar y
  centra su contenido, así en pantallas altas ya no asoma el final de la sección anterior sobre
  el itinerario.
- **Hero más compacto y formulario a la vista:** se quitó el texto "Las distancias, tiempos y
  recomendaciones son estimaciones demostrativas…" de la portada y el párrafo de arriba quedó en
  dos líneas. `tope.js` tiene además un punto de tope en el recuadro del formulario ("Planea en
  minutos"): al deslizar cerca de él, la página lo deja completo bajo el navbar, sin textos del
  hero encima (con 768 px de alto caben sus 694 px). Sin ruta calculada, el hero recibe espacio
  extra abajo (`body:has([data-resultados][hidden]) .hero` en `styles.css`) para que en pantallas
  altas haya scroll suficiente para subirlo hasta el navbar.
- Probado en vivo (escritorio 1024x768 y 1280x1000, celular 375): encogido/expandido, centrado
  exacto (mismos px a cada lado), sin saltos de contenido, sesión y menú de perfil, ventanas
  flotantes encima, mapa por debajo, enlaces de sección, y el tope con rueda (una muesca desde
  arriba queda libre, cerca de "Ruta" se acomoda, una muesca más allá queda libre).

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

## Campos del formulario sin teclado (burbujas; la hora ahora es el duration-picker)

- **Hora de salida**: hoy es el selector gooey `duration-picker` de rare-ui
  (`efectos/duracion.js`, ver sección de efectos visuales). Antes fue una rueda tipo iOS
  en un `<dialog>` (`time_picker.js`, ya eliminado). Sigue guardando `HH:MM` (24 h) en
  `[data-time-hidden]`, así que `form.js` y `main.js` casi no cambiaron.
- **Presupuesto** (hoy ya no existe, ver "Gasto máximo recomendado") y **Horas máximas de manejo**: en vez de una lista
  plana de `<datalist>` (se veía sosa), ahora son una fila de "burbujas"
  deslizable — mismo estilo que los chips de "¿Qué buscas?" — con montos
  predefinidos (presupuesto: $1,000, $3,000, $5,000, $7,000, $9,000; horas:
  1 a 16) más una burbuja "Otro" que revela un campo normal para escribir
  un valor exacto distinto.
- `app/static/js/bubble_picker.js` maneja las burbujas (el selector de hora ahora es
  `efectos/duracion.js`).

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
  "Dividir el viaje en: Automático · 2 a 10 · Más" ("Más" abre un campo para
  elegir de 11 a 30 tramos; el botón queda como "Más · 14"). El selector y la
  barra de tramos ocupan todo el ancho; si hay muchos tramos pasan a otra línea,
  sin barra de desplazamiento. Automático = ~3 h
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

## Gastronomía destacada (UNESCO, Guía Michelin y Latin America's 50 Best)

- Primer paso del plan `04_PLAN_RESTAURANTES_Y_HOTELES.md`. Se marcaron **21
  lugares** con gastronomía reconocida públicamente (columnas nuevas
  `gastronomia_destacada` y `reconocimiento_gastronomico` en `destinos`, con la
  fuente y los restaurantes en el texto). Ciudad de México, Guadalajara, Puerto
  Vallarta, Ensenada, Valle de Guadalupe, Tijuana, Mérida, Playa del Carmen,
  Tulum, Los Cabos, San José del Cabo, Oaxaca de Juárez, Monterrey, San Pedro
  Garza García, Puebla de Zaragoza, Atlixco y 5 lugares **agregados nuevos**
  (coordenadas reales de Nominatim): Chocholá, Cabo San Lucas, Puerto Morelos,
  Tixkokob y El Pescadero. La base tiene ahora **374 destinos**.
- **Fuentes (todas con la ciudad de cada restaurante confirmada):** UNESCO
  Ciudades Creativas de la Gastronomía (solo Ensenada y Mérida en México);
  Guía Michelin México 2026 — estrellas y la **lista completa de Bib Gourmand**
  ([Wikipedia](https://en.wikipedia.org/wiki/List_of_Michelin_Bib_Gourmand_restaurants_in_Mexico),
  [estrellas](https://en.wikipedia.org/wiki/List_of_Michelin-starred_restaurants_in_Mexico));
  y Latin America's 50 Best Restaurants 2025, lugares 1-100
  ([Forbes México](https://forbes.com.mx/forbes-life/cuales-son-los-representantes-mexicanos-en-la-edicion-2025-de-latin-americas-50-best-restaurants/)).
  **No se usaron:** los 133 "recomendados" de Michelin y la cocina tradicional
  mexicana de la UNESCO (patrimonio inmaterial, paradigma Michoacán), porque no
  dan una ciudad por restaurante.
- Nadie perdió ninguna etiqueta: solo se agregó "comida" a los que no la tenían
  (Puerto Vallarta, Playa del Carmen, Los Cabos, San José del Cabo, Tulum,
  Atlixco).
- En la app: cuando una sugerencia es de uno de estos lugares (para comer o
  para visitar, en cualquier tramo), la tarjeta lleva una **estrellita ★ dorada
  arriba a la derecha** y una línea en la descripción que dice quién lo
  recomienda ("★ Gastronomía recomendada por la Guía Michelin y la UNESCO"),
  con el detalle de restaurantes al pasar el mouse. La parada también lleva ★
  en el itinerario y en las opciones del chat de IA. En un tramo de **Comer**
  esos lugares salen primero (también en `asignar_paradas_a_objetivos`, o sea
  en "Planear con IA"). Código: `textoDeReconocimiento` en `main.js`, plantilla
  `discover_section.html`, estilos `.card__estrella`.
- Script: `scripts/marcar_gastronomia_destacada.py` (migración + marcado +
  alta de lugares nuevos; seguro de repetir).
- Nota técnica: la columna `fuente` de `destinos` solo acepta `curada` o
  `ia_generada` (restricción de la base); los lugares nuevos quedaron `curada`.

## Prioridad a los lugares distinguidos (estrella / Michelin / UNESCO)

- **Regla de Angel:** una ciudad o pueblo con reconocimiento gastronómico
  (estrella ★) tiene preferencia en las recomendaciones **siempre que la ruta
  pase cerca** (a **40 km o menos** de desvío, `RADIO_PRIORIDAD_KM`). Salen en la
  **primera página** (las primeras 4 sugerencias) y, de ser posible, en el
  primer lugar, tanto en "Todo el camino" como dentro de un tramo. Aplica igual
  en automático que en un tramo de "Comer", y también a "Planear con IA"
  (`asignar_paradas_a_objetivos`).
- **Cómo se ordena:** `ai_service.prestigio()` da puntos por reconocimiento
  (estrella Michelin > UNESCO / 50 Best > Bib Gourmand; 2 estrellas suman más);
  `prioridad()` lo aplica solo si el lugar está a ≤ 40 km de la carretera;
  `_distinguidos_primero()` los sube al frente (los más distinguidos primero; a
  igual puntaje, el más cercano al inicio del viaje). Cada sugerencia trae ahora
  `distancia_a_ruta_km`.
- **Por qué el límite de 40 km:** las sugerencias aceptan lugares hasta 150 km de
  la ruta; sin este límite, en León → Monterrey Guadalajara (145 km de la
  carretera) saltaba al primer lugar solo por tener estrella. Más allá de 40 km
  el lugar sigue pudiendo aparecer, pero sin prioridad (conserva su ★).
- Ejemplos verificados: CDMX → Oaxaca (Atlixco y Puebla primero), Mérida → Cancún
  (Playa del Carmen y Puerto Morelos primero; Tulum, a 48 km, sin prioridad),
  León → Monterrey (Guadalajara ya no va primero).
- 4 tests nuevos (rutas y prioridad).

## Sugerencias como línea de tiempo (5 visibles, "Ver más" y máximo 2 estrellas)

> **REEMPLAZADO (2026-09-19 noche):** la primera vista ya no son "los 5 primeros por hora
> con máx. 2 estrellas" sino **5 recomendadas repartidas por franjas de horas** (ver la sección
> "Recomendaciones por franjas de horas" más abajo). `_linea_de_tiempo` y
> `_elegir_con_distinguidos` siguen en `ai_service.py` (y con sus tests) pero **ya no se usan**
> en el flujo principal. Lo demás de esta sección (5 columnas, botón "Ver más ▸") sigue igual.

- **Pedido de Angel:** que las recomendaciones no salgan "desfasadas" (una a 6 h,
  luego a 1 h, luego a 4 h) sino como una **línea de tiempo del viaje**, para ver
  rápido qué hay disponible en las primeras horas.
- **Orden (`ai_service._linea_de_tiempo`):** (1) al frente los lugares distinguidos
  (★) cercanos a la ruta, sin importar la hora, **máximo 2**
  (`MAX_DISTINGUIDOS_AL_FRENTE`) para que ninguna ruta se llene de puras
  estrellas; (2) después todo lo demás en orden de camino (a 1 h, luego a 2 h,
  luego a 3 h y media…). Las estrellas que sobran conservan su ★ pero entran a la
  línea de tiempo por su hora y **nunca dentro de la primera vista**. Aplica en
  "Todo el camino" y dentro de un tramo, y valdrá igual para restaurantes.
  `_elegir_con_distinguidos` asegura que ningún distinguido cercano se pierda.
- **5 visibles, no 4:** se ven 5 tarjetas en una fila (5 columnas en pantallas de
  más de ~980 px; 3, 2 o 1 en pantallas más chicas), más compactas que antes
  (`TAMANO_PAGINA_SUGERENCIAS` en `ai_service.py` y `MOSTRAR_SUGERENCIAS` en
  `main.js`, deben coincidir). Se piden 20 por lote (`TAMANO_LOTE`), repartidos a
  lo largo de la ruta y ordenados por hora.
- **"Ver más ▸" en vez de "ver más recomendaciones":** botón centrado con una
  flechita; al tocarlo se **despliegan todas las demás** (mismas tarjetas, mismo
  diseño, en filas de 5, ordenadas por hora del viaje) y se recorren con el
  scroll de la página. El botón pasa a "Ver menos" (flecha girada) y las vuelve a
  plegar, dejando solo las primeras 5. Agregar o descartar una tarjeta la quita de
  la lista y la vuelve a dibujar (si quedan pocas, trae otro lote).
- ~~**Etiqueta** sobre las tarjetas: "★ 2 destacados cerca de tu ruta · de 54 min a
  1 h 18 min del inicio"~~ — **eliminada** a pedido de Angel (ver sección de "Descubre en el camino").
- **Hallazgo:** en CDMX → Oaxaca casi todos los candidatos caen en la primera mitad
  del viaje y entre las 3 h y la llegada solo hay uno (Tehuacán): la base tiene
  pocos lugares a lo largo de esa carretera. Se resuelve agregando más lugares
  (ver plan 04).
- Tests nuevos: orden por horas, máximo 2 estrellas en la primera vista, que
  ninguna se pierda, y línea de tiempo por la API.

## Selector de tramos hasta 10 + "Más", a todo lo ancho

- Pedido de Angel tras probar Tijuana → Puerto Vallarta (27.5 h; en automático
  salieron 9 tramos de 3 h cada uno). El selector manual llega hasta **10 tramos**
  con botones y **"Más"** abre un campo (11 a 30). La fila de botones y la de
  tramos cubren todo el ancho (`.tramos-control__opciones--ancho`, `.lapsos`
  con `flex-wrap`).
- Arreglo incluido: la fila "¿Qué buscas en el tramo N?" aparecía como una barra
  vacía cuando no había tramo elegido, porque `.tramos-control { display: flex }`
  ganaba al atributo `hidden`; ahora hay `.tramos-control[hidden] { display: none }`.
- Ojo: cuando un elemento con `hidden` tenga un `display` propio en CSS, hay que
  agregar la regla `[hidden] { display: none }` (pasó también con la estrella).

## Efectos visuales (solo frontend) tomados de rare-ui

- Pedido de Angel: usar 7 efectos (el step-player se quitó y después se sumó el duration-picker; hoy son 7) de la carpeta `efectos visuales rare-ui` (que
  **no se modificó**; es una librería de componentes React/Tailwind/Motion). Como
  RutaMX es Flask + JS/CSS puro, cada uno se **reescribió sin librerías** en
  `app/static/js/efectos/` + `app/static/css/efectos.css`. **No se tocó nada del
  backend ni del flujo**: solo se agregaron llamadas donde antes se escribía
  `textContent`, y una plantilla/ancla mínima.
- **Contador tipo odómetro** (`contador.js`): los números del "Resumen del viaje"
  (distancia, tiempo, gasto, paradas) y del "Resumen de aventura" ruedan dígito por
  dígito hasta su nuevo valor. Funciona con cualquier texto ("$2,077", "5 h 47 min").
  Uso: `RutaEfectos.contador.set(elemento, texto)`; el texto real queda para
  lectores de pantalla.
- **Borrar con confirmación en el mismo botón** (`eliminar.js`): el bote de basura de cada parada
  del itinerario abre la tapa y muestra ✓ / ✕ (Esc y clic afuera cancelan). Ojo: antes
  borraba al primer clic; ahora hace falta confirmar. Se borra por identidad del objeto,
  no por posición, para que un borrado pendiente no elimine la parada equivocada.
- **PIN por casillas** (`pin.js`): en login y registro el PIN son 4 casillas a todo lo ancho de la ventana, con el
  dígito rodando y un cursor que se desliza; pegar el código completo funciona; si el
  servidor rechaza el PIN, se sacuden. El `<input name="pin">` original sigue existiendo
  (oculto) con el valor, así que `auth.js` no cambió.
- **Menú gooey en el navbar** (`gooey.js`): Ruta / Descubre / Itinerario; la opción se
  separa con un cuello elástico **al pasar el cursor** (al salir vuelve a la sección
  actual, que sigue el scroll); también al hacer clic, con scroll suave. En pantallas ≤640 px el menú pasa a su propia fila. Los botones solo están en el navbar
  completo (arriba de la página); al bajar, la píldora de progreso ocupa su lugar.
- **Píldora de progreso** (`pildora.js`): un anillo que se llena al bajar y el nombre de la
  sección; al tocarla se despliega (hacia abajo) para saltar a Inicio / Ruta / Descubre /
  Itinerario. **Vive dentro del navbar compacto**, en el segundo tercio de la pantalla (donde
  antes estaba la píldora flotante abajo a la derecha, que ya no existe): solo se ve cuando el
  navbar se encoge, es decir, cuando empiezas a deslizar; con el navbar completo no está en ningún
  lado, y si estaba desplegada al volver arriba, se cierra. Se ve también sin ruta calculada (con
  la sección "Inicio"). El resalte del menú desplegado **sigue al cursor** (y al foco del teclado)
  con su animación de resorte y vuelve a la sección activa al salir; la sección activa se marca además
  con un punto terracota. `secciones.js` es el módulo compartido de "sección activa".
- **Selector de hora gooey** (`duracion.js`, efecto `duration-picker` de rare-ui): la hora
  de salida es una píldora `[ HH Hr. ][ MM Min. ][ ✎ ]`; al tocar el lápiz (o la hora/los
  minutos) se separa en tres piezas con resorte y el lápiz pasa a palomita. **No se escribe**:
  al tocar la hora o los minutos se abre una **ruedita** (scroll-snap, como la de iOS) para
  deslizar y escoger (una a la vez, cada campo la suya); también sirven las flechas ↑↓ del
  teclado. Botón "Sin hora definida" dentro de la rueda. Al abrir sin hora se propone 08:00.
  Enter o ✓ guardan, Esc descarta; tocar fuera guarda solo si se cambió algo; enviar el
  formulario guarda lo elegido. Vacío = sin hora. Reemplazó a la rueda en `<dialog>` anterior
  (`time_picker.js`, borrado). `main.js` la restaura con `RutaEfectos.horaSalida.poner("HH:MM")`.
  (Primera versión: se escribía a mano; a Angel no le gustó teclear y se cambió a ruedita.)
- **Ajustes posteriores del selector de hora y del contador (2026-09-19):** el fondo del selector de
  hora ahora es el **naranja de la app** (`--color-terracota`, texto blanco, ruedita con banda naranja
  clarita) en vez del verde pálido; y el **contador** rueda **más lento** (1.6 s con rebote suave, y los
  dígitos arrancan en cascada de derecha a izquierda, `transition-delay` por columna en `contador.js`).
- **Botones de sesión del navbar** (Iniciar/Cerrar sesión): al pasar el cursor se resaltan en
  su lugar con el mismo efecto del menú gooey (terracota, esquinas más cuadradas, rebote suave).
  Arreglo: la primera versión animaba el radio desde `999px` y la esquina no se notaba hasta el
  final (se veía como un salto raro al segundo); ahora parte de `18px` y todo cambia a la par en ~0.35 s.
  Con sesión iniciada "Iniciar sesión" se oculta (el monito ocupa su lugar) y "Cerrar sesión" vive en
  la ventana de perfil, donde esta regla sigue aplicando.
- **Orbe de puntos** (`orbe.js`, grande: 120 px en sugerencias y 92 px en el chat): reemplaza el texto "Buscando ideas para tu
  recorrido…" y los tres puntitos de "Planear con IA" mientras piensa.
- Todo respeta `prefers-reduced-motion`. Ancla nueva `id="inicio"` en el hero (para la
  píldora).
- **Step-player quitado** a pedido de Angel (no le gustó): se borraron `stepplayer.js`, su
  CSS y sus enganchos. Ajustes posteriores: PIN a lo ancho, gooey animado con el cursor,
  píldora a la esquina derecha y más grande, orbe más grande.
- Probado en vivo (desktop y móvil 375 px): cálculo de ruta, cambio de tramos,
  reproducción, agregar/borrar parada, login con PIN incorrecto, píldora, menú;
  sin errores de consola y sin desborde horizontal. 123 tests siguen pasando.

## Filtro principal: lo que se marca en "¿Qué buscas?" manda

- **Bug encontrado (pedido de Angel):** al marcar Naturaleza + Cultura salían lugares de otras
  cosas. Los intereses solo *ordenaban* (después de las estrellas Michelin y del propósito por
  hora) y nunca filtraban. Además **"Pueblos mágicos" no coincidía con nada**: no existe como
  interés guardado en los 374 destinos; es su `tipo` (`pueblo_magico`).
- **Regla nueva** (`ai_service.coincide_intereses` / `_puntos_interes`): un lugar solo se
  recomienda si cumple **al menos uno** de los intereses marcados (sin ninguno marcado, todos
  valen); "pueblos_magicos" se compara contra el `tipo`. Es un **filtro estricto** que se aplica
  antes que estrellas, propósito por hora o cercanía. Entre los que pasan, los que cumplen más
  intereses van primero.
- **Única excepción:** un tramo que el usuario personalizó a mano (Comer / Dormir / Turismo) manda
  sobre los intereses de ese tramo (`_encaja_con_lo_pedido`).
- El radio de búsqueda alrededor de la carretera (20 → 60 → 150 km) ahora se amplía hasta juntar
  suficientes lugares **que sí cumplen los intereses** (`_candidatos_en_el_corredor(..., intereses)`).
- Verificado con datos reales (CDMX → Oaxaca): Naturaleza+Cultura, Pueblos mágicos, Playas (solo 1
  lugar cerca de esa ruta: la base es honesta) y Comida cumplen el 100 %.
- Ojo: el chat de "Planear con IA" (`planificador_ia_service.py`) no usa este filtro (ver 02).

## Recomendaciones por franjas de horas (5 recomendadas, "Ver más", "Ver menos")

- **Pedido de Angel:** que la primera vista de 5 tarjetas sean **5 recomendaciones repartidas por las
  horas del viaje** (ej. viaje de 10 h: una entre la hora 1 y 2, otra entre la 2 y 4…), que cumplan
  el filtro de intereses y con **prioridad siempre a lo que tenga estrella**.
- **Backend (`ai_service._repartir_por_franjas`, usado por `_sugerir_por_lapsos`):** la ventana del
  viaje (o del tramo elegido; de 30 min después de salir a 20 min antes de llegar) se parte en 5
  franjas iguales. Dentro de cada franja se ordena por: 1) distinguido (★ cerca de la ruta),
  2) que encaje con el propósito de la hora (comer/dormir), 3) que cumpla más intereses, 4) que
  quede más cerca de la carretera. Cada lugar sale con `franja`, `rango_franja`, `rango_global` y
  `recomendada` (las 5 mejores: una por franja). La lista completa va en orden de hora.
  Si una franja queda vacía, se completa con los siguientes mejores del resto.
- **Frontend (`main.js`):** `recomendadas()` toma la mejor de cada franja (en orden de hora).
  **"Ver más"** muestra todas ordenadas por hora del viaje desde la primera; **"Ver menos"** vuelve a las
  recomendadas. Si se agregó o descartó una recomendada, entra la siguiente mejor **de su misma franja**
  (o, si no hay, otra) — sin pedir nada al servidor (por eso se piden 40 por lote: `TAMANO_LOTE`).
  Al cambiar de vista las tarjetas **se mueven** hasta su nuevo lugar (animación FLIP con la Web
  Animations API, `animarReacomodo`); las nuevas entran con fundido.
- **Hallazgo de datos:** en CDMX → Oaxaca casi no hay destinos entre Tehuacán (3 h) y Oaxaca, así que
  solo se llenan ~3 de las 5 franjas y el resto se completa con los siguientes mejores. Solución de
  fondo: más lugares en la base (plan 04).
- Tests nuevos: franjas, una recomendada por franja con estrella al frente, y completar hasta 5.

## Tarjetas de recomendación simétricas

- **Pedido de Angel:** la información se veía "encimada" y no rellenaba la tarjeta. Ahora cada tarjeta
  es la misma estructura de franjas fijas (`discover_section.html`, `#tpl-sugerencia`; `styles.css`):
  cabecera (categoría + estrella en su propio espacio, sin `position:absolute`) · título (2 renglones
  de alto mínimo) · descripción (3 renglones) · caja de camino (🚗 ≈X de camino / 🕘 Llegas HH:MM) ·
  **franja que se estira y rellena** (notas de gastronomía / comer / dormir y los **intereses del
  lugar** como etiquetas, así nunca queda hueca) · botones. Medido: las 5 tarjetas quedan con la misma
  altura y títulos y botones a la misma altura.
- Trampa: `.card__nota { display:flex }` le ganaba al atributo `hidden` (barras vacías); ahora hay
  `.card__nota[hidden] { display:none }`.

## Descubre en el camino: se quitó la etiqueta de horas

- Se eliminó por completo la línea de arriba de las tarjetas ("★ 2 destacados cerca de tu
  ruta · de 48 min a 1 h 30 min del inicio"): Angel dijo que no servía y se veía mal.
  Se borró `<p data-linea-tiempo>`, su CSS y su lógica; `actualizarLineaDeTiempo` quedó como
  `actualizarBotonVerMas` (solo maneja "Ver más / Ver menos"). Las tarjetas conservan su
  "≈ X de camino · llegas HH:MM" y la ★.

## "Planea mi ruta" abre al instante + grid reveal en el mapa

- Antes la página se quedaba congelada hasta que el servidor respondía. Ahora, en cuanto se
  pulsa el botón (`calcularRuta` en `main.js`): se muestran ya los resultados, se baja hasta
  ellos y se puede seguir deslizando mientras carga. El scroll se hace **solo al pulsar**, no
  al llegar los datos (para no arrastrar al usuario). Si se pulsa otra vez, manda solo la
  respuesta más reciente (`idCalculo`); si falla y no había resultados antes, se vuelven a ocultar.
- Mientras carga: **grid reveal** (`gridreveal.js`, efecto `grid-reveal` de rare-ui) sobre el
  mapa: cuadrícula gris cálida que se parte en cuadritos al ritmo de ~4.5 s estimados; cuando
  llega la ruta se deshace en una ola diagonal y deja ver el mapa (pastilla "Trazando tu
  ruta…"). No se agregó espera artificial: si el servidor responde rápido, la cuadrícula
  acelera y se disuelve antes. Además, orbe grande "Buscando ideas…" en las sugerencias, y el panel
  de resumen se atenúa. **Ya no hay orbe "Calculando tu ruta…"** (se quitó a pedido de Angel,
  2026-09-20): al pulsar "Emprender ruta" la página baja directo a la sección "Tu recorrido"
  (`irASeccionRuta()` en `main.js`), alineada bajo el navbar y con su contenido centrado, mientras el
  mapa muestra la cuadrícula. El mismo scroll se usa al aplicar un plan de "Planear con IA".

## Tramos en automático = "Paradas sugeridas" del resumen

- El panel "Paradas sugeridas" sale de la distancia (`max(1, min(4, round(km/250)))` en
  `route_service.py`) y los tramos automáticos salían de la duración (~3 h por tramo), así que
  no coincidían. Ahora, **en automático, el frontend manda `tramos = paradas_estimadas`** a
  `/api/sugerencias` (solo `main.js`; el backend no cambió). Si el usuario elige un número, manda
  el suyo. El botón ahora dice "Automático · N" para que se vea cuántos tramos salen.
  Verificado: CDMX→Oaxaca 2 y 2; CDMX→Monterrey (897 km) 4 y 4.

## Rediseño visual (base de Stitch)

Se rediseñó el frontend a partir de `stitch_rutamx_road_trip_planner` (DESIGN.md,
logo y paleta de Angel). Solo diseño: no se tocó el backend.

- **Paleta y tipografía:** los tokens `--color-*` de `styles.css` conservan su
  nombre pero cambiaron de valor (lino `#faf7f2`, terracota `#c85a32`, agave
  `#1b4332`, ocre `#e9a825`, cuero `#2c221e`), así los 8 efectos rare-ui se
  recolorearon solos. Fuentes: Newsreader (títulos) y Plus Jakarta Sans (texto),
  cargadas de Google Fonts en `base.html`.
- **Logo:** `app/static/img/logo-emblema.svg` (emblema del círculo con sol, montaña
  y camino) junto al texto "RutaMX" y el lema con los puntos tricolor.
- **Componentes:** bloque "Rediseño RutaMX" al final de `styles.css`: campos en
  píldora con halo terracota, chips seleccionados en agave, botón primario terracota
  y secundario fantasma, etiquetas tipo "luggage tag" (borde punteado ocre),
  itinerario con línea de carretera a la izquierda, tarjeta de aventura en agave.
- **Iconos a medida (sin emojis en toda la app):** los 26 iconos de la carpeta de Stitch
  (`stitch_rutamx_road_trip_planner 2`) viven en **un solo sprite**,
  `templates/partials/iconos_sprite.html` (un `<symbol id="i-nombre">` por icono, incluido
  una vez en `base.html`). Desde plantillas se usan con la macro `{{ icono("ruta") }}`
  (`partials/icons.html`); desde JS con `RutaIconos.html("ruta")` o
  `RutaIconos.nodo("comer", "Comer")` (`static/js/iconos.js`, que arma el texto con
  `textContent`, sin inyección). Nombres: ruta, planear_ruta, ia, guardadas, itinerario,
  cerrar, mapa_pin, ver_mas, arriba, abajo, palomita, tache, lapiz, bote, estrella,
  siguiente, comer, dormir, turismo, gasolina, casetas, mochila, noche, auto, llegada,
  ajustes. `main.js` ya no escribe emojis (etiquetas Comer/Dormir, desglose del gasto,
  tarjetas de sugerencias, tramos, estrella de gastronomía, enlaces por tramo).
  Los efectos que dibujan su propio SVG (bote/✓/✕ de `eliminar.js`, lápiz/✓ de `duracion.js`)
  usan los dibujos nuevos con sus mismas clases (`del__tapa`, `del__trazo`, `dur__pluma`,
  `dur__palomita`). El botón de ajustes de gasto lleva su texto en `[data-ajustes-texto]`.
- **Luz que sigue al cursor (spotlight-card, JS/CSS puro):** aro brillante en el borde y
  resplandor interior que se acercan al puntero, terracota→ocre según la posición. Se aplica
  solo a `.card`, `.ruta-burbuja`, `.navbar__menu` (ventana de perfil del avatar, solo el
  resplandor interior) y las ventanas `.modal-auth/-ajustes/-rutas/-ia`
  (`efectos/spotlight.js` + bloque 9 de `efectos.css`). **Con una ventana abierta, la luz es solo
  de esa ventana** (y de lo que lleva dentro): la de las tarjetas de atrás se apaga al instante y
  no se enciende aunque el cursor pase por encima; al cerrarla, todo vuelve a la normalidad. Aplica
  a las 4 ventanas de la app (sesión, ajustes de gasto, mis rutas y chat de IA) y a cualquier
  `<dialog>` futuro.
- **Fondo de líneas que fluyen (background-paths, JS/SVG/CSS puros):** capa fija detrás de toda
  la página (`efectos/fondo.js` + bloque 10 de `efectos.css`). **Respeta el código original del
  componente, incluido su arranque (sin entrada propia):** dos juegos (position 1 y -1) de 36
  curvas con la misma fórmula, `viewBox 0 0 696 316`, grosor `0.5 + i*0.03` y `strokeOpacity
  0.1 + i*0.03`; cada curva anima `pathLength` 0.3→1, `pathOffset` 0→1→0 y `opacity` 0.3→0.6→0.3,
  en linear y en bucle, con duración distinta por curva. **Solo dos cambios, pedidos por Angel:**
  (1) velocidad: cada vuelta dura ~16.5–26 s en lugar de 20–30 s, un punto medio que Angel escogió
  entre el original y una versión más rápida de 13–22 s (`DURACION_BASE` y `DURACION_AZAR` en
  `fondo.js`); (2) color: el original usa un solo color y aquí cada curva recorre los 9 tonos de
  la paleta de la app (terracota, terracota vivo, arcilla, ocre, ocre profundo, agave, agave medio,
  salvia y cuero) con su propio ritmo y fase (`--fondo-c0..8` en `efectos.css`). En pantallas
  ≤700 px son 18 curvas por juego en vez de 36. Las secciones de la página son transparentes o
  translúcidas para que se vea; las tarjetas siguen opacas.
- **Hora de salida, minutos de 10 en 10:** la ruedita de minutos ofrece 00, 10, 20, 30, 40 y 50
  (antes 60 filas de uno en uno); las horas siguen de 1 en 1. También aplica a las flechas ↑↓ del
  teclado y a los clics en la rueda (`PASO` en `efectos/duracion.js`). Una hora ya guardada que no
  sea múltiplo de 10 (por ejemplo 08:25 de una ruta vieja) se conserva tal cual hasta que se cambie.
- **"Descubre en el camino":** el título, el aviso de demostración y los selectores de tramos
  van dentro de una tarjeta (`.card--descubre-cabecera` en `discover_section.html`) para que el
  texto no se pierda con las líneas del fondo; las tarjetas de sugerencias quedan sueltas debajo,
  con el fondo visible entre ellas. El botón "Ver más" está centrado (`.btn--ver-mas` al final de
  `styles.css`: `.btn` le ganaba con `inline-flex` y el margen automático no lo centraba).
- **Corrección móvil:** la fila del itinerario (nombre + etiqueta + botones) desbordaba a
  375 px; ahora baja de línea y las cuadrículas usan `minmax(0, 1fr)`.
- Verificado: 123 tests pasan, consola sin errores, sin scroll horizontal en 375 px.

## Calidad / pruebas

- 123 tests automatizados (`pytest -q`), cubren cálculo de ruta, geocoding,
  sugerencias, guardado de rutas, generación de PDF, generación de
  destinos con IA (con el proveedor mockeado, sin gastar tokens reales),
  cuentas de usuario (registro, login, aislamiento entre cuentas), y el
  chat de planeación con IA (asignación de objetivos, filtro de hora del
  día, orquestación del chat — todo con el proveedor mockeado).
- Falla conocido: `test_registrar_usuario_duplicado_por_acentos_y_mayusculas` choca con la cuenta
  real "Angel Mata" de la base (ver `02_LO_QUE_FALTA.md`). Los tests corren contra Supabase: con
  el servidor abierto a la vez, la suite completa puede dar `EMAXCONNSESSION` en 1 o 2 tests;
  repetidos solos pasan.
- Grafo de conocimiento del proyecto generado con graphify
  (`graphify-out/`), se actualiza con `/graphify update`.

## Commits recientes (los últimos 8)

1. Avatar de sesión con Blobatar, navbar fijo que se encoge y tope suave entre secciones — ver
   las secciones "Cuentas de usuario" y "Navbar fijo que se encoge…" de arriba.
2. Rediseño del frontend con la base de Stitch, iconos a medida y efectos de fondo.
3. Efectos visuales de rare-ui, filtro de intereses y recomendaciones por franjas de horas.
4. Selector de tramos hasta 10 con "Más" (11 a 30) y barras a todo lo ancho.
5. Sugerencias como línea de tiempo: prioridad a lugares con estrella, 5 visibles y "Ver más".
6. Gastronomía destacada (UNESCO, Michelin, 50 Best) con estrella en las tarjetas.
7. Documenta el plan para re-etiquetar la base y agregar restaurantes y hoteles.
8. Tramos con hora y propósito, gasto que se deduce solo, ajustes en el resumen e IA al día.
