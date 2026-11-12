# [V2] Reporte de avance: incremento v0.3.0 (guardar y recuperar rutas, agregar parada y pedir aclaraciones)

- Fecha: 2026-11-12 (CDMX), clase 2 de 4 de trabajo. Equipo: Angel Mata y Roberto Valderrama, con Claude y Codex como apoyo.
- Corte: 08:31 (CDMX). Fuente de requerimientos: `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf` (44 RF, 33 RNF). Plan: `documentacion/plan_incrementos.md` (aprobado el 2026-11-05).
- Palabras de estado: **programado** (existe en el código), **probado en simulación** (pasó pruebas sin lo real) y **verificado en uso real** (probado con lo real, con fecha). Lo que no se pudo comprobar dice **sin verificar**. Hoy **ningún RF está verificado de extremo a extremo en uso real**.

## 1. Resumen

| Dato | Valor |
|---|---|
| Incrementos del plan | 5 (el 1 es M-09, ya hecho; el 2 al 5 son los de clase, v0.2.0 a v0.5.0) |
| Incremento trabajado hoy | 3 (v0.3.0), asignado a la clase 2 de 4 |
| RF del incremento | 9 asignados (RF-25, 26, 33, 38, 39, 40, 41, 42 y 44), todos **probados en simulación** |
| Avance del proyecto | 17 de 44 RF completos en simulación (38.6%); 4 de 44 parciales (9.1%); 23 de 44 sin iniciar (52.3%); 0 de 44 verificados de extremo a extremo en uso real |
| Pruebas | 362 pasan y 27 se omiten (`pytest v2/tests base_datos/tests`): v2 313 pasan y 1 se omite; `base_datos` 49 pasan y 26 se omiten por no haber PostgreSQL desechable |
| Lo que falta para cerrar v0.3.0 | Verificación en navegador, pruebas de integración de `actualizar_ruta` con PostgreSQL, regresión de v1, commit y tag `v0.3.0` |

El incremento **no se declara cerrado**: el código está probado en simulación, pero el criterio de cierre del plan incluye verificarlo en un navegador real, la regresión de lo anterior y el tag (sección 6). Tampoco está cerrado el v0.2.0: sigue sin tag, sin verificación visual y sin IA real.

## 2. Incrementos desarrollados

| # | Versión | Objetivo | RF asignados | Estado al corte |
|---|---|---|---|---|
| 1 | v0.1.0 | M-09 Repositorio de rutas | 0 cerrados; evidencia parcial en RF-38, 39, 40 y 42 | Hecho, **probado en simulación**; tag `v0.1.0` publicado |
| 2 | v0.2.0 | Planear con IA | 12 | Código listo y **probado en simulación** (2026-11-10), publicado en `main`; sin tag |
| 3 | v0.3.0 | Guardar y recuperar rutas, agregar parada, aclaraciones | 9 | **En curso**: código listo y **probado en simulación** (2026-11-12); sin commit ni tag |
| 4 | v0.4.0 | Descubrir: catálogo, búsqueda, filtros, detalle | 10 | No iniciado (bloqueado por P-01 y P-03) |
| 5 | v0.5.0 | Edición por chat completa, copiar, mapa, cierre | 13 | No iniciado |

Avance por incrementos: 1 de 5 cerrado (20%); el 2 y el 3 tienen el código completo en simulación pero ninguno está cerrado. No se suma un porcentaje parcial a esos dos.

### Lo construido hoy en el v0.3.0

| Módulo | Qué hace | Archivos | Pruebas de hoy |
|---|---|---|---|
| M-09 Repositorio | `actualizar_ruta`: reemplaza la misma fila solo del dueño, con rollback | `base_datos/repositorios/rutas_repositorio.py` | 49 pasan y 26 se omiten (7 nuevas de integración omitidas) |
| M-07 Adaptador de IA | `interpretar_modificacion`: agregar parada, aclarar o no soportada | `v2/integracion/adaptador_ia.py` | 59 pasan (23 nuevas) |
| M-05 Gestor de rutas | `agregar_parada` atómica con D-03 | `v2/negocio/gestor_rutas.py` | 87 pasan (19 nuevas) |
| M-04 Orquestador | Agregar parada por chat, pedir aclaración y conservar la intención | `v2/negocio/orquestador.py` | 42 pasan (7 nuevas) |
| Guardado | Guardar (crear o actualizar), listar y recuperar sin migración de esquema | `v2/negocio/guardado_rutas.py` | 13 pasan |
| M-03, M-06, M-10 Interfaz | Endpoints de guardar, abrir y listar con sesión de v1; pantalla de rutas guardadas; botón Guardar y aviso de sesión | `v2/interfaz/rutas_planear.py`, `v2/interfaz/rutas_guardadas.py`, `v2/__init__.py`, `v2/templates/planear_ia.html`, `v2/templates/rutas_guardadas.html`, `v2/static/planear_ia.js` y `.css` | 29 nuevas más las 22 de Planear, todas pasan |

v1 no se modificó. No hay cambios de esquema: los datos de v2 van dentro de `resumen`.

## 3. Planeado contra real

### 3.1 Tiempos

Lo que el plan dice: el v0.3.0 es el incremento de la **clase 2 de 4** y la clase dura **90 minutos** (dato de Angel, 2026-11-10). El plan no estimó minutos por módulo, solo un incremento por clase.

| Hora (CDMX) | Evento |
|---|---|
| 08:14 | Propuesta de la tabla de 8 pasos (se ajustó una vez por observaciones de la revisora) |
| 08:16 | Tabla aprobada por el usuario |
| 08:31 | Corte de este reporte (los 7 pasos anteriores, cerrados por la revisora) |

| Concepto | Planeado | Observado |
|---|---|---|
| Duración del incremento | 1 clase = 90 min | De la aprobación (08:16) al corte (08:31): unos 15 min de ventana observada |
| Pasos de la tabla | 8 | 8 (el octavo es este reporte) |

Lo que **no** se puede afirmar: la hora en que empezó la clase, cuánto trabajaron Angel y Roberto antes o fuera de ella, ni cuánto tardaría una persona sola. Los minutos son tiempo de las dos IA trabajando en paralelo, no horas del equipo humano. Con dos muestras (v0.2.0 y v0.3.0) todavía no se recalibran los incrementos 4 y 5.

### 3.2 Alcance y desviaciones

| Concepto | Planeado | Real |
|---|---|---|
| Módulos del v0.3.0 | M-03, M-04, M-05, M-06, M-09, M-10, M-11 | Todos tienen código y pruebas; M-11 no cambió |
| RF-25, 26, 33, 38, 39, 40, 41, 42, 44 | Cubiertos en el incremento | Probados en simulación |
| Esquema | Sin migración obligatoria para actualizar | Cumplido: contenedor `resumen.rutamx_v2`; las siete columnas autorizadas siguen sin ejecutarse |
| Interpretación de D-11 | «Guardar de nuevo actualiza la misma ruta» | Se actualiza solo si es el mismo usuario y el mismo origen y destino; un viaje distinto crea otra ruta (decisión documentada en `03`, falta que el equipo la confirme) |
| IA real | Adaptador real configurable | Programado, **sin verificar**: no hay llave ni modelo |
| Persistencia real de `actualizar_ruta` | Probada con PostgreSQL desechable | **Sin verificar**: el sistema rechazó el comando que lo levantaba |

Desviaciones que conviene que el profesor conozca:

1. **Persistencia no comprobada con una base real.** Las pruebas de guardado usan un repositorio falso; las 7 de integración nuevas de `actualizar_ruta` se omiten.
2. **Sesión simulada.** La autenticación de v1 (M-10) solo se leyó; en las pruebas la sesión se simula escribiendo el identificador en la cookie firmada.
3. **Verificación en navegador sin hacer**: Playwright no está instalado y Chromium estuvo bloqueado en el v0.2.0; no se buscó eludirlo.
4. **Dos caminos para agregar una parada** (`GestorRutas.agregar_parada` y el armado de propuesta del orquestador): quedó anotado como limpieza pendiente.

### 3.3 Qué encontró la revisión cruzada

Cada paso lo revisó la IA que no lo escribió. Hallazgos reales corregidos antes de cerrar cada paso:

| Paso | Hallazgo | Resultado |
|---|---|---|
| M-04 (orquestador) | Si fallaba la confirmación de una modificación, el siguiente mensaje regeneraba la ruta y se perdían las paradas agregadas | Corregido con una prueba del caso exacto |
| Guardado | Las rutas de v2 rompían «Mis rutas» de v1 al abrirse (faltaban `origen` y `destino` en `resumen`); re-guardar sin nombre borraba el personalizado | Corregido: campos de compatibilidad y nombre conservado |
| Interfaz (endpoints) | Una ruta válida con dos confirmaciones de D-03 no se podía reabrir | Corregido: se resuelven hasta dos confirmaciones, con prueba |
| Pantalla de rutas | Enlaces internos sin destino y un diálogo sin uso | Corregido |
| Adaptador de IA | La posición de la parada se cuenta desde 0 y la del gestor desde 1 (nota de coordinación) | Anotado y cubierto con pruebas del orden |

## 4. Porcentaje de avance

Denominador **44 RF** (o 33 RNF), redondeo a un decimal. «Probado en simulación» no equivale a «cerrado»: el plan marca un RF cerrado cuando su incremento está integrado y con tag, y ningún RF lo está todavía.

### 4.1 Requerimientos funcionales (44)

| Categoría | RF | Cantidad | % de 44 |
|---|---|---|---|
| Completo para su incremento, probado en simulación | RF-17, 19, 20, 21, 22, 23, 35, 36 (v0.2.0) y RF-25, 26, 33, 38, 39, 40, 41, 42, 44 (v0.3.0) | 17 | 38.6% |
| Parcial, probado en simulación | RF-18, 24, 37, 43 | 4 | 9.1% |
| Sin iniciar | RF-01 a 16, 27 a 32 y 34 | 23 | 52.3% |
| **Verificado de extremo a extremo en uso real** | ninguno | 0 | 0.0% |

Reserva general de los 9 RF del v0.3.0: RF-38, 39, 40, 42 y 44 se probaron con un repositorio falso; la persistencia real de M-09 contra PostgreSQL (crear, listar y actualizar) y el guardado con un login real siguen sin verificar. RF-33 y RF-25 se probaron con IA simulada. Los 4 parciales siguen igual que en el v0.2.0 (RF-18, 24 y 37 cierran en el v0.5.0; RF-43 necesita el mapa).

### 4.2 Requerimientos no funcionales (33)

Solo se cuentan los que tienen una prueba concreta. El plan asigna al v0.3.0 RNF-10 y RNF-11; **no se declaran cumplidos**: RNF-11 (cada usuario ve solo sus rutas) está probado con el repositorio falso y sin base real, y RNF-10 no se midió. Los demás conteos no cambian respecto al reporte del v0.2.0.

### 4.3 Otras medidas

| Medida | Valor |
|---|---|
| Módulos del v0.3.0 con código y pruebas | 7 de 7 (M-11 sin cambios) |
| Pasos de la tabla cerrados al corte | 7 de 8 (este reporte es el octavo) |
| Pruebas nuevas | 91 en `v2/tests` (313 contra 222) y 15 que pasan más 7 omitidas en `base_datos/tests` |
| Cambios sin commit | 13 archivos modificados y 4 nuevos en la carpeta de código (736 líneas añadidas y 20 quitadas en lo ya existente, sin contar los archivos nuevos) |
| Commit y tag del incremento | Sin commit y sin tag `v0.3.0` al corte |

## 5. Decisiones tomadas hoy

- **Incremento = v0.3.0**, el segundo de los cuatro de clase.
- **Sin migración de esquema:** los datos de v2 se guardan en `resumen.rutamx_v2`.
- **Compatibilidad con v1:** `resumen` también trae `origen.nombre` y `destino.nombre`; se agregaron los campos que exige el lector de v1; abrir en v1 una ruta de v2 está sin verificar (2026-11-12) y puede dar una vista parcial.
- **D-11 interpretado:** misma fila solo con el mismo usuario y el mismo viaje.
- **Iniciar sesión desde Planear:** en otra pestaña, porque el login vive en v1, que no se toca.
- **Aclaración:** el siguiente mensaje es su respuesta; para otro tema se reinicia.

Detalle en `bitacora_proyecto/03_DECISIONES_Y_NOTAS.md`.

## 6. Lo que no se comprobó

| Pendiente | Por qué | Cómo cerrarlo |
|---|---|---|
| Verificación en navegador (guardar, aviso de sesión, aclaración, `/v2/rutas`; 1280 y 375 px) | Playwright no está instalado y Chromium estuvo bloqueado por macOS en el v0.2.0 | Abrir la app (`venv/bin/python run.py` o la demostración) y revisar a ojo; anotar la fecha |
| Integración de `actualizar_ruta` y del guardado con PostgreSQL | No hay base desechable; el sistema rechazó el comando que la levantaba | Levantar el PostgreSQL desechable y correr `base_datos/tests` con `RUTAMX_TEST_DB_URL` |
| Login real de v1 con guardar y abrir | La sesión se simuló en las pruebas | Iniciar sesión en la app y guardar una ruta |
| IA real | No hay `ANTHROPIC_API_KEY` ni `IA_V2_MODELO` | Conseguir llave y modelo y probar con ellos |
| Regresión de v1 y de `base_datos` | La suite de v1 escribe en Supabase; las de `base_datos` piden base desechable | Base aislada y correr las tres suites |
| Commit y tag `v0.3.0` | Esperan las verificaciones anteriores | Commit `[V2]`, `git push origin main` y luego el tag |

Preguntas abiertas del plan sin respuesta: P-01 (cómo se marca una ruta pública), P-02 (proveedor de mapas) y P-03 (valores de categoría y región). P-01 y P-03 bloquean el v0.4.0.

## 7. Cómo reproducir lo que se afirma

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

## 8. Siguiente paso

1. Verificar en navegador y con un login real, y anotar la fecha.
2. Levantar un PostgreSQL desechable y correr las pruebas de integración de M-09.
3. Regresión de v1 y `base_datos` contra bases aisladas.
4. Si todo sale bien, commit `[V2]`, push y los tags `v0.2.0` y `v0.3.0`; después sigue el v0.4.0, que necesita las respuestas a P-01 y P-03.
