---
title: "Plan de implementación del primer incremento: M-09 Repositorio de rutas"
subtitle: "RutaMx · Desarrollo de Aplicaciones y Servicios Virtuales · Universidad Iberoamericana León"
---

# Datos del equipo

| Registro | Dato |
|---|---|
| Proyecto | RutaMx (apartado nuevo v2.0: Descubrir y Planear con Ayuda IA) |
| Integrantes | Roberto Valderrama (arquitectura / diseño y análisis) · Angel Mata (operación de IA y validación técnica). Al ser dos integrantes, los roles de analista, operador de IA y validador/tester se comparten (Requerimientos v2.0, sección 1.2). |
| Fecha / versión del plan | 29 de octubre de 2026 · v1.1 (versión final, revisada por Angel y Roberto) |
| Repositorio | github.com/angelmataco/RutaMX |
| Alcance de este documento | Solo el PLAN de un módulo. No se escribe código ni se toca la base de datos real. |

**Módulo elegido: M-09 Repositorio de rutas** (capa de datos). Lo marcado como SUPUESTO o PENDIENTE sigue sin confirmarse y se resuelve en las tareas indicadas antes de programar.

# Paso 1. Insumos reunidos y verificados

| Documento / artefacto | Disponible | Versión / observación |
|---|---|---|
| Alcance y exclusiones | Sí | Requerimientos v2.0 (8 oct 2026), secciones 3.1–3.3. |
| RF y RNF priorizados | Sí | RF-01 a RF-44, RNF-01 a RNF-33; decisiones D-01 a D-14. |
| HU y criterios de aceptación | Sí | HU-01 a HU-23 con CA-xx.1 a CA-xx.4 (normal, error de datos, error de sistema, límite). |
| Matriz de trazabilidad | Sí | Requerimientos v2.0, sección 9, y resumen por grupos en el diseño modular (sección 5). |
| Diseño modular y estructura de carpetas | Sí | "Diseño modular y arquitectura inicial (actualizado)": M-01 a M-11, sección 9 de carpetas. El repositorio se reorganizó el 29 oct 2026 en `v1/`, `v2/` y `base_datos/` (ver Paso 3). |
| Diseño de persistencia | Sí | "Persistencia y diseño mínimo de BD" (15 oct 2026). Falta la revisión de Roberto y la aprobación de Angel para tocar la tabla de la v1. |
| Repositorio y bitácora de IA | Sí | Repo con `bitacora_proyecto/` 01 a 05; las bitácoras de IA están en cada documento (secciones 13–14 y 9). |

**Documentos no revisados para este plan:** `RutaMx_Documento_Requerimientos.pdf` (v1.0, sustituido por v2.0) y `RutaMx_Entrega_Documentacion_Completa.pdf` (sin seguimiento en git; se asume que compila los anteriores, SUPUESTO sin verificar).

## Revisión de consistencia (Prompt 1)

| # | Hallazgo | Evidencia | Impacto | Pregunta para el equipo |
|---|---|---|---|---|
| H-1 | La ubicación propuesta para M-09 no coincidía con el código real (RESUELTO). | Persistencia (sec. 5) propone `paginas_nav_bar/`; esa carpeta solo contiene `pagina_descubrir/` y `pagina_planear_con_IA/` vacías. El código de la v1 vive en `base_datos/modelos.py` y `app/services/`. | Puede crear archivos en un lugar equivocado (riesgo para RNF-16/17). | Resuelto con la reorganización del repositorio: M-09 va en `base_datos/repositorios/` (ver Paso 3). |
| H-2 | Ya existen `guardar_ruta` y `listar_rutas` en `base_datos/modelos.py` y los usan `/api/rutas` (GET/POST). | `v1/routes.py` líneas 165–202; Persistencia dice "RF-40 ya existe como `listar_rutas`". | Si M-09 los reemplaza, se rompe la v1 (RNF-25). | ¿M-09 convive con las funciones de la v1 o las envuelve? |
| H-3 | El cambio a `rutas_guardadas` toca una tabla que se había acordado no modificar. | Persistencia, sec. 7: espera "confirmación explícita de Angel". | Bloquea la migración y todo lo que dependa de las columnas nuevas. | ¿Angel aprueba el cambio? |
| H-4 | La revisión técnica de Roberto del diseño de persistencia sigue pendiente. | Persistencia, sec. 9 (fila "Revisión") y sec. 10 (pregunta 6). | El plan se apoya en un diseño sin revisar. | ¿Cuándo lo revisa Roberto? |
| H-5 | P-01 (cómo una ruta pasa a pública) y P-03 (valores de categoría y región) siguen abiertos. | Diseño modular sec. 13; Persistencia sec. 7. | Condicionan Descubrir (M-01/M-02), no el almacenamiento básico de M-09. | Se confirma con el cliente (profesor); no se inventa. |
| H-6 | No está dicho quién valida la "ruta válida" (D-03) antes de escribir. | D-03 define ruta válida; Persistencia dice que M-09 "no valida reglas de negocio" pero "garantiza que no se registren datos incompletos". | Riesgo de que nadie valide, o de validar dos veces. | Propuesta: M-05 aplica D-03; M-09 solo impone restricciones de integridad de la BD (NOT NULL, CHECK). ¿De acuerdo? |
| H-7 | Las pruebas de la v1 no cubren Postgres aislado. | `v1/tests/conftest.py` solo apaga la IA de casetas; el modelo usa `ARRAY` y `JSONB` propios de PostgreSQL. | Probar M-09 contra SQLite no funcionaría (SUPUESTO sin verificar). | ¿Qué base de prueba aislada se usará? |

# Paso 2. Primer incremento funcional

## Prioridades

Se evalúan solo los RF/HU que M-09 atiende (diseño modular, sección 4: M-09 → RF-14, 16, 38–40, 42).

| RF/HU | Prioridad | Valor para el usuario | Dependencia | ¿En incremento 1? |
|---|---|---|---|---|
| RF-38, RF-39 / HU-21 (guardar y asociar a la cuenta) | Alta | Sin guardado se pierde el resultado de la planeación. | M-09 + tabla extendida | Sí |
| RF-40 / HU-22 (consultar solo mis rutas) | Alta | Completa el ciclo guardar y recuperar. | M-09 | Sí |
| RF-42 / CA-21.3 / CA-21.4 (guardado atómico y actualización de la misma ruta, D-11) | Alta | Nunca queda información incompleta. | M-09 | Sí |
| RF-44 / CA-22.3 (error de lectura sin dañar otros datos) | Alta | Confianza al recuperar. | M-09 | Sí |
| RNF-11 / PNF-11 (aislamiento entre usuarios) | Alta | Nadie ve ni toca rutas ajenas. | M-09 (filtro por `usuario_id`) | Sí |
| RF-14, RF-16 / HU-07 (copia atómica de una ruta pública) | Media | Conecta Descubrir con Planear. | M-09; la decisión de qué es "pública" depende de P-01 | Sí, como última tarea (se corta primero si falta tiempo) |
| RF-41, RF-15 / HU-23, HU-08 (pedir inicio de sesión) | Alta / Media | Informar al usuario. | M-10 (ya existe) + interfaz | No: no es responsabilidad de M-09 |
| RF-01 a RF-10 (catálogo público) | Alta | Descubrir. | M-02 (consulta) + P-01 + P-03 | No |
| RF-17 a RF-37 (IA) | Alta | Planear. | M-04, M-05, M-07 | No |

## Selección del incremento (Prompt 2): dos opciones

| | Opción A: M-09 con guardado y consulta reales | Opción B: M-05 Gestor de rutas con repositorio simulado en memoria |
|---|---|---|
| RF/HU incluidos | RF-38, 39, 40, 42, 44 (+ RF-14, 16 al final) / HU-21, HU-22 (+ HU-07 en lo que toca a datos) | RF-13 a 16, 21 a 32, 35, 37 a 44 (23 RF) |
| Valor demostrable | Guardar una ruta ficticia, recuperarla solo con la cuenta dueña y comprobar que un fallo no deja nada a medias. | Reglas de rutas probadas sin base de datos real. |
| Módulos | M-09 (+ columnas nuevas de `rutas_guardadas`) | M-05, M-09 simulado |
| Dependencias | Aprobar el cambio de tabla, migración, base de prueba aislada. | Contrato de M-09 y de M-10. |
| Riesgo | Medio: migración en Supabase y pruebas con PostgreSQL. | Alto: M-05 es el módulo más grande (23 RF) y atomicidad; muchas decisiones juntas. |
| Prueba observable | Guardar → listar con la cuenta A (aparece) → listar con la cuenta B (no aparece). | Una operación inválida no cambia la ruta. |

**Información que faltaba para decidir:** H-2 a H-4 (convivencia con la v1, aprobación y revisión); la ubicación (H-1) quedó resuelta con la reorganización.

## Incremento elegido y justificación

**Se elige la Opción A: M-09 Repositorio de rutas.** Justificación:

1. Es la base de la que dependen M-05 (gestor), M-02 (catálogo) y M-06 (rutas guardadas): ninguno puede guardar ni leer sin él (diseño modular, sección 4; Persistencia, pregunta de cierre 1).
2. Se puede probar aislado, sin IA, sin mapas y sin interfaz.
3. Es pequeño y tiene un resultado observable (guardar y recuperar con aislamiento por usuario).
4. M-05, el módulo "más importante" por concentrar la lógica, es también el más grande y se apoya en M-09: construirlo primero obligaría a simular la base y a repetir trabajo. Será el segundo módulo.
5. Ya hay una decisión de persistencia documentada (PostgreSQL de Supabase, extender `rutas_guardadas`) y la entrega de persistencia lo señala como candidato.

## Expresamente fuera del primer incremento

- M-05 Gestor de rutas (reglas de negocio, validación D-03, orquestación de cambios).
- M-10 Control de acceso: se reutiliza lo que existe; no se crea login nuevo (D-13).
- M-01, M-03, M-06 (interfaces); M-04, M-07 (IA); M-08 (mapas).
- Búsqueda y filtros del catálogo (RF-02 a RF-08), que dependen de P-01 y P-03.
- Mecanismo para publicar una ruta (P-01) y valores de categoría y región (P-03).
- Borrar rutas completas (ningún RF lo pide), historial o versiones (D-11), guardar el chat (D-09).
- Cambiar los endpoints `/api/rutas` de la v1.

# Paso 3. Módulos y dependencias

Se distingue la dependencia de ejecución (un módulo necesita a otro) del orden de trabajo (se puede crear un contrato o simulación antes de integrar).

| Módulo | Responsabilidad | Necesita de | Entrega a | Prioridad |
|---|---|---|---|---|
| M-09 Repositorio de rutas | Único acceso a la BD para rutas: crear, actualizar, leer, listar por usuario y copiar de forma atómica. | Tabla `rutas_guardadas` extendida; conexión SQLAlchemy compartida (`base_datos/conexion.py`) | M-05, M-02 | 1 |
| M-10 Control de acceso | Verificar sesión y propiedad (reutiliza la autenticación existente). | `auth_service` existente | M-05 | 2 (ya existe; solo se consume) |
| M-11 Utilerías | Errores seguros, validación, configuración. | Configuración existente | Todos | 2 (reutilizar; solo lo mínimo) |
| M-05 Gestor de rutas | Reglas, validación D-03, atomicidad de cambios. | M-09, M-10, M-11 | M-03, M-01, M-04, M-06 | 3 (siguiente incremento) |
| M-02 Catálogo de rutas públicas | Consulta, búsqueda y filtros del catálogo. | M-09, P-01, P-03 | M-01 | 3 |
| M-06 Rutas guardadas | Vista mínima de rutas personales. | M-05, M-09 | Usuario | 3 |
| M-07 / M-08 / M-04 / M-03 / M-01 | IA, mapas, orquestador e interfaces. | M-05 y otros | Usuario | 4 |

## Mapa de módulos por capa (referencia a la arquitectura)

Fuente: "Diseño modular y arquitectura inicial (actualizado)", secciones 3, 6 y 7. Los once módulos son responsabilidades lógicas dentro de una sola aplicación, no servicios separados. El módulo de este incremento es M-09.

| Capa | Módulos | Relación con este incremento |
|---|---|---|
| Presentación | M-01 Interfaz de Descubrir · M-03 Interfaz de Planear con IA · M-06 Rutas guardadas | Fuera del incremento; consumirán M-05 después. |
| Negocio | M-02 Catálogo · M-04 Orquestador · M-05 Gestor de rutas | Fuera del incremento; M-05 y M-02 llamarán a M-09. |
| Integración | M-07 Adaptador de IA · M-08 Adaptador de mapas | Fuera del incremento. |
| Seguridad | M-10 Control de acceso | Se reutiliza la autenticación existente. |
| **Datos** | **M-09 Repositorio de rutas** | **Módulo de este incremento.** |
| Compartido | M-11 Utilerías transversales | Solo lo mínimo (errores y configuración). |

[[DIAGRAMA]]

## Estructura del repositorio (reorganización del 29 de octubre de 2026)

Para no mezclar lo terminado con lo nuevo y saber dónde está lo que se va a modificar, el repositorio se separó en tres carpetas dentro del mismo proyecto. Hay una sola aplicación: `run.py` la arma y registrará ahí lo de v2.

| Carpeta | Contenido | Puede importar de |
|---|---|---|
| `v1/` | App de la versión 1 (terminada), con sus pruebas | `base_datos` |
| `v2/` | Todo lo nuevo: Descubrir y Planear con Ayuda IA (M-01 a M-08) | `base_datos` y, de v1, solo la autenticación (M-10) |
| `base_datos/` | Conexión, modelos, repositorios (M-09), migraciones y scripts; compartida por v1 y v2 | Nada de v1 ni de v2 |
| Raíz | `run.py`, `config.py`, `instance/`, `documentacion/`, `bitacora_proyecto/` | |

Los cambios a la base de datos solo se permiten si no afectan ni a v1 ni a v2 (compatibles hacia atrás: columnas nuevas opcionales o con valor por defecto, sin borrar ni renombrar). La reorganización no cambió el comportamiento: la misma suite de pruebas dio el mismo resultado antes y después. Con esto, M-09 queda en `base_datos/repositorios/`, sin crear carpetas de primer nivel por módulo (diseño modular, sección 9).

**Orden acordado y por qué (revisado por el equipo):** M-09 primero porque es la hoja del grafo de dependencias (no necesita a ningún módulo nuevo). Después M-05, que lo consume. Contrato antes de integración: se fija la interfaz de M-09 (T-02) y M-05 puede probarse después con un repositorio simulado. Qué puede probarse aislado: todo M-09, con una base de prueba y datos ficticios, sin IA, mapas ni sesión web.

**Interfaz propuesta de M-09 (nombres en español, a confirmar en T-06):**

| Operación | Entradas | Salida | Error |
|---|---|---|---|
| `crear_ruta` | datos de ruta, `usuario_id` | ruta creada (dueño = autor = usuario) | `ErrorRepositorio` sin dejar filas |
| `actualizar_ruta` | `ruta_id`, datos, `usuario_id` | ruta actualizada | `ErrorRepositorio`, la versión anterior queda intacta |
| `obtener_ruta` | `ruta_id`, `usuario_id` | ruta o "no encontrada" | `ErrorRepositorio` |
| `listar_rutas_de_usuario` | `usuario_id` | lista (puede estar vacía) | `ErrorRepositorio` |
| `crear_copia_de_ruta` | `ruta_origen_id`, `usuario_id` | nueva ruta independiente | `ErrorRepositorio` sin copia parcial |

# Paso 4. Backlog técnico

Los cambios en `rutas_guardadas` y en `base_datos/modelos.py` solo se ejecutan tras T-02. Rutas previstas relativas a `Proyecto_RutaMX/`.

| ID | Tarea técnica | RF/HU | Módulo / archivo | Predecesora | Evidencia de terminado |
|---|---|---|---|---|---|
| T-01 | Revisar con Roberto el diseño de persistencia y resolver H-2 y H-6 | Técnica (H-2 a H-6) | `documentacion/` | Ninguna | Acta o nota en `bitacora_proyecto/03_DECISIONES_Y_NOTAS.md` |
| T-02 | Aprobar explícitamente el cambio de columnas en `rutas_guardadas` (H-3) | RF-38, D-10, D-11 | Decisión de Angel | T-01 | Registro de la aprobación en la bitácora 03 |
| T-03 | Definir la base de prueba aislada y los datos ficticios (H-7) | RNF-26, RNF-28 | `base_datos/tests/conftest.py` | T-01 | `pytest` corre sin tocar la base real ni depender del `.env` real |
| T-04 | Escribir el script de migración `ALTER TABLE` de las columnas nuevas, repetible y con respaldo previo | RF-38, RF-40, D-10 | `base_datos/migraciones/migrar_rutas_v2.py` (nombre SUPUESTO) | T-02 | Migración ejecutada primero en una copia; salida guardada |
| T-05 | Extender el modelo `RutaGuardada` con las columnas nuevas y sus restricciones (`visibilidad` CHECK, `duracion_dias` > 0, FK con `ON DELETE SET NULL`) | RF-38, RF-39, D-10 | `base_datos/modelos.py` | T-04 | Las filas anteriores de la v1 siguen leyéndose; pruebas de la v1 en verde |
| T-06 | Escribir los casos de prueba de M-09 (sin implementación, deben fallar al inicio) | RF-38 a RF-44, RNF-11 | `base_datos/tests/test_rutas_repositorio.py` (nombre SUPUESTO) | T-03, T-05 | Archivo de pruebas con casos del Paso 6 |
| T-07 | Implementar `crear_ruta` y `actualizar_ruta` en una transacción con reversión | RF-38, 39, 42; CA-21.1, 21.3, 21.4 | `base_datos/repositorios/rutas_repositorio.py` | T-06 | Pruebas T-06 de crear/actualizar en verde |
| T-08 | Implementar `obtener_ruta` y `listar_rutas_de_usuario` filtrando siempre por `usuario_id` | RF-40, 44; CA-22.1 a 22.4; PNF-11 | mismo archivo | T-07 | Pruebas de lectura y aislamiento en verde |
| T-09 | Implementar `crear_copia_de_ruta` atómica | RF-14, 16; CA-07.1, 07.3, 07.4 | mismo archivo | T-08 | Pruebas de copia en verde; la original no cambia |
| T-10 | Correr la regresión de la v1 y comprobar que `/api/rutas` sigue igual | RNF-25, RNF-29 | `v1/tests/` existentes | T-09 | Suite completa en verde; salida guardada |
| T-11 | Prueba en la app corriendo: guardar una ruta ficticia, verla con la cuenta dueña y no verla con otra | PNF-11; CA-22.1 | Verificación manual | T-10 | Captura o descripción en la bitácora; datos ficticios |
| T-12 | Actualizar la bitácora (01, 02, 03) y el registro de uso de IA | RNF-30, RNF-33 | `bitacora_proyecto/` | T-11 | Archivos actualizados y commit con Conventional Commits |

# Paso 5. Persistencia y configuración

| Decisión | Respuesta del equipo (tomada en la práctica de persistencia) |
|---|---|
| ¿Qué datos serán temporales? | La propuesta de ruta antes de guardar y el estado del chat; viven en memoria de la sesión (D-08, D-09). |
| ¿Qué datos deben mantenerse tras cerrar el sistema? | Rutas con paradas ordenadas, visibilidad, dueño, autor y ruta de origen si es copia. |
| ¿Qué solución se eligió y por qué? | PostgreSQL de Supabase ya usado por la v1, vía SQLAlchemy. Da atomicidad y control por usuario, que un JSON o CSV no dan; SQLite obligaría a una segunda base. |
| ¿Qué módulo accede a esos datos? | M-09, llamado solo por M-05 (y por M-02 para el catálogo). |
| ¿Qué estructura inicial, archivo o esquema hace falta? | Columnas nuevas en `rutas_guardadas`: `descripcion`, `duracion_dias`, `categoria`, `region`, `visibilidad` (por defecto `privada`), `ruta_origen_id`, `autor_id`. Las filas existentes quedan privadas y sin ruta origen. |
| ¿Cómo se evitará almacenar información inválida? | Restricciones de la base (NOT NULL, CHECK de `visibilidad`, `duracion_dias` > 0) más transacción única por guardar y copiar. La validación de negocio (D-03) la aplica M-05 antes de llamar a M-09. |

**Tareas de datos (Prompt 5):** T-04 (migración), T-05 (modelo y restricciones), T-07 a T-09 (almacenamiento, lectura y copia atómicas) y T-03 (base de prueba aislada).

**Riesgos de pérdida o inconsistencia:** `create_all` de SQLAlchemy no modifica tablas existentes, por eso hace falta `ALTER TABLE`; se respalda y se prueba primero en una copia. Paradas en JSONB no permiten consultar paradas sueltas; aceptable para el MVP porque ningún RF lo pide.

# Paso 6. Plan de pruebas

Todas son pruebas de diseño, aún sin código. El estado de todas es "no ejecutada". Datos siempre ficticios; las pruebas no usan el `.env` real ni la red.

| ID | RF/HU / CA | Tipo | Datos / condición | Resultado esperado | Nivel | Evidencia |
|---|---|---|---|---|---|---|
| PR-01 | CA-21.1 / RF-38, 39 | Normal | Usuario A y una ruta ficticia válida | La ruta se guarda, queda asociada a A (dueño y autor) y con visibilidad `privada` | Integración (BD de prueba) | Salida de `pytest` |
| PR-02 | CA-21.2 | Error (datos) | Ruta sin nombre, sin origen o sin paradas | Se rechaza con error claro y no se crea ninguna fila | Unitaria / integración | `pytest`; conteo de filas igual antes y después |
| PR-03 | CA-21.3 / RF-42 | Error (sistema) | Fallo forzado a mitad de la escritura (por ejemplo, excepción simulada) | Se revierte la transacción y no queda una ruta incompleta | Integración | `pytest` |
| PR-04 | CA-21.4 / D-11 | Límite | Ruta ya guardada y modificada; guardar de nuevo | Se actualiza la misma fila y no se crea otra | Integración | `pytest` |
| PR-05 | CA-21.4 | Error (sistema) | Igual que PR-04 con fallo forzado | La versión guardada antes queda intacta | Integración | `pytest` |
| PR-06 | CA-22.1 / RF-40 | Normal | A tiene 2 rutas y B tiene 1 | `listar_rutas_de_usuario(A)` devuelve solo las 2 de A | Integración | `pytest` |
| PR-07 | PNF-11 / RNF-11 | Error (acceso) | B intenta obtener o actualizar una ruta de A | Resultado "no encontrada" o rechazo; la ruta de A no cambia | Integración | `pytest` |
| PR-08 | CA-22.2 | Error (datos) | Ruta guardada con `descripcion` vacía | Se devuelve con la información válida disponible | Unitaria | `pytest` |
| PR-09 | CA-22.3 / RF-44 | Error (sistema) | Fallo forzado de lectura | Error controlado; otras rutas y datos del usuario no se modifican | Integración | `pytest` |
| PR-10 | CA-22.4 | Límite | Usuario sin rutas | Lista vacía, no error | Unitaria | `pytest` |
| PR-11 | CA-07.1 / RF-14 | Normal | Ruta pública de A copiada por B | Nueva fila de B con `ruta_origen_id` = original y autor = autor original; la original no cambia | Integración | `pytest` |
| PR-12 | CA-07.3 / RF-16 | Error (sistema) | Fallo forzado durante la copia | No queda copia parcial | Integración | `pytest` |
| PR-13 | CA-07.4 | Límite | B copia dos veces la misma ruta | Dos copias independientes; ni la original ni la primera copia cambian | Integración | `pytest` |
| PR-14 | Esquema / D-10 | Error (datos) | `visibilidad` distinta de `privada` o `publica`; `duracion_dias` = 0 | La base rechaza el valor | Integración | `pytest` |
| PR-15 | RNF-25, RNF-29 | Regresión | Filas de la v1 sin columnas nuevas | `/api/rutas` y las pruebas actuales siguen en verde | Integración | Suite completa |

**Avisos de cobertura:** (1) CA-21.2 y CA-22.3 exigen "mostrar el motivo / un mensaje" al usuario; M-09 solo devuelve el error, el mensaje visible se prueba en M-05 y en las interfaces (siguiente incremento). (2) CA-07.2 (ruta con información inválida que impide copiar) depende de la validación D-03 de M-05; en M-09 se cubre solo la parte de restricciones de la base (PR-14). (3) Los CA de HU-23 y HU-08 (inicio de sesión) quedan fuera de este incremento.

# Paso 7. Plan de ejecución

Esfuerzo relativo (B/M/A); no se suponen fechas ni horas. Cada tarea tiene un responsable y el otro integrante revisa; la asignación fue revisada y aceptada por Angel y Roberto.

| Orden | Tarea | Responsable | Revisa | Esfuerzo | Entrega / hito | Estado |
|---|---|---|---|---|---|---|
| 1 | T-01 | Roberto | Angel | B | Hito 0: decisiones H-2 y H-6 cerradas | Pendiente |
| 2 | T-02 | Angel | Roberto | B | Hito 0: cambio de tabla aprobado | Pendiente |
| 3 | T-03 | Angel | Roberto | M | Hito 1: base de prueba lista | Pendiente |
| 4 | T-04 | Angel | Roberto | M | Hito 1: migración probada en copia | Pendiente |
| 5 | T-05 | Roberto | Angel | B | Hito 1: modelo extendido, v1 sin romper | Pendiente |
| 6 | T-06 | Roberto | Angel | M | Hito 2: pruebas escritas (fallan al inicio) | Pendiente |
| 7 | T-07 | Angel | Roberto | M | Hito 3: guardar y actualizar en verde | Pendiente |
| 8 | T-08 | Roberto | Angel | M | Hito 3: consulta con aislamiento en verde | Pendiente |
| 9 | T-09 | Angel | Roberto | M | Hito 3: copia atómica en verde (se corta primero si falta tiempo) | Pendiente |
| 10 | T-10 | Roberto | Angel | B | Hito 4: regresión v1 en verde | Pendiente |
| 11 | T-11 | Angel | Roberto | B | Hito 4: demostración de guardar y recuperar | Pendiente |
| 12 | T-12 | Ambos | Ambos | B | Hito 4: bitácora y commit | Pendiente |

**Lógica del orden (propuesta de IA, revisada por el equipo):** primero se cierran las decisiones y se prepara la base (T-01 a T-05), porque bloquean todo; las pruebas se escriben antes que el código (T-06); después se implementa de lo más sencillo a lo más delicado (crear, leer, copiar); al final se hace regresión y la demostración. T-03 y T-04 pueden avanzar en paralelo una vez aprobado T-02. Sin conocer la disponibilidad real no se asignan fechas.

# Paso 8. Riesgos, supuestos y control de cambios

| Riesgo / supuesto | Impacto | Acción preventiva | Responsable |
|---|---|---|---|
| La migración sobre Supabase falla o daña datos de la v1 | Alto (bloqueante) | Respaldar, escribir el script de forma repetible y probarlo en una copia antes de la base real (T-04) | Angel |
| Se pierde el aislamiento entre usuarios | Alto | Toda consulta filtra por `usuario_id`; prueba PR-07 obligatoria (PNF-11) | Roberto |
| SUPUESTO: SQLite no sirve para probar `ARRAY` y `JSONB` | Medio | Resolver H-7 en T-03 antes de escribir pruebas | Angel |
| Cambiar la tabla de la v1 contradice un acuerdo previo | Medio | Aprobación explícita (T-02), columnas opcionales, regresión (T-10) | Angel |
| P-01 y P-03 sin respuesta del cliente | Bajo para este incremento | No se implementan en M-09; se registran como pendientes | Equipo |
| M-05 crecerá demasiado en el siguiente incremento | Medio | Subdividir internamente (diseño modular, sección 11) | Roberto |
| Tiempo del proyecto (8 semanas, 2 integrantes) | Alto | T-09 se corta primero; no se agrega alcance sin autorización | Equipo |

**Control de cambios:** si cambia una decisión aprobada, se registra qué cambió, por qué, qué RF/HU/CA afecta y cómo se refleja en tareas y pruebas.

| Fecha | Qué cambió | Por qué | RF/HU/CA que afecta | Reflejo en tareas y pruebas |
|---|---|---|---|---|
| 29 oct 2026 | El repositorio se separó en `v1/`, `v2/` y `base_datos/`; M-09 va en `base_datos/repositorios/`. | No mezclar versiones y saber dónde está lo que se modifica; la base de datos es base de v1 y v2. | Ninguno (no cambia requerimientos ni criterios). | Se actualizaron las rutas de T-03 a T-10; se cerró H-1; las pruebas de v1 pasan a `v1/tests/`. |

## Revisión crítica del plan (Prompt 8, autoevaluación preliminar)

Hecha por la misma IA que redactó el plan, por lo que **no sustituye** una revisión independiente (idealmente otro modelo o Roberto).

| Nivel | Observación |
|---|---|
| Bloqueante | T-02 (aprobación del cambio de tabla) debe cerrarse antes de T-04, y H-2 y H-6 antes de T-07. |
| Importante | CA-21.2, CA-22.3 y CA-07.2 solo quedan cubiertos parcialmente a nivel de M-09 (ver avisos del Paso 6). RF-14 y RF-16 dependen en la práctica de P-01. |
| Mejora opcional | Definir los nombres exactos de archivos y funciones al iniciar T-06. Considerar una vista de 7 bloques para explicar el plan al grupo. |

Sin tareas huérfanas ni dependencias circulares detectadas. RF-38, 39, 40, 42 y 44 tienen tarea y prueba.

# Bitácora de uso de IA

Herramienta: Claude Code (modelo Sonnet 5.5), operado por Angel Mata. Revisada por Angel y Roberto.

| Paso | Consulta / prompt usado | Propuesta útil | Qué aceptamos o cambiamos | Responsable |
|---|---|---|---|---|
| 1 | Se indicó la guía y se pidió leerla y revisar los documentos del proyecto (equivalente al Prompt 1). | Inventario de insumos y 7 hallazgos de consistencia (H-1 a H-7). | Revisado y aceptado por el equipo (Angel y Roberto) | Angel Mata |
| 2 | Se pidió proponer el módulo más importante como base (equivalente al Prompt 2). | Dos opciones; recomienda M-09. | Revisado y aceptado por el equipo (Angel y Roberto) | Angel Mata |
| 3 a 5 | Secuencia, tareas y datos según los Prompts 3 a 5 de la guía. | Backlog T-01 a T-12 y tabla de persistencia. | Revisado y aceptado por el equipo (Angel y Roberto) | Angel Mata |
| 6 a 8 | Pruebas, plan de ejecución y revisión crítica según los Prompts 6 a 8. | PR-01 a PR-15, hitos y riesgos. | Revisado y aceptado por el equipo (Angel y Roberto) | Angel Mata |
| 9 | Se pidió separar el repositorio en v1, v2 y base_datos (29 oct 2026). | Estructura de carpetas, reglas de dependencia y M-09 en `base_datos/repositorios/`. | Aceptado por el equipo; se actualizaron las rutas del plan. | Angel Mata |

# Paso 9. Verificación final y aprobación del equipo

Solo se marca lo que el documento demuestra. Lo demás queda con acción pendiente.

- [x] Todos los RF del primer incremento (RF-38, 39, 40, 42, 44, 14, 16) están incluidos en una o más tareas.
- [x] Cada tarea importante tiene responsable, dependencia y evidencia de terminado. *Responsables confirmados en la revisión del equipo.*
- [x] Los criterios de aceptación del incremento cuentan con pruebas diseñadas (con los avisos de cobertura parcial del Paso 6).
- [x] Los módulos y archivos previstos coinciden con la arquitectura o se justificó su cambio. *M-09 va en `base_datos/repositorios/` (capa de datos); la reorganización se registró en el control de cambios.*
- [x] La estrategia de persistencia está reflejada en tareas concretas (T-03 a T-05, T-07 a T-09).
- [x] El plan distingue lo incluido y excluido del primer incremento.
- [x] Los riesgos bloqueantes tienen acción y responsable.
- [x] Las sugerencias de IA fueron revisadas por el equipo; no quedan supuestos ocultos. *Revisadas por Angel y Roberto; los supuestos que siguen (H-2, H-6, H-7) están listados como decisiones pendientes.*

## Decisiones pendientes y cómo se resolverán

| Decisión | Cómo se resuelve | Quién |
|---|---|---|
| H-2: convivencia con `guardar_ruta` y `listar_rutas` de la v1 | Decidir si M-09 las envuelve o coexiste (T-01) | Roberto y Angel |
| H-3: aprobar el cambio de columnas en `rutas_guardadas` | Aprobación explícita (T-02) | Angel |
| H-6: quién aplica D-03 | Propuesta: M-05; confirmarlo (T-01) | Roberto y Angel |
| H-7: base de prueba aislada | Decidir en T-03 | Angel |
| P-01 y P-03 | Preguntar al cliente (profesor); fuera de este incremento | Equipo |

**Módulo y tarea con la que comenzaremos:** M-09, tarea T-01 (cierre de H-2 y H-6), seguida de T-02.

**Primera demostración que presentaremos:** guardar una ruta ficticia con la cuenta A, verla en la lista de A, comprobar que no aparece para la cuenta B y que un fallo forzado no deja una ruta incompleta.

*Este plan es un instrumento vivo: se actualiza durante la implementación y todo cambio se registra como indica el Paso 8.*
