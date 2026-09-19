# Lo que ya está hecho — RutaMX

Última actualización: 2026-09-19

RutaMX es una app web para planear road trips por México. Flujo completo
funcionando de punta a punta: formulario → cálculo de ruta → mapa →
sugerencias de paradas → armar itinerario → guardar → descargar PDF.

## Mapa y ruta

- Mapa con Leaflet + OpenStreetMap.
- Ruta real por carretera (no línea recta) con Leaflet Routing Machine +
  OSRM (servidor demo gratuito, sin API key).
- Distancia, tiempo y costo estimado calculados con la ruta real de OSRM;
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
- **Presupuesto** y **Horas máximas de manejo**: en vez de una lista
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

## Calidad / pruebas

- 49 tests automatizados (`pytest -q`), cubren cálculo de ruta, geocoding,
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
