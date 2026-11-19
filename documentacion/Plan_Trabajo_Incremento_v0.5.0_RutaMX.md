# [V2] Plan de trabajo: incremento v0.5.0 — Editar por chat, copiar rutas públicas, mapa y cierre (13 RF)

- Fecha: **2026-11-19 (CDMX)**. Equipo: Angel Mata y Roberto Valderrama, con **claude-par y codex-par en modo par**.
- Clase: **cuarta y última clase de trabajo (90 min)** antes de las 2 clases de exposición. Este plan se ejecuta completo en esta clase; no hay clase siguiente para terminarlo.
- Repo: `angelmataco/RutaMX`, rama de trabajo del plan original: `incremento-5` (si no se usa rama, trabajar en `main` como en los incrementos anteriores, pero sin mezclar con otra cosa).
- Fuentes verificadas antes de escribir este plan (2026-11-19, en `main` @ `b64954e`): `documentacion/plan_incrementos.md` (ficha del incremento 5, líneas 207–226), `documentacion/A3_Propuesta_Incrementos.md` (ficha 5 idéntica), `documentacion/RutaMX_Plan_de_Incrementos.pdf` (versión de entrega del mismo plan, 2026-11-05), `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf` (texto exacto de los RF y los CA de HU-06, 07, 08, 14, 15, 16 y 18), `documentacion/Reporte_Avance_Incremento_v0.4.0.md`, el PDF subido por Angel `Reporte_Avance_Incremento_v0.4.0.pdf` (sintaxis del reporte final), `bitacora_proyecto/01, 02, 03 y 05`, y el código actual de `v2/` y `base_datos/`.
- Nota de ruta: `A3_Propuesta_Incrementos.md` **no está en la raíz**; está en `documentacion/A3_Propuesta_Incrementos.md`.

## 0. Cómo se trabaja este plan (modo par)

1. claude-par y codex-par negocian este plan entre ellos; **Angel aprueba la tabla de módulos antes de tocar código**. Si el par quiere cambiar una decisión de la sección 2, lo dice explícitamente y Angel decide; no se cambia en silencio (regla de `AGENTS.md`).
2. **Un módulo a la vez, en orden M1 → M7.** No se abre el siguiente hasta que el anterior tenga: implementación, pruebas normal/límite/error en verde y revisión cruzada de la otra IA.
3. **Un commit por módulo** (o por tarea dentro del módulo), formato del proyecto: `[V2] tipo(RF-XX): descripción`. Ejemplo: `[V2] feat(RF-27): eliminar parada por chat en M-05 y M-04`.
4. Reparto habitual del repo: una IA implementa y la otra revisa cada paso; el equipo (Angel y Roberto) decide y verifica. Quien no escribió el paso es quien lo revisa.
5. Reglas que no se rompen: datos ficticios en pruebas; **no tocar `v1/`**; **no ejecutar la migración en Supabase**; no inventar resultados (estados honestos: *programado*, *probado en simulación*, *verificado en uso real*, *sin verificar*); todo documento nuevo lleva `[V2]`; al terminar cada cambio real, actualizar la bitácora que corresponda (`01` lo hecho, `02` lo que siga faltando, `03` el porqué de decisiones no obvias).
6. Antes de proponer código, leer: `AGENTS.md`, `bitacora_proyecto/01, 02 y 03` (siempre) y `05_EFECTOS_VISUALES_PROTEGIDOS.md` (se toca frontend en M5 y M6: los efectos protegidos no se quitan ni se reemplazan).

## 1. Qué es exactamente el v0.5.0 (los 13 RF, texto de la especificación v2.0)

| RF | Texto corto (spec v2.0) | HU | Prioridad | Módulos (matriz 9.1) | CP |
|---|---|---|---|---|---|
| RF-27 | Pedir por chat eliminar una parada | HU-14 | Media | M-04, M-05 | CP-27 |
| RF-28 | Actualizar el itinerario sin afectar las demás paradas | HU-14 | Media | M-03, M-05 | CP-28 |
| RF-29 | Pedir por chat reordenar las paradas | HU-15 | Media | M-04, M-05 | CP-29 |
| RF-30 | Mostrar la nueva secuencia tras reordenar | HU-15 | Media | M-03, M-05 | CP-30 |
| RF-31 | Modificar **solo** duración y tipo de lugares durante la conversación (D-04) | HU-16 | Media | M-04, M-05 | CP-31 |
| RF-32 | Mostrar el itinerario actualizado tras cambiar preferencias | HU-16 | Media | M-03, M-05 | CP-32 |
| RF-34 | Avisar que una acción no soportada no está disponible (D-05) | HU-18 | Media | M-04 | CP-34 |
| RF-13 | Copiar una ruta pública como base de una ruta propia (autenticado) | HU-07 | Media | M-01, M-05, M-10 | CP-13 |
| RF-14 | Crear la copia asociada al usuario sin tocar la original | HU-07 | Media | M-05, M-09 | CP-14 |
| RF-15 | Pedir iniciar sesión si un anónimo intenta copiar | HU-08 | Media | M-01, M-10 | CP-15 |
| RF-16 | Informar el error al copiar y no crear copia incompleta | HU-07 | Media | M-05, M-09, M-11 | CP-16 |
| RF-11 | Mostrar el recorrido en un mapa en el detalle, si hay proveedor configurado (D-06) | HU-06 | **Baja** | M-01, M-08 | CP-11 |
| RF-12 | Avisar que el mapa no cargó y mostrar lo demás | HU-06 | **Baja** | M-01, M-08, M-11 | CP-12 |

Además, este incremento **cierra la cobertura parcial** de incrementos anteriores (ficha del plan, sección 2 del plan de incrementos): al probar **todas** las operaciones de modificación se marcan terminados **RF-18** (las 5 intenciones de D-05 ya quedan todas soportadas), **RF-24** (la ruta estructurada refleja todos los cambios aceptados) y **RF-37** (atomicidad en eliminar, reordenar y preferencias; CA-20.4 y CA-12.5 con modificaciones). Y el mapa del detalle cierra la vista que faltaba de **RF-43** (vistas derivadas de la ruta única: chat, itinerario **y mapa**).

RNF que se verifican aquí (ficha): **RNF-13, RNF-23, RNF-25, RNF-26, RNF-27, RNF-28, RNF-29, RNF-30, RNF-31, RNF-33**. No declarar cumplido ningún RNF sin su evidencia (ver M7): RNF-13 (HTTPS) y RNF-23 (navegadores) probablemente queden *sin verificar* y así se escriben en el reporte.

Criterios de aceptación a probar: **los 28 CA de HU-06, HU-07, HU-08, HU-14, HU-15, HU-16 y HU-18** (4 por HU), repartidos por módulo abajo. Dos CA quedan con tratamiento especial y honesto desde el inicio:

- **CA-18.4** (una solicitud con varias operaciones, ejecutar solo las soportadas): el contrato actual de M-07 interpreta **una** acción por mensaje. No se finge: se registra como limitación en el reporte (si la IA devuelve `no_soportada`, no se aplica nada y la ruta no cambia).
- **CA-08.4** (tras iniciar sesión, completar la copia de la misma ruta sin volver a seleccionarla): queda como **estirable** en M5 (paso 5.4). Si no se verifica, en el reporte va como *programado/parcial*, no como completo.

## 2. Decisiones cerradas antes de programar (aprobar en los primeros 5 minutos)

Estas decisiones ya vienen fundamentadas en el propio repo; el par las aplica tal cual salvo que Angel diga otra cosa al aprobar la tabla.

### D-V5-1 · P-02 (mapas) se resuelve con el proveedor que el sitio ya tiene
El sitio **ya cuenta con proveedor de mapas sin credenciales**: Leaflet 1.9.4 + teselas de OpenStreetMap (+ OSRM) en v1 (`v1/templates/base.html`, `v1/static/js/map.js`, `v1/services/maps_service.py` con Nominatim). Por tanto, para D-06, «proveedor configurado» = **Leaflet/OSM cargado desde el mismo CDN que usa v1**; no se pide ninguna API key ni proveedor nuevo. «Proveedor no disponible» = la librería no carga o falla → aplica RF-12. Esta resolución de P-02 se anota en `bitacora_proyecto/03` y en el reporte (sigue siendo decisión del equipo, no respuesta del profesor).

### D-V5-2 · De dónde salen las coordenadas del mapa del detalle
De los datos que la ruta **ya guarda**, sin geocodificar en caliente y sin llamadas nuevas a Nominatim al abrir el detalle:
- Origen y destino: `resumen.rutamx_v2.ruta.origen_lugar` / `destino_lugar` (`{id, latitud, longitud}`).
- Cada parada: `paradas[].lugar` (mismo formato, lo escribe M-05 al validar con D-03).
- Un punto sin coordenadas válidas (mismas reglas que `GestorRutas._coordenada_valida`: número finito, no booleano, latitud −90..90, longitud −180..180) **se omite del mapa y se cuenta** en `puntos_omitidos` (CA-06.2 y CA-06.4). Si no queda ningún punto válido, `puntos_mapa` va vacío y la pantalla muestra el aviso de RF-12 con el resto del detalle intacto.
- El mapa dibuja **marcadores en orden y una línea que los une en ese orden** (origen → paradas → destino). No se calcula ruta por carretera en el detalle (eso ya lo hace el mapa principal de v1 con OSRM); queda anotado como límite en el reporte.

### D-V5-3 · Edición por chat: se amplía el contrato existente, no se crea otro chat
Hoy M-07 (`v2/integracion/adaptador_ia.py`, `_SISTEMA_MODIFICACION` y `_modificacion`) solo acepta `agregar_parada`, `aclarar` y `no_soportada`, y M-04 (`v2/negocio/orquestador.py::_modificar`) solo despacha `agregar_parada`. El v0.5.0 amplía **ese mismo contrato** con tres acciones nuevas (sección M1) y **ese mismo despachador**. Formatos cerrados:
- Eliminar se identifica por `nombre` **o** por `posicion` (índice desde 0 entre las paradas, misma convención que ya usa M-07 para agregar; M-05 trabaja desde 1). Si vienen ambos o ninguno → respuesta inválida de la IA / aclaración, sin tocar la ruta.
- Reordenar se pide con la **lista completa** de nombres en el nuevo orden (`orden`), usando los nombres exactos de la ruta adjunta. Orden parcial o con nombres ajenos = error de datos (CA-15.2), sin cambios.
- Cambiar preferencias lleva `duracion_dias` y/o `intereses` (al menos uno; ningún otro campo: D-04 son solo esas dos preferencias).

### D-V5-4 · Las operaciones nuevas del Gestor pasan por `aplicar()` (atomicidad real)
`GestorRutas` ya tiene `agregar_parada()` probada sobre `aplicar()` (copia → valida D-03 completo → reemplaza solo si todo sale bien). Las operaciones nuevas (`eliminar_parada`, `reordenar_paradas`) se implementan **igual**: métodos del Gestor sobre `aplicar()`, nunca mutando la ruta vigente a mano. En el Orquestador se despachan con un ayudante que reutiliza el manejo de confirmaciones de `_aceptar` (si salta `ErrorRutaRequiereConfirmacion`, se guarda el pendiente y `confirmar()` lo reintenta con la confirmación agregada).
**No se refactoriza el camino actual de agregar parada en esta clase** (la limpieza anotada en la bitácora 02 queda como pendiente registrado): proteger la regresión manda sobre la elegancia cuando quedan 90 minutos.

### D-V5-5 · Cambiar preferencias = regenerar la propuesta con los datos nuevos
RF-32/CA-16.1 piden una **versión actualizada del itinerario conforme al nuevo criterio**, no solo cambiar dos campos sobre la ruta vieja. Por eso `cambiar_preferencias` en M-04: valida los valores nuevos (reutilizar `_validar_datos`), los mezcla con `self._datos`, llama a `generar_ruta` y acepta la propuesta por el camino normal (`_aceptar`, con las mismas comprobaciones de que la propuesta respeta origen/destino/duración/intereses que ya hace `procesar`). Reglas:
- Si el valor nuevo es **inválido** → se pide un valor válido y **no cambia nada** (CA-16.2).
- Si la IA falla o la propuesta no se puede validar → error seguro y **se conserva la última versión válida, incluidos los datos anteriores** (CA-16.3): los `self._datos` nuevos solo se confirman cuando la propuesta se acepta (ojo: el flujo de creación sí guarda los datos del usuario aunque falle la generación; aquí se decide lo contrario y se anota en bitácora 03).
- Si la preferencia nueva **es igual a la vigente** (misma duración y mismos intereses) → se responde con el itinerario actual sin llamar a la IA y sin modificar nada (CA-16.4).

### D-V5-6 · Copiar = un solo `INSERT … SELECT` atómico en M-09
La copia se implementa en `base_datos/repositorios/catalogo_repositorio.py` (es quien ya conoce las columnas del catálogo y traduce el error de «migración pendiente», código 42703), como **una sola sentencia** `INSERT INTO rutas_guardadas (…) SELECT …, :usuario_id, 'privada', id FROM rutas_guardadas WHERE id = :id AND visibilidad = 'publica'`:
- Copia: `nombre, origen, destino, presupuesto, intereses, resumen, paradas, descripcion, duracion_dias, categoria, region`. Fija: `usuario_id` = quien copia, `visibilidad = 'privada'`, `ruta_origen_id` = id de la original. `autor_id` queda vacío (la copia es privada; si algún día se publica, el script de publicar asigna autor explícitamente, como hoy).
- Una sola sentencia = todo o nada: si falla, **no existe copia parcial** (RF-16, CA-07.3) y la original jamás se escribe (RF-14).
- Si la fila no existe o no es pública → 0 filas → «no encontrada» (mismo trato para privada e inexistente, como ya hace el detalle).
- Copiar dos veces la misma ruta crea **dos copias independientes** (CA-07.4): no hay deduplicación.
- La validación de datos (CA-07.2) se hace **antes**, en el servicio, leyendo el detalle con el `obtener_publica` que ya existe: nombre/origen/destino con texto y `paradas` como lista de objetos con nombre; si algo no cumple, se rechaza y no se crea nada.
- El modelo `RutaGuardada` **no se toca** (misma decisión que en v0.4.0: las columnas del catálogo viven en SQL propio para no romper v1 antes de migrar).

### D-V5-7 · El endpoint de copiar reutiliza la sesión y el CSRF que ya existen
- `POST /v2/descubrir/rutas/<id>/copiar` en el blueprint de Descubrir (M-01), con el servicio inyectable desde `registrar_v2` igual que hoy se inyecta `Catalogo`.
- Sin sesión (`usuario_de_sesion()` de `v2/interfaz/rutas_guardadas.py`) → `respuesta_sin_sesion()`: **401** con `requiere_sesion=true` y el mensaje de iniciar sesión (RF-15, CA-08.1). El dueño sale **solo** de la sesión, nunca del cuerpo de la petición.
- CSRF con el patrón vigente: la página de Descubrir asegura el token `planear_v2_csrf` en sesión (como ya hacen las páginas de Planear y de rutas guardadas), lo pasa a la plantilla y el JS lo manda en la cabecera `X-RutaMX-CSRF`; si no coincide → 403. Sin esto, el POST nuevo sería el único sin protección del proyecto.

## 3. Orden, tiempos y cortes (clase de 90 min)

Bloques del plan de incrementos: implementación → pruebas → integración. Tiempos orientativos (la clase dura 90 min, dato de Angel en la bitácora 02):

| Bloque | Módulos | Tiempo sugerido |
|---|---|---|
| 0. Decisiones | Aprobar sección 2 y esta tabla | 5 min |
| 1. Implementación + pruebas por módulo | M1 (10 min) → M2 (15 min) → M3 (10 min) → M4 (15 min) → M5 (10 min) → M6 (10 min) | 70 min |
| 2. Integración y cierre | M7: regresión completa, bitácoras, evidencias, reporte y tag | 15 min |

**Orden de corte si el tiempo no alcanza** (el del plan de incrementos, sec. 3): primero cae **M6 (mapa, RF-11/12, Baja)**, después **M3 (preferencias, RF-31/32)**. RF-34 no se corta: sale casi gratis dentro de M1/M2 (es el mensaje de `no_soportada` actualizado). Lo que se corte se registra como pendiente con destino (reporte, sección 7, y bitácora 02), **nunca se declara hecho**. M7 no se recorta: sin regresión ni reporte no hay cierre, aunque un módulo quede fuera.

## 4. Módulos de trabajo

### M1 · M-07 Adaptador de IA: las 5 intenciones de D-05
**RF:** 27, 29, 31 y 34 (contrato); apoya 18 (cierre). **Archivos:** `v2/integracion/adaptador_ia.py`; pruebas en `v2/tests/test_adaptador_ia.py`.

1. Ampliar `_SISTEMA_MODIFICACION`: las acciones permitidas pasan a ser `agregar_parada`, `eliminar_parada`, `reordenar_paradas`, `cambiar_preferencias`, `aclarar` y `no_soportada`, con el JSON exacto de cada una (D-V5-3), la orden de usar los nombres exactos de la ruta adjunta para eliminar/reordenar, y la prohibición de siempre (no inventar lugares, coordenadas, precios ni una ruta nueva).
2. Ampliar `_modificacion()` con validación estricta por acción (lista cerrada de campos; cualquier campo extra o tipo incorrecto → `ErrorValidacion(ERROR_RESPUESTA)`, como hoy):
   - `eliminar_parada`: `nombre` (texto) **o** `posicion` (entero ≥ 0, no booleano); exactamente uno.
   - `reordenar_paradas`: `orden` = lista de textos no vacía, sin duplicados.
   - `cambiar_preferencias`: `duracion_dias` (entero positivo, reutilizar `validar_entero_positivo`) y/o `intereses` (reutilizar `validar_lista_de_textos`, máx. 10); al menos uno presente.
3. Sin cambios en `AdaptadorSimulado`: las pruebas le pasan las acciones nuevas por su lista `modificaciones`, como hoy.
4. **Pruebas (CP-27/29/31/34, lado contrato):** cada acción nueva válida se normaliza; variantes inválidas (ambos identificadores, posición negativa o booleana, orden vacío o con duplicados, preferencias vacías o con campos ajenos, duración cero) → respuesta inválida; `no_soportada` y `aclarar` siguen intactas.
5. Commit: `[V2] feat(RF-27): contrato de eliminar, reordenar y preferencias en M-07`.

### M2 · M-05 Gestor + M-04 Orquestador: eliminar y reordenar (y el aviso de RF-34)
**RF:** 27, 28, 29, 30, 34; cierra evidencia de 24 y 37 para estas operaciones. **Archivos:** `v2/negocio/gestor_rutas.py`, `v2/negocio/orquestador.py`; pruebas en `v2/tests/test_gestor_rutas.py` y `v2/tests/test_orquestador.py`.

1. `GestorRutas.eliminar_parada(nombre=None, posicion=None, confirmaciones=())` sobre `aplicar()`:
   - Por posición (desde 1 en M-05): fuera de rango → `ErrorValidacion`, ruta intacta.
   - Por nombre: comparación normalizada (sin mayúsculas/acentos extremos: `strip` + `casefold`); 0 coincidencias → error «no existe esa parada» (CA-14.2); más de 1 coincidencia → error que pide precisar cuál (apoya CA-17.4).
   - Si el nombre coincide con el **origen o el destino** → se impide con mensaje claro (CA-14.4): origen y destino no son paradas y no se eliminan.
   - Eliminar la última parada es válido: la ruta puede quedar sin paradas (RF-22). Las demás paradas conservan su orden relativo (CA-14.1, RF-28).
2. `GestorRutas.reordenar_paradas(orden, confirmaciones=())` sobre `aplicar()`:
   - `orden` debe ser exactamente el mismo conjunto de nombres actuales (comparación normalizada, con multiplicidad); si falta o sobra un nombre → error «no se pudo identificar» (CA-15.2), orden intacto.
   - Con 0 o 1 paradas, o si el orden pedido es el actual → **sin cambios**: el método devuelve la ruta tal cual y el Orquestador responde informando que no hay otro orden posible (CA-15.4), sin pasar por validación geográfica innecesaria.
3. Orquestador `_modificar()`: despachar las acciones nuevas a los métodos del Gestor con el ayudante de confirmaciones de D-V5-4; la vista ya devuelve `ruta` e `itinerario` actualizados, que es lo que muestran RF-28 y RF-30 (la pantalla de Planear ya pinta la vista que devuelve el servidor; verificar que no haga falta tocar `planear_ia.js`, y si hace falta, cambio mínimo).
4. **RF-34:** actualizar el mensaje de `no_soportada` en `_modificar()` al nuevo conjunto soportado, p. ej.: «Esa acción no está disponible. Sí puedes crear una ruta, agregar o eliminar paradas, reordenarlas y cambiar la duración o el tipo de lugares.» La ruta no cambia (CA-18.1, CA-18.2). CA-18.3 ya lo cubre `aclarar`; CA-18.4 queda como limitación registrada (sección 1).
5. **Pruebas (CP-27, CP-28, CP-29, CP-30, CP-34):** en el Gestor — eliminar por nombre y por posición, parada inexistente, origen/destino protegidos, eliminar la última, reordenar válido, nombre ajeno, una sola parada, fallo del verificador a mitad de la operación → la ruta queda **exactamente igual** (atomicidad, CA-14.3/CA-15.3). En el Orquestador (con `AdaptadorSimulado`) — flujo completo por chat de cada operación, itinerario actualizado en la vista, `no_soportada` con el mensaje nuevo y ruta intacta, y aclaración previa reutilizando el mecanismo de `_aclaracion` que ya existe.
6. Commits: `[V2] feat(RF-27): eliminar parada en M-05 y despacho en M-04` · `[V2] feat(RF-29): reordenar paradas en M-05 y M-04` · `[V2] feat(RF-34): aviso de acción no soportada con las operaciones vigentes`.

### M3 · Preferencias por chat (duración y tipo de lugares)
**RF:** 31, 32; cierra evidencia de 18/24/37 para preferencias. **Archivos:** `v2/negocio/orquestador.py` (solo el despacho de `cambiar_preferencias`); pruebas en `v2/tests/test_orquestador.py`.

1. Implementar el flujo de D-V5-5 en `_modificar()`: validar → comparar con lo vigente (CA-16.4) → `generar_ruta` con los datos mezclados → mismas comprobaciones de fidelidad que en `procesar()` → `_aceptar(..., origen="modificar")`.
2. La vista resultante muestra la ruta y el itinerario nuevos (RF-32) y `resumen_chat()` los resume, como en crear/agregar.
3. **Pruebas (CP-31, CP-32):** cambiar solo duración, solo intereses y ambos; valor inválido (duración 0 o texto, intereses que no son lista) → pide valor válido y nada cambia (CA-16.2); la IA lanza error o devuelve propuesta que no respeta lo pedido → error seguro, ruta **y** datos anteriores intactos (CA-16.3); mismo valor que el vigente → no se llama a `generar_ruta` (probar con el simulado sin respuestas de generación) y el itinerario queda igual (CA-16.4).
4. Commit: `[V2] feat(RF-31): cambiar duración e intereses por chat regenerando la propuesta`.

### M4 · Copiar rutas públicas: repositorio y servicio
**RF:** 13, 14, 16. **Archivos:** `base_datos/repositorios/catalogo_repositorio.py`, **nuevo** `v2/negocio/copia_rutas.py`; pruebas en `base_datos/tests/test_catalogo_repositorio.py` (o nuevo `base_datos/tests/test_copiar_ruta.py`) y **nuevo** `v2/tests/test_copia_rutas.py`.

1. `catalogo_repositorio.copiar_publica(ruta_id, usuario_id)` según D-V5-6: valida que ambos id sean enteros válidos, ejecuta el `INSERT … SELECT … RETURNING id` en la sesión propia de siempre (`_abrir_sesion`), commit; 0 filas → `None`; error de columna inexistente → `ErrorMigracionPendiente` (reutilizar `_traducir`); cualquier otro fallo → `ErrorRepositorio("No se pudo copiar la ruta.")` tras rollback. Actualizar el docstring del módulo («solo lectura» → consulta **y copia** del catálogo).
2. Servicio `CopiaRutas` (M-05) con repositorio inyectable, patrón `GuardadoRutas`/`Catalogo`: `copiar(ruta_id, usuario_id)` → valida ids; lee el detalle con `obtener_publica`; si es `None` → `ErrorCopia("No se encontró la ruta.")`; valida los datos copiables (CA-07.2); llama a `copiar_publica`; si devuelve `None` (dejó de ser pública entre la lectura y la copia) → mismo «no se encontró»; excepciones → `ErrorCopia("No se pudo copiar la ruta. Intenta de nuevo.")` sin filtrar detalles internos. Devuelve `{"id": <id de la copia>, "nombre": <nombre>}`.
3. **Pruebas (CP-13, CP-14, CP-16):** con sesión falsa (patrón de las pruebas actuales del catálogo) — la sentencia lleva `visibilidad = 'publica'` como condición, `ruta_origen_id` = id original y el `usuario_id` del que copia; con PostgreSQL desechable si está disponible (integración, se omiten sin `RUTAMX_TEST_DB_URL`, como las 34 actuales) — copiar crea una fila nueva privada del usuario correcto, la original queda **byte a byte igual**, copiar dos veces crea dos copias, copiar una privada o inexistente no crea nada, y un fallo forzado a mitad no deja fila parcial. En el servicio — ruta con datos inválidos (nombre vacío, paradas que no son lista) → rechazo sin llamar a copiar (CA-07.2).
4. Commit: `[V2] feat(RF-13): copiar ruta pública en M-09 con servicio de copia en M-05`.

### M5 · Copiar: endpoint, botón y sesión
**RF:** 13, 15 (y la parte visible de 16). **Archivos:** `v2/interfaz/rutas_descubrir.py`, `v2/__init__.py`, `v2/templates/descubrir.html`, `v2/static/descubrir.js`; pruebas en `v2/tests/test_interfaz_descubrir.py` y `v2/tests/test_pantalla_descubrir.py`. Leer antes la bitácora 05 (efectos protegidos).

1. `registrar_descubrir(app, *, catalogo=None, copia=None)` y `registrar_v2` inyecta `CopiaRutas()` compartido, como hace con `Catalogo` y `GuardadoRutas`.
2. `POST /v2/descubrir/rutas/<ruta_id>/copiar`: id con el mismo formato que el detalle (400 si no); CSRF según D-V5-7 (403); sin sesión → `respuesta_sin_sesion()` (401, RF-15); éxito → **201** `{"copia": {"id": …, "nombre": …}, "mensaje": "Ruta copiada a tus rutas."}`; no encontrada → 404 con el mismo mensaje del detalle; datos inválidos → 400; fallo del servicio o migración pendiente → 503 con mensaje seguro (RF-16).
3. Plantilla: el `GET /v2/descubrir` asegura el token CSRF en sesión y lo expone a la plantilla (meta o atributo `data-csrf`, patrón de las otras pantallas).
4. JS del detalle: botón **«Copiar a mis rutas»** dentro del diálogo de detalle; al copiar muestra el resultado en el mismo `data-detalle-estado`: éxito → mensaje + enlace a `/v2/rutas`; 401 → «Inicia sesión para copiar esta ruta» + enlace a la página principal (donde vive el login de v1); error → el mensaje seguro del servidor. Mantener el descarte de respuestas tardías que ya usa el detalle (`consultaDetalle`).
5. **(Estirable, CA-08.4)** Guardar el id pendiente en `sessionStorage` al recibir 401 y, al volver a Descubrir con sesión, reabrir ese detalle con el botón visible. Solo si M1–M4 van en tiempo; si se hace, se prueba; si no, se registra como parcial.
6. **Pruebas (CP-13, CP-15, CP-16):** endpoint con servicio falso — anónimo → 401 y el servicio **no** es llamado; con sesión → 201 y el dueño es el de la sesión aunque el cuerpo mande otro id; CSRF incorrecto → 403; id inválido → 400; servicio que lanza error → 503 sin copia. Render: la plantilla real incluye el botón de copiar y el token (patrón de `test_pantalla_descubrir.py`; no ejecuta JavaScript).
7. Commit: `[V2] feat(RF-13): endpoint y botón para copiar rutas públicas con sesión`.

### M6 · Mapa en el detalle de Descubrir
**RF:** 11, 12; cierra la vista de mapa de RF-43. **Archivos:** `base_datos/repositorios/catalogo_repositorio.py` (solo `obtener_publica`), `v2/negocio/catalogo.py` (solo `detalle`), `v2/templates/descubrir.html`, `v2/static/descubrir.js`, `v2/static/descubrir.css`; pruebas en `base_datos/tests/test_catalogo_repositorio.py`, `v2/tests/test_catalogo.py`, `v2/tests/test_interfaz_descubrir.py` y `v2/tests/test_pantalla_descubrir.py`. Leer antes la bitácora 05.

1. `obtener_publica` agrega `r.resumen` a su SELECT (nada más cambia).
2. `Catalogo.detalle` construye `puntos_mapa` y `puntos_omitidos` según D-V5-2 (origen, paradas en orden, destino; validación de coordenadas con las mismas reglas del Gestor), sin exponer el `resumen` crudo ni ningún dato privado: la proyección cerrada de `_vista` se mantiene.
3. Plantilla/JS: en el diálogo de detalle, contenedor del mapa (`data-mapa`, alto fijo en CSS). Al mostrar un detalle con `puntos_mapa` no vacío: cargar Leaflet 1.9.4 (CSS + JS, **mismas URLs de CDN que `v1/templates/base.html`**) de forma diferida; crear el mapa, marcadores en orden con el nombre de cada punto, línea que los une y encuadre a los puntos; **llamar a `invalidateSize()` después de abrir el diálogo** (dentro de un `<dialog>` el mapa nace con tamaño 0 y sin esto se ve gris). Al cerrar el diálogo, destruir el mapa para no duplicarlo en el siguiente detalle.
4. RF-12 (CA-06.3): si Leaflet no carga (`window.L` indefinido tras el intento, o error al crear el mapa) → aviso visible «El mapa no pudo cargarse. El resto de la ruta sigue disponible.» y el detalle (descripción, paradas, copiar) se muestra completo igual. Si `puntos_mapa` viene vacío → mismo aviso con el motivo de datos («Esta ruta no tiene ubicaciones para mostrar en el mapa.»).
5. **Pruebas (CP-11, CP-12):** servicio — detalle con coordenadas completas devuelve los puntos en orden origen→paradas→destino; parada con coordenadas inválidas o sin `lugar` se omite y se cuenta (CA-06.2/06.4); ruta sin `resumen` v2 devuelve `puntos_mapa` vacío sin fallar; la proyección sigue sin traer `usuario_id` ni `resumen`. Render — la plantilla incluye el contenedor del mapa y las URLs de Leaflet de v1 (sin ejecutar JavaScript, como las pruebas actuales de pantalla). La verificación visual real queda para el bloque de navegador de M7 si se puede; si no, *sin verificar* en el reporte.
6. Commit: `[V2] feat(RF-11): mapa del recorrido en el detalle de Descubrir con Leaflet`.

### M7 · Cierre: regresión, bitácoras, evidencias, reporte por clase y tag
**RF/RNF:** RNF-25, RNF-26, RNF-27, RNF-28, RNF-29, RNF-30, RNF-31, RNF-33 (con la evidencia que de verdad exista). **Archivos:** bitácoras, `documentacion/Evidencia_v0.5.0_pruebas.md`, `documentacion/Reporte_Avance_Incremento_v0.5.0.md` + su PDF, tag `v0.5.0`.

1. **Regresión completa** con el comando de los reportes anteriores (sin red, datos ficticios):
   ```sh
   env -u RUTAMX_TEST_DB_URL PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest base_datos/tests v2/tests -q -p no:cacheprovider -k 'not test_navegador_escritorio_y_movil'
   ```
   Base conocida (2026-11-17): **529 passed, 34 skipped, 1 deselected**. Al cerrar v0.5.0: **0 fallos** y más aprobadas que la base (las nuevas de M1–M6); las omitidas solo pueden ser las de integración sin PostgreSQL. Si hay un PostgreSQL local desechable disponible (como el que levantó Angel el 2026-11-17), correr también con `RUTAMX_TEST_DB_URL` y registrar ambas corridas en la evidencia.
2. **Matriz RF → prueba de este incremento** (RNF-33 y RNF-26): tabla CP-11 a CP-16, CP-27 a CP-32 y CP-34 con el archivo y nombre de cada prueba; va en la evidencia y se resume en el reporte. Ningún RF del incremento queda sin al menos un caso (RNF-26).
3. **Bitácoras:** `01` — lo construido en v0.5.0 con archivos y pruebas; `02` — **borrar** lo que ya se hizo (copiar en M-09, cierre de RF-18/24/37, etc.) y dejar solo pendientes reales (migración en Supabase, navegador, IA real, CA-18.4, CA-08.4 si quedó parcial, limpieza del camino de agregar en M-04/M-05); `03` — decisiones D-V5-1 a D-V5-7 con su porqué.
4. **Evidencia:** `documentacion/Evidencia_v0.5.0_pruebas.md` con los comandos exactos, las corridas (inicial y final si hubo fallos corregidos, como en v0.4.0) y qué no se ejecutó. Si se corrió PostgreSQL local, evidencia aparte como en v0.4.0 (`Evidencia_v0.5.0_postgres.md`).
5. **Reporte de esta clase** (sección 5 de este plan): un solo archivo para este incremento, `documentacion/Reporte_Avance_Incremento_v0.5.0.md`, y su PDF con el script del repo:
   ```sh
   venv/bin/python scripts/md_a_pdf.py documentacion/Reporte_Avance_Incremento_v0.5.0.md documentacion/Reporte_Avance_Incremento_v0.5.0.pdf
   ```
6. **Tag y push (los hace Angel, como en los incrementos anteriores; las IA no suben a remotos):**
   ```sh
   git tag -a v0.5.0 -m "[V2] Incremento v0.5.0: edición por chat, copiar rutas, mapa y cierre"
   git push origin main
   git push origin v0.5.0
   ```
   Comprobar con `git ls-remote --tags origin` y registrar el hash en el reporte y la bitácora.
7. Si sobra tiempo dentro del bloque: verificación en navegador de `/v2/descubrir` (detalle con mapa y botón de copiar) y `/v2/planear` (eliminar/reordenar/preferencias) en 1280×900 y 375×812, anotando fecha y resultado en la evidencia. Es lo único que puede mover RF-06 y RF-08 (JavaScript de Descubrir) de *programados* a probados; si no se hace, quedan como están y el reporte lo dice.

## 5. El reporte final: uno por clase, con la sintaxis del PDF de v0.4.0

**Regla de Angel (2026-11-19): un reporte por clase/incremento, sin juntarlos.** Ya existen `Reporte_Avance_Incremento_v0.2.0`, `v0.3.0` y `v0.4.0` por separado; el de esta clase es **solo** `Reporte_Avance_Incremento_v0.5.0.md` (+ PDF). No se reescriben ni se fusionan los anteriores; a lo sumo se citan sus cifras como «reporte anterior».

El reporte sigue **exactamente** la estructura del PDF subido (`Reporte_Avance_Incremento_v0.4.0.pdf`, sesión del 2026-11-17), con los datos reales de esta sesión (sin inventar horas ni cifras: las horas salen del historial de Git y del registro del equipo; las cifras, de las corridas de pruebas de M7):

- **Encabezado:** `# [V2] Reporte de avance: cuarto incremento de clase, v0.5.0 (Editar por chat, copiar rutas públicas, mapa y cierre)` + fecha (19 de noviembre de 2026, CDMX), equipo, objetivo de la sesión, alcance del informe y fuentes. Aclarar la numeración como en el PDF anterior: v0.5.0 es el **incremento 5 del plan general y el cuarto de los cuatro incrementos de clase**, porque v0.1.0 corresponde al repositorio M-09 previo.
- **Qué contiene este reporte:** tabla `Lo que se pide | Dónde está | Respuesta corta` con las 4 filas de siempre (incrementos desarrollados → sec. 1; planeado contra real en tiempos → sec. 2; porcentaje de avance → sec. 3; diferencias con la app del incremento anterior → sec. 4).
- **1. Incrementos desarrollados:** tabla de las 5 versiones con estado al 19 de noviembre + tabla `Trabajo realizado hoy` (`Actividad | Resultado | Evidencia`) solo con lo de **esta** clase.
- **2. Planeado contra real: tiempos:** 2.1 Comparación (planeado: una clase de 90 min; real: solo lo registrado), 2.2 Hitos comprobables de hoy (horas de los commits), 2.3 Alcance planeado contra real. Sin duraciones inventadas.
- **3. Porcentaje de avance del proyecto:** con la fórmula de siempre (RF completos y probados en simulación / 44). Cifras esperadas si se completan los 13 RF y se cierran los parciales, **a confirmar con la evidencia real antes de escribirlas**:
  - Antes (reporte v0.4.0): **25 de 44 = 56.8%** completos; 2 solo programados (RF-06, RF-08); 4 parciales (RF-18, 24, 37, 43); 13 sin iniciar.
  - Solo con los 13 del v0.5.0: 38 de 44 = **86.4%**.
  - Contando además el cierre de RF-18, RF-24, RF-37 y RF-43: **42 de 44 = 95.5%**, con RF-06 y RF-08 como únicos no completos (2 programados, 4.5%), salvo que la verificación en navegador de M7.7 los mueva.
  - 3.1 Evolución del avance (tabla por corte, cada fila suma 44), 3.2 Estado de los requerimientos (categorías con sus RF), 3.3 RNF (conteo conservador: solo los probados; base anterior 5 de 33 = 15.2%), 3.4 Resultados de pruebas de hoy (corridas inicial/final, con y sin PostgreSQL si aplica).
- **4. Diferencias con la app del incremento anterior:** 4.1 funcionalidad de v0.5.0 respecto a v0.4.0, 4.2 qué cambió hoy respecto al estado recibido, 4.3 efecto para el usuario y límites.
- **5. Hallazgos y correcciones de hoy:** tabla `Hallazgo | Causa | Corrección` con lo que la revisión cruzada del par encontró de verdad (si no hubo, se dice).
- **6. Decisiones aplicadas en la sesión:** D-V5-1 a D-V5-7 tal como se aplicaron (y cualquier cambio aprobado por Angel sobre la marcha).
- **7. Lo que falta comprobar:** tabla `Pendiente actual | Condición para cerrarlo` — como mínimo: migración y publicación en Supabase, navegador de escritorio y móvil, login real, IA real de Planear, regresión de v1, P-01/P-03 ante el profesor, CA-18.4 y lo que haya quedado cortado en la sección 3.
- **8. Evidencias y reproducción:** archivos de evidencia de `documentacion/` y los comandos exactos con su resultado documentado.
- **9. Siguiente paso:** preparar la exposición (2 clases), y los pendientes reales de la sección 7 en orden.

## 6. Lo que NO se hace en este incremento

- No se agrega función de **publicar** rutas en la app (P-01 sigue ante el profesor; publicar es el script administrativo de v0.4.0).
- No se implementa **eliminar rutas guardadas** (ningún RF lo pide; no confundir con eliminar **paradas**, que sí es RF-27).
- No se ejecuta la migración en Supabase ni se publican rutas reales; eso lo hace Angel con respaldo, fuera de esta clase.
- No se prueba con IA real (sin llave válida; todo va con `AdaptadorSimulado`, como en los incrementos anteriores) ni con login real si no hay sesión disponible: se declara *sin verificar*.
- No se tocan `v1/`, el modelo `RutaGuardada`, ni los efectos visuales protegidos de la bitácora 05.
- Ningún módulo cortado se declara hecho: se registra como pendiente con destino (reporte sec. 7 + bitácora 02).

## 7. Verificación de este plan contra sus fuentes

- Los 13 RF coinciden en las tres fuentes: resumen del plan (sec. 1), inventario A2 y ficha del incremento 5 en `plan_incrementos.md` y en `A3_Propuesta_Incrementos.md`: **RF-11, 12, 13, 14, 15, 16, 27, 28, 29, 30, 31, 32, 34**. HU: 06, 07, 08, 14, 15, 16, 18. RNF de la ficha: 13, 23, 25, 26, 27, 28, 29, 30, 31, 33. CA a probar: 28.
- El estado de partida coincide con el reporte de v0.4.0 y la bitácora 02 al 2026-11-17: 25 de 44 RF completos en simulación (56.8%), suite base 529/34/1 sin PostgreSQL y 563/0/1 con PostgreSQL local, tags v0.2.0–v0.4.0 publicados, v0.5.0 «No iniciado», M-09 sin operación de copiar, y `GestorRutas.puntos_mapa()` ya existente para la vista de mapa de la ruta de Planear (la vista que faltaba era la del **detalle de Descubrir**, que es la de RF-11).
