# Lo que falta — RutaMX

Última actualización: 2026-11-19

Este archivo es solo lo que **todavía no está hecho**. En cuanto algo se
termina, se mueve a `01_LO_QUE_YA_ESTA_HECHO.md` (con su explicación) y
se borra de aquí — nunca queda un "✅ Ya implementado" aquí adentro. Ver
la regla completa en `AGENTS.md`.

## Por planear / decidir con Angel (pedido explícito)

- **Re-etiquetar la base y agregar restaurantes y hoteles (plan pendiente de Angel, sin pagar nada).** Plan completo en
  [`04_PLAN_RESTAURANTES_Y_HOTELES.md`](04_PLAN_RESTAURANTES_Y_HOTELES.md).
  Orden acordado: (1) revisar las etiquetas del catálogo de destinos con criterios
  comprobables y un reporte que Angel revisa antes de cambiar nada; (2) crear
  la tabla `establecimientos` (restaurantes y hoteles buenos, con cupos según
  el tamaño del lugar, más algunos en carretera con menos prioridad); (3)
  adaptar TODA la app y la IA de "Planear con IA" para que sigan fluyendo igual
  con las tablas nuevas; (4) nueva forma de recomendar (restaurantes primero,
  luego pueblos/ciudades con muy buena comida, marcados claramente). Decisión
  abierta principal: cómo definir "bueno" sin pagar; revisar las condiciones
  de las fuentes comerciales antes de elegir proveedor. La poda de "comida" espera a los restaurantes; se
  conservan los 21 lugares destacados (lista y regla en el plan `04`, copia de
  seguridad en `base_datos/scripts/datos/`). **Falta:**
  revisar las demás etiquetas (cultura, naturaleza, playas, descanso), podar
  "comida" de los 86 lugares no destacados de la copia de 2026-09-19 (recontar antes de aplicar). Esperar a tener
  restaurantes para que "Comer" no quede vacío y el resto del plan.

- **Tiempo de la app vs Google Maps.** León → Cabo San Lucas: la app dice
  ~50 h y Google Maps ~44 h. Causa probable: OSRM (servidor demo) usa
  velocidades genéricas por tipo de vía, más lentas que las autopistas de
  cuota de México. No se pudo verificar contra Google desde el código.
  Opciones: (1) calibrar con un factor de corrección usando el tiempo de
  Google en ~5 rutas reales (hipótesis sin costo por validar; no se midió su precisión); (2) usar la API de
  Google Routes (exacto, pero pide cuenta con tarjeta y key); (3) otro
  servicio gratuito (mismo problema de velocidades genéricas). Se
  recomienda la 1; falta que Angel pase los tiempos de Google.

## Pendientes del rediseño visual

- Revisar con Angel las secciones que siguen sin rediseño fino: modal de "Mis rutas
  guardadas", ventana del chat de IA con sus 2 opciones, y `efectos.css` (los
  efectos ya toman la paleta nueva, pero sus radios y sombras no se afinaron).
- Iconos opcionales que hoy no existen: los 6 intereses de "¿Qué buscas?" (Naturaleza,
  Playas, Pueblos mágicos, Comida, Descanso, Cultura) siguen siendo solo texto.
- El fondo de líneas y la luz de las tarjetas no se han medido en un teléfono real
  (solo emulado a 375 px): medirlo antes de proponer ajustes. La regla protegida solo permite cambiar color y velocidad del fondo; no reducir sus líneas sin nueva decisión de Angel.

## Pendiente marcado en el código (TODOs reales)

- Revisar el comentario `TODO` de `v1/static/js/map.js:4`: aún menciona navegación en vivo propia. El flujo de navegación ya se delegó al enlace/QR de Google Maps; no es una función nueva aprobada.

## Pendientes sueltos de funcionalidad ya implementada

**Del gasto máximo recomendado:**
- Los valores son estimados con supuestos que conviene afinar con viajes
  reales: casetas $1.1/km (promedio: ~$1.5/km en cuota × ~70% del
  trayecto; la fuente da un rango de $1–2/km), rendimiento 13 km/l y
  precio del litro ($25.5 promedio; Magna $23.8 verificada en sep 2026;
  Premium $29 es aproximada, sin verificar). Los precios de gasolina
  cambian: actualizar `PRECIOS_LITRO` en `gasto_service.py`.
- La estimación de casetas con IA nunca se ha probado con una key real
  (solo con el proveedor mockeado). Falta ver que la respuesta sea
  razonable para rutas conocidas.
- Decidir si el chat de v1 debe heredar también coche, gasolina y cantidades manuales del formulario. Hoy usa personas y hora de salida de la conversación; esos datos sí afectan el gasto de cada opción.

Estos NO son features sin hacer — son detalles/riesgos que quedaron
abiertos dentro de features que ya están terminadas y documentadas en
`01_LO_QUE_YA_ESTA_HECHO.md`. Se listan aquí porque siguen siendo trabajo
real por hacer, no porque la feature esté incompleta.

**De cuentas de usuario:**
- El test `test_registrar_usuario_duplicado_por_acentos_y_mayusculas` usa el nombre "Ángel
  Mata" y falla porque esa cuenta real ya existe; hay que cambiarlo a un nombre ficticio.

**De la interfaz (navbar, secciones y avatar):**
- El navbar compacto, el tope entre secciones y la portada solo se probaron con mouse/rueda y
  ventanas emuladas: falta probarlos en un teléfono real y con trackpad (momentum). El
  seguimiento de ojos del avatar no corre sin mouse fino ni con "reducir movimiento" (lo decide
  el paquete).
- Dos medidas del CSS son aproximadas y hay que ajustarlas si cambian el formulario o el navbar:
  `--tope-superior` (54px, alto del navbar compacto) y los 760px del espacio bajo el hero sin
  resultados (recuadro ~694 + navbar + holgura), ambas en `styles.css`.

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

**De "Planear con IA" de v1 (modal del formulario; distinto de `/v2/planear`):**
- Los prompts nuevos (reglas de tramos, dormir después de las 8 pm, ventana
  de 30/20 min, sin preguntar por presupuesto ni horas máximas) solo se han
  probado con el proveedor mockeado. Falta probarlos con una key real y ver
  que el modelo los siga bien (el servidor ya corrige lo que se salga de las
  reglas).
- "Planear con IA" no permite elegir el propósito de cada tramo (eso es solo
  del flujo manual).
- **El chat en sí no se ha podido probar de punta a punta con una IA
  real todavía.** Se probó con una key presente en el entorno de
  desarrollo, pero resultó inválida para uso directo del SDK (error 401
  "API key is invalid") — el manejo de error funcionó perfecto (mensaje
  claro al usuario, no rompe nada), pero falta la prueba real con una key
  de Anthropic/OpenAI/Gemini genuina para confirmar que el chat completo
  (preguntas, quick-replies, las dos opciones finales) funciona de
  extremo a extremo.
- Los tests de `planificador_ia_service.py` y de la asignación de
  objetivos están con el proveedor mockeado (correcto para no gastar
  tokens en cada `pytest`), pero por lo mismo no prueban el prompt real
  contra un modelo de verdad — si el modelo devuelve algo fuera de lo
  esperado en producción, revisar primero el prompt en `llm_provider.py`.

## Recomendaciones y tarjetas: pendientes que salieron hoy

- **Pocos destinos a lo largo de algunas carreteras.** En CDMX → Oaxaca casi no hay lugares entre
  Tehuacán (3 h) y Oaxaca, así que de las 5 franjas de horas solo se llenan ~3. Se resuelve con más
  destinos en la base (plan `04`), no con código.
- **El chat de "Planear con IA" no aplica el filtro estricto de intereses** (`planificador_ia_service.py`
  llama a `obtener_pool_con_horas` sin `intereses`; los intereses salen de la conversación). Decidir con
  Angel si debe respetarlo igual que el formulario.
- **Código sin uso:** `_linea_de_tiempo`, `_elegir_con_distinguidos` y `MAX_DISTINGUIDOS_AL_FRENTE` en
  `ai_service.py` ya no los usa el flujo principal (quedan con sus tests). Borrarlos cuando Angel confirme
  que la regla nueva de franjas es la definitiva.
- **Fallback demo** (`_sugerir_desde_demo`, solo si la base de datos no responde) no aplica el filtro
  estricto de intereses.
- El grafo de conocimiento (`graphify-out/`, ignorado por git) está desactualizado: correr `/graphify update`.

## Efectos visuales: verificaciones pendientes

- El orbe de "Planear con IA" (`planificador_ia.js`) se probó solo en el estado de
  carga de sugerencias; falta verlo en el chat con una API key real conectada.
- Los efectos no se han probado con lector de pantalla ni con teclado en todos los
  flujos (el contador expone su texto real y el PIN tiene etiquetas por casilla, pero
  falta una pasada de accesibilidad).
- El menú gooey y la píldora comparten las secciones fijas de `secciones.js`
  (Inicio, Ruta, Descubre, Itinerario); si se agrega otra sección a la página, hay que
  añadirla ahí.

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

## Pendientes del documento de requerimientos v2.0 (confirmar con el cliente)

- **P-01:** ningún RF describe cómo se marca una ruta como pública (el perfil «Creador de rutas» y RNF-15 lo suponen).
- **P-02:** el equipo la resolvió el 2026-11-19 con Leaflet y OpenStreetMap, como v1 (D-V5-1); no hay respuesta del profesor. Si el profesor pide otro proveedor, solo cambia la carga de `descubrir.js`.
- **P-03:** definir los valores de categoría y región de los filtros (RF-05) al cargar las rutas públicas.
- Roberto debe validar el documento v2.0 (rol de validador) antes de entregarlo.

## Persistencia del apartado nuevo (práctica de persistencia, 2026-10-15)

Diseño listo en `documentacion/RutaMx_Persistencia_y_Diseno_de_BD.pdf`; el código de M-09 con cuatro operaciones (crear, obtener, listar y actualizar) ya existe (ver `01`), pero no hay cambios en la base de datos todavía (columnas nuevas y migración siguen sin hacerse).

- Roberto debe revisar el diseño de persistencia (rol de revisor técnico) y se corrige lo que encuentre.
- Angel **aprobó** (2026-11-03) agregar las columnas nuevas a `rutas_guardadas` (`descripcion`,
  `duracion_dias`, `categoria`, `region`, `visibilidad`, `ruta_origen_id`, `autor_id`), pero **no se ha ejecutado**: es una tabla de la v1.
  Hace falta un script de migración con `ALTER TABLE` (SQLAlchemy `create_all` no modifica tablas existentes),
  probado primero en una copia y con respaldo previo.
- [V2] Ejecutar con PostgreSQL local las 5 integraciones nuevas de `copiar_publica`, omitidas sin base.
- Cerrar P-01 y P-03 (ver abajo): de ellos depende cómo se publica una ruta y qué valores tienen categoría y región.

## Después de la reorganización y del plan de M-09 (2026-10-29)

- Confirmar que Supabase vuelve a responder. En la reorganización del 2026-10-29 se registraron `FATAL: tenant/user ... not found`, 24 pruebas fallidas y 42 con error (ver 01); no se volvió a consultar la base en esta auditoría. Revisar el panel, sin tratar aquel resultado histórico como una medición actual.
- Roberto debe hacer pull de `main` para recibir la estructura nueva (`app/` ahora es `v1/`); la rama `reorganizacion` ya se mezcló y se borró (2026-11-03).
- [V2] Regresión de la v1 contra una base aislada y verificación en navegador de M-09: sin verificar (2026-11-03).
- [V2] Quedan para otro incremento T-04/T-05, autor y visibilidad, copia y regresión de v1. Siguen P-01 y P-03.

## [V2] Después del plan de incrementos (2026-11-05)

- [V2] Incremento v0.2.0 (2026-11-10): falta comprobar M-07 con credenciales válidas de un proveedor real y el flujo integrado en navegador. Chromium no pudo arrancar por sandbox de macOS (Permission denied 1100); falta verificar visualmente 1280×900 y 375×812, errores, confirmaciones y efectos. El caso opcional está en `v2/tests/test_interfaz_planear.py::test_navegador_escritorio_y_movil`. RF-18, RF-24 y RF-37 quedan en cobertura parcial hasta el v0.5.0.

- [V2] Pasar cuánto trabaja el equipo fuera de clase (la clase dura 1 h 30 min, dato de Angel del 2026-11-10; 4 clases de trabajo y 2 de exposición): con eso se calibra el tamaño de los incrementos. El tamaño actual (12, 9, 10 y 13 RF) es estimación, no medición.
- [V2] Consultar con el profesor o el cliente P-01 (cómo se publica una ruta), P-02 (proveedor de mapas) y P-03 (valores de categoría y región). P-01 y P-03 bloquean el catálogo del v0.4.0; P-02 decide el mapa del v0.5.0.
- [V2] Revisar a ojo `/v2/planear` con `scripts/demo_planear_v2.py` (escritorio y 375 px) y anotar la fecha: sin verificar (2026-11-10).
- [V2] Conectar la IA real (falta `ANTHROPIC_API_KEY` e `IA_V2_MODELO`; Angel no tiene llave): RF-21 y RF-36 siguen probados solo en simulación, sin verificar (2026-11-10).
- [V2] Antes de publicar, exigir una `SECRET_KEY` real (config.py usa un valor de desarrollo) y poner tope propio a `/v2/planear/reiniciar`.
- [V2] Cerrar la integración del v0.2.0: revisión visual, regresión aislada de v1/base_datos y tag tras las verificaciones. Sus módulos y demostración están publicados en `origin/main` hasta `407a14e` (verificado el 2026-11-10 con `git status -sb`, `git rev-parse` y `git ls-remote origin refs/heads/main`); no repetir su implementación.
- [V2] Eliminar rutas guardadas no está en la v2.0 y no se planea (no confundir con eliminar paradas).
- [V2] Sigue pendiente ejecutar el cambio de esquema de las siete columnas que Angel autorizó el 2026-11-03 (script, prueba en copia y respaldo). Cualquier otro cambio de esquema necesita nueva aprobación.

- [V2] Regresión integrada de la app compartida con v2: v1 sigue sin regresión verificada al corte de 2026-11-10 porque su suite escribe en Supabase; las 19 pruebas de integración de base_datos se omiten sin PostgreSQL desechable (`RUTAMX_TEST_DB_URL`).

## [V2] Después del v0.3.0 (2026-11-12)

- [V2] Verificar en navegador el v0.3.0 (guardar, aviso de iniciar sesión, pregunta de aclaración y pantalla `/v2/rutas`, en 1280×900 y 375×812): sin verificar (2026-11-12). Playwright no está instalado y Chromium no pudo arrancar en el v0.2.0 por el sandbox de macOS.
- [V2] Correr contra un PostgreSQL desechable las pruebas de integración de `actualizar_ruta` (7 nuevas, omitidas con las otras de `base_datos/tests`): sin él, la persistencia y el rollback de actualizar están sin verificar (2026-11-12). El sistema rechazó el comando que lo levantaba y no se buscó otra vía.
- [V2] Probar guardar y abrir con una sesión real de v1 (login real): hoy la sesión se simula escribiendo `usuario_id` en la cookie firmada; sin verificar (2026-11-12).
- [V2] Abrir en «Mis rutas» de v1 una ruta guardada por v2: Angel autorizó (2026-11-12) un cambio mínimo en v1 (`abrirRutaGuardada` en `v1/static/js/main.js`) que redirige a `/v2/rutas` cuando `resumen.rutamx_v2` existe. Programado; solo se comprobó la sintaxis con `node --check`. Sin verificar (2026-11-12): el clic real en «Mis rutas» de v1 en navegador y que las rutas de v1 sigan abriéndose igual.
- [V2] Limpieza de M-04/M-05: `GestorRutas.agregar_parada` está probada, pero el orquestador agrega la parada armando la propuesta y pasándola por `proponer`; unificar para no tener dos caminos. Además, instalar una ruta guardada usa hoy un adaptador envoltorio en `rutas_planear.py`; un método público de M-04 sería más limpio.
- [V2] Limitación actual: mientras hay una aclaración pendiente, el siguiente mensaje se toma como su respuesta; para cambiar de viaje hay que reiniciar la conversación.
- [V2] Cerrar el v0.3.0: regresión de v1 y `base_datos` contra bases aisladas. El commit `[V2]` del incremento es `f7cbf8e`, y el tag `v0.3.0` está en GitHub desde el 2026-11-17 (puesto sin esperar esa regresión).

## [V2] Después del v0.4.0 (2026-11-12)

- [V2] Aprobar con el profesor P-01 y P-03: la propuesta del equipo (ruta pública = `visibilidad = 'publica'`, marcada solo con `base_datos/scripts/publicar_ruta.py`, y las listas de categorías y regiones de `base_datos/catalogo_valores.py`) no está aprobada por el profesor. Si cambia, hay que ajustar `catalogo_valores.py`, la migración y el script.
- [V2] Ejecutar la migración `base_datos/migraciones/agregar_columnas_catalogo.py` en Supabase (la corre Angel, con respaldo previo y regresión de v1 y v2). Ya se ensayó en un PostgreSQL local desechable (2026-11-17: dos corridas sin error, 7 columnas, filas previas conservadas; ver `Evidencia_v0.4.0_migracion.md`), pero en la base real sigue sin ejecutarse. Sin ejecutarla, `/v2/descubrir/rutas` responde «migración pendiente».
- [V2] Publicar al menos una ruta (con el script) en la base real para que el catálogo no esté vacío, después de migrar. Con una ruta ficticia en la base local desechable ya funcionó (2026-11-17); rutas públicas en otras bases: sin verificar.
- [V2] Concurrencia del `FOR UPDATE` de `publicar_ruta.py` y SQL contra la base real (Supabase): el SQL (`jsonb_array_length`, `FOR UPDATE`, `#>>`, `ILIKE ... ESCAPE`) ya se ejecutó en PostgreSQL local con resultado correcto (2026-11-17); no se probó contención ni Supabase.
- [V2] Verificar en navegador `/v2/descubrir` (1280×900 y 375×812): filtros, reinicio (se corrigió a `setTimeout` por orden de eventos, sin ejecutar en navegador), detalle y descarte de respuestas tardías: sin verificar (2026-11-12).
- [V2] Notas de la revisión de M-02: una parada mal formada hace fallar todo el detalle («No se pudo leer la ruta»), y el servicio limita la duración a 1 a 60 días mientras el repositorio acepta cualquier entero positivo; el script de publicar no impide una duración mayor de 60.
- [V2] Cerrar el v0.4.0: commit `[V2]` (hecho el 2026-11-13: código en `4204079` y bitácoras, reporte y borradores en `2fef30d`), migración en Supabase y regresión de v1. El push de `main` (`e3aff8c`) y los tags `v0.2.0`, `v0.3.0` y `v0.4.0` los hizo Angel el 2026-11-17 y se comprobaron con `git ls-remote --tags origin`.
- [V2] Fragilidad de orden en las pruebas de integración: `base_datos/tests/test_catalogo_repositorio.py::test_integracion_sin_migracion_da_migracion_pendiente` supone que la tabla `rutas_guardadas` no está migrada y pasa solo porque corre primero en una base nueva (el mismo caso con `esquema_anterior` lo haría independiente del orden). Las 7 pruebas que fallaban con PostgreSQL ya se corrigieron el 2026-11-17 (ver `01`); con una base nueva la suite da `563 passed, 0 failed, 0 skipped`, sin ella `529 passed, 34 skipped`.
- [V2] Regresión de v1: bloqueada, sin verificar (2026-11-17). `v1/tests/test_auth_service.py` usa `create_app('development')` con `instance/config.py` y no hay una guardia que fuerce una base local. Antes de correrla hace falta esa guardia (cambio en pruebas de v1, que Angel debe aprobar) o una base aislada.
- [V2] Navegador de `/v2/descubrir`: no consta que se haya resuelto el rechazo de Chromium del 2026-11-10 (`Permission denied (1100)`); no se reintentó el 2026-11-17. La sección «Condiciones para completar» de `documentacion/Evidencia_v0.4.0_navegador.md` quedó con el plan viejo (PostgreSQL propio en 55434, «paso 5»): ahora bastaría la base `rutamx_navegador_prueba` en el servidor local (55433), forzando la URI efectiva antes de `db.init_app`. Para probarlo con datos hace falta una base local: levantar otro PostgreSQL con `initdb` y `pg_ctl` (el sistema le rechazó ese comando a este equipo, así que lo corre Angel con `!`).
- [V2] v0.5.0 (2026-11-19): sigue sin verificar con una IA real que el modelo devuelva los JSON nuevos de eliminar, reordenar y cambiar preferencias.
- [V2] Cerrar el v0.5.0: Angel hace los commits (sugeridos en la bitácora 01, un `[V2]` por módulo), el tag `v0.5.0` y el push, y anota el hash aquí y en el reporte. Aún no hay commits ni tag del incremento.
- [V2] CA-18.4 (limitación, 2026-11-19): M-07 interpreta una operación por mensaje; una solicitud con varias operaciones no ejecuta las soportadas y salta las demás. No es un defecto escondido: está declarado en el reporte.
- [V2] RF-06, RF-08, RF-11 y RF-12 siguen «programados» y RF-43 «parcial» hasta que se revise el navegador (son el único camino de 39 a 42 de 44 RF). RNF-13 (HTTPS) y RNF-23 (navegadores): sin verificar (2026-11-19).

- [V2] v0.5.0, copia desde Descubrir: verificar en navegador de escritorio y 375 px el botón, errores, doble clic y el flujo anónimo → login real → volver al mismo detalle → copiar (CA-08.4). Bloqueo documentado de Chromium; se requiere revisión manual de Angel, sin verificar (2026-11-19). La simulación de DOM/fetch y las sesiones de prueba no verifican ese uso real.
- [V2] Mapa del detalle de Descubrir (v0.5.0, 2026-11-19): sin verificar en navegador real (Chromium bloqueado, no se reintentó). Falta que Angel confirme a mano en `/v2/descubrir` el mapa en 1280×900 y 375×812 (marcadores, línea, popups, encuadre y que no se vea gris), el aviso con la red cortada y el aviso de ubicaciones omitidas. P-02 (proveedor de mapas) se resolvió por decisión del equipo con Leaflet y OSM, sin respuesta del profesor.
