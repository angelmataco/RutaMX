---
tags: [proyecto, rutamx, decisiones]
---
# Decisiones

Parte de [[RutaMX]]. El proyecto guarda el detalle en `bitacora_proyecto/03_DECISIONES_Y_NOTAS.md`; aquí va lo esencial.

## Producto
- **Cuentas sin correo** (nombre + apellido + PIN de 4 dígitos): por ser proyecto escolar, pedir correo era de más. Consecuencias aceptadas: no hay "recuperar PIN" y dos personas con el mismo nombre exacto no pueden registrarse ambas. El PIN se guarda con hash. Si algún día se publica la app, ahí sí convendría agregar correo.
- **Solo guardar pide login**: calcular rutas y ver sugerencias no tiene nada que proteger.
- **Gasto automático**: comidas y noches se deducen solas del viaje; los ajustes manuales quedan en un desplegable opcional. Las casetas se estiman con IA o con un promedio de $1.1/km, porque la API SAKBÉ de INEGI pedía registrar un token y se prefirió no registrarse en nada.
- **Tramos automáticos de ~3 h** en vez de preguntar "horas máximas de manejo": una pregunta menos en el formulario. Por eso un viaje largo sale con 9 o 10 tramos; no se cambió por ahora.
- **El filtro "¿Qué buscas?" manda** sobre estrellas, cercanía y propósito. Solo lo pisa un tramo que el usuario personalizó a mano.
- **Estrella por franja de horas** (hasta 5 por ruta) y 5 recomendadas visibles; el tope de 2 estrellas se abandonó a pedido de Angel.
- **Cerca del destino sí se sugiere, cerca del origen no.** Histórico: la regla original descartaba lo que quedaba a menos de 1 h de manejo del origen. Vigente (2026-11-13): el viaje se divide en tramos de ~3 h y solo se recomiendan lugares entre 30 min después de salir y 20 min antes de llegar.
- **Nada con teclado** en los campos numéricos. Histórico: presupuesto y horas máximas de manejo se elegían con burbujas; ambos se retiraron del formulario (el servidor calcula el gasto y los tramos son automáticos). Vigente (2026-11-13): la hora de salida se elige con un selector tipo rueda.

## IA
- **En v1, la IA nunca elige el lugar**, solo propósito y hora. En v2 (Planear con IA) la IA sí propone nombres de lugares, pero cada uno lo verifica M-08 contra Nominatim y M-05 valida la regla D-03 antes de aceptar la ruta (ver [[RutaMX - Arquitectura]]). Cualquier modelo puede inventar un sitio o una coordenada, así que en v1 el destino real sale siempre de la tabla con un algoritmo determinista; en v2 no hay esa tabla en el flujo: la ruta solo se acepta con lo que verifica M-08. Las coordenadas de destinos nuevos se obtienen de Nominatim, nunca de la IA; si no aparece, se descarta el intento.
- **Multi-proveedor en v1** (Claude, OpenAI o Gemini): Roberto trabaja con [[Codex CLI|Codex]] y puede tener otra key. Solo `llm_provider.py` conoce a los proveedores de v1. En v2, el adaptador `v2/integracion/adaptador_ia.py` (M-07) es el único que conoce al proveedor y hoy solo implementa Anthropic.
- **Misma lógica con y sin IA (flujo manual y chat de v1)**: el reparto de paradas es el mismo, así que agregar "hora de salida" al formulario manual mejora las sugerencias de cualquiera.
- **Regla de mantenimiento**: cuando cambian las reglas de la app, hay que reflejarlas en los prompts y también hacerlas cumplir en el servidor, porque el modelo puede equivocarse.

## Frontend
- **Sin librerías ni compilación**: los efectos de rare-ui se reescribieron en JS/CSS puro en lugar de instalar React. `<dialog>` nativo en vez de librería de modales.
- **Efectos protegidos**: no se quitan ni se reemplazan (ver `05_EFECTOS_VISUALES_PROTEGIDOS.md` del proyecto). El step-player se eliminó a pedido de Angel y no se reintroduce. En la app no hay emojis, solo los iconos a medida.
- **Rediseño por remapeo de tokens**: se dejaron los nombres de variables CSS y solo cambiaron sus valores, para no tocar los efectos que las leen.
- **Fondo animado barato**: se volvió al código original del componente cambiando solo color y velocidad; animar opacidad por curva rompía el pintado.
- **Tope entre secciones con JS**, no con `scroll-snap`: el de CSS atraía demasiado y no dejaba leer.
- **Navbar fijo con espaciador**, no `sticky`, para evitar saltos de contenido al encogerse.
- **Blobatar copiado a `vendor/`** porque no hay [[Node.js y npm|npm]] ni bundler.

## Datos
- **Nunca inventar datos geográficos**: coordenadas verificadas contra Nominatim, población del Censo INEGI 2020.
- **Gastronomía destacada de forma aditiva**: se agregó una marca (UNESCO, Michelin, 50 Best) en lugar de quitar la etiqueta "comida", para que los tramos de "Comer" no queden vacíos. La poda espera a que existan los restaurantes. Sesgo conocido: 23 de 32 estados quedan sin ningún lugar destacado.
- **Las calificaciones de Tripadvisor y Google no se pueden guardar ni son gratis**, y OpenStreetMap está mapeado de forma desigual (León 51 restaurantes, Oaxaca 369), así que contar restaurantes no mide la gastronomía.
- **Prioridad a lo distinguido solo si la ruta pasa a menos de 40 km**: sin eso, Guadalajara (a 145 km) subía al primer lugar de León → Monterrey.

## Proceso
- **La bitácora se sube a GitHub** y `CLAUDE.md` / `AGENTS.md` obligan a leerla antes de tocar código, para que Angel (Claude) y Roberto ([[Codex CLI|Codex]]) no se pisen ni dupliquen trabajo.
- **Verificar en la app corriendo**, no solo con `pytest`: varios bugs solo se vieron en vivo.

## Estructura del repo y plan de M-09 (2026-10-29)
- **Una sola app, tres carpetas** (`v1/`, `v2/`, `base_datos/`) para no mezclar lo ya hecho con lo nuevo y saber dónde se modifica cada cosa. Reglas de importación en [[RutaMX - Arquitectura]]. Descartado (2026-10-29): dos apps separadas.
- **La base es independiente de las versiones** y solo cambia de forma compatible hacia atrás.
- **Plan de implementación de un módulo (clase DASV):** se eligió M-09 (repositorio de rutas) por ser la capa de datos que usan M-05 y M-02; alternativa descartada: empezar por M-05. Plan v1.1 entregado y revisado por Angel y Roberto; no incluye código.
- **Resueltas el 2026-11-03** (sección siguiente): M-09 convive con `guardar_ruta`/`listar_rutas` sin tocarlas; la regla D-03 la aplica M-05; las pruebas usan una base aislada; Angel aprobó las columnas nuevas, aún sin ejecutar.

## [V2] Primer módulo implementado: M-09 (2026-11-03)
- **Alcance reducido a tres operaciones** (crear, obtener, listar) para caber en la práctica. Actualizar y copiar quedan fuera. No se declara terminado el módulo ni cumplidos CA-21.4/D-11.
- **No se toca `modelos.py`:** `autor_id` y `visibilidad` esperan la migración. Angel aprobó el cambio de columnas el 2026-11-03, pero su ejecución se difiere; el dueño es `usuario_id`.
- **Integridad mínima dentro de M-09** (texto obligatorio no vacío, paradas como lista, ids enteros) porque `NOT NULL` no rechaza texto vacío. La validez del itinerario (D-03) sigue siendo de M-05.
- **Salidas:** diccionarios con `id`, nunca objetos ORM; "no encontrada" es `None`. Todo fallo es `ErrorRepositorio`.
- **Sesión propia por operación** en vez de `db.session` (ver [[RutaMX - Arquitectura]]).
- **Base de prueba:** un [[Supabase y Postgres|PostgreSQL]] 16 temporal instalado con Homebrew y creado en una carpeta temporal. Descartado (2026-11-03): [[Docker]], porque su daemon no estaba corriendo y no había imagen descargada. [[SQLite]] tampoco sirve por `ARRAY` y `JSONB`.
- **Estado dicho con la palabra «probado en simulación»** porque no se tocó la base real, aunque las pruebas sí usan un Postgres de verdad.
- **Una sola rama:** `reorganizacion` se mezcló en `main` con avance directo (sin conflictos, con el visto bueno de Roberto) y se borró, porque la rama aparte volvía invisible lo nuevo en GitHub.
- **Marcador `[V2]`** al inicio de cada commit y de cada entrada nueva de la bitácora, por regla del profesor desde 2026-11-03.
- **Flujo con dos IAs:** [[Codex CLI|Codex]] redacta la orden de implementación y revisa; [[Claude Code]] analiza, programa y prueba; el equipo decide. Codex no modifica código.

## [V2] Plan de incrementos (2026-11-05)
Práctica «plan de incrementos». Angel y Roberto aprobaron el plan el 2026-11-05. Detalle y cifras en [[RutaMX]].
- **Incremento 1 = solo M-09** (tag `v0.1.0`). La v1 es el sitio existente y no cuenta como requerimientos cumplidos; los 44 RF y 33 RNF quedan «Pendiente». Descartado (2026-11-05): contar la v1 como incremento ya hecho.
- **Cuatro incrementos más** (v0.2.0 a v0.5.0), uno por clase de trabajo, porque las clases restantes son 4 de trabajo y 2 de exposición. El v0.5.0 es el que se recorta si falta tiempo. Alternativa guardada: 3 incrementos.
- **Calendario condicionado** (decisión del 2026-11-05): faltaban la duración de cada clase y el trabajo fuera de clase; si el v0.2.0 no cabía en una clase, el plan pasaba a 3 incrementos. Actualización (2026-11-13): una clase dura 1 h 30 min (dato de Angel) y los reportes de avance comparan lo planeado con los minutos reales; el trabajo fuera de clase sigue sin medirse.
- **Limitación de la validación A4 (aceptada):** [[Codex CLI|Codex]] ya había revisado la propuesta, así que no fue una validación con conversación nueva ni totalmente independiente.
- **Cobertura parcial:** RF-18, RF-24 y RF-37 se asignan al v0.2.0 pero se cierran en el v0.5.0.
- **Excepción de prioridad:** se adelanta el flujo de mayor riesgo (Planear con IA) y HU-01 y HU-05 (Alta) quedan en el v0.4.0, después de HU-19 (Media), que es el camino de error de la generación; HU-17 se agrupa en el v0.3.0. El equipo la aceptó.
- **Reparto invertido de la consigna:** [[Claude Code]] hace el análisis y la documentación; [[Codex CLI|Codex]] desarrolla y prueba; cada paso lo revisa la otra IA.
- **Plan en `documentacion/`**, no en `docs/` como decía la consigna.
- **Preguntas abiertas al profesor:** P-01 (cómo se publica una ruta), P-02 (proveedor de mapas) y P-03 (valores de categoría y región).

## [V2] Incremento v0.2.0: Planear con IA (2026-11-10)
Estado de lo construido en [[RutaMX - Arquitectura]]; cifras en [[RutaMX]].
- **M-08 se agregó fuera de la tabla aprobada** por indicación de Angel, porque la tabla del plan no se podía reabrir en marcha; lo revisó [[Codex CLI|Codex]] dentro del paso de la pantalla, sin paso propio.
- **Sin IA real por ahora:** no hay llave ni modelo y no los habrá en este incremento. La pantalla y las pruebas usan IA simulada; la geografía puede usar Nominatim real. Conectar la IA real queda pendiente («sin verificar») y RF-21 y RF-36 no están comprobados con IA real.
- **Sin simulación automática:** si falta configuración la app muestra «Planear con IA no está configurado». Solo la inyección de pruebas del servidor puede mostrar la franja de modo demostración, y solo con `app.testing`. Descartado (2026-11-10): un selector de demostración por petición.
- **Pantalla acordada en un debate** entre las dos IAs (escritorio 60/40, pestañas en móvil, confirmaciones en `<dialog>` donde Escape descarta y nunca confirma); reutiliza los efectos protegidos de v1 sin editarlos.
- **Estado de la conversación en el servidor**, no en el navegador: ligado a una cookie firmada y con tope y caducidad.
- **D-03 en M-05 con la fuente geográfica inyectada**, para poder cambiar de proveedor sin tocar el gestor.

## [V2] Incremento v0.3.0: guardar y recuperar rutas (2026-11-12)
Estado en [[RutaMX - Arquitectura]]; cifras en [[RutaMX]].
- **Guardar sin migración de esquema:** los datos de v2 van dentro de `resumen` (`rutamx_v2`, versión 1), porque M-09 solo persiste las columnas actuales y los cambios a la base deben ser compatibles hacia atrás. Las siete columnas autorizadas el 2026-11-03 siguen sin ejecutarse.
- **Compatibilidad con v1:** v1 lista las rutas de v2 porque comparten tabla y filtro por usuario. Como v2 no guarda distancia ni tiempo, Angel autorizó (2026-11-12) una excepción a la congelación de v1: `abrirRutaGuardada` redirige a `/v2/rutas` (6 líneas, programado, sin verificar en navegador).
- **«Guardar de nuevo actualiza la misma ruta» (D-11) se interpreta así:** se actualiza la misma fila solo si es el mismo usuario y el mismo origen y destino; un viaje distinto crea una ruta nueva. Si el equipo prefiere actualizar siempre, es un cambio de una línea, pero hay que decidirlo.
- **El dueño sale siempre de la sesión**, nunca del cuerpo de la petición; un id inválido cuenta como anónimo.
- **Abrir una ruta guardada** crea una conversación nueva y la revalida con D-03; las confirmaciones se resuelven solas (máximo dos) porque el usuario ya las confirmó al crearla.
- **Aclaración:** la instrucción ambigua se conserva y el siguiente mensaje es su respuesta; para cambiar de tema hay que reiniciar. Es una limitación actual, sin aceptación explícita de Angel.
- **Sin PostgreSQL desechable en esta sesión:** el sistema rechazó el comando que lo levantaba y no se buscó otra vía; las pruebas de integración quedaron omitidas.

## [V2] Incremento v0.4.0: Descubrir (2026-11-12)
Estado en [[RutaMX - Arquitectura]]; cifras en [[RutaMX]].
- **P-01 y P-03 siguen abiertas ante el profesor; el equipo avanzó con una propuesta**, que Angel aprobó al aprobar la tabla de pasos: una ruta es pública solo si su columna `visibilidad` vale `publica`, se marca con un script (el plan no permite asumir una función de publicar) y las listas de categorías y regiones son cortas. No es una respuesta del profesor; si decide otra cosa, hay que ajustar los valores, la migración y el script.
- **El modelo `RutaGuardada` no cambia:** el catálogo usa SQL propio para que v1 no se rompa si la migración no se ha ejecutado; sin ella responde «migración pendiente».
- **La migración no se ejecuta en esta sesión:** la ejecución real queda para Angel, con respaldo y regresión.
- **Autor:** el repositorio no infiere autores al leer; al publicar, el script conserva el autor, o pone al dueño de forma explícita si no hay, y solo `--rutamx` fuerza el autor vacío. Del autor solo se muestra nombre e inicial del apellido.
- **Una ruta no pública se comporta como inexistente** (mismo 404), para no revelar que existe.
- **Reporte de avance en cuatro partes** (por indicación del profesor): incrementos desarrollados, tiempos planeados contra reales (una clase dura 1 h 30 min), un solo porcentaje de avance y diferencias con la app anterior.

## Documento de requerimientos v2.0
Detalle y versiones en [[RutaMX]]; el PDF es la fuente. Las ambigüedades del apartado 10.1 del documento v1.0 se cerraron con sus propias recomendaciones (D-01 a D-14):
- **Filtros:** duración, categoría y región; ningún otro.
- **Datos obligatorios del chat:** origen, destino y duración; los intereses son opcionales.
- **Solo 2 preferencias** (duración y tipo de lugares) y un conjunto cerrado de intenciones: crear ruta, agregar, eliminar, reordenar paradas y cambiar preferencias.
- **Ruta válida:** origen y destino identificables, secuencia coherente y cada lugar con identificador y coordenadas de una fuente geográfica.
- **La ruta estructurada es la fuente única de verdad:** el chat, el itinerario y el mapa se derivan de ella.
- **Solo se guarda la ruta, no la conversación;** guardar de nuevo actualiza la misma ruta, sin historial (el versionado está fuera del alcance).
- **Los criterios de login validan solo el comportamiento de RutaMx:** la autenticación ya existe y no se reconstruye.
- **Nada de funcionalidad nueva:** lo que ningún RF respalda (publicar rutas) se deja como pendiente, no se inventa.

## Diseño modular (2026-10-13)
Del PDF de diseño modular (ver [[RutaMX]] y [[RutaMX - Arquitectura]]):
- **Una sola aplicación modular, sin microservicios:** se conserva RutaMX como una aplicación; los 11 módulos son responsabilidades lógicas.
- **Reutilizar antes de crear:** primero se reutiliza o extiende lo que ya existe (autenticación, persistencia, mapas); solo se agrega un archivo o carpeta si no hay una responsabilidad equivalente.
- **El Gestor de rutas (M-05) es el único punto para crear, copiar, modificar y guardar rutas,** para que Descubrir y Planear no dupliquen lógica; sus cambios son atómicos.
- **Qué falta del diseño** (actualizado 2026-11-13): están programados M-01, M-02, M-03, M-04, M-05, M-06, M-07, M-08 y M-11, y M-09 con 4 de sus 5 operaciones (falta copiar); M-10 reutiliza la sesión de v1 (ver P-01 a P-03 en "Lo que falta y por qué", más abajo y el estado en [[RutaMX - Arquitectura]]).

## Lo que falta y por qué
Del archivo `02_LO_QUE_FALTA.md` del proyecto (conciliado con el código el 2026-11-10 y revisado de nuevo el 2026-11-13, tras los incrementos v0.3.0 y v0.4.0):

### Pendientes grandes
- **Restaurantes y hoteles** (plan en `04_PLAN_RESTAURANTES_Y_HOTELES.md`, parcial: la lectura de reconocimientos y el marcado gastronómico están hechos). Orden acordado: revisar etiquetas de los destinos (369 en el catálogo inicial, cifra histórica) con un reporte que Angel aprueba; crear la tabla `establecimientos` con cupos según el tamaño del lugar; adaptar toda la app y la IA; y una nueva forma de recomendar (restaurantes primero, luego pueblos con muy buena comida). Decisión abierta: cómo definir "bueno" sin pagar.
- **Tiempo vs Google Maps**: la causa probable es que OSRM usa velocidades genéricas más lentas que las autopistas de cuota. Se recomienda calibrar con un factor usando ~5 rutas reales; falta que Angel pase los tiempos de Google.
- **Desplegar** en Render o Railway.

### Sin probar con una IA real
- El chat completo, la generación de destinos y la estimación de casetas con IA solo se probaron con un proveedor simulado. Una key disponible dio error 401.
- Los modelos de OpenAI y Gemini y sus llamadas se escribieron con el patrón típico del SDK, sin poder probarlas.

### Detalles abiertos
- Pocos destinos en algunas carreteras (CDMX → Oaxaca casi no tiene nada entre Tehuacán y Oaxaca). Se resuelve con más datos, no con código.
- El chat de IA no aplica el filtro estricto de intereses.
- Código sin uso en `ai_service.py` (`_linea_de_tiempo`, `_elegir_con_distinguidos`, `MAX_DISTINGUIDOS_AL_FRENTE`).
- Acordar con Roberto quién actualiza la bitácora y cuándo hacer `git pull`.
- **Documento de requerimientos v2.0:** ningún RF dice cómo se marca una ruta como pública (P-01; el v0.4.0 avanzó con una propuesta, ver arriba); confirmar si el sitio ya tiene proveedor de mapas y credenciales (P-02); definir los valores de categoría y región de los filtros (P-03); Roberto debe validar el documento.

Bugs ya corregidos: [[RutaMX - Problemas resueltos]]. Stack: [[RutaMX - Tecnologías]].
