# [V2] Plan de incrementos de RutaMX

- Fecha: 2026-11-05 (CDMX). Redacta: claude-par. Revisa: codex-par. Aprobó: el equipo (Angel Mata y Roberto Valderrama).
- **Estado: plan aprobado por el equipo (Angel Mata y Roberto Valderrama) el 2026-11-05.** Se aprobaron el escenario de 4 incrementos, cada ficha, la excepción de prioridad y la limitación de independencia de A4. Siguen abiertas las preguntas P-01, P-02 y P-03 (sección 8).
- Fuente única: `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf` (versión 2.0, 8 de octubre de 2026). Lo que no está ahí no se planea; queda como pregunta (sección 8).
- Documentos de apoyo (en `documentacion/`): `Consigna_Plan_Incremental.md`, `A1_Verificacion_Especificacion.md`, `A1_Conteo_Independiente_Codex.md`, `A2_Inventario_Requerimientos.md`, `A3_Propuesta_Incrementos.md`, `A4_Validacion_Plan.md`.
- El plan vive en `documentacion/` y no en `docs/` como dice la consigna (decisión del usuario, 2026-11-05).

## 1. Resumen

| Incremento | Versión | Objetivo | RF | HU | Estado |
|---|---|---|---|---|---|
| 1 | v0.1.0 | Módulo M-09 Repositorio de rutas (crear, obtener, listar), ya en `main` | 0 cerrados (evidencia parcial en RF-38, 39, 40, 42) | — | Hecho, probado en simulación (2026-11-03); tag por publicar |
| 2 | v0.2.0 | Planear con IA: de la conversación a una ruta estructurada | 12 | HU-09, HU-10, HU-11, HU-12, HU-19, HU-20 | Aprobado |
| 3 | v0.3.0 | Guardar y recuperar rutas, agregar parada y pedir aclaraciones | 9 | HU-13, HU-17, HU-21, HU-22, HU-23 | Aprobado |
| 4 | v0.4.0 | Descubrir: catálogo, búsqueda, filtros y detalle de rutas públicas | 10 | HU-01, HU-02, HU-03, HU-04, HU-05 | Aprobado |
| 5 | v0.5.0 | Completar la edición por chat, copiar rutas públicas y mostrar el mapa; cierre | 13 | HU-06, HU-07, HU-08, HU-14, HU-15, HU-16, HU-18 | Aprobado |

Totales vigentes de la especificación v2.0: **44 RF, 33 RNF, 23 HU y 93 CA** (los dos conteos independientes coinciden; la cifra «92» del control de documento es de la versión 1.0, la v2.0 agregó CA-12.5).

## 2. Restricciones y reparto de trabajo

| Dato | Respuesta |
|---|---|
| Semanas hasta la entrega final | 3 |
| Clases | 6: 4 de trabajo y 2 de exposición |
| Integrantes | 2: Roberto Valderrama y Angel Mata |
| Duración de cada clase y trabajo fuera de clase | **No se conoce todavía.** Se pidió al usuario |
| Reparto de IA (invertido respecto a la consigna, decisión del usuario) | Claude analiza, planea y documenta (lo que la consigna asigna a ChatGPT); Codex desarrolla y prueba (lo que la consigna asigna a Claude); cada paso lo revisa la otra IA; el equipo decide y verifica |
| Marcador | Todo commit, entrada de bitácora y documento nuevo lleva `[V2]`; commits con el formato `[V2] tipo(RF-XX): descripción` |

**Cómo se leen los cuatro incrementos:** son un **escenario condicionado**, no una garantía. El tamaño (12, 9, 10 y 13 RF) es estimación por número de RF y riesgo, no medición de esfuerzo. En cada clase de trabajo se reservan tres bloques en este orden: implementación por tareas (un commit y un push por tarea), pruebas normal/límite/error, e integración (regresión de los anteriores, merge y tag); este último bloque no recibe tareas nuevas. Al cerrar el v0.2.0 se compara lo planeado con lo hecho y se reajustan los siguientes en el registro de cambios. Si el v0.2.0 no cabe en una clase, el plan pasa al escenario de 3 incrementos de la sección 3.

**Definición de terminado con cobertura parcial:** un tag no afirma RF completos si su ficha declara cobertura parcial. RF-18, RF-24 y RF-37 se asignan al v0.2.0 pero se marcan terminados solo al cerrar el v0.5.0, cuando se prueban todas sus operaciones; hasta entonces el estado en la matriz es «cobertura parcial».

## 3. Cuántos incrementos y qué se recorta

- **Escenario principal: 4 incrementos** (v0.2.0 a v0.5.0), uno por clase de trabajo. Se agrupa por flujo de usuario y se ordena por dependencias, prioridad de las HU, riesgo técnico (lo más riesgoso primero) y que cada incremento sea ejecutable e integrado con el anterior.
- **Escenario conservador: 3 incrementos.** (A) v0.2.0 igual: 12 RF (RF-17 a 24, 35, 36, 37, 43); (B) guardar, agregar parada y lo Alto de Descubrir: 14 RF (RF-25, 26, 33, 38 a 42, 44, 01, 02, 03, 09, 10); (C) resto de Descubrir, edición restante, copia y mapa: 18 RF (RF-04 a 08, 27 a 32, 34, 13 a 16, 11, 12). Suman 44 sin repetir; (C) queda muy cargado.
- **Si algo no cabe**, queda registrado como pendiente con el incremento donde se atendería. Se recorta primero del v0.5.0: RF-11 y RF-12 (HU-06, Baja, que la sec. 7 ya prevé recortar por el riesgo «Tiempo del proyecto»), luego RF-34 y las preferencias RF-31 y RF-32. Lo de los incrementos 2 a 4 y el cierre de RNF-29 a RNF-33 no se recorta.

## 4. Observaciones de la validación A4 y cómo se resolvieron

| # | Observación de `A4_Validacion_Plan.md` | Resolución en este plan |
|---|---|---|
| 1 | Alta: precisar cuándo se considera terminado cada RF (RF-18, 24, 37 se reparten entre v0.2.0, v0.3.0 y v0.5.0) | **Resuelta.** Se mantienen asignados una sola vez al v0.2.0, pero con **cobertura parcial** declarada en la ficha del incremento 2 y en la matriz (sección 9); se marcan terminados al cerrar el v0.5.0, tras probar todas las operaciones |
| 2 | Alta: sostener o reducir el compromiso de calendario | **Resuelta como condicionada.** Sección 2 y 3: escenario con bloques, calibración al cerrar el v0.2.0, alternativa de 3 y recortes con destino. El equipo aprobó las fichas el 2026-11-05 |
| 3 | Alta para Descubrir: cerrar condiciones del catálogo (P-01, P-03; esquema) | **Resuelta.** La ficha del v0.4.0 declara P-01 y P-03 como bloqueos explícitos y P-02 para el mapa; reconoce la aprobación de esquema del 2026-11-03 (no se pide otra vez) y deja pendiente solo su ejecución con script, copia y respaldo |
| 4 | Media: completar módulos del catálogo (M-05, M-09, esquema) | **Resuelta.** La ficha del v0.4.0 agrega M-05 y M-09 y los metadatos categoría, región y visibilidad |
| 5 | Justificar la excepción de prioridad (HU-01, HU-05 y HU-17 Alta después de HU-19 Media) | **Excepción propuesta por el equipo y aceptada al aprobar el plan (2026-11-05).** El prompt A3 de la consigna ordena: dependencias, prioridad, riesgo técnico y ejecutabilidad; este plan **propone** adelantar el flujo de mayor riesgo (M-04 y M-07, sec. 10.4 y 12) aun cuando eso deje HU-01 y HU-05 (Alta) en el v0.4.0. Razones propuestas: HU-19 (RF-35) es el camino de error de la generación y se prueba junto con ella (sec. 7: depende de D-03), y 10 de las 12 HU de prioridad Alta están en los incrementos 2 y 3. HU-17 (RF-33, aclaraciones) se agrupa en el v0.3.0 con la primera operación de modificación por conveniencia de agrupación; ni la sec. 7 ni la consigna lo exigen. Si más adelante se quiere cambiar, hay que reordenar |
| — | Limitación de independencia de A4 (no hubo conversación nueva) | **Declarada y aceptada por el equipo al aprobar el plan (2026-11-05).** A4 la hizo Codex, que revisó antes los pasos de A3; no se afirma independencia total |

## 5. Inventario de requerimientos

El inventario es el de `A2_Inventario_Requerimientos.md` (copiado aquí tal cual). Estado de todo el inventario: **Pendiente**; el incremento 1 es M-09 y no cierra ningún RF de extremo a extremo.

### 5.1 Requerimientos funcionales

| ID | Descripción breve | Prioridad | Prioridad de su HU (derivada, sec. 7) | HU | Depende de | Sección | Estado | Evidencia en el código |
|---|---|---|---|---|---|---|---|---|
| RF-01 | Mostrar catálogo de rutas públicas en Descubrir | no indicada | Alta | HU-01 | — | Sec. 7 (HU-01: sin catálogo no hay búsqueda, detalle ni copia) | Pendiente | — |
| RF-02 | Mostrar nombre, origen, destino, duración, paradas y autor por ruta | no indicada | Alta | HU-01 | RF-01 | Sec. 7 (HU-01) | Pendiente | — |
| RF-03 | Indicar si la ruta es de RutaMx o de un usuario | no indicada | Alta | HU-01 | RF-01 | Sec. 7 (HU-01) | Pendiente | — |
| RF-04 | Buscar rutas públicas por palabras clave | no indicada | Media | HU-02 | RF-01 | Sec. 7 (HU-01) | Pendiente | — |
| RF-05 | Filtrar por duración, categoría y región | no indicada | Media | HU-03 | RF-01 | Sec. 7 (HU-01); D-01 y P-03 (valores de categoría y región) | Pendiente | — |
| RF-06 | Actualizar el listado al cambiar los filtros | no indicada | Media | HU-03 | RF-05 | Sec. 5 (texto de RF-06) | Pendiente | — |
| RF-07 | Mostrar mensaje cuando no hay rutas coincidentes | no indicada | Media | HU-04 | RF-04, RF-05 | Sec. 5 (texto de RF-07) | Pendiente | — |
| RF-08 | Reiniciar filtros para volver al catálogo completo | no indicada | Media | HU-03 | RF-05 | Sec. 5 (texto de RF-08) | Pendiente | — |
| RF-09 | Seleccionar una ruta y consultar su detalle | no indicada | Alta | HU-05 | RF-01 | Sec. 7 (HU-05: paso obligatorio del flujo Descubrir) | Pendiente | — |
| RF-10 | Detalle con descripción, origen, destino, duración y paradas ordenadas | no indicada | Alta | HU-05 | RF-09 | Sec. 5 (texto de RF-10) | Pendiente | — |
| RF-11 | Mostrar el recorrido en un mapa si hay proveedor configurado | no indicada | Baja | HU-06 | RF-10 | Sec. 7 (HU-06), 10.1 y D-06; abierto P-02 | Pendiente | equivalente en v1: maps_service |
| RF-12 | Avisar que el mapa no cargó y mostrar lo demás | no indicada | Baja | HU-06 | RF-11 | Sec. 5 (texto de RF-12) | Pendiente | — |
| RF-13 | Copiar una ruta pública como base de una ruta propia (autenticado) | no indicada | Media | HU-07 | RF-10 | Sec. 7 (HU-05: precondición de la copia) | Pendiente | — |
| RF-14 | Crear la copia asociada al usuario sin tocar la original | no indicada | Media | HU-07 | RF-13 | Sec. 5 (texto de RF-14) | Pendiente | — |
| RF-15 | Pedir iniciar sesión si un anónimo intenta copiar | no indicada | Media | HU-08 | RF-13 | Sec. 7 (HU-08: acompaña a HU-07) | Pendiente | — |
| RF-16 | Informar el error al copiar y no crear copia incompleta | no indicada | Media | HU-07 | RF-13, RF-14 | Sec. 5 (texto de RF-16) | Pendiente | — |
| RF-17 | Entrar a Planear con Ayuda IA e iniciar conversación | no indicada | Alta | HU-09 | — | Sec. 7 (HU-09: entrada del flujo Planear con IA) | Pendiente | equivalente en v1: /api/ia/planear |
| RF-18 | Describir el roadtrip en lenguaje natural; solo 5 intenciones soportadas | no indicada | Alta | HU-09 | RF-17 | Sec. 5 (texto de RF-18) y D-05 | Pendiente | equivalente en v1: chat IA |
| RF-19 | Aceptar origen, destino y duración (obligatorios) e intereses (opcional) | no indicada | Alta | HU-09 | RF-17 | Sec. 5 (texto de RF-19) y D-02 | Pendiente | equivalente en v1 |
| RF-20 | Pedir solo los datos obligatorios faltantes antes de proponer | no indicada | Alta | HU-10 | RF-19 | Sec. 5 (texto de RF-20) y D-02 | Pendiente | — |
| RF-21 | Generar una propuesta inicial de ruta | no indicada | Alta | HU-11 | RF-19, RF-20 | Sec. 7 (HU-10: evita propuestas sobre datos incompletos) | Pendiente | equivalente en v1: planificador_ia_service |
| RF-22 | La propuesta incluye origen, destino y paradas ordenadas (puede ir vacía) | no indicada | Alta | HU-11 | RF-21 | Sec. 5 (texto de RF-22) y CA-11.4 | Pendiente | — |
| RF-23 | Mostrar la ruta en una representación estructurada aparte del chat | no indicada | Alta | HU-12 | RF-21 | Sec. 7 (HU-11: todas las modificaciones parten de ella) | Pendiente | — |
| RF-24 | Reflejar los cambios aceptados en la ruta estructurada (fuente única) | no indicada | Alta | HU-12 | RF-23 | Sec. 7 (HU-12) y D-08 | Pendiente | — |
| RF-25 | Pedir por chat agregar una parada | no indicada | Alta | HU-13 | RF-24 | Sec. 7 (HU-12: sin ella no hay modificación) | Pendiente | — |
| RF-26 | Actualizar el itinerario al agregar una parada | no indicada | Alta | HU-13 | RF-25 | Sec. 5 (texto de RF-26) | Pendiente | — |
| RF-27 | Pedir por chat eliminar una parada | no indicada | Media | HU-14 | RF-24 | Sec. 7 (HU-14: reutiliza el patrón de HU-13) | Pendiente | — |
| RF-28 | Actualizar el itinerario sin afectar las demás paradas | no indicada | Media | HU-14 | RF-27 | Sec. 5 (texto de RF-28) | Pendiente | — |
| RF-29 | Pedir por chat reordenar las paradas | no indicada | Media | HU-15 | RF-24 | Sec. 7 (HU-15: reutiliza el patrón de HU-13) | Pendiente | — |
| RF-30 | Mostrar la nueva secuencia tras reordenar | no indicada | Media | HU-15 | RF-29 | Sec. 5 (texto de RF-30) | Pendiente | — |
| RF-31 | Modificar solo duración y tipo de lugares durante la conversación | no indicada | Media | HU-16 | RF-24 | Sec. 7 (HU-16) y D-04 | Pendiente | — |
| RF-32 | Mostrar el itinerario actualizado tras cambiar preferencias | no indicada | Media | HU-16 | RF-31 | Sec. 5 (texto de RF-32) | Pendiente | — |
| RF-33 | Pedir aclaración si la instrucción es ambigua | no indicada | Alta | HU-17 | RF-18 | Sec. 7 (HU-17) y 10.4 | Pendiente | — |
| RF-34 | Avisar que una acción no soportada no está disponible | no indicada | Media | HU-18 | RF-18 | Sec. 5 (texto de RF-34) y D-05 | Pendiente | — |
| RF-35 | Informar si no se puede generar una ruta válida y pedir cambios | no indicada | Media | HU-19 | RF-21 | Sec. 7 (HU-19) y D-03 | Pendiente | — |
| RF-36 | Avisar el error del servicio de IA y conservar la ruta previa | no indicada | Alta | HU-20 | RF-21, RF-23 | Sec. 5 (texto de RF-36) | Pendiente | — |
| RF-37 | No aplicar cambios parciales si falla una operación de IA | no indicada | Alta | HU-20 | RF-24 | Sec. 5 (texto de RF-37) y 10.4 (atomicidad en M-05) | Pendiente | — |
| RF-38 | Guardar una ruta generada en Planear (autenticado) | no indicada | Alta | HU-21 | RF-21 | Sec. 7 (HU-21: último paso del flujo Planear) | Pendiente | parcial en M-09: crear_ruta; equivalente en v1: POST /api/rutas |
| RF-39 | Asociar la ruta guardada con la cuenta del usuario | no indicada | Alta | HU-21 | RF-38 | Sec. 5 (texto de RF-39) | Pendiente | parcial en M-09: usuario_id obligatorio |
| RF-40 | Consultar después las rutas guardadas (vista mínima) | no indicada | Alta | HU-22 | RF-38 | Sec. 7 (HU-22: completa el ciclo guardar y recuperar) y D-07 | Pendiente | parcial en M-09: listar_rutas_de_usuario; equivalente en v1: GET /api/rutas |
| RF-41 | Pedir iniciar sesión si un anónimo intenta guardar | no indicada | Alta | HU-23 | RF-38 | Sec. 7 (HU-23: puerta de acceso a HU-21) | Pendiente | equivalente en v1: requiere sesión |
| RF-42 | Informar el error al guardar y no registrar datos incompletos | no indicada | Alta | HU-21 | RF-38 | Sec. 5 (texto de RF-42) | Pendiente | parcial en M-09: rollback, sin datos incompletos |
| RF-43 | Mantener consistentes chat, itinerario y mapa derivándolos de la ruta estructurada | no indicada | Alta | HU-12 | RF-23, RF-24 | Sec. 5 (texto de RF-43) y D-08 | Pendiente | — |
| RF-44 | Mensaje de error si una ruta guardada no se recupera, sin tocar otros datos | no indicada | Alta | HU-22 | RF-40 | Sec. 5 (texto de RF-44) | Pendiente | — |


### 5.2 Requerimientos no funcionales

| ID | Categoría | Descripción breve | Prioridad | Depende de | Sección | Estado |
|---|---|---|---|---|---|---|
| RNF-01 | Usabilidad | Interfaz consistente con el diseño del sitio existente | no indicada | — | Sec. 6 | Pendiente |
| RNF-02 | Usabilidad | Funciones principales a máximo 3 interacciones | no indicada | — | Sec. 6 | Pendiente |
| RNF-03 | Usabilidad | Mensajes de error comprensibles con acción siguiente | no indicada | — | Sec. 6 | Pendiente |
| RNF-04 | Usabilidad | Controles principales con etiqueta o elemento visual claro | no indicada | — | Sec. 6 | Pendiente |
| RNF-05 | Usabilidad | Retroalimentación visual si una operación tarda más de 1 s | no indicada | — | Sec. 6 | Pendiente |
| RNF-06 | Rendimiento | Catálogo carga en máximo 3 s | no indicada | RNF-32 (entorno de pruebas, texto del RNF) | Sec. 6 | Pendiente |
| RNF-07 | Rendimiento | Búsqueda y filtrado responden en máximo 2 s | no indicada | RNF-32 (entorno de pruebas, texto del RNF) | Sec. 6 | Pendiente |
| RNF-08 | Rendimiento | Detalle de ruta en máximo 3 s | no indicada | — | Sec. 6 | Pendiente |
| RNF-09 | Rendimiento | Interfaz utilizable mientras espera a la IA | no indicada | — | Sec. 6 | Pendiente |
| RNF-10 | Seguridad básica | Solo autenticados guardan o copian rutas | no indicada | — | Sec. 6 | Pendiente |
| RNF-11 | Seguridad básica | Nadie modifica o elimina rutas de otro usuario | no indicada | — | Sec. 6 | Pendiente |
| RNF-12 | Seguridad básica | Validar todas las entradas del usuario | no indicada | — | Sec. 6 | Pendiente |
| RNF-13 | Seguridad básica | HTTPS en producción | no indicada | — | Sec. 6 | Pendiente |
| RNF-14 | Seguridad básica | No mostrar datos sensibles en errores | no indicada | — | Sec. 6 | Pendiente |
| RNF-15 | Seguridad básica | Rutas privadas fuera de Descubrir salvo marcadas públicas | no indicada | Abierto P-01 (sec. 4.3) y D-10 | Sec. 6 | Pendiente |
| RNF-16 | Mantenibilidad | Presentación, negocio y datos modificables por separado | no indicada | — | Sec. 6 | Pendiente |
| RNF-17 | Mantenibilidad | Seguir convenciones de nombres del proyecto existente | no indicada | — | Sec. 6 | Pendiente |
| RNF-18 | Mantenibilidad | Documentar propósito y versión de dependencias nuevas | no indicada | — | Sec. 6 | Pendiente |
| RNF-19 | Mantenibilidad | Constantes de configuración fuera de la lógica principal | no indicada | — | Sec. 6 | Pendiente |
| RNF-20 | Modularidad | Descubrir desacoplado de Planear; solo hablan por el gestor de rutas | no indicada | — | Sec. 6 | Pendiente |
| RNF-21 | Modularidad | Servicios externos (mapas, IA) encapsulados | no indicada | — | Sec. 6 | Pendiente |
| RNF-22 | Modularidad | Lógica de crear, modificar y guardar rutas centralizada | no indicada | — | Sec. 6 | Pendiente |
| RNF-23 | Compatibilidad | Chrome, Edge y Firefox (dos versiones recientes) | no indicada | — | Sec. 6 | Pendiente |
| RNF-24 | Compatibilidad | Adaptable a escritorio y móvil desde 360 px | no indicada | — | Sec. 6 | Pendiente |
| RNF-25 | Compatibilidad | No romper funciones existentes del sitio | no indicada | RNF-29 (verificación, texto del RNF) | Sec. 6 | Pendiente |
| RNF-26 | Pruebas | Al menos un caso de prueba por RF | no indicada | — | Sec. 6 | Pendiente |
| RNF-27 | Pruebas | Probar flujos principales de Descubrir y Planear | no indicada | Sec. 3.2 (texto del RNF) | Sec. 6 | Pendiente |
| RNF-28 | Pruebas | Probar escenarios de error (IA, guardado, sin resultados, acceso) | no indicada | — | Sec. 6 | Pendiente |
| RNF-29 | Pruebas | Pruebas de regresión antes de la entrega final | no indicada | — | Sec. 6 | Pendiente |
| RNF-30 | Documentación | Documentación técnica de módulos e interacción | no indicada | — | Sec. 6 | Pendiente |
| RNF-31 | Documentación | Documentar dependencias externas (IA, mapas, APIs) | no indicada | — | Sec. 6 | Pendiente |
| RNF-32 | Documentación | Instrucciones para configurar y ejecutar en desarrollo | no indicada | — | Sec. 6 | Pendiente |
| RNF-33 | Documentación | Relación entre RF y casos de prueba | no indicada | — | Sec. 6 | Pendiente |


## 6. Fichas por incremento (aprobadas por el equipo el 2026-11-05)

### Incremento 2 · v0.2.0: Planear con IA: de la conversación a una ruta estructurada

| Campo | Respuesta |
|---|---|
| Incremento y versión | Incremento 2 · v0.2.0 |
| Objetivo en una frase | El usuario conversa con la IA, esta pide los datos que faltan y le entrega una ruta (origen, destino, paradas) mostrada como itinerario estructurado, sin perder la ruta previa si la IA falla. |
| RF incluidos | RF-17, RF-18, RF-19, RF-20, RF-21, RF-22, RF-23, RF-24, RF-35, RF-36, RF-37, RF-43 (12) |
| Cobertura parcial | En este incremento RF-18 se prueba con la intención «crear ruta», RF-24 con los cambios de la creación y RF-37 con la creación atómica. **No se marcan terminados** hasta probar sus escenarios completos al cerrar el v0.5.0 (agregar, eliminar, reordenar y preferencias; CA-20.4). Se registra como cobertura parcial y regresión final en la matriz de trazabilidad. |
| HU incluidas (sec. 7) | HU-09, HU-10, HU-11, HU-12, HU-19, HU-20 |
| RNF que se verifican aquí | RNF-03, RNF-05, RNF-09, RNF-12, RNF-14, RNF-16, RNF-17, RNF-18, RNF-19, RNF-20, RNF-21, RNF-22, RNF-32 |
| Criterios de aceptación (sec. 8) | 25 criterios en total para HU-09, HU-10, HU-11, HU-12, HU-19 y HU-20. **Diferidos** (necesitan modificar una ruta ya generada, que existe desde el v0.3.0): **CA-12.5** (vistas iguales tras una modificación aceptada) y **CA-20.4** (sin cambios parciales si falla una modificación). **Parciales** (se prueban aquí sin modificaciones y se repiten con ellas en v0.3.0 y v0.5.0): CA-12.1, CA-20.1, CA-20.2 y CA-20.3. Los otros 19 se prueban completos aquí |
| Módulos involucrados (sec. 10.3) | M-03, M-04, M-05, M-07, M-08, M-11 |
| Depende de | Incremento 1 (M-09 existe, aunque este incremento aún no guarda). Reutiliza la autenticación existente (D-13); el servicio de IA se encapsula en M-07 (RNF-21). |
| Pruebas mínimas: normal, límite y error | Casos de prueba CP-nn de la matriz 9.1 (misma numeración que su RF), p. ej. CP-17, CP-18, CP-19, CP-20 .... Normal: CA-09.1, CA-10.1, CA-11.1 (+4 más). Límite: CA-09.4, CA-10.4, CA-11.4 (+3 más). Error de datos: CA-09.2, CA-10.2, CA-11.2 (+3 más). Error de sistema: CA-09.3, CA-10.3, CA-11.3 (+3 más). Más regresión de los incrementos anteriores (RNF-29). |
| Rama de Git | `incremento-2` |
| Fecha de cierre | Clase 1 de 4 (por confirmar con el calendario real) |
| Por qué se agrupa así | Riesgo técnico más alto del proyecto (M-04 y M-07, sec. 10.4 y 12); sus HU son prioridad Alta (sec. 7) y todo lo demás de Planear parte de la propuesta (HU-11) y de la ruta estructurada (HU-12, D-08). |
| Decisión del equipo y justificación | Aceptada · aprobada por el equipo (Angel Mata y Roberto Valderrama), 2026-11-05 |

### Incremento 3 · v0.3.0: Guardar y recuperar rutas, agregar parada y pedir aclaraciones

| Campo | Respuesta |
|---|---|
| Incremento y versión | Incremento 3 · v0.3.0 |
| Objetivo en una frase | El usuario autenticado guarda su ruta generada (y al volver a guardarla se actualiza esa misma ruta, D-11), la consulta después, se le pide iniciar sesión si no lo está, y puede agregar paradas por chat con aclaración cuando la instrucción es ambigua. |
| RF incluidos | RF-25, RF-26, RF-33, RF-38, RF-39, RF-40, RF-41, RF-42, RF-44 (9) |
| HU incluidas (sec. 7) | HU-13, HU-17, HU-21, HU-22, HU-23 |
| RNF que se verifican aquí | RNF-10, RNF-11 |
| CA diferidos del v0.2.0 | Aquí se prueban **CA-12.5 y CA-20.4** con la operación agregar parada (y CA-12.1, 20.1 a 20.3 con modificaciones); se completan para eliminar, reordenar y preferencias en el v0.5.0 |
| Criterios de aceptación (sec. 8) | 20 criterios: todos los CA de HU-13, HU-17, HU-21, HU-22, HU-23; se prueban todos |
| Módulos involucrados (sec. 10.3) | M-03, M-04, M-05, M-06, M-09, M-10, M-11 |
| Esquema | Actualizar la misma ruta al volver a guardar se puede hacer sobre las columnas actuales y por sí mismo no exige migración. Sigue pendiente la **ejecución** de las siete columnas ya autorizadas por Angel el 2026-11-03 (`descripcion`, `duracion_dias`, `categoria`, `region`, `visibilidad`, `ruta_origen_id`, `autor_id`) con script, prueba en copia y respaldo; cualquier columna o cambio distinto, aún no definido, necesita nueva aprobación de Angel. |
| Depende de | Incremento 2 (ruta generada y ruta estructurada) e incremento 1 (M-09: crear, obtener y listar). **Incluye agregar a M-09 la operación de actualizar al volver a guardar** (D-11 y CA-21.4: guardar de nuevo actualiza la misma ruta y, si falla, la versión anterior queda intacta); es parte de RF-42 / HU-21, no funcionalidad nueva. Un cambio de esquema distinto de las siete columnas ya autorizadas necesitaría nueva aprobación de Angel (bitácora 02). |
| Pruebas mínimas: normal, límite y error | Casos de prueba CP-nn de la matriz 9.1 (misma numeración que su RF), p. ej. CP-25, CP-26, CP-33, CP-38 .... Normal: CA-13.1, CA-17.1, CA-21.1 (+2 más). Límite: CA-13.4, CA-17.4, CA-21.4 (+2 más). Error de datos: CA-13.2, CA-17.2, CA-21.2 (+2 más). Error de sistema: CA-13.3, CA-17.3, CA-21.3 (+2 más). Más regresión de los incrementos anteriores (RNF-29). |
| Rama de Git | `incremento-3` |
| Fecha de cierre | Clase 2 de 4 (por confirmar con el calendario real) |
| Por qué se agrupa así | Cierra el flujo extremo a extremo Planear → guardar → consultar con HU de prioridad Alta (HU-21, 22, 23, 13, 17, sec. 7) usando M-09 del incremento 1. |
| Decisión del equipo y justificación | Aceptada · aprobada por el equipo (Angel Mata y Roberto Valderrama), 2026-11-05 |

### Incremento 4 · v0.4.0: Descubrir: catálogo, búsqueda, filtros y detalle de rutas públicas

| Campo | Respuesta |
|---|---|
| Incremento y versión | Incremento 4 · v0.4.0 |
| Objetivo en una frase | Cualquier visitante explora el catálogo de rutas públicas, las busca, las filtra por duración, categoría y región y consulta el detalle de una ruta. |
| RF incluidos | RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08, RF-09, RF-10 (10) |
| HU incluidas (sec. 7) | HU-01, HU-02, HU-03, HU-04, HU-05 |
| RNF que se verifican aquí | RNF-01, RNF-02, RNF-04, RNF-06, RNF-07, RNF-08, RNF-15, RNF-24 |
| Criterios de aceptación (sec. 8) | 20 criterios: todos los CA de HU-01, HU-02, HU-03, HU-04, HU-05; se prueban todos |
| Módulos involucrados (sec. 10.3 y 10.1/10.5) | M-01, M-02, M-11, y también **M-05 y M-09** (gestor y repositorio compartidos, sec. 10.1 y 10.5) para la consulta de rutas públicas, la visibilidad (RNF-15, D-10) y los metadatos categoría/región/visibilidad |
| Bloqueos explícitos | **P-01 y P-03 (sec. 4.3) bloquean la implementación y la aceptación del catálogo**: no se asume cómo se publican rutas ni se inventan categorías o regiones. Una ruta guardada no es pública por eso (RNF-15, D-10). **P-02** decide el mapa del v0.5.0. |
| Esquema | Las siete columnas de `rutas_guardadas` que Angel autorizó el 2026-11-03 (`descripcion`, `duracion_dias`, `categoria`, `region`, `visibilidad`, `ruta_origen_id`, `autor_id`) no se vuelven a pedir; su **ejecución** sigue pendiente (script, prueba en copia y respaldo previo). Cualquier columna o cambio distinto, aún no definido, necesita nueva aprobación de Angel. |
| Depende de | Incremento 1 (M-09 y la tabla de rutas) e incremento 3 (rutas guardadas/públicas). Depende de aclarar P-01 (cómo se marca una ruta pública) y P-03 (valores de categoría y región) de la sec. 4.3. |
| Pruebas mínimas: normal, límite y error | Casos de prueba CP-nn de la matriz 9.1 (misma numeración que su RF), p. ej. CP-01, CP-02, CP-03, CP-04 .... Normal: CA-01.1, CA-02.1, CA-03.1 (+2 más). Límite: CA-01.4, CA-02.4, CA-03.4 (+2 más). Error de datos: CA-01.2, CA-02.2, CA-03.2 (+2 más). Error de sistema: CA-01.3, CA-02.3, CA-03.3 (+2 más). Más regresión de los incrementos anteriores (RNF-29). |
| Rama de Git | `incremento-4` |
| Fecha de cierre | Clase 3 de 4 (por confirmar con el calendario real) |
| Por qué se agrupa así | Segundo flujo del MVP (sec. 3.2); HU-01 y HU-05 son Alta y HU-02, 03, 04 Media. Va después de Planear porque tiene menos riesgo técnico (criterio 3) y porque el catálogo necesita las rutas que genera y guarda Planear. |
| Decisión del equipo y justificación | Aceptada · aprobada por el equipo (Angel Mata y Roberto Valderrama), 2026-11-05 |

### Incremento 5 · v0.5.0: Completar la edición por chat, copiar rutas públicas y mostrar el mapa; cierre

| Campo | Respuesta |
|---|---|
| Incremento y versión | Incremento 5 · v0.5.0 |
| Objetivo en una frase | El usuario elimina y reordena paradas y ajusta preferencias por chat, copia una ruta pública a sus rutas (con inicio de sesión si hace falta) y ve el recorrido en un mapa; el equipo cierra pruebas de regresión, compatibilidad y documentación. |
| RF incluidos | RF-11, RF-12, RF-13, RF-14, RF-15, RF-16, RF-27, RF-28, RF-29, RF-30, RF-31, RF-32, RF-34 (13) |
| HU incluidas (sec. 7) | HU-06, HU-07, HU-08, HU-14, HU-15, HU-16, HU-18 |
| RNF que se verifican aquí | RNF-13, RNF-23, RNF-25, RNF-26, RNF-27, RNF-28, RNF-29, RNF-30, RNF-31, RNF-33 |
| Criterios de aceptación (sec. 8) | 28 criterios: todos los CA de HU-06, HU-07, HU-08, HU-14, HU-15, HU-16, HU-18; se prueban todos |
| Módulos involucrados (sec. 10.3) | M-01, M-03, M-04, M-05, M-08, M-09, M-10, M-11 |
| Depende de | Incrementos 2 (ruta estructurada), 3 (agregar parada, guardar) y 4 (detalle de ruta, necesario para copiar y para el mapa). Copiar exige la operación copiar en M-09, que hoy no existe. Mapa depende de P-02 (proveedor de mapas). |
| Pruebas mínimas: normal, límite y error | Casos de prueba CP-nn de la matriz 9.1 (misma numeración que su RF), p. ej. CP-11, CP-12, CP-13, CP-14 .... Normal: CA-06.1, CA-07.1, CA-08.1 (+4 más). Límite: CA-06.4, CA-07.4, CA-08.4 (+4 más). Error de datos: CA-06.2, CA-07.2, CA-08.2 (+4 más). Error de sistema: CA-06.3, CA-07.3, CA-08.3 (+4 más). Más regresión de los incrementos anteriores (RNF-29). |
| Rama de Git | `incremento-5` |
| Fecha de cierre | Clase 4 de 4 (por confirmar con el calendario real) |
| Por qué se agrupa así | Prioridad Media y Baja (HU-14, 15, 16, 18, 07, 08 Media; HU-06 Baja, sec. 7). Es el incremento recortable: si el tiempo no alcanza, se recortan primero RF-11 y RF-12 (HU-06, que la sec. 7 ya prevé recortar por el riesgo «Tiempo del proyecto»), luego RF-34 y las preferencias. |
| Decisión del equipo y justificación | Aceptada · aprobada por el equipo (Angel Mata y Roberto Valderrama), 2026-11-05 |


## 7. Asignación de RNF por incremento

Cada RNF se asigna a un solo incremento: donde se comprueba por primera vez o donde se cierra. RNF-26, 27, 28, 29 y 33 se practican en todos los incrementos y se cierran en el v0.5.0; RNF-32 se escribe en el v0.2.0 porque RNF-06 y RNF-07 dependen de ese entorno (sec. 6).

| Incremento | RNF incluidos |
|---|---|
| 2 (v0.2.0) | RNF-03, RNF-05, RNF-09, RNF-12, RNF-14, RNF-16, RNF-17, RNF-18, RNF-19, RNF-20, RNF-21, RNF-22, RNF-32 |
| 3 (v0.3.0) | RNF-10, RNF-11 |
| 4 (v0.4.0) | RNF-01, RNF-02, RNF-04, RNF-06, RNF-07, RNF-08, RNF-15, RNF-24 |
| 5 (v0.5.0) | RNF-13, RNF-23, RNF-25, RNF-26, RNF-27, RNF-28, RNF-29, RNF-30, RNF-31, RNF-33 |

## 8. Ambigüedades, preguntas abiertas y riesgos

**Resueltas en la v2.0 (sec. 4.2 y 12.1):** D-01 (filtros del MVP), D-02 (datos mínimos), D-03 (ruta válida), D-04 (preferencias), D-05 (intenciones), D-06 (mapas), D-07 (vista de rutas guardadas), D-08 (ruta estructurada como fuente única), D-09, D-10 (visibilidad), D-11 (guardar de nuevo actualiza la misma ruta), D-12, D-13 (autenticación existente), D-14 (interacción).

**Abiertas (no se resuelven en el plan; se consultan con el profesor o el cliente):**

1. **P-01:** cómo se marca o publica una ruta como pública. Ningún RF lo describe. Bloquea la implementación y la aceptación del catálogo (v0.4.0). No se agrega una función de publicar.
2. **P-02:** si hay proveedor de mapas y credenciales (D-06). Decide RF-11 y RF-12.
3. **P-03:** valores de categoría y región para RF-05.
4. **Calendario:** duración de cada clase y trabajo fuera de clase (para calibrar el tamaño de los incrementos).
5. **Ejecución del esquema:** Angel autorizó el 2026-11-03 siete columnas de `rutas_guardadas` (`descripcion`, `duracion_dias`, `categoria`, `region`, `visibilidad`, `ruta_origen_id`, `autor_id`); falta ejecutar la migración con script, prueba en copia y respaldo. Cualquier otro cambio de esquema, aún no definido, necesita nueva aprobación.
6. **Fuera del plan:** eliminar rutas guardadas (ningún RF ni decisión lo pide). Actualizar al volver a guardar sí entra (D-11, v0.3.0); copiar entra en el v0.5.0 (RF-13, 14, 16).

**Riesgos (sec. 12.2):** interpretación no determinista de la IA (por eso M-04 va primero y se prueba con un adaptador de IA simulado), atomicidad de los cambios (RF-37, CA-20.4, CA-21.4), tiempo del proyecto (el v0.5.0 es el recortable) y que el estado «probado en simulación» no equivale a uso real: nada de lo construido hasta ahora está verificado en uso real.

## 9. Matriz de trazabilidad inicial

Une cada requerimiento con su sección, historia, incremento, módulo, prueba sugerida y estado. «Commits» se llena al implementar. El tag es el del incremento donde se cierra. Evidencia previa: M-09 (incremento 1, v0.1.0) aporta cobertura parcial a RF-38, 39, 40 y 42.

| RF / HU | Sección del documento | Incremento | Módulo(s) | Commits | Tag | Prueba | Estado |
|---|---|---|---|---|---|---|---|
| RF-01 / HU-01 | Sec. 5, 7, 8 y 9.1 | 4 | M-01, M-02 | — | v0.4.0 | CP-01 | Pendiente |
| RF-02 / HU-01 | Sec. 5, 7, 8 y 9.1 | 4 | M-01, M-02 | — | v0.4.0 | CP-02 | Pendiente |
| RF-03 / HU-01 | Sec. 5, 7, 8 y 9.1 | 4 | M-01, M-02 | — | v0.4.0 | CP-03 | Pendiente |
| RF-04 / HU-02 | Sec. 5, 7, 8 y 9.1 | 4 | M-01, M-02, M-11 | — | v0.4.0 | CP-04 | Pendiente |
| RF-05 / HU-03 | Sec. 5, 7, 8 y 9.1 | 4 | M-01, M-02 | — | v0.4.0 | CP-05 | Pendiente |
| RF-06 / HU-03 | Sec. 5, 7, 8 y 9.1 | 4 | M-01, M-02 | — | v0.4.0 | CP-06 | Pendiente |
| RF-07 / HU-04 | Sec. 5, 7, 8 y 9.1 | 4 | M-01 | — | v0.4.0 | CP-07 | Pendiente |
| RF-08 / HU-03 | Sec. 5, 7, 8 y 9.1 | 4 | M-01 | — | v0.4.0 | CP-08 | Pendiente |
| RF-09 / HU-05 | Sec. 5, 7, 8 y 9.1 | 4 | M-01, M-02 | — | v0.4.0 | CP-09 | Pendiente |
| RF-10 / HU-05 | Sec. 5, 7, 8 y 9.1 | 4 | M-01, M-02 | — | v0.4.0 | CP-10 | Pendiente |
| RF-11 / HU-06 | Sec. 5, 7, 8 y 9.1 | 5 | M-01, M-08 | — | v0.5.0 | CP-11 | Pendiente |
| RF-12 / HU-06 | Sec. 5, 7, 8 y 9.1 | 5 | M-01, M-08, M-11 | — | v0.5.0 | CP-12 | Pendiente |
| RF-13 / HU-07 | Sec. 5, 7, 8 y 9.1 | 5 | M-01, M-05, M-10 | — | v0.5.0 | CP-13 | Pendiente |
| RF-14 / HU-07 | Sec. 5, 7, 8 y 9.1 | 5 | M-05, M-09 | — | v0.5.0 | CP-14 | Pendiente |
| RF-15 / HU-08 | Sec. 5, 7, 8 y 9.1 | 5 | M-01, M-10 | — | v0.5.0 | CP-15 | Pendiente |
| RF-16 / HU-07 | Sec. 5, 7, 8 y 9.1 | 5 | M-05, M-09, M-11 | — | v0.5.0 | CP-16 | Pendiente |
| RF-17 / HU-09 | Sec. 5, 7, 8 y 9.1 | 2 | M-03, M-04 | — | v0.2.0 | CP-17 | Pendiente |
| RF-18 / HU-09 | Sec. 5, 7, 8 y 9.1 | 2 | M-03, M-04, M-07 | — | v0.2.0 y v0.5.0 | CP-18 | Pendiente (cobertura parcial en v0.2.0; cierre pleno en v0.5.0) |
| RF-19 / HU-09 | Sec. 5, 7, 8 y 9.1 | 2 | M-04, M-07 | — | v0.2.0 | CP-19 | Pendiente |
| RF-20 / HU-10 | Sec. 5, 7, 8 y 9.1 | 2 | M-04 | — | v0.2.0 | CP-20 | Pendiente |
| RF-21 / HU-11 | Sec. 5, 7, 8 y 9.1 | 2 | M-04, M-05, M-07 | — | v0.2.0 | CP-21 | Pendiente |
| RF-22 / HU-11 | Sec. 5, 7, 8 y 9.1 | 2 | M-05 | — | v0.2.0 | CP-22 | Pendiente |
| RF-23 / HU-12 | Sec. 5, 7, 8 y 9.1 | 2 | M-03, M-05 | — | v0.2.0 | CP-23 | Pendiente |
| RF-24 / HU-12 | Sec. 5, 7, 8 y 9.1 | 2 | M-03, M-05 | — | v0.2.0 y v0.5.0 | CP-24 | Pendiente (cobertura parcial en v0.2.0; cierre pleno en v0.5.0) |
| RF-25 / HU-13 | Sec. 5, 7, 8 y 9.1 | 3 | M-04, M-05 | — | v0.3.0 | CP-25 | Pendiente |
| RF-26 / HU-13 | Sec. 5, 7, 8 y 9.1 | 3 | M-03, M-05 | — | v0.3.0 | CP-26 | Pendiente |
| RF-27 / HU-14 | Sec. 5, 7, 8 y 9.1 | 5 | M-04, M-05 | — | v0.5.0 | CP-27 | Pendiente |
| RF-28 / HU-14 | Sec. 5, 7, 8 y 9.1 | 5 | M-03, M-05 | — | v0.5.0 | CP-28 | Pendiente |
| RF-29 / HU-15 | Sec. 5, 7, 8 y 9.1 | 5 | M-04, M-05 | — | v0.5.0 | CP-29 | Pendiente |
| RF-30 / HU-15 | Sec. 5, 7, 8 y 9.1 | 5 | M-03, M-05 | — | v0.5.0 | CP-30 | Pendiente |
| RF-31 / HU-16 | Sec. 5, 7, 8 y 9.1 | 5 | M-04, M-05 | — | v0.5.0 | CP-31 | Pendiente |
| RF-32 / HU-16 | Sec. 5, 7, 8 y 9.1 | 5 | M-03, M-05 | — | v0.5.0 | CP-32 | Pendiente |
| RF-33 / HU-17 | Sec. 5, 7, 8 y 9.1 | 3 | M-04 | — | v0.3.0 | CP-33 | Pendiente |
| RF-34 / HU-18 | Sec. 5, 7, 8 y 9.1 | 5 | M-04 | — | v0.5.0 | CP-34 | Pendiente |
| RF-35 / HU-19 | Sec. 5, 7, 8 y 9.1 | 2 | M-04, M-05 | — | v0.2.0 | CP-35 | Pendiente |
| RF-36 / HU-20 | Sec. 5, 7, 8 y 9.1 | 2 | M-04, M-07, M-11 | — | v0.2.0 | CP-36 | Pendiente |
| RF-37 / HU-20 | Sec. 5, 7, 8 y 9.1 | 2 | M-05 | — | v0.2.0 y v0.5.0 | CP-37 | Pendiente (cobertura parcial en v0.2.0; cierre pleno en v0.5.0) |
| RF-38 / HU-21 | Sec. 5, 7, 8 y 9.1 | 3 | M-05, M-09, M-10 | — | v0.3.0 | CP-38 | Pendiente (parcial en M-09, v0.1.0) |
| RF-39 / HU-21 | Sec. 5, 7, 8 y 9.1 | 3 | M-05, M-09 | — | v0.3.0 | CP-39 | Pendiente (parcial en M-09, v0.1.0) |
| RF-40 / HU-22 | Sec. 5, 7, 8 y 9.1 | 3 | M-05, M-06, M-09 | — | v0.3.0 | CP-40 | Pendiente (parcial en M-09, v0.1.0) |
| RF-41 / HU-23 | Sec. 5, 7, 8 y 9.1 | 3 | M-03, M-10 | — | v0.3.0 | CP-41 | Pendiente |
| RF-42 / HU-21 | Sec. 5, 7, 8 y 9.1 | 3 | M-05, M-09 | — | v0.3.0 | CP-42 | Pendiente (parcial en M-09, v0.1.0) |
| RF-43 / HU-12 | Sec. 5, 7, 8 y 9.1 | 2 | M-03, M-05, M-08 | — | v0.2.0 | CP-43 | Pendiente |
| RF-44 / HU-22 | Sec. 5, 7, 8 y 9.1 | 3 | M-05, M-06, M-11 | — | v0.3.0 | CP-44 | Pendiente |

| RNF | Sección | Incremento | Tag | Estado |
|---|---|---|---|---|
| RNF-03 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-05 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-09 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-12 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-14 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-16 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-17 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-18 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-19 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-20 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-21 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-22 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-32 | Sec. 6 y 9.2 | 2 | v0.2.0 | Pendiente |
| RNF-10 | Sec. 6 y 9.2 | 3 | v0.3.0 | Pendiente |
| RNF-11 | Sec. 6 y 9.2 | 3 | v0.3.0 | Pendiente |
| RNF-01 | Sec. 6 y 9.2 | 4 | v0.4.0 | Pendiente |
| RNF-02 | Sec. 6 y 9.2 | 4 | v0.4.0 | Pendiente |
| RNF-04 | Sec. 6 y 9.2 | 4 | v0.4.0 | Pendiente |
| RNF-06 | Sec. 6 y 9.2 | 4 | v0.4.0 | Pendiente |
| RNF-07 | Sec. 6 y 9.2 | 4 | v0.4.0 | Pendiente |
| RNF-08 | Sec. 6 y 9.2 | 4 | v0.4.0 | Pendiente |
| RNF-15 | Sec. 6 y 9.2 | 4 | v0.4.0 | Pendiente |
| RNF-24 | Sec. 6 y 9.2 | 4 | v0.4.0 | Pendiente |
| RNF-13 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-23 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-25 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-26 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-27 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-28 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-29 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-30 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-31 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |
| RNF-33 | Sec. 6 y 9.2 | 5 | v0.5.0 | Pendiente |

## 10. Registro de cambios al plan

| Fecha | Cambio al plan | Motivo | Aprobado por |
|---|---|---|---|
| 2026-11-05 | El plan y los apoyos viven en `documentacion/`, no en `docs/` | La carpeta del repo ya se llama `documentacion/` | Usuario (Angel) |
| 2026-11-05 | Reparto de IA invertido: Claude hace análisis y planeación, Codex desarrolla y prueba | Decisión del usuario | Usuario (Angel) |
| 2026-11-05 | Incremento 1 (v0.1.0) = solo M-09; v1 no cuenta como RF cumplidos | Decisión del usuario | Usuario (Angel) |
| 2026-11-05 | Total de criterios de aceptación = 93 (no 92) | La v2.0 agregó CA-12.5 (sec. 4.1, 11, Anexo A.4); ambos conteos independientes coinciden | Verificado por Claude y Codex; no requiere decisión |
| 2026-11-05 | Calendario: 4 clases de trabajo y 2 de exposición | Aclaración del usuario | Usuario (Angel) |
| 2026-11-05 | Actualizar al volver a guardar entra al v0.3.0 | Observación de Codex en A3: D-11 y CA-21.4 (sec. 4.2 y 8) | Equipo (Angel y Roberto), 2026-11-05 |
| 2026-11-05 | RNF-32 pasa del v0.5.0 al v0.2.0 | Observación de Codex en A3: RNF-06 y RNF-07 dependen de él (sec. 6) | Equipo (Angel y Roberto), 2026-11-05 |
| 2026-11-05 | Cuatro incrementos pasan a escenario condicionado, con alternativa de 3 y recortes | Observaciones de Codex en A3 y A4: sin horas por clase no se puede afirmar viabilidad | Equipo (Angel y Roberto), 2026-11-05 |
| 2026-11-05 | Ficha del v0.4.0 agrega M-05, M-09, bloqueos P-01/P-03 y esquema; ficha del v0.2.0 declara cobertura parcial de RF-18, 24, 37 | Observaciones 1, 3 y 4 de A4 | Equipo (Angel y Roberto), 2026-11-05 |
| 2026-11-05 | Aprobación del plan completo (4 incrementos, fichas, excepción de prioridad, limitación de independencia de A4) | Decisión conjunta de los dos integrantes | Equipo (Angel Mata y Roberto Valderrama) |

## 11. Bitácora de IA

| Fecha | Herramienta | Prompt o tarea | Qué se aceptó | Qué se modificó o rechazó, y por qué |
|---|---|---|---|---|
| 2026-11-05 | Claude (claude-par) | A1: verificación de la especificación v2.0 | Conteo 44 RF, 33 RNF, 23 HU, 93 CA y el hallazgo 92 contra 93 | Codex pidió un comando autocontenido, los subtítulos completos y no presentar la prioridad de la HU como prioridad del RF; se corrigió |
| 2026-11-05 | Codex (codex-par) | A1: conteo ciego e independiente | Los mismos totales, con SHA256 y comando reproducible | Sin cambios |
| 2026-11-05 | Claude (claude-par) | A2: contraste e inventario | Tabla de 44 RF y 33 RNF con dependencias citadas | Codex detectó que escribí «seis operaciones y 124 pruebas» tomándolo de un relevo sin verificarlo: el repo tiene tres operaciones. Se corrigió y se quitó la dependencia temática RNF-33 → RNF-26 |
| 2026-11-05 | Claude (claude-par) | A3: propuesta de incrementos | Agrupación por flujo y orden por dependencias | Codex observó que faltaba actualizar al re-guardar (D-11), que RNF-32 iba tarde y que afirmé viabilidad sin base; se corrigieron las tres |
| 2026-11-05 | Codex (codex-par) | A4: validación cruzada | Checklist de 5 puntos y su verificación reproducible (la corrí: código 0) | Sus 4 observaciones y la excepción de prioridad se resuelven en la sección 4 de este plan. No fue una conversación nueva |

## 12. Publicación en GitHub

El tag `v0.1.0` se creó **en local** sobre el último commit de `main` antes de los documentos del plan (estado de M-09), y el commit del plan se hizo después, también en local. Ambos se subieron el 2026-11-05 con los comandos de abajo, que ejecutó Angel (Claude no sube a remotos). No se incluye `RutaMx_Entrega_Documentacion_Completa.pdf`, que no es parte del plan.

```sh
git push origin main
git push origin v0.1.0
```

| Evidencia | Dato |
|---|---|
| URL de `documentacion/plan_incrementos.md` en GitHub | `https://github.com/angelmataco/RutaMX/blob/main/documentacion/plan_incrementos.md` (válida después del push) |
| Tag v0.1.0 visible en GitHub (Tags) | `https://github.com/angelmataco/RutaMX/releases/tag/v0.1.0` (válida después del push) |
| Hash del commit del plan | `3e11b46` (publicado en `main` el 2026-11-05) |
| Commit al que apunta el tag `v0.1.0` | `d74a1ba` (estado de M-09, antes de los documentos del plan) |

## 13. Verificación de este documento

```sh
grep -c '^| RF-' documentacion/plan_incrementos.md      # filas de RF: inventario (44) + matriz (44) = 88
grep -L '\[V2\]' documentacion/A*.md documentacion/plan_incrementos.md documentacion/Consigna_Plan_Incremental.md   # sin salida
```

