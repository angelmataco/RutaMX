# [V2] A2: contraste de conteos e inventario de requerimientos

- Fecha: 2026-11-05 (CDMX). Autora: claude-par. Revisora: codex-par.
- Fuente única: `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf`. Consigna: `documentacion/Consigna_Plan_Incremental.md` (prompt A2).

## 1. Contraste de los conteos (pasos 2 y 3)

| Tipo | A1 de Claude | Conteo ciego de Codex | ¿Coinciden? |
|---|---|---|---|
| RF | 44 | 44 | Sí |
| RNF | 33 | 33 | Sí |
| HU | 23 | 23 | Sí |
| CA | 93 | 93 | Sí |

Diferencia encontrada por ambos y resuelta: la cifra "92 criterios" del control de documento (p. 2) describe la versión 1.0; la v2.0 define 93 porque agregó CA-12.5 (sec. 8; sec. 4.1 declara 93; sec. 11 y Anexo A.4 lo identifican como nuevo). **Total vigente: 93 criterios.** Ninguna otra diferencia.

## 2. Cómo leer el inventario

- **Prioridad:** los RF y RNF no traen prioridad propia en el documento. La columna "Prioridad" dice "no indicada". La columna "Prioridad de su HU" es un dato derivado de la sección 7 (cada RF pertenece a una historia con prioridad Alta, Media o Baja); no es una prioridad explícita del RF.
- **Depende de:** solo dependencias que el documento respalda, con la sección o decisión citada. Si no hay respaldo, dice "—". Las dependencias entre RF salen de la justificación de prioridad de las historias (sec. 7) o del propio texto del RF (sec. 5).
- **Estado:** `Pendiente` o `Implementado`. Es una **propuesta** de claude-par basada en el código y la bitácora; el usuario ya decidió qué cuenta como incremento 1 (ver sección 5). "Evidencia" aclara lo que ya existe sin afirmar cumplimiento de extremo a extremo.

## 3. Requerimientos funcionales

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

## 4. Requerimientos no funcionales

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

## 5. Estado del incremento 1 (decisión del usuario, 2026-11-05)

**Decisión del usuario:** el incremento 1 (tag `v0.1.0`) es **solo el módulo M-09 Repositorio de rutas**. v1 se trata como el sitio existente reutilizable (login, mapas, IA) y **no cuenta como RF cumplidos**.

Evidencia de este checkout (`main`, commit d74a1ba), verificada el 2026-11-05:
- **v2 (arquitectura nueva):** `base_datos/repositorios/rutas_repositorio.py` define **tres operaciones**: `crear_ruta` (línea 81), `obtener_ruta` (110) y `listar_rutas_de_usuario` (128). `actualizar`, `copiar` y `eliminar` **no existen** en este checkout. La bitácora 01 registra 53 pruebas, estado "probado en simulación (2026-11-03)", contra un PostgreSQL desechable; **no las volví a ejecutar** en este paso. Esto cubre de forma **parcial** RF-38, RF-39, RF-40 y RF-42, solo en la capa de datos (sin interfaz ni autenticación). `v2/` no tiene aún interfaz, catálogo, orquestador ni adaptadores.
- **v1 (sitio existente, congelado):** login, planificador con IA, mapa, guardado y listado de rutas. No se cuenta como cumplimiento de la v2.0.

Consecuencia para el inventario: ningún RF queda cerrado de extremo a extremo con el incremento 1, así que las 44 filas de RF y las 33 de RNF están en `Pendiente`. RF-13, RF-14 y RF-16 (copiar una ruta) quedan completamente pendientes: M-09 todavía no tiene la operación de copiar. Los cuatro RF con evidencia parcial se completan en los incrementos siguientes sobre la base de M-09.

## 6. Verificación

```sh
grep -c '^| RF-' documentacion/A2_Inventario_Requerimientos.md    # 44
grep -c '^| RNF-' documentacion/A2_Inventario_Requerimientos.md   # 33
grep -c '\[V2\]' documentacion/A2_Inventario_Requerimientos.md   # >= 1
```

