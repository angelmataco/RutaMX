# [V2] Reporte de avance: incremento v0.2.0 (Planear con IA)

- Fecha: 2026-11-10 (CDMX), clase 1 de 4 de trabajo. Equipo: Angel Mata y Roberto Valderrama, con Claude y Codex como apoyo.
- Corte de las cifras: 09:49 (CDMX). Fuente de requerimientos: `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf` (44 RF, 33 RNF). Plan: `documentacion/plan_incrementos.md` (aprobado el 2026-11-05).
- Palabras de estado: **programado** (existe en el código), **probado en simulación** (pasó pruebas sin lo real) y **verificado en uso real** (probado con lo real, con fecha). Lo que no se pudo comprobar dice **sin verificar**. Hoy **ningún RF está verificado de extremo a extremo en uso real**. Lo único comprobado con algo real es una integración parcial: un servidor Flask levantado de verdad, atendido por HTTP, con IA simulada y Nominatim real, que resolvió Ciudad de México, Puebla y Oaxaca (`relation:1376330`, `relation:1376491`, `relation:2529822`) y devolvió la propuesta. No incluye navegador ni IA real.

## Qué contiene este reporte

| Lo que se pide | Dónde está | Respuesta corta |
|---|---|---|
| Incrementos desarrollados | Sección 1 | 2 de 5: el 1 (M-09, v0.1.0, con tag) y el 2 (Planear con IA, v0.2.0, este reporte, **probado en simulación**) |
| Planeado contra real en tiempos | Sección 2 | Planeado: 90 min (una clase). Real: 37 min del arranque (09:12) al corte (09:49) |
| Porcentaje de avance del proyecto | Sección 3 | **18.2%** del proyecto (8 de 44 requerimientos funcionales completos, probados en simulación); antes de este incremento era 0% |
| Diferencias con la app del incremento anterior | Sección 4 | Antes de este incremento solo existía el repositorio de rutas en la base de datos, sin pantalla de v2; ahora hay una pantalla de chat que genera una ruta con paradas validadas |

## 1. Incrementos desarrollados

| # | Versión | Objetivo | RF asignados | Estado al corte |
|---|---|---|---|---|
| 1 | v0.1.0 | M-09 Repositorio de rutas (crear, obtener, listar) | 0 cerrados; evidencia parcial en RF-38, 39, 40 y 42 | Hecho, **probado en simulación** (2026-11-03); tag `v0.1.0` publicado el 2026-11-05 |
| 2 | v0.2.0 | Planear con IA: de la conversación a una ruta estructurada | 12 | **Este reporte**: código listo y **probado en simulación** (2026-11-10); sin tag |
| 3 | v0.3.0 | Guardar y recuperar rutas, agregar parada, aclaraciones | 9 | No iniciado |
| 4 | v0.4.0 | Descubrir: catálogo, búsqueda, filtros, detalle | 10 | No iniciado (bloqueado por P-01 y P-03) |
| 5 | v0.5.0 | Edición por chat completa, copiar, mapa, cierre | 13 | No iniciado |

El v0.2.0 **no se declara cerrado**: el plan pide además verificarlo en un navegador real, la regresión de lo anterior y el tag (sección 7).

### Lo construido en este incremento (v0.2.0)

| Módulo | Qué hace | Archivos | Pruebas (resultado de hoy) |
|---|---|---|---|
| M-11 Utilerías | Errores con mensaje seguro, validación de entradas, constantes de límites | `v2/utilerias.py` | 40 pasan |
| M-07 Adaptador de IA | Contrato único de IA; adaptador real configurable (Anthropic, por variables de entorno) y adaptador simulado | `v2/integracion/adaptador_ia.py` | 36 pasan |
| M-05 Gestor de rutas | Ruta estructurada como fuente única, validación D-03 completa, cambios atómicos, vistas derivadas | `v2/negocio/gestor_rutas.py` | 68 pasan |
| M-04 Orquestador | Conversación: acumula datos, pide solo lo faltante, genera la propuesta, pide confirmaciones, conserva la ruta previa si falla | `v2/negocio/orquestador.py` | 35 pasan |
| M-08 Verificador geográfico | Valida lugares con Nominatim (OpenStreetMap): id y coordenadas | `v2/integracion/verificador_geografico.py` | 21 pasan |
| M-03 Interfaz de Planear | Pantalla `/v2/planear`: chat, itinerario aparte, confirmaciones, endpoints con sesión en servidor | `v2/interfaz/rutas_planear.py`, `v2/templates/planear_ia.html`, `v2/static/planear_ia.js` y `.css`, `run.py` | 22 pasan y 1 se omite (la de navegador) |
| Demostración | Servidor aparte con IA de reglas fijas y franja «Modo demostración» | `scripts/demo_planear_v2.py` | Probado con el cliente de pruebas de Flask |

v1 no se modificó (sin cambios en `v1/`). La app se arma en `run.py`, que registra el blueprint de v2.

## 2. Planeado contra real: tiempos

### 2.1 Comparación

| Concepto | Planeado | Real | Diferencia |
|---|---|---|---|
| Duración del incremento | 1 clase = **90 min** (dato de Angel, 2026-11-10; el plan asigna un incremento por clase) | **37 min** del arranque (09:12) al corte (09:49) | 53 min menos: se usó el 41% de la clase |
| Desde que se aprobó la tabla | 90 min | 28 min (09:21 a 09:49) | 62 min menos |
| Pasos de trabajo | 6 en la tabla aprobada | 6, más M-08 y el script de demostración fuera de la tabla | +2 pasos no planeados |
| RF del incremento | 12 | 8 completos y 4 parciales en simulación (los 4 parciales ya estaban planeados como parciales) | Ninguna |
| Bloque de implementación | Parte de la clase | Los 6 módulos con código y pruebas al corte | Cumplido |
| Bloque de pruebas (normal, límite, error) | Parte de la clase | 222 pruebas con casos normal, límite y error en simulación | Cumplido |
| Bloque de integración (regresión, merge, tag) | Parte de la clase | **Parcial**: 9 commits locales `[V2]` (2026-11-10); sin regresión de v1, sin push y sin tag | Pendiente (sección 7) |

El plan **no asigna minutos a cada bloque** (solo «un incremento por clase» con tres bloques), por eso la comparación se hace contra la clase completa y no se inventan tiempos por bloque.

Lo que **no** se puede afirmar con estos datos: la hora a la que empezó la clase, cuánto trabajaron Angel y Roberto antes o fuera de ella, ni cuánto tardaría una persona sola en lo que hicieron las IA. Los 37 minutos son tiempo de las IA trabajando en equipo, no horas del equipo humano. Con esta sola muestra tampoco se calibran los incrementos 3 a 5 (el plan pide recalibrar al cerrar el v0.2.0, y todavía no está cerrado).

### 2.2 Cómo transcurrió (hora de CDMX, tomada del registro del equipo)

| Hora | Evento |
|---|---|
| 09:12 | Arranque de la sesión de Claude (anfitriona); Codex se registró después (su primer relevo es de las 09:16) |
| 09:18 | Propuesta de la tabla de 6 pasos (se ajustó dos veces por observaciones de la revisora) |
| 09:21 | Tabla aprobada por el usuario |
| 09:35 | M-08 creado fuera de la tabla (la tabla aprobada no se podía reabrir) |
| 09:37 | Debate de la pantalla acordado (2 rondas) |
| 09:44 | Chromium no arranca en el entorno de la IA (bloqueo de macOS); verificación visual no hecha |
| 09:49 | Corte de este reporte |

### 2.3 Alcance planeado contra real

| Concepto | Planeado | Real |
|---|---|---|
| Módulos del v0.2.0 | M-03, M-04, M-05, M-07, M-08, M-11 | Los seis tienen código y pruebas |
| Cobertura de RF-18, RF-24, RF-37 | Parcial, cierre en v0.5.0 | Igual |
| Validación de ruta (D-03) | M-05 la aplica | La primera versión solo revisaba forma y aceptaba lugares inexistentes; la corrigió la revisión cruzada (ver sección 5) |
| IA real | Adaptador real configurable | Adaptador real programado, **sin verificar**: no hay llave ni modelo; todo se probó con IA simulada |
| Reparto de IA | Claude analiza, planea y documenta; Codex desarrolla y prueba | En la práctica Claude también escribió M-11, M-05, M-08 y la demostración, y Codex escribió M-07, M-04 y M-03; cada paso lo revisó la otra IA |

Desviaciones que conviene que el profesor conozca:

1. **M-08 no estaba en la tabla.** El plan lo listaba entre los módulos del incremento, pero ningún paso lo construía. Se descubrió al corregir M-05 (D-03 exige coordenadas de una fuente geográfica). Se creó fuera de la tabla por indicación del usuario porque la herramienta de coordinación no permite reabrir una tabla aprobada. Lo revisó la otra IA como parte del paso de la pantalla, sin paso formal propio.
2. **Sin llave de IA.** Por eso los RF que dependen de la IA no se pueden dar por verificados.
3. **Verificación visual sin hacer** por el bloqueo de Chromium en el entorno de la IA; la hará el usuario a ojo (sección 7).

## 3. Porcentaje de avance del proyecto

> **El proyecto lleva 18.2% de avance**: 8 de 44 requerimientos funcionales están completos y probados en simulación. Antes de este incremento eran 0 de 44 (0%): este incremento sumó 18.2 puntos.
> **Verificado de extremo a extremo en uso real: 0%.** Ninguna función se ha visto todavía con navegador, IA real y base de datos real a la vez.

Cómo se calcula: requerimientos funcionales (RF) completos para su incremento entre los 44 del documento de requerimientos, redondeado a un decimal. «Completo» significa probado en simulación; el plan marca un RF **cerrado** solo cuando su incremento está integrado y con tag, y ninguno lo está todavía.

### 3.1 Cómo ha crecido el avance

| Corte | RF completos | % de 44 | RF parciales | Sin iniciar | Incrementos con código |
|---|---|---|---|---|---|
| Tras v0.1.0 (2026-11-03) | 0 | 0.0% | 4 | 40 | 1 de 5 |
| **Tras v0.2.0 (2026-11-10)** | **8** | **18.2%** | **8** | **28** | **2 de 5** |
| Meta del plan (v0.5.0, sin recortes) | 44 | 100% | 0 | 0 | 5 de 5 |

Contra el calendario: va 1 de las 4 clases de trabajo (25%) y el proyecto lleva 18.2% de los RF. Faltan los incrementos v0.3.0 a v0.5.0 más las 2 clases de exposición.

### 3.2 Requerimientos funcionales (44)

| Categoría | RF | Cantidad | % de 44 |
|---|---|---|---|
| Completo para el v0.2.0, probado en simulación | RF-17, 19, 20, 21, 22, 23, 35, 36 | 8 | 18.2% |
| Parcial, probado en simulación | RF-18, 24, 37, 43 (del v0.2.0) y RF-38, 39, 40, 42 (de M-09, v0.1.0) | 8 | 18.2% |
| Sin iniciar | RF-01 a 16, 25 a 34, 41, 44 | 28 | 63.6% |
| **Verificado de extremo a extremo en uso real** | ninguno (la integración por HTTP con Nominatim real no cuenta: falta navegador e IA real) | 0 | 0.0% |

Por qué los 4 del v0.2.0 son parciales: RF-18, RF-24 y RF-37 se prueban solo con la creación de la ruta y se cierran en el v0.5.0 (agregar, eliminar, reordenar, preferencias); RF-43 pide chat, itinerario **y mapa** y el mapa no existe todavía (solo hay los puntos con coordenadas). Los 8 completos tienen una reserva: RF-21 y RF-36 se probaron con IA simulada, y RF-17 y RF-23 (pantalla e itinerario) no se vieron en un navegador.

Detalle de los 12 RF del v0.2.0:

| RF | Estado | Reserva |
|---|---|---|
| RF-17 Entrar y empezar la conversación | Completo, probado en simulación | Pantalla sin ver en navegador |
| RF-18 Describir el viaje (solo «crear ruta» soportada) | Parcial | Cierra en v0.5.0 |
| RF-19 Aceptar origen, destino, duración e intereses | Completo, probado en simulación | IA simulada |
| RF-20 Pedir solo lo que falta | Completo, probado en simulación | IA simulada |
| RF-21 Generar propuesta inicial | Completo, probado en simulación | Sin IA real |
| RF-22 Propuesta con origen, destino y paradas ordenadas | Completo, probado en simulación | — |
| RF-23 Representación estructurada aparte del chat | Completo, probado en simulación | Pantalla sin ver en navegador |
| RF-24 Reflejar cambios en la ruta estructurada | Parcial | Cierra en v0.5.0 |
| RF-35 Informar si no hay ruta válida y pedir cambios | Completo, probado en simulación | Geografía simulada en las pruebas; con Nominatim real, por HTTP, se resolvieron tres lugares (ver el encabezado) y un lugar inventado devolvió «no identificado» |
| RF-36 Error de IA conserva la ruta previa | Completo, probado en simulación | Sin IA real |
| RF-37 Sin cambios parciales si falla una operación | Parcial | Cierra en v0.5.0 |
| RF-43 Chat, itinerario y mapa consistentes | Parcial | Falta el mapa (v0.5.0) |

### 3.3 Requerimientos no funcionales (33)

Solo se cuentan los que tienen una prueba concreta. Los demás no se declaran cumplidos.

| Categoría | RNF | Cantidad | % de 33 |
|---|---|---|---|
| Probado en simulación | RNF-12 (validar entradas), RNF-14 (sin datos sensibles en errores), RNF-19 (constantes fuera de la lógica), RNF-21 (servicios externos encapsulados) | 4 | 12.1% |
| Programado, sin verificar en navegador | RNF-03, RNF-05, RNF-09 | 3 | 9.1% |
| Asignados al v0.2.0 sin comprobar | RNF-16, 17, 18, 20, 22, 32 | 6 | 18.2% |
| Resto del proyecto, sin iniciar | los otros 20 | 20 | 60.6% |

### 3.4 Otras medidas

| Medida | Valor |
|---|---|
| Módulos del v0.2.0 con código y pruebas | 6 de 6 (100%) |
| Pasos de la tabla cerrados al corte | 5 de 6 (este reporte es el sexto) |
| Código nuevo de v2 (sin pruebas) | 909 líneas de Python (recuento de Codex, 2026-11-10) |
| Pruebas nuevas de v2 | 222 (más 1 omitida) |
| Commits y tag del incremento | 9 commits locales con prefijo `[V2]` (hechos el 2026-11-10 tras el corte); sin push a GitHub y sin tag `v0.2.0` |

## 4. Diferencias con la app del incremento anterior

Se compara la app al terminar el v0.1.0 (la app v1 ya terminada más el repositorio de rutas M-09 en la base de datos, sin nada de v2 visible) con la app al terminar el v0.2.0.

### 4.1 Qué puede hacer ahora el usuario

| Función | Antes (v0.1.0) | Ahora (v0.2.0) |
|---|---|---|
| Planear con chat en v2 | **No existía** nada de v2 | **Nuevo**: pantalla `/v2/planear` con chat e itinerario aparte |
| Qué entiende el chat | — | Origen, destino, duración e intereses; pide solo lo que falta |
| Propuesta de ruta | — | Ruta con origen, destino y paradas ordenadas, generada por la IA |
| Validación de lugares | — | Cada lugar se valida con una fuente geográfica (Nominatim) y se piden confirmaciones si el origen es igual al destino o hay repetidos |
| Si la IA falla | — | Se conserva la ruta anterior y los datos que el usuario ya dio |
| Planear con IA de v1 | Existía como ventana del formulario, con asignación determinista | Sigue igual; la de v2 es una pantalla distinta y no la reemplaza |
| Guardar la ruta | Solo desde v1; v2 no tenía rutas | Todavía no (llega en el v0.3.0) |

### 4.2 Qué cambió por dentro

| Aspecto | Antes (v0.1.0) | Ahora (v0.2.0) | Diferencia |
|---|---|---|---|
| RF completos (probados en simulación) | 0 de 44 (0%) | 8 de 44 (18.2%) | +8 RF, +18.2 puntos |
| RF parciales | 4 (los de M-09) | 8 | +4 |
| Módulos de v2 | 0 | 6 (M-03, M-04, M-05, M-07, M-08, M-11) | +6 |
| Código nuevo de v2 | 0 | 909 líneas de Python (sin pruebas) | +909 |
| Pruebas de v2 | 0 | 222 pasan y 1 se omite | +222 |
| Pruebas de `base_datos` | 34 pasan y 19 se omiten | Igual | Ninguna |
| Pruebas en total (`v2` y `base_datos`) | 34 pasan y 19 se omiten | 256 pasan y 20 se omiten | +222 pasan y +1 omitida |
| Entrada de la app | `run.py` solo con v1 | `run.py` registra también el blueprint de v2 | +1 |
| Servicios externos | Los de v1 | Además un verificador geográfico (Nominatim) y un adaptador de IA configurable | +2 |
| Esquema de la base | Sin cambios | Sin cambios | Ninguna |
| v1 | Terminada | Sin cambios | Ninguna |

### 4.3 Qué sigue igual

- v1 no se tocó.
- M-09 (crear, obtener, listar) no cambió; todavía nadie lo usa desde v2 (se usa en el v0.3.0).

## 5. Qué encontró la revisión cruzada

Cada paso lo revisó la IA que no lo escribió. Hallazgos reales corregidos antes de cerrar cada paso:

| Paso | Hallazgo | Resultado |
|---|---|---|
| M-11 | La bitácora de pendientes tenía una línea de trabajo ya terminado | Corregido |
| M-05 | Validaba solo la forma: aceptaba lugares inexistentes y origen igual a destino sin confirmar, contra D-03 | Corregido: D-03 completo con verificador geográfico inyectable y confirmaciones; 39 pruebas pasaron a 68 |
| M-04 | Si la IA fallaba al generar la ruta, se perdían los datos que el usuario ya había dado | Corregido: se conservan y el reintento no vuelve a pedirlos |
| Tabla del plan | Faltaba el adaptador real de IA, el registro de v2 desde `run.py` en vez de desde v1, y la verificación en navegador | Corregido en el plan antes de empezar |

## 6. Decisiones tomadas hoy

- **Incremento = v0.2.0.** «Implementación 1» se tomó como el primero de los 4 incrementos de clase (el plan llama incremento 1 a M-09, que ya estaba hecho).
- **IA simulada por ahora.** No hay llave ni modelo oficial; la API real queda pendiente.
- **M-08 con Nominatim**, el mismo proveedor de coordenadas que ya usa el proyecto, limitado a México, una petición por segundo y sin datos personales.
- **Pantalla acordada entre las dos IA:** página propia `/v2/planear` sin tocar v1, dos tarjetas en escritorio y pestañas en móvil, confirmaciones en `<dialog>`, efectos protegidos conservados.

## 7. Lo que no se comprobó

| Pendiente | Por qué | Cómo cerrarlo |
|---|---|---|
| Verificación visual (chat, itinerario, error que conserva la ruta, 1280 y 375 px) | Chromium no arranca en el entorno de la IA (bloqueo de macOS) | Abrir `http://127.0.0.1:5055/v2/planear` con la demostración (sección 8) y revisar a ojo; después registrarlo con fecha |
| IA real | No hay `ANTHROPIC_API_KEY` ni `IA_V2_MODELO` | Conseguir una llave y un modelo, probar RF-21 y RF-36 con ellos |
| Regresión de v1 y de `base_datos` | Las pruebas de v1 escriben en la base real de Supabase (documentado) y las de `base_datos` piden una base desechable (`RUTAMX_TEST_DB_URL`) | Base aislada y correr las tres suites |
| Mapa (parte de RF-43) | Es del v0.5.0 y depende de P-02 | Incremento 5 |
| `SECRET_KEY` por defecto en `config.py` | Valor de desarrollo; con él la sesión de la conversación se podría falsificar | Exigir una llave real antes de publicar |
| Push y tag `v0.2.0` | El push lo hace el usuario; el tag espera la verificación visual y la regresión | `git push origin main`; luego el tag |

Preguntas abiertas del plan que siguen sin respuesta: P-01 (cómo se marca una ruta pública), P-02 (proveedor de mapas) y P-03 (valores de categoría y región). P-01 y P-03 bloquean el v0.4.0.

## 8. Cómo reproducir lo que se afirma

```sh
# Todas las pruebas de v2 (sin red, datos ficticios)
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest v2/tests          # 222 passed, 1 skipped

# La app normal (sin IA configurada muestra «Planear con IA no está configurado»)
venv/bin/python run.py                                                   # http://127.0.0.1:5000/v2/planear

# Demostración con IA simulada (franja «Modo demostración: respuestas de prueba»)
venv/bin/python scripts/demo_planear_v2.py                               # http://127.0.0.1:5055/v2/planear
```

Frases que entiende la IA de la demostración: «Salgo de Ciudad de México», «Voy a Oaxaca durante 3 días» o «de León a Guanajuato en 2 días». Es un simulado con reglas fijas, no entiende lenguaje natural. Con Ciudad de México a Oaxaca propone las paradas Puebla y Tehuacán. Los lugares se validan con Nominatim real (necesita internet); sin red, `RUTAMX_DEMO_GEO_REAL=0` usa una geografía falsa.

## 9. Siguiente paso

1. Revisar a ojo la pantalla con la demostración y registrar el resultado con fecha.
2. Preparar una base aislada para la regresión y correr las tres suites.
3. Si ambas salen bien, subir los commits `[V2]` con `git push origin main` y crear el tag `v0.2.0`, y recalibrar los incrementos 3 a 5 con lo medido.
4. Mientras no haya llave de IA, el v0.3.0 (guardar, recuperar, agregar parada) se puede avanzar con la IA simulada.
