# [V2] Reporte de avance: incremento v0.4.0 (Descubrir: catálogo de rutas públicas, búsqueda, filtros y detalle)

- Fecha: 2026-11-12 (CDMX), incremento 4 del plan (el tercero de clase, asignado a la clase 3 de 4 del plan, por confirmar con el calendario real). Equipo: Angel Mata y Roberto Valderrama, con Claude y Codex como apoyo.
- Corte de las cifras: 11:24 (CDMX). Fuente de requerimientos: `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf` (44 RF, 33 RNF). Plan: `documentacion/plan_incrementos.md` (aprobado el 2026-11-05).
- Palabras de estado: **programado** (existe en el código), **probado en simulación** (pasó pruebas sin lo real) y **verificado en uso real** (probado con lo real, con fecha). Lo que no se pudo comprobar dice **sin verificar**. Hoy **ningún RF está verificado de extremo a extremo en uso real**.
- **Condición de este incremento:** el plan lo bloquea hasta resolver P-01 (cómo se marca una ruta pública) y P-03 (valores de categoría y región). Siguen **abiertas ante el profesor**. El equipo avanzó con una **propuesta**, que Angel aprobó al aprobar la tabla de pasos: una ruta es pública solo si su columna `visibilidad` vale `publica`, se marca con un script (no hay botón de publicar en la app) y las listas son categorías Playa, Cultural, Naturaleza, Gastronomía y Pueblo Mágico y regiones Noroeste, Noreste, Occidente, Centro y Sureste. No es una respuesta del profesor.

## Qué contiene este reporte

| Lo que se pide | Dónde está | Respuesta corta |
|---|---|---|
| Incrementos desarrollados | Sección 1 | 4 de 5: el 1 (M-09, v0.1.0), el 2 (Planear con IA, v0.2.0), el 3 (guardar y recuperar, v0.3.0) y el 4 (Descubrir, este v0.4.0). Los cuatro están **probados en simulación**; solo el 1 tiene tag |
| Planeado contra real en tiempos | Sección 2 | Planeado: 90 min (una clase). Real: 14 min del arranque (11:10) al corte (11:24) |
| Porcentaje de avance del proyecto | Sección 3 | **56.8%** del proyecto (25 de 44 requerimientos funcionales completos, probados en simulación); en el reporte anterior era 38.6%. Otros 2 del incremento están solo programados. Sin contar los 10 de este incremento, que dependen de aprobar P-01 y P-03, los firmes son 17 de 44 (38.6%) |
| Diferencias con la app del incremento anterior | Sección 4 | La app ahora tiene una pantalla pública para buscar, filtrar y ver el detalle de rutas; antes solo se podía planear, guardar y reabrir las rutas propias. Hoy el catálogo está vacío: falta ejecutar la migración y publicar rutas |

## 1. Incrementos desarrollados

| # | Versión | Objetivo | RF asignados | Estado al corte |
|---|---|---|---|---|
| 1 | v0.1.0 | M-09 Repositorio de rutas (crear, obtener, listar) | 0 cerrados; evidencia parcial en RF-38, 39, 40 y 42 | Hecho, **probado en simulación** (2026-11-03); tag `v0.1.0` publicado |
| 2 | v0.2.0 | Planear con IA: de la conversación a una ruta estructurada | 12 | Código listo y **probado en simulación** (2026-11-10), publicado en `main`; sin tag |
| 3 | v0.3.0 | Guardar y recuperar rutas, agregar parada, aclaraciones | 9 | Código listo y **probado en simulación** (2026-11-12); commits locales sin push; sin tag |
| 4 | v0.4.0 | Descubrir: catálogo, búsqueda, filtros, detalle | 10 | **Este reporte**: código listo y **probado en simulación** (2026-11-12); sin commit, sin migración ejecutada y sin tag |
| 5 | v0.5.0 | Edición por chat completa, copiar, mapa, cierre | 13 | No iniciado |

Ningún incremento nuevo está **cerrado**: el plan pide además verificarlo en un navegador real, la regresión de lo anterior y el tag (sección 7).

### Lo construido en este incremento (v0.4.0)

| Módulo | Qué hace | Archivos | Pruebas de hoy |
|---|---|---|---|
| Valores del catálogo | Listas propuestas de categorías y regiones, visibilidades y límites, en un solo lugar | `base_datos/catalogo_valores.py` | Cubiertas por las demás |
| M-09 Migración | Agrega las 7 columnas autorizadas (`descripcion`, `duracion_dias`, `categoria`, `region`, `visibilidad`, `ruta_origen_id`, `autor_id`); idempotente, en una transacción con rollback. **No se ejecutó** | `base_datos/migraciones/agregar_columnas_catalogo.py` | 8 pasan y 5 se omiten |
| M-09 y M-02 Repositorio | Consulta pública (palabra clave, duración, categoría, región) y detalle; solo rutas `publica`; sin `usuario_id`, hash ni PIN | `base_datos/repositorios/catalogo_repositorio.py` | 32 pasan y 3 se omiten |
| M-02 Servicio del catálogo | Valida filtros, arma la lista (RF-01 a RF-03) y el detalle con paradas ordenadas (RF-09, RF-10); autor «Nombre A.» o «RutaMx» | `v2/negocio/catalogo.py` | 21 pasan |
| M-01 Endpoints | `GET /v2/descubrir`, `GET /v2/descubrir/rutas` y `GET /v2/descubrir/rutas/<id>`; abiertos a visitantes; errores seguros | `v2/interfaz/rutas_descubrir.py`, `v2/__init__.py` | 48 pasan |
| M-01 Pantalla | Buscador, filtros que actualizan la lista, mensaje sin coincidencias, reinicio, tarjetas y detalle | `v2/templates/descubrir.html`, `v2/static/descubrir.js` y `.css` | Sin prueba de navegador; render comprobado a mano |
| Publicar una ruta | Script de línea de comandos para marcar una ruta como pública (o privada), con autor explícito | `base_datos/scripts/publicar_ruta.py` | 51 pasan |

v1 no se modificó en este incremento. No se tocó el modelo `RutaGuardada`: el catálogo usa SQL propio, así que v1 no se rompe antes de migrar.

## 2. Planeado contra real: tiempos

### 2.1 Comparación

| Concepto | Planeado | Real | Diferencia |
|---|---|---|---|
| Duración del incremento | 1 clase = **90 min** (dato de Angel; el plan asigna un incremento por clase) | **14 min** de la propuesta del plan (11:10) al corte (11:24) | 76 min menos: se usó el 16% de la clase |
| Pasos de trabajo | 6 en la tabla aprobada | 6 (el sexto es este reporte) | Ninguna |
| RF del incremento | 10 | 8 completos en simulación y 2 solo programados (RF-06 y RF-08, JavaScript sin ejecutar) | 2 RF sin prueba ejecutada |
| Verificación en navegador, migración, regresión y tag | Parte del bloque de integración | **No hechos** | Pendiente (sección 7) |

El plan reserva tres bloques por clase: implementación, pruebas (normal, límite y error) e integración (regresión, merge y tag). **No asigna minutos a cada bloque**, por eso la comparación se hace contra la clase completa y no se inventan tiempos por bloque.

Comparación con los incrementos anteriores: el v0.2.0 tomó 37 min, el v0.3.0 tomó 20 min y el v0.4.0 tomó 14 min, todos contra 90 planeados. La ventana medida es tiempo de las dos IA trabajando en paralelo, no horas del equipo humano.

### 2.2 Cómo transcurrió (hora de CDMX, tomada del registro del equipo)

| Hora | Evento |
|---|---|
| 11:10 | Propuesta de la tabla de 6 pasos |
| 11:11 | Tabla aprobada por el usuario, tras ajustarla una vez por las observaciones de la revisora |
| Entre 11:11 y 11:24 | Se cierran los pasos 1 (datos del catálogo), 2 (servicio), 3 (endpoints), 4 (pantalla) y 5 (script de publicar), cada uno tras la revisión de la otra IA |
| 11:24 | Corte de este reporte |

Lo que **no** se puede afirmar: la hora en que empezó la clase, cuánto trabajaron Angel y Roberto antes o fuera de ella, ni cuánto tardaría una persona sola. Con tres muestras todavía no se recalibra el v0.5.0.

### 2.3 Alcance planeado contra real

| Concepto | Planeado | Real |
|---|---|---|
| Módulos del v0.4.0 | M-01, M-02, M-05, M-09 y M-11 | M-01, M-02, M-09 y M-11 con código y pruebas; M-05 no se tocó (el catálogo no pasa por el gestor de rutas) |
| RF-01 a RF-10 | Cubiertos en el incremento | 8 probados en simulación y 2 programados (RF-06, RF-08), condicionados a P-01 y P-03 |
| Bloqueo P-01 y P-03 | El plan pide no asumir cómo se publican las rutas ni inventar categorías o regiones | Se avanzó con una **propuesta** del equipo; siguen abiertas ante el profesor |
| Esquema | Ejecución de las 7 columnas autorizadas el 2026-11-03 con script, prueba en copia y respaldo | Script y pruebas hechos; **ejecución pendiente** (la hace Angel) |
| Función de publicar | «No se agrega una función de publicar» | Cumplido: la publicación es un script administrativo, no una función de la app |
| Pruebas en navegador | Parte del cierre | **No hechas**: no hay herramienta de navegador usable |

Desviaciones que conviene que el profesor conozca:

1. **Se avanzó sin la respuesta del profesor a P-01 y P-03.** Lo implementado es una propuesta; si el profesor decide otra cosa, hay que ajustar `catalogo_valores.py`, la migración y el script.
2. **El catálogo está vacío hasta migrar y publicar.** Sin la migración responde «migración pendiente» y, con ella, no hay rutas públicas hasta que se publique alguna con el script. En esta sesión no se publicó ninguna; si existen rutas públicas en otras bases, está sin verificar (2026-11-12).
3. **Persistencia no comprobada con una base real.** El SQL se probó con una sesión falsa; las 8 pruebas de integración nuevas se omiten sin PostgreSQL desechable.
4. **Verificación en navegador sin hacer**, y la comprobación del render de la plantilla real no quedó como prueba repetible (no estaba en la tabla aprobada).

## 3. Porcentaje de avance del proyecto

> **El proyecto lleva 56.8% de avance**: 25 de 44 requerimientos funcionales están completos y probados en simulación. En el reporte anterior (v0.3.0) eran 17 de 44 (38.6%): este incremento sumó 18.2 puntos. Otros 2 RF (4.5%) están solo programados.
> Los 10 RF del v0.4.0 (8 probados y 2 programados) dependen de que el profesor apruebe la propuesta para P-01 y P-03; sin ellos, los firmes son 17 de 44 (38.6%).
> **Verificado de extremo a extremo en uso real: 0%.** Ninguna función se ha visto todavía con navegador, IA real y base de datos real a la vez.

Cómo se calcula: requerimientos funcionales (RF) completos para su incremento entre los 44 del documento de requerimientos, redondeado a un decimal. «Completo» significa probado en simulación; el plan marca un RF **cerrado** solo cuando su incremento está integrado y con tag, y ninguno lo está todavía.

### 3.1 Cómo ha crecido el avance

| Corte | RF completos | % de 44 | RF parciales | Sin iniciar | Incrementos con código |
|---|---|---|---|---|---|
| Tras v0.1.0 (2026-11-03) | 0 | 0.0% | 4 | 40 | 1 de 5 |
| Tras v0.2.0 (2026-11-10) | 8 | 18.2% | 8 | 28 | 2 de 5 |
| Tras v0.3.0 (2026-11-12) | 17 | 38.6% | 4 | 23 | 3 de 5 |
| **Tras v0.4.0 (2026-11-12)** | **25** | **56.8%** | **4** | **13** | **4 de 5** |
| Meta del plan (v0.5.0, sin recortes) | 44 | 100% | 0 | 0 | 5 de 5 |

Contra el calendario: van 3 de las 4 clases de trabajo (75%, por confirmar) y el proyecto lleva 56.8% de los RF. Falta el v0.5.0 (13 RF: edición por chat, copiar rutas, mapa y cierre) más las 2 clases de exposición. Los 13 que faltan sin iniciar son exactamente los del v0.5.0.

### 3.2 Requerimientos funcionales (44)

| Categoría | RF | Cantidad | % de 44 |
|---|---|---|---|
| Completo para su incremento, probado en simulación | RF-17, 19, 20, 21, 22, 23, 35, 36 (v0.2.0); RF-25, 26, 33, 38, 39, 40, 41, 42, 44 (v0.3.0); RF-01 a 05, 07, 09 y 10 (v0.4.0, condicionados a P-01 y P-03) | 25 | 56.8% |
| Programado, sin prueba ejecutada | RF-06, RF-08 (v0.4.0; JavaScript sin ejecutar) | 2 | 4.5% |
| Parcial, probado en simulación | RF-18, 24, 37, 43 | 4 | 9.1% |
| Sin iniciar | RF-11 a 16, 27 a 32 y 34 | 13 | 29.5% |
| **Verificado de extremo a extremo en uso real** | ninguno | 0 | 0.0% |

En la tabla de crecimiento (3.1) los 2 RF programados no se cuentan como completos ni como parciales ni como sin iniciar: 25 + 2 + 4 + 13 = 44.

Detalle de los 10 RF del v0.4.0:

| RF | Estado | Reserva |
|---|---|---|
| RF-01 Mostrar el catálogo de rutas públicas | Completo, probado en simulación | Repositorio y sesión falsos; sin rutas públicas reales |
| RF-02 Nombre, origen, destino, duración, paradas y autor por ruta | Completo, probado en simulación | Igual |
| RF-03 Indicar si la ruta es de RutaMx o de un usuario | Completo, probado en simulación | «RutaMx» solo con la marca explícita; sin verificar con datos reales |
| RF-04 Buscar por palabras clave | Completo, probado en simulación | SQL `ILIKE` sin verificar en PostgreSQL real |
| RF-05 Filtrar por duración, categoría y región | Completo, probado en simulación | Listas propuestas, no aprobadas por el profesor (P-03) |
| RF-06 Actualizar el listado al cambiar los filtros | **Programado** (solo JavaScript) | El endpoint se probó, pero el JavaScript que actualiza la lista no se ejecutó en ninguna prueba ni navegador |
| RF-07 Mensaje si no hay rutas coincidentes | Completo, probado en simulación | El servidor devuelve el mensaje y está probado; cómo se dibuja en pantalla está programado |
| RF-08 Reiniciar filtros | **Programado** (solo JavaScript) | Se corrigió un defecto del reinicio; sin ejecutar en navegador |
| RF-09 Seleccionar una ruta y ver su detalle | Completo, probado en simulación | Ruta privada o inexistente da el mismo 404 |
| RF-10 Detalle con descripción, origen, destino, duración y paradas ordenadas | Completo, probado en simulación | Una parada mal formada hace fallar el detalle completo |

### 3.3 Requerimientos no funcionales (33)

Solo se cuentan los que tienen una prueba concreta: **5 de 33 (15.2%)** probados en simulación: RNF-12, 14, 19 y 21 (como en el v0.3.0) y **RNF-15** (rutas privadas fuera de Descubrir), probado con repositorio falso y con el SQL generado; falta comprobarlo contra PostgreSQL real. El plan asigna al v0.4.0 también RNF-01, 02, 04, 06, 07, 08 y 24: **no se declaran cumplidos**, no se midieron.

### 3.4 Otras medidas

| Medida | Valor |
|---|---|
| Módulos del v0.4.0 con código y pruebas | 4 de 5 (M-05 no se tocó) |
| Pasos de la tabla cerrados al corte | 5 de 6 (este reporte es el sexto) |
| Archivos nuevos | 14 (9 de código y pantalla, 5 de pruebas) y 1 modificado (`v2/__init__.py`); unas 800 líneas en los archivos de código y pantalla |
| Commits | Sin commit de este incremento al corte; los de v0.3.0 siguen locales, sin push |
| Push y tag del incremento | Sin push y sin tag `v0.4.0` |

## 4. Diferencias con la app del incremento anterior

Se compara la app al terminar el v0.3.0 (el usuario con sesión planeaba, guardaba, listaba, reabría y agregaba paradas a sus propias rutas; no existía forma de ver rutas de otros) con la app al terminar el v0.4.0.

### 4.1 Qué puede hacer ahora el usuario

| Función | Antes (v0.3.0) | Ahora (v0.4.0) |
|---|---|---|
| Planear, guardar, reabrir y agregar paradas | Sí | Igual |
| Ver rutas de otros o de RutaMX | **No existía** | **Nuevo**: página pública `/v2/descubrir`, abierta a visitantes sin sesión |
| Buscar rutas por palabras | No | **Sí**: por nombre, origen, destino o descripción (hasta 80 caracteres) |
| Filtrar | No | **Sí**: por duración (1 a 60 días), categoría y región; la lista se actualiza al cambiar |
| Si no hay coincidencias | — | Mensaje «No hay rutas que coincidan con tu búsqueda…» |
| Reiniciar filtros | — | Botón que borra la búsqueda y los tres filtros |
| Ver el detalle de una ruta | Solo las propias, al reabrir | Descripción, origen, destino, duración, autor y paradas ordenadas, de cualquier ruta pública |
| Marcar una ruta como pública | No existía | Solo un administrador con el script `publicar_ruta.py`; no hay botón en la app |

### 4.2 Qué cambió por dentro

| Aspecto | Antes (v0.3.0) | Ahora (v0.4.0) | Diferencia |
|---|---|---|---|
| RF completos (probados en simulación) | 17 de 44 (38.6%) | 25 de 44 (56.8%) | +8 RF, +18.2 puntos |
| RF solo programados | 0 | 2 (4.5%) | +2 |
| RF parciales | 4 | 4 | Ninguna |
| RF sin iniciar | 23 | 13 | −10 (los que faltan son los del v0.5.0) |
| RNF probados en simulación | 4 de 33 | 5 de 33 | +1 (RNF-15) |
| Pruebas de v2 | 313 pasan y 1 se omite | 382 pasan y 1 se omite | +69 |
| Pruebas de `base_datos` | 49 pasan y 26 se omiten | 140 pasan y 34 se omiten | +91 pasan y +8 omitidas (necesitan PostgreSQL) |
| Pruebas en total | 362 pasan y 27 se omiten | 522 pasan y 35 se omiten | +160 pasan y +8 omitidas |
| Módulos de v2 | Planear, rutas guardadas y servicios | Además el servicio del catálogo (M-02) y la pantalla de Descubrir (M-01) | +1 servicio y +1 pantalla |
| Base de datos | `rutas_guardadas` sin columnas de catálogo | Script de migración listo; **no ejecutado** | Pendiente |
| Archivos nuevos | — | 14 | +14 |
| Esquema de la base | Sin cambios | Sin cambios hasta que se ejecute la migración | Ninguna |
| v1 | 6 líneas en `v1/static/js/main.js` | Sin cambios | Ninguna |

### 4.3 Qué sigue igual y límites

- El catálogo no tiene rutas publicadas por esta sesión (rutas públicas en otras bases: sin verificar, 2026-11-12): hasta ejecutar la migración y publicar rutas con el script, `/v2/descubrir/rutas` responde «migración pendiente» o una lista vacía.
- La IA real sigue sin verificarse: todo se prueba con IA simulada.
- Siguen parciales RF-18, RF-24, RF-37 y RF-43 (cierran en el v0.5.0; el mapa no existe).
- Sigue sin verificarse en navegador y con login real.

## 5. Qué encontró la revisión cruzada

Cada paso lo revisó la IA que no lo escribió. Hallazgos reales corregidos antes de cerrar cada paso:

| Paso | Hallazgo | Resultado |
|---|---|---|
| Plan | Faltaban pruebas de migración, definir de dónde sale el autor (sin copiar `usuario_id` por defecto), la prueba de respuestas tardías en la pantalla y dejar claro que P-01 y P-03 no estaban resueltas | Corregido en la tabla antes de empezar |
| Script de publicar | Cada uso dejaba abierto un contexto de Flask | Corregido con 3 pruebas |
| Pantalla de Descubrir | El botón «Reiniciar filtros» buscaba con los valores anteriores (microtask antes del restablecimiento de los campos); faltaba singular en «1 ruta encontrada» y una espera en el buscador | Corregido (`setTimeout`, singular y espera de 250 ms) |
| Pantalla de Descubrir | La plantilla real no tenía prueba de render persistente | **Pendiente**: el archivo de pruebas no estaba reservado en la tabla |
| Servicio del catálogo | Una parada mal formada hace fallar todo el detalle; el servicio limita la duración a 1 a 60 y el repositorio acepta cualquier entero positivo | Anotado, sin cambio |

## 6. Decisiones tomadas hoy

- **Incremento = v0.4.0**, el tercero de los cuatro de clase.
- **P-01 y P-03 abiertas, con propuesta del equipo:** publicar solo con la columna `visibilidad` y un script; lista corta de categorías y regiones (ver la condición al inicio). Angel eligió esta propuesta y aprobó la tabla.
- **El modelo `RutaGuardada` no cambia:** el catálogo usa SQL propio para que v1 no se rompa antes de migrar.
- **La migración no se ejecuta aún:** las siete columnas ya estaban autorizadas (2026-11-03); la ejecución real la hace Angel, con respaldo.
- **Autor explícito:** el repositorio no infiere autores al leer. Al publicar, el script conserva el `autor_id` que ya tenga la ruta; si no tiene, asigna al dueño como autor de forma explícita; `--rutamx` fuerza el autor vacío y es la única forma de que una ruta aparezca como de RutaMx. Del autor solo se muestra nombre e inicial del apellido.

Detalle en `bitacora_proyecto/03_DECISIONES_Y_NOTAS.md`.

## 7. Lo que no se comprobó

| Pendiente | Por qué | Cómo cerrarlo |
|---|---|---|
| Aprobación del profesor para P-01 y P-03 | El plan las deja abiertas y se avanzó con una propuesta | Consultar al profesor; ajustar `catalogo_valores.py`, la migración y el script si cambia |
| Ejecutar la migración de las 7 columnas | No hay base desechable y la ejecución real es de Angel | Probarla en una copia, con respaldo y regresión de v1 y v2; luego `python base_datos/migraciones/agregar_columnas_catalogo.py` |
| SQL del catálogo y del script contra PostgreSQL real | Las 8 pruebas de integración nuevas se omiten sin `RUTAMX_TEST_DB_URL` | Levantar el PostgreSQL desechable y correr `base_datos/tests` |
| Publicar al menos una ruta | No se publicaron rutas en esta sesión; la existencia de rutas públicas en otras bases está sin verificar (2026-11-12) | Usar `base_datos/scripts/publicar_ruta.py` después de migrar |
| Navegador (`/v2/descubrir`, 1280 y 375 px) | No hay herramienta de navegador usable (Playwright no está instalado; Chromium estuvo bloqueado por macOS) | Abrir la app y revisar a ojo el reinicio, los filtros y el detalle; anotar la fecha |
| Prueba persistente del render de la plantilla real | No estaba en la tabla aprobada | Agregar `v2/tests/test_pantalla_descubrir.py` en un paso con reserva |
| IA real, login real de v1 y regresión de v1 y de `base_datos` | Sin llave de IA; sesión simulada; la suite de v1 escribe en Supabase | Llave y modelo, login real y bases aisladas |
| Commit, push y tags `v0.2.0`, `v0.3.0` y `v0.4.0` | Esperan las verificaciones anteriores | `git push origin main` y luego los tags |

Preguntas abiertas del plan sin respuesta: P-01 y P-03 (con propuesta, sección 6) y P-02 (proveedor de mapas), que decide el v0.5.0.

## 8. Cómo reproducir lo que se afirma

```sh
# Todas las pruebas (sin red, datos ficticios)
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest v2/tests base_datos/tests -q   # 522 passed, 35 skipped

# La app: /v2/descubrir abre, pero la lista responde «migración pendiente» hasta migrar
venv/bin/python run.py                                                              # http://127.0.0.1:5000/v2/descubrir

# Después de migrar y probar en una copia: publicar una ruta guardada (ejemplo con datos inventados)
venv/bin/python base_datos/scripts/publicar_ruta.py 12 --categoria Playa --region Sureste --descripcion "Ruta de ejemplo"
```

## 9. Siguiente paso

1. Consultar con el profesor P-01 y P-03 y ajustar si cambia la propuesta.
2. Probar la migración en un PostgreSQL desechable, ejecutarla con respaldo (Angel) y publicar una ruta.
3. Verificar `/v2/descubrir` en navegador y agregar la prueba persistente de render.
4. Regresión de v1 y `base_datos`, push de los commits locales y tags `v0.2.0`, `v0.3.0` y `v0.4.0`; después sigue el v0.5.0 (edición completa por chat, copiar, mapa y cierre), que necesita la respuesta a P-02.
