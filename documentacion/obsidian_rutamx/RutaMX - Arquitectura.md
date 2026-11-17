---
tags: [proyecto, rutamx, arquitectura]
---
# Arquitectura

Parte de [[RutaMX]]. Es una aplicación [[Flask]] con el patrón *application factory* (`create_app` en `v1/__init__.py`), en v1 un solo blueprint (`main_bp`) y la lógica separada en servicios; v2 registra los suyos (`planear_v2`, `rutas_guardadas_v2` y `descubrir_v2`) y `run.py` compone las dos versiones en la misma app llamando a `registrar_v2(app)`. El frontend es HTML con plantillas Jinja y JavaScript puro; no hay React ni paso de compilación.

## Estructura del repo (desde 2026-10-29)
Una sola app de [[Flask]] (`run.py`), repartida en tres carpetas con reglas de importación. Programado (reorganización hecha el 2026-10-29 y mezclada en `main` el 2026-11-03).
- `v1/`: solo lo de la versión 1 (código, plantillas, estáticos, `tests/` y `scripts/` que usan el geocodificador de v1).
- `v2/`: lo nuevo (descubrir y planear con ayuda de IA). Hoy tiene los módulos de Planear con IA (v0.2.0), guardar y recuperar rutas (v0.3.0) y Descubrir (v0.4.0), descritos en las secciones de más abajo.
- `base_datos/`: modelos (`modelos.py`), conexión (`conexion.py`), `repositorios/`, `migraciones/`, `scripts/` de datos y `catalogo_valores.py`. Es de las dos versiones.
- Reglas: `base_datos` no importa de v1 ni de v2; v1 importa solo de `base_datos`; v2 importa de `base_datos` y, de v1, solo la autenticación; v1 nunca importa de v2.
- Cambios a la base: solo compatibles hacia atrás, probados en una copia, con pruebas de v1 y v2 antes de aplicar.
- El módulo M-09 (repositorio de rutas) está en `base_datos/repositorios/` (ver la sección siguiente); su plan entregado está en `documentacion/` del repo (ver [[RutaMX - Decisiones]]).

## [V2] M-09 Repositorio de rutas (2026-11-03)
Programado y probado en simulación (2026-11-03): tres de sus cinco operaciones, en `base_datos/repositorios/rutas_repositorio.py`. Trabaja con las columnas actuales de `RutaGuardada`; no modifica `modelos.py` ni `v1/`.

| Función | Qué hace |
|---|---|
| `crear_ruta(datos, usuario_id)` | Valida, guarda en una transacción propia y devuelve un diccionario con `id` y `usuario_id`. El dueño sale del argumento, no de los datos. |
| `obtener_ruta(ruta_id, usuario_id)` | Busca por `id` **y** dueño en la misma consulta; devuelve el diccionario o `None` si no existe o es ajena. |
| `listar_rutas_de_usuario(usuario_id)` | Solo las rutas del dueño, la más reciente primero; lista vacía si no tiene. |
| `ErrorRepositorio` | Única excepción del módulo; todo fallo sale con ella, sin SQL ni detalles internos, y se conserva la causa. |

Cada operación abre una `Session` propia de [[SQLAlchemy]] en vez de usar `db.session`, para no confirmar cambios pendientes ajenos. Límite: no ve datos sin confirmar de otra sesión ni se puede revertir desde una transacción exterior, algo que M-05 deberá resolver si orquesta varias escrituras.

Las pruebas viven en `base_datos/tests/`. Su `conftest.py` usa solo la base de `RUTAMX_TEST_DB_URL`: exige host local y un nombre que termine en `_prueba` o `_test`, y sin la variable omite las pruebas de integración con aviso. Nunca carga el `.env` ni usa [[Supabase y Postgres|Supabase]] de respaldo.

## Flujo de una ruta
```
Navegador (main.js, form.js, map.js)
   │  POST /api/ruta   GET /api/sugerencias
   ▼
routes.py ──> route_service ──> OSRM (ruta real, distancia, tiempo, geometría)
   │              └─ si falla: estimación en línea recta
   ├──> maps_service ──> tabla destinos ──> Nominatim (si no está en la base)
   ├──> ai_service ──> filtra destinos cerca de la carretera y los reparte por tramos
   ├──> gasto_service ──> gasto máximo recomendado
   └──> Supabase (Postgres): estados, destinos, usuarios, rutas_guardadas
```

## Backend (`v1/`)
| Archivo | Qué hace |
|---|---|
| `__init__.py` | Application factory; carga `.env` y la configuración. |
| `routes.py` | Los 15 endpoints (ver abajo). |
| `base_datos/modelos.py` | Modelos `Estado`, `Destino`, `Usuario`, `RutaGuardada` (antes `app/models.py`). |
| `services/route_service.py` | Ruta real con OSRM: distancia, tiempo y geometría para calcular el "corredor". |
| `services/maps_service.py` | Geocodificación (tabla `destinos`, luego Nominatim, luego un catálogo demo de 18 ciudades). |
| `services/ai_service.py` | El motor de sugerencias (el archivo más grande; su tamaño está en [[RutaMX]]): filtra por cercanía y por intereses, reparte por franjas de horas y asigna destinos reales a cada tramo. |
| `services/gasto_service.py` | Gasolina, casetas, imprevistos, comidas y hospedaje. |
| `services/llm_provider.py` | Única parte que conoce a Claude, OpenAI y Gemini. |
| `services/ia_destinos_service.py` | Crea destinos nuevos con la respuesta de la IA. |
| `services/planificador_ia_service.py` | Orquesta el chat "Planear con IA". |
| `services/auth_service.py` | Registro e inicio de sesión (nombre + apellido + PIN). |
| `services/pdf_service.py` | Itinerario en PDF. |
| `services/navegacion_service.py` | Enlace de Google Maps y QR. |

## Endpoints
- Página: `GET /`
- Ruta y sugerencias: `POST /api/ruta`, `GET /api/sugerencias`, `GET /api/destinos/nombres` (autocompletado)
- IA: `GET /api/ia/disponible`, `POST /api/ia/planear`
- Cuentas: `POST /api/auth/registro`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/yo`
- Rutas guardadas: `GET /api/rutas`, `POST /api/rutas`
- Itinerario: `POST /api/itinerario/pdf`, `POST /api/itinerario/enlaces`
- Gasto: `POST /api/gasto`

## Base de datos (Supabase / Postgres)
- `estados`: los 32 estados (nombre y clave).
- `destinos`: nombre, estado, tipo, coordenadas, descripción, `intereses` (arreglo), población, `gastronomia_destacada`, `reconocimiento_gastronomico` y `fuente` (`curada` o `ia_generada`).
- `usuarios`: nombre, apellido, clave normalizada única y `pin_hash`.
- `rutas_guardadas`: origen, destino, intereses, `resumen` y `paradas` en JSONB, ligada a `usuario_id`. Las siete columnas del catálogo (v0.4.0) están programadas en una migración que se ensayó en un PostgreSQL local desechable (2026-11-17) y no se ha ejecutado en Supabase.
- Se usa la conexión del *Session pooler* de Supabase, no la directa (esa solo resuelve por IPv6).

## Idea central en v1: la IA nunca elige el lugar
En la v1, la IA solo decide el **propósito** de cada tramo y la **hora** conveniente. Un algoritmo determinista de `ai_service.py` (`asignar_paradas_a_objetivos`) escoge el destino real de la tabla. La misma lógica sirve con y sin IA: sin IA, `generar_objetivos_automaticos` produce los objetivos con una fórmula. Razones en [[RutaMX - Decisiones]]. En v2 (Planear con IA) el flujo es otro: la IA sí propone nombres de lugares, pero cada uno lo verifica M-08 contra Nominatim y M-05 valida la regla D-03 antes de aceptar la ruta; sin esa verificación la propuesta no se presenta como válida.

## Frontend (`v1/static/` y `v1/templates/`)
- `base.html` más parciales por sección: hero, mapa, descubre, itinerario, planificador de IA, navbar e iconos.
- JS por responsabilidad: `main.js` (flujo principal, el más grande), `form.js`, `map.js`, `auth.js`, `avatar.js`, `navbar.js`, `tope.js`, `planificador_ia.js`, `bubble_picker.js`.
- `js/efectos/`: 11 módulos de efectos visuales protegidos (contador, gooey, spotlight, fondo, píldora, grid reveal, orbe…).
- `js/vendor/`: copias de Blobatar 2.7, no se editan.
- CSS: `styles.css` (diseño), `efectos.css` (efectos) y dos de Blobatar. Tamaños en [[RutaMX]].
- Los 26 iconos son SVG a medida en un solo sprite (`partials/iconos_sprite.html`).

## Scripts de datos (`base_datos/scripts/`)
Cargan y corrigen la base de destinos: dos lotes de `seed_destinos`, `verify_coordenadas.py` (contra Nominatim; vive en `v1/scripts/`), tres correcciones de intereses, dos de población (Censo INEGI 2020), la marca de gastronomía destacada (en `v1/scripts/`) y la migración `agregar_usuario_id.py` (en `base_datos/migraciones/`). Hay una copia de seguridad de "comida" en `base_datos/scripts/datos/`.

## Pruebas
`v1/tests/` con pruebas de servicios, rutas, gasto, planificador IA, destinos IA y autenticación (cifras en [[RutaMX]]). Las de IA usan un proveedor simulado.

## [V2] Incremento v0.2.0: Planear con IA (2026-11-10)
Programado y probado en simulación (2026-11-10); sin verificar en navegador ni con una IA real. Cifras de pruebas en [[RutaMX]].
- **M-11 `v2/utilerias.py`:** errores con mensaje seguro (cualquier excepción ajena se oculta tras un mensaje genérico) y validación de texto, enteros y listas con topes técnicos. No importa de otro módulo de v2.
- **M-07 `v2/integracion/adaptador_ia.py`:** contrato `extraer_datos` y `generar_ruta`. `AdaptadorAnthropic` encapsula el SDK y se configura con `IA_V2_PROVEEDOR`, `IA_V2_MODELO` y `ANTHROPIC_API_KEY`; no carga `.env` ni activa simulación si falta configuración. `AdaptadorSimulado` recibe respuestas explícitas para las pruebas. Un solo proveedor real implementado.
- **M-05 `v2/negocio/gestor_rutas.py`:** la ruta estructurada vive en memoria de la conversación y es la única fuente. Aplica la regla D-03 completa (origen y destino identificables, secuencia sin repetidas no confirmadas, lugares con identificador y coordenadas válidas) y los cambios son atómicos: si algo falla, la ruta anterior queda igual. La fuente geográfica se inyecta; sin verificador la propuesta no se presenta como válida.
- **M-08 `v2/integracion/verificador_geografico.py`:** `VerificadorNominatim.verificar(nombre)` devuelve `{id, latitud, longitud}`, `None` o falla con mensaje seguro. Una petición por segundo, caché por instancia, sin reintentos y búsqueda limitada a México. «Oaxaca» resuelve al estado, no a la ciudad. Se agregó fuera de la tabla del plan.
- **M-04 `v2/negocio/orquestador.py`:** coordina M-07 y M-05 por conversación. Pide solo los datos obligatorios que faltan, conserva lo ya extraído si falla generar o validar y permite reintentar sin volver a pedirlo; las confirmaciones de D-03 las pide y resuelve él.
- **M-03 `v2/interfaz/rutas_planear.py`, plantilla y estáticos:** pantalla `/v2/planear` en dos columnas en escritorio y pestañas en móvil, con confirmaciones en `<dialog>`. La conversación vive en el servidor, ligada a una cookie firmada, con tope de conversaciones, caducidad por inactividad y token CSRF. Reutiliza estáticos y efectos de v1 sin editarlos. Sin configuración de IA muestra «Planear con IA no está configurado».
- **Límite:** la conversación y la ruta sin guardar viven en la memoria de un solo proceso; guardar rutas se agregó en el v0.3.0 (sección siguiente).
- **Demostración:** `scripts/demo_planear_v2.py` levanta un servidor aparte con una IA de reglas fijas y una franja visible de modo demostración; la app normal no lo usa.

## [V2] Incremento v0.3.0: guardar y recuperar rutas (2026-11-12)
Programado y probado en simulación (2026-11-12); la persistencia real, el login real y el navegador están sin verificar (2026-11-12). Cifras de pruebas en [[RutaMX]].
- **M-09 `actualizar_ruta`:** reemplaza los datos de la misma fila solo si es del dueño, con bloqueo de fila, rollback y la versión anterior intacta si falla. El repositorio ya tiene cuatro operaciones; falta copiar.
- **M-07 `interpretar_modificacion`:** devuelve agregar parada (con posición opcional), pedir aclaración o acción no soportada.
- **M-05 `agregar_parada`:** pasa por la misma validación D-03 y es atómica; hoy el orquestador agrega la parada por otro camino (`proponer`), así que hay dos caminos por unificar.
- **M-04:** con una ruta aceptada interpreta el mensaje como modificación; una instrucción ambigua devuelve la pregunta y el siguiente mensaje la resuelve. Las propuestas pendientes recuerdan si nacieron de crear o de modificar.
- **Guardado `v2/negocio/guardado_rutas.py`:** sin migración de esquema; la ruta estructurada va dentro de `resumen` bajo `rutamx_v2` (versión 1) y se escriben `origen` y `destino` por compatibilidad con v1. Una ruta sin ese contenedor se informa como incompatible.
- **Endpoints de v2:** `POST /v2/planear/guardar`, `POST /v2/planear/abrir`, `GET /v2/rutas` y `GET /v2/rutas/lista` (`v2/interfaz/rutas_planear.py` y `rutas_guardadas.py`, este último M-06). El dueño sale de `session["usuario_id"]` (la sesión de v1, M-10, solo se lee); sin sesión responden 401. Abrir crea una conversación nueva y revalida la ruta con M-04 y M-05; usa un adaptador envoltorio de un solo uso para instalar la ruta guardada sin agregar al orquestador un método público de instalación.
- **Pantalla:** botón «Guardar ruta», `<dialog>` que pide iniciar sesión en otra pestaña y «Mis rutas guardadas»; reutiliza los estáticos de v1 sin editarlos.
- **Único cambio en v1** (autorizado por Angel el 2026-11-12): `abrirRutaGuardada` redirige a `/v2/rutas` cuando el resumen trae `rutamx_v2`.

## [V2] Incremento v0.4.0: Descubrir (2026-11-12)
Programado y probado en simulación (2026-11-12) con repositorio y sesión falsos; el SQL real, la migración y la publicación se ensayaron en un PostgreSQL local desechable (2026-11-17), sin verificar en Supabase ni en navegador. Cifras en [[RutaMX]].
- **`base_datos/catalogo_valores.py`:** categorías (Playa, Cultural, Naturaleza, Gastronomía, Pueblo Mágico), regiones (Noroeste, Noreste, Occidente, Centro, Sureste), visibilidades y límites. Es una propuesta del equipo (P-03 abierta).
- **Migración `base_datos/migraciones/agregar_columnas_catalogo.py`:** agrega a `rutas_guardadas` las siete columnas autorizadas el 2026-11-03 (`descripcion`, `duracion_dias`, `categoria`, `region`, `visibilidad`, `ruta_origen_id`, `autor_id`) con `IF NOT EXISTS`, en una transacción. Ensayada dos veces en PostgreSQL local, sin error y conservando las filas anteriores como privadas (2026-11-17); **no se ha ejecutado en Supabase.** El modelo `RutaGuardada` no cambia, para que v1 no se rompa antes de migrar.
- **Repositorio `catalogo_repositorio.py`:** SQL propio con parámetros enlazados; siempre filtra `visibilidad = 'publica'`; nunca devuelve el usuario, su hash ni el PIN; sin las columnas lanza «migración pendiente».
- **M-02 `v2/negocio/catalogo.py`:** valida filtros y arma lista y detalle; una ruta privada da el mismo error que una inexistente.
- **M-01 `v2/interfaz/rutas_descubrir.py`, plantilla y estáticos:** `GET /v2/descubrir`, `GET /v2/descubrir/rutas` y `GET /v2/descubrir/rutas/<id>`, abiertos a visitantes; errores 400, 404 y 503 con mensaje seguro. La pantalla actualiza la lista al cambiar los filtros, descarta respuestas tardías y muestra el detalle en `<dialog>`.
- **Script `base_datos/scripts/publicar_ruta.py`:** administrativo, no es función de la app; marca una ruta como pública o privada, con autor explícito (`--rutamx` deja el autor vacío).

## Módulos propuestos (documento de requerimientos v2.0)
Es una **propuesta del documento**; hoy están programados M-01, M-02, M-03, M-04, M-05, M-06, M-07, M-08, M-09 (parcial: falta copiar) y M-11 (secciones anteriores); M-10 reutiliza la sesión de v1. Separa presentación, negocio y datos, y deja Descubrir desacoplado de Planear con Ayuda IA:
- **Presentación:** M-01 Interfaz de Descubrir, M-03 Interfaz de Planear con Ayuda IA, M-06 Interfaz de rutas guardadas.
- **Negocio:** M-02 Catálogo de rutas públicas, M-04 Orquestador de planeación (interpreta el chat y valida la respuesta de la IA), M-05 Gestor de rutas (único lugar donde se crean, copian, modifican y guardan rutas; aplica los cambios completos o no los aplica).
- **Servicios externos:** M-07 Adaptador del servicio de IA, M-08 Adaptador de mapas y geocodificación.
- **Datos y seguridad:** M-09 Repositorio de rutas, M-10 Control de acceso (reutiliza la autenticación existente).
- **Utilerías:** M-11 validador de entradas, manejador de errores, configuración e indicador de carga.
El módulo más difícil de probar es M-04, por la IA; se prueba con un adaptador de IA simulado. Ver [[Pruebas con simulación]].

### Diseño modular (PDF de diseño modular y arquitectura inicial, 2026-10-13)
También es **propuesta, no código**. Resumen de lo que agrega al documento v2.0 (detalle y tablas en el PDF; ver [[RutaMX]]):
- **Criterios de partida:** separación en capas (RNF-16), Descubrir y Planear sin depender directamente entre sí (RNF-20), IA y mapas detrás de adaptadores (RNF-21), lógica de rutas centralizada en el Gestor de rutas (RNF-22) y la ruta estructurada como fuente única de verdad (D-08 / RF-43).
- **Los 11 módulos son responsabilidades lógicas dentro de una sola aplicación,** no microservicios ni once carpetas de primer nivel. Cada módulo lista sus entradas, salidas y requerimientos (RF) relacionados; los RF se agrupan por funcionalidad para no duplicar las 44 filas de la matriz de trazabilidad.
- **Flujos y reglas:**
  - Explorar rutas: M-01 → M-02 → M-09; la interfaz no accede directo a los datos.
  - Copiar una ruta pública: M-01 → M-10 → M-05 → M-09; se valida la autenticación antes de guardar una copia independiente.
  - Planear con IA: M-03 → M-04 → M-07 → M-04 → M-05; la IA propone o interpreta y el Gestor valida antes de cambiar la ruta.
  - Guardar: solo usuarios autenticados y completo o nada; consultar guardadas: solo las de la cuenta.
- **Modelo conceptual mínimo:** *Ruta* (identificador, nombre, origen, destino, duración, paradas ordenadas, intereses o tipo de lugares, autor, propietario, visibilidad privada o pública) y *Lugar* (identificador geográfico, nombre, coordenadas válidas). La conversación no se guarda (D-09).
- **Regla de integración con el repo:** las funciones nuevas se integran en el proyecto RutaMX existente reutilizando su estructura, autenticación, configuración y persistencia; solo se crea una carpeta o archivo nuevo si no hay una responsabilidad equivalente. No se crea un login nuevo ni una segunda raíz `src/`.
- **Riesgos que marca (nivel Alto):** M-04 (lenguaje natural y comportamiento no determinista de la IA), M-05 (concentra 23 RF y puede crecer demasiado; se subdividiría internamente), consistencia de estado entre chat, itinerario y mapa, y el tiempo (8 semanas, 2 integrantes). Medio: M-11 puede volverse un "cajón de sastre"; medio-alto: servicios externos con latencia o fallos.
- **Alternativa más simple** si 11 módulos son demasiados: 7 bloques (Descubrir = M-01 + M-02; Planeación IA = M-03 + M-04; Gestor de rutas = M-05; Rutas guardadas = M-06; Integraciones = M-07 + M-08; Persistencia y acceso = M-09 + M-10; Compartido = M-11).
- **Pendientes que condicionan el diseño:** P-01 (cómo se marca una ruta como pública), P-02 (proveedor de mapas y credenciales; decide si HU-06 / M-08 se implementa o se recorta) y P-03 (valores de categoría y región). Ver [[RutaMX - Decisiones]].

Tecnologías en [[RutaMX - Tecnologías]].
