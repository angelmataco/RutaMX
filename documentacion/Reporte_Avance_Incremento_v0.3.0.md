# [V2] Reporte de avance: incremento v0.3.0 (guardar y recuperar rutas, agregar parada y pedir aclaraciones)

- Fecha: 2026-11-12 (CDMX), clase 2 de 4 de trabajo. Equipo: Angel Mata y Roberto Valderrama, con Claude y Codex como apoyo.
- Corte de las cifras: 08:31 (CDMX). Los commits y la redirección de v1 son posteriores (hasta las 08:45). Fuente de requerimientos: `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf` (44 RF, 33 RNF). Plan: `documentacion/plan_incrementos.md` (aprobado el 2026-11-05).
- Palabras de estado: **programado** (existe en el código), **probado en simulación** (pasó pruebas sin lo real) y **verificado en uso real** (probado con lo real, con fecha). Lo que no se pudo comprobar dice **sin verificar**. Hoy **ningún RF está verificado de extremo a extremo en uso real**.

## Qué contiene este reporte

| Lo que se pide | Dónde está | Respuesta corta |
|---|---|---|
| Incrementos desarrollados | Sección 1 | 3 de 5: el 1 (M-09, v0.1.0), el 2 (Planear con IA, v0.2.0) y el 3 (este, v0.3.0). Los tres están **probados en simulación**; solo el 1 tiene tag |
| Planeado contra real en tiempos | Sección 2 | Planeado: 90 min (una clase). Real: 20 min hasta el corte (08:11 a 08:31) |
| Porcentaje de avance del proyecto | Sección 3 | **38.6%** del proyecto (17 de 44 requerimientos funcionales completos, probados en simulación); en el reporte anterior era 18.2% |
| Diferencias con la app del incremento anterior | Sección 4 | La app ahora guarda, lista y reabre rutas y agrega paradas por chat; antes solo creaba una propuesta que se perdía al cerrar |

## 1. Incrementos desarrollados

| # | Versión | Objetivo | RF asignados | Estado al corte |
|---|---|---|---|---|
| 1 | v0.1.0 | M-09 Repositorio de rutas (crear, obtener, listar) | 0 cerrados; evidencia parcial en RF-38, 39, 40 y 42 | Hecho, **probado en simulación** (2026-11-03); tag `v0.1.0` publicado |
| 2 | v0.2.0 | Planear con IA: de la conversación a una ruta estructurada | 12 | Código listo y **probado en simulación** (2026-11-10), publicado en `main`; sin tag |
| 3 | v0.3.0 | Guardar y recuperar rutas, agregar parada, aclaraciones | 9 | **Este reporte**: código listo y **probado en simulación** (2026-11-12); commit local `f7cbf8e` (sin push) y sin tag |
| 4 | v0.4.0 | Descubrir: catálogo, búsqueda, filtros, detalle | 10 | No iniciado (bloqueado por P-01 y P-03) |
| 5 | v0.5.0 | Edición por chat completa, copiar, mapa, cierre | 13 | No iniciado |

Ningún incremento nuevo está **cerrado**: el plan pide además verificarlo en un navegador real, la regresión de lo anterior y el tag (sección 7).

### Lo construido en este incremento (v0.3.0)

| Módulo | Qué hace | Archivos | Pruebas de hoy |
|---|---|---|---|
| M-09 Repositorio | `actualizar_ruta`: reemplaza la misma fila solo del dueño, con rollback | `base_datos/repositorios/rutas_repositorio.py` | 49 pasan y 26 se omiten (7 nuevas de integración omitidas) |
| M-07 Adaptador de IA | `interpretar_modificacion`: agregar parada, aclarar o no soportada | `v2/integracion/adaptador_ia.py` | 59 pasan (23 nuevas) |
| M-05 Gestor de rutas | `agregar_parada` atómica con D-03 | `v2/negocio/gestor_rutas.py` | 87 pasan (19 nuevas) |
| M-04 Orquestador | Agregar parada por chat, pedir aclaración y conservar la intención | `v2/negocio/orquestador.py` | 42 pasan (7 nuevas) |
| Guardado | Guardar (crear o actualizar), listar y recuperar sin migración de esquema | `v2/negocio/guardado_rutas.py` | 13 pasan |
| M-03, M-06, M-10 Interfaz | Endpoints de guardar, abrir y listar con sesión de v1; pantalla de rutas guardadas; botón Guardar y aviso de sesión | `v2/interfaz/rutas_planear.py`, `v2/interfaz/rutas_guardadas.py`, `v2/__init__.py`, `v2/templates/planear_ia.html`, `v2/templates/rutas_guardadas.html`, `v2/static/planear_ia.js` y `.css` | 29 nuevas más las 22 de Planear, todas pasan |

Cambio mínimo en v1 (autorizado por Angel el 2026-11-12): `abrirRutaGuardada` en `v1/static/js/main.js` redirige a `/v2/rutas` si la ruta es de v2 (6 líneas). No hay cambios de esquema: los datos de v2 van dentro de `resumen`.

## 2. Planeado contra real: tiempos

### 2.1 Comparación

| Concepto | Planeado | Real | Diferencia |
|---|---|---|---|
| Duración del incremento | 1 clase = **90 min** (dato de Angel; el plan asigna un incremento por clase) | **20 min** del arranque (08:11) al corte (08:31) | 70 min menos: se usó el 22% de la clase |
| Duración con las correcciones posteriores | 90 min | 34 min hasta las 08:45 (commits, redirección de v1 y reporte corregido) | 56 min menos: 38% de la clase |
| Pasos de trabajo | 8 en la tabla aprobada | 8 (el octavo es este reporte) | Ninguna |
| RF del incremento | 9 | 9 completos en simulación | Ninguna |
| Verificación en navegador, regresión y tag | Parte del bloque de integración | **No hechos** | Pendiente (sección 7) |

El plan reserva tres bloques por clase en este orden: implementación, pruebas (normal, límite y error) e integración (regresión, merge y tag). **No asigna minutos a cada bloque**, por eso la comparación se hace contra la clase completa y no se inventan tiempos por bloque.

Comparación con el incremento anterior: el v0.2.0 tomó 37 min (planeados 90) y el v0.3.0 tomó 20 min. La ventana medida es corta porque los minutos son de las dos IA trabajando en paralelo, no horas del equipo humano.

### 2.2 Cómo transcurrió (hora de CDMX, tomada del registro del equipo)

| Hora | Evento |
|---|---|
| 08:11 | Arranque de la meta del incremento |
| 08:14 | Propuesta de la tabla de 8 pasos (se ajustó una vez por observaciones de la revisora) |
| 08:16 | Tabla aprobada por el usuario |
| 08:20 a 08:21 | Se cierran el orquestador y el servicio de guardado, ambos tras corregir un defecto que halló la revisión |
| 08:24 a 08:28 | Endpoints entregados y corregidos; revisión de la pantalla |
| 08:31 | Corte de este reporte (los 7 pasos anteriores, cerrados por la revisora) |
| 08:34 | La revisora observa cuatro afirmaciones del reporte; se corrigen y se cierra la meta |

Lo que **no** se puede afirmar: la hora en que empezó la clase, cuánto trabajaron Angel y Roberto antes o fuera de ella, ni cuánto tardaría una persona sola. Con dos muestras (v0.2.0 y v0.3.0) todavía no se recalibran los incrementos 4 y 5.

### 2.3 Alcance planeado contra real

| Concepto | Planeado | Real |
|---|---|---|
| Módulos del v0.3.0 | M-03, M-04, M-05, M-06, M-09, M-10, M-11 | Todos tienen código y pruebas; M-11 no cambió |
| RF-25, 26, 33, 38, 39, 40, 41, 42, 44 | Cubiertos en el incremento | Probados en simulación |
| Esquema | Sin migración obligatoria para actualizar | Cumplido: contenedor `resumen.rutamx_v2`; las siete columnas autorizadas siguen sin ejecutarse |
| Interpretación de D-11 | «Guardar de nuevo actualiza la misma ruta» | Se actualiza solo si es el mismo usuario y el mismo origen y destino; un viaje distinto crea otra ruta (confirmado por Angel el 2026-11-12) |
| IA real | Adaptador real configurable | Programado, **sin verificar**: no hay llave ni modelo |
| Persistencia real de `actualizar_ruta` | Probada con PostgreSQL desechable | **Sin verificar**: el sistema rechazó el comando que lo levantaba |

Desviaciones que conviene que el profesor conozca:

1. **Persistencia no comprobada con una base real.** Las pruebas de guardado usan un repositorio falso; las 7 de integración nuevas de `actualizar_ruta` se omiten.
2. **Sesión simulada.** La autenticación de v1 (M-10) solo se leyó; en las pruebas la sesión se simula escribiendo el identificador en la cookie firmada.
3. **Verificación en navegador sin hacer**: Playwright no está instalado y Chromium estuvo bloqueado en el v0.2.0; no se buscó eludirlo.
4. **Dos caminos para agregar una parada** (`GestorRutas.agregar_parada` y el armado de propuesta del orquestador): quedó anotado como limpieza pendiente.

## 3. Porcentaje de avance del proyecto

> **El proyecto lleva 38.6% de avance**: 17 de 44 requerimientos funcionales están completos y probados en simulación. En el reporte anterior (v0.2.0) eran 8 de 44 (18.2%): este incremento sumó 20.4 puntos.
> **Verificado de extremo a extremo en uso real: 0%.** Ninguna función se ha visto todavía con navegador, IA real y base de datos real a la vez.

Cómo se calcula: requerimientos funcionales (RF) completos para su incremento entre los 44 del documento de requerimientos, redondeado a un decimal. «Completo» significa probado en simulación; el plan marca un RF **cerrado** solo cuando su incremento está integrado y con tag, y ninguno lo está todavía.

### 3.1 Cómo ha crecido el avance

| Corte | RF completos | % de 44 | RF parciales | Sin iniciar | Incrementos con código |
|---|---|---|---|---|---|
| Tras v0.1.0 (2026-11-03) | 0 | 0.0% | 4 | 40 | 1 de 5 |
| Tras v0.2.0 (2026-11-10) | 8 | 18.2% | 8 | 28 | 2 de 5 |
| **Tras v0.3.0 (2026-11-12)** | **17** | **38.6%** | **4** | **23** | **3 de 5** |
| Meta del plan (v0.5.0, sin recortes) | 44 | 100% | 0 | 0 | 5 de 5 |

Contra el calendario: van 2 de las 4 clases de trabajo (50%) y el proyecto lleva 38.6% de los RF. Faltan v0.4.0 y v0.5.0 más las 2 clases de exposición. El v0.4.0 está bloqueado por las preguntas P-01 y P-03.

### 3.2 Requerimientos funcionales (44)

| Categoría | RF | Cantidad | % de 44 |
|---|---|---|---|
| Completo para su incremento, probado en simulación | RF-17, 19, 20, 21, 22, 23, 35, 36 (v0.2.0) y RF-25, 26, 33, 38, 39, 40, 41, 42, 44 (v0.3.0) | 17 | 38.6% |
| Parcial, probado en simulación | RF-18, 24, 37, 43 | 4 | 9.1% |
| Sin iniciar | RF-01 a 16, 27 a 32 y 34 | 23 | 52.3% |
| **Verificado de extremo a extremo en uso real** | ninguno | 0 | 0.0% |

Reserva de los 9 RF del v0.3.0: RF-38, 39, 40, 42 y 44 se probaron con un repositorio falso; la persistencia real de M-09 contra PostgreSQL (crear, listar y actualizar) y el guardado con un login real siguen sin verificar. RF-33 y RF-25 se probaron con IA simulada. Los 4 parciales siguen igual que en el v0.2.0 (RF-18, 24 y 37 cierran en el v0.5.0; RF-43 necesita el mapa).

### 3.3 Requerimientos no funcionales (33)

Solo se cuentan los que tienen una prueba concreta: **4 de 33 (12.1%)** probados en simulación (RNF-12, 14, 19 y 21), igual que en el v0.2.0. El plan asigna al v0.3.0 RNF-10 y RNF-11; **no se declaran cumplidos**: RNF-11 (cada usuario ve solo sus rutas) está probado con el repositorio falso y sin base real, y RNF-10 no se midió.

### 3.4 Otras medidas

| Medida | Valor |
|---|---|
| Módulos del v0.3.0 con código y pruebas | 7 de 7 (M-11 sin cambios) |
| Pasos de la tabla cerrados al corte | 7 de 8 (este reporte es el octavo) |
| Commits locales | `f7cbf8e` (el incremento: 22 archivos, 1737 líneas añadidas y 30 quitadas) y `8057244` (redirección de v1 hacia v2); ninguno subido a `origin/main` |
| Push y tag del incremento | Sin push y sin tag `v0.3.0` |

## 4. Diferencias con la app del incremento anterior

Se compara la app al terminar el v0.2.0 (solo creaba una propuesta de ruta por chat, que se perdía al cerrar la pantalla) con la app al terminar el v0.3.0.

### 4.1 Qué puede hacer ahora el usuario

| Función | Antes (v0.2.0) | Ahora (v0.3.0) |
|---|---|---|
| Crear una ruta por chat | Sí: propuesta con origen, destino y paradas | Igual |
| Guardar la ruta | **No**: se perdía al reiniciar o cerrar | **Sí**: botón Guardar; crea la ruta o actualiza la misma fila si es el mismo usuario y el mismo viaje; sin sesión responde que hace falta iniciar sesión |
| Ver las rutas guardadas | No existía en v2 | **Nuevo**: página `/v2/rutas` (y su lista en JSON) |
| Reabrir una ruta guardada | No | **Sí**: se abre en Planear, se revalida con D-03 y se resuelven hasta dos confirmaciones |
| Agregar una parada | No (RF-24 solo cubría crear) | **Sí**: «agrega X» con posición opcional, validada con D-03 y atómica |
| Preguntas de aclaración | Solo pedía datos faltantes del viaje | **Además** pide aclaración si el cambio es ambiguo; el siguiente mensaje es su respuesta |
| «Mis rutas» de v1 con una ruta de v2 | No existían rutas de v2 | Redirige a `/v2/rutas` (cambio mínimo autorizado en v1) |
| Iniciar sesión | No se pedía | Aviso con enlace al login de v1, en otra pestaña |

### 4.2 Qué cambió por dentro

| Aspecto | Antes (v0.2.0) | Ahora (v0.3.0) | Diferencia |
|---|---|---|---|
| RF completos (probados en simulación) | 8 de 44 (18.2%) | 17 de 44 (38.6%) | +9 RF, +20.4 puntos |
| RF parciales | 8 | 4 | Los 4 de M-09 (RF-38, 39, 40, 42) pasaron a completos |
| Pruebas de v2 | 222 pasan y 1 se omite | 313 pasan y 1 se omite | +91 |
| Pruebas de `base_datos` | 34 pasan y 19 se omiten | 49 pasan y 26 se omiten | +15 pasan y +7 omitidas (necesitan PostgreSQL) |
| Pruebas en total | 256 pasan y 20 se omiten | 362 pasan y 27 se omiten | +106 pasan y +7 omitidas |
| Funciones de M-09 | crear, obtener, listar (sin uso desde v2) | además `actualizar_ruta`, ya usada por el guardado | +1 |
| Módulos de v2 | 6 (M-03, M-04, M-05, M-07, M-08, M-11) | los mismos más el servicio de guardado y la pantalla de rutas | +1 servicio y +1 pantalla |
| Archivos nuevos | — | `v2/negocio/guardado_rutas.py`, `v2/interfaz/rutas_guardadas.py`, `v2/templates/rutas_guardadas.html`, `v2/tests/test_guardado_rutas.py`, `v2/tests/test_interfaz_guardadas.py` | 5 |
| Esquema de la base | Sin cambios | Sin cambios: los datos de v2 van en `resumen.rutamx_v2` | Ninguna |
| v1 | Sin cambios | 6 líneas en `v1/static/js/main.js` | Excepción autorizada |

### 4.3 Qué sigue igual

- La IA real sigue sin verificarse: todo se prueba con IA simulada.
- Siguen parciales RF-18, RF-24, RF-37 y RF-43 (cierran en el v0.5.0; el mapa no existe).
- Sigue sin verificarse en navegador y con login real.

## 5. Qué encontró la revisión cruzada

Cada paso lo revisó la IA que no lo escribió. Hallazgos reales corregidos antes de cerrar cada paso:

| Paso | Hallazgo | Resultado |
|---|---|---|
| M-04 (orquestador) | Si fallaba la confirmación de una modificación, el siguiente mensaje regeneraba la ruta y se perdían las paradas agregadas | Corregido con una prueba del caso exacto |
| Guardado | Las rutas de v2 rompían «Mis rutas» de v1 al abrirse (faltaban `origen` y `destino` en `resumen`); re-guardar sin nombre borraba el personalizado | Corregido: campos de compatibilidad y nombre conservado |
| Interfaz (endpoints) | Una ruta válida con dos confirmaciones de D-03 no se podía reabrir | Corregido: se resuelven hasta dos confirmaciones, con prueba |
| Pantalla de rutas | Enlaces internos sin destino y un diálogo sin uso | Corregido |
| Adaptador de IA | La posición de la parada se cuenta desde 0 y la del gestor desde 1 (nota de coordinación) | Anotado y cubierto con pruebas del orden |

## 6. Decisiones tomadas hoy

- **Incremento = v0.3.0**, el segundo de los cuatro de clase.
- **Sin migración de esquema:** los datos de v2 se guardan en `resumen.rutamx_v2`.
- **Compatibilidad con v1:** `resumen` también trae `origen.nombre` y `destino.nombre`. Con autorización de Angel (2026-11-12), `abrirRutaGuardada` de v1 redirige a `/v2/rutas` si la ruta es de v2; programado, sin verificar en navegador (2026-11-12).
- **D-11 interpretado:** misma fila solo con el mismo usuario y el mismo viaje (confirmado por Angel el 2026-11-12).
- **Iniciar sesión desde Planear:** en otra pestaña, porque el login vive en v1.
- **Aclaración:** el siguiente mensaje es su respuesta; para otro tema se reinicia.

Detalle en `bitacora_proyecto/03_DECISIONES_Y_NOTAS.md`.

## 7. Lo que no se comprobó

| Pendiente | Por qué | Cómo cerrarlo |
|---|---|---|
| Verificación en navegador (guardar, aviso de sesión, aclaración, `/v2/rutas`, la redirección de v1; 1280 y 375 px) | Playwright no está instalado y Chromium estuvo bloqueado por macOS en el v0.2.0 | Abrir la app (`venv/bin/python run.py` o la demostración) y revisar a ojo; anotar la fecha |
| Integración de `actualizar_ruta` y del guardado con PostgreSQL | No hay base desechable; el sistema rechazó el comando que la levantaba | Levantar el PostgreSQL desechable y correr `base_datos/tests` con `RUTAMX_TEST_DB_URL` |
| Login real de v1 con guardar y abrir | La sesión se simuló en las pruebas | Iniciar sesión en la app y guardar una ruta |
| IA real | No hay `ANTHROPIC_API_KEY` ni `IA_V2_MODELO` | Conseguir llave y modelo y probar con ellos |
| Regresión de v1 y de `base_datos` | La suite de v1 escribe en Supabase; las de `base_datos` piden base desechable | Base aislada y correr las tres suites |
| Push y tag `v0.3.0` | Esperan las verificaciones anteriores | `git push origin main` y luego el tag |

Preguntas abiertas del plan sin respuesta: P-01 (cómo se marca una ruta pública), P-02 (proveedor de mapas) y P-03 (valores de categoría y región). P-01 y P-03 bloquean el v0.4.0.

## 8. Cómo reproducir lo que se afirma

```sh
# Todas las pruebas (sin red, datos ficticios)
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest v2/tests base_datos/tests -q   # 362 passed, 27 skipped

# La app (sin IA configurada muestra «Planear con IA no está configurado»)
venv/bin/python run.py                                                              # http://127.0.0.1:5000/v2/planear y /v2/rutas

# Demostración aislada con IA simulada: solo sirve para ver la planeación y el HTML.
# No registra el login de v1 ni configura la base: iniciar sesión desde este servidor
# no basta; guardar, abrir y la pantalla de rutas se prueban con `run.py`.
venv/bin/python scripts/demo_planear_v2.py                                          # http://127.0.0.1:5055/v2/planear
```

## 9. Siguiente paso

1. Verificar en navegador y con un login real, y anotar la fecha.
2. Levantar un PostgreSQL desechable y correr las pruebas de integración de M-09.
3. Regresión de v1 y `base_datos` contra bases aisladas.
4. Si todo sale bien, push de los commits locales y los tags `v0.2.0` y `v0.3.0`; después sigue el v0.4.0, que necesita las respuestas a P-01 y P-03.
