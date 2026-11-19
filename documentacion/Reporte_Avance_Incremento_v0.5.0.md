# [V2] Reporte de avance: cuarto incremento de clase, v0.5.0 (Editar por chat, copiar rutas públicas, mapa y cierre)

- Fecha: **19 de noviembre de 2026 (CDMX)**. Equipo: Angel Mata y Roberto Valderrama, con Claude y Codex como apoyo en modo par.
- Objetivo de la sesión: completar el plan de cuatro clases con la edición por chat (eliminar, reordenar y cambiar preferencias), la copia de rutas públicas, el mapa del detalle de Descubrir y el cierre documental.
- Alcance del informe: trabajo del 19 de noviembre. v0.5.0 es el incremento 5 del plan general y el cuarto de los cuatro incrementos de clase, porque v0.1.0 corresponde al repositorio M-09 previo.
- Fuentes: especificación v2.0 (44 RF y 33 RNF), plan de incrementos, plan de trabajo del v0.5.0, bitácoras, el registro del par de IA, la evidencia `Evidencia_v0.5.0_pruebas.md` y las corridas de pruebas de esta sesión. Este reporte no reescribe los anteriores; solo cita sus cifras.

## Qué contiene este reporte

| Lo que se pide | Dónde está | Respuesta corta |
|---|---|---|
| Incrementos desarrollados | Sección 1 | Hay código de los 5 incrementos del plan. v0.5.0 se programó hoy completo; su tag lo pone Angel. |
| Planeado contra real en tiempos | Sección 2 | Referencia planeada: una clase de 90 min. Hay horas del registro del par para los hitos; la hora de inicio y fin de la clase no quedó registrada. |
| Porcentaje de avance del proyecto | Sección 3 | 88.6% de los RF completos según el criterio de simulación de los reportes (39 de 44). |
| Diferencias con la app del incremento anterior | Sección 4 | Se pueden eliminar y reordenar paradas y cambiar duración e intereses por chat, copiar rutas públicas y ver un mapa en el detalle. |

## 1. Incrementos desarrollados

| Versión | Objetivo | Estado al 19 de noviembre |
|---|---|---|
| v0.1.0 | M-09: crear, obtener y listar rutas | Base previa, probada en simulación; tag publicado. |
| v0.2.0 | Planear con IA y generar una ruta estructurada | Probado con IA simulada; tag publicado. |
| v0.3.0 | Guardar, recuperar y agregar paradas por chat | Probado en simulación; tag publicado. |
| v0.4.0 | Descubrir: catálogo, búsqueda, filtros y detalle | Probado en simulación y en PostgreSQL local el 17 de noviembre; tag publicado. |
| v0.5.0 | Edición completa por chat, copiar rutas, mapa y cierre | **Programado y probado en simulación hoy.** Sin commit ni tag todavía: los hace Angel. |

### Trabajo realizado hoy

| Actividad | Resultado del 19 de noviembre | Evidencia |
|---|---|---|
| M1: contrato de M-07 | El adaptador acepta eliminar, reordenar y cambiar preferencias, rechaza campos ajenos y lista las cinco intenciones. | `test_adaptador_ia.py` |
| M2: eliminar y reordenar | M-05 y M-04 eliminan por nombre o posición (origen y destino protegidos) y reordenan; la operación es atómica y avisa lo que no se soporta (RF-34). | `test_gestor_rutas.py`, `test_orquestador.py` |
| M3: preferencias por chat | Cambiar duración e intereses regenera la propuesta; los datos nuevos se confirman solo al aceptar. | `test_orquestador.py` |
| M4: copiar en M-09 | `copiar_publica` es un solo `INSERT ... SELECT` atómico que fija el dueño, deja la copia privada y guarda la ruta de origen; servicio `CopiaRutas` en M-05. | `test_catalogo_repositorio.py`, `test_copia_rutas.py` |
| M5: endpoint y botón de copiar | `POST /v2/descubrir/rutas/<id>/copiar` con sesión y CSRF; sin sesión responde 401 y pide iniciar sesión. | `test_interfaz_descubrir.py`, `test_pantalla_descubrir.py` |
| M6: mapa del detalle | El detalle devuelve los puntos en orden y los cuenta si omite alguno; Leaflet y OpenStreetMap se cargan solo al abrir un detalle con puntos, con aviso si fallan. | `test_catalogo.py`, `test_pantalla_descubrir.py`, ensayo en Node |
| M7: cierre | Regresión, matriz RF-prueba, bitácoras, evidencia y este reporte con su PDF. | `Evidencia_v0.5.0_pruebas.md` |

Todo se hizo con datos ficticios y sin tocar Supabase ni la app principal congelada (`v1/`).

## 2. Planeado contra real: tiempos

### 2.1 Comparación

| Concepto | Planeado | Real de hoy | Diferencia |
|---|---|---|---|
| Tiempo disponible | Una clase de 90 min | Sin registro de inicio y fin de la clase | No calculable con la evidencia disponible. |
| Siete módulos (M1 a M7) | Todos dentro de la clase, con corte previsto del mapa y las preferencias si faltaba tiempo | Los siete módulos se programaron; no se cortó ninguno | Se cumplió el alcance de código; el cierre en navegador no. |
| Pruebas | Regresión sin fallos | 746 aprobadas, 0 fallidas, 39 omitidas, 1 excluida | Sin PostgreSQL ni navegador. |

No se presenta ahorro ni exceso de tiempo: hace falta la duración completa con el mismo alcance que lo planeado, y la medición humana de cada bloque no se registró. El plan sí sugería un reparto orientativo (decisiones 5 min, M1 10, M2 15, M3 10, M4 15, M5 10, M6 10 y cierre 15), pero no hay tiempos reales con qué compararlo.

### 2.2 Hitos comprobables de hoy (hora de CDMX)

| Hora | Evento | Fuente |
|---|---|---|
| 08:23 | Se registra la tabla aprobada de siete pasos de la meta 15. | Registro del par |
| 08:33 a 08:35 | M3 cerrado; M4 tomado y entregado a revisión. | Registro del par |
| 08:39 a 08:40 | M5 entregado y cerrado; se abre el debate del mapa. | Registro del par |
| 08:41 a 08:45 | M6 tomado, implementado y entregado a revisión. | Registro del par |
| 08:45 | Relevo guardado con el estado de la meta. | Registro del par |
| Después | Dos ciclos de corrección del mapa y el cierre M7. | Registro del par |

Las horas provienen del registro del par y son aproximadas al minuto. **No hay commits de hoy**: el historial de Git acredita el último commit del 17 de noviembre (`b64954e`); el trabajo está sin commit en el árbol.

### 2.3 Alcance planeado contra real

Se cumplieron los 13 RF programados. No se verificó nada en navegador ni contra PostgreSQL. Quedaron como limitaciones declaradas CA-18.4 y CA-08.4 (sección 7). La eliminación de rutas guardadas no se hizo porque ningún RF la pide.

## 3. Porcentaje de avance del proyecto

> **Avance acumulado: 88.6% (39 de 44 RF completos y probados en simulación).** Respecto al reporte de v0.4.0 (25 de 44, 56.8%), el v0.5.0 suma 11 RF nuevos y cierra tres que estaban parciales: 14 RF y 31.8 puntos porcentuales.

Se conserva el criterio de los reportes anteriores: RF completos y probados en simulación divididos entre los 44 RF. No es un porcentaje de aceptación final ni hay verificación de extremo a extremo en uso real.

**El plan estimaba 42 de 44 (95.5%) y esta cifra no se alcanza.** Se aplicó el mismo criterio que mantuvo a RF-06 y RF-08 como «programados» en el v0.4.0: lo que depende solo de JavaScript sin ejecutar en navegador no cuenta como completo. Por eso RF-11 y RF-12 (mapa y su aviso) quedan programados y RF-43 (vista de mapa de la ruta única) sigue parcial. Si Angel verifica el navegador, el techo es 42 de 44.

### 3.1 Evolución del avance

| Corte | Completos | Solo programados | Parciales | Sin iniciar | Avance RF |
|---|---|---|---|---|---|
| Reporte anterior, v0.4.0 | 25 | 2 | 4 | 13 | 56.8% |
| **19 de noviembre, tras v0.5.0** | **39** | **4** | **1** | **0** | **88.6%** |

Cada fila suma 44 RF.

### 3.2 Estado de los requerimientos

| Categoría | RF | Cantidad |
|---|---|---|
| Completos en simulación, de incrementos previos | RF-17, 19, 20, 21, 22, 23, 35, 36; RF-25, 26, 33, 38, 39, 40, 41, 42, 44; RF-01 a 05, 07, 09 y 10 (condicionados a P-01 y P-03) | 25 |
| Completos en simulación, de v0.5.0 | RF-13, 14, 15, 16 (copiar); RF-27 a 32 y 34 (editar por chat) | 11 |
| Completos al cerrar la cobertura parcial | RF-18, RF-24 y RF-37 | 3 |
| Solo programados | RF-06 y RF-08 (listado y reinicio de Descubrir); RF-11 y RF-12 (mapa y su aviso): JavaScript sin ejecutar en navegador | 4 |
| Parciales | RF-43: chat e itinerario derivan de la ruta única; falta verificar la vista de mapa | 1 |
| Sin iniciar | Ninguno | 0 |

### 3.3 Requerimientos no funcionales

Se mantiene el conteo conservador de **5 de 33 RNF (15.2%)** probados en simulación. La matriz RF a prueba de la evidencia respalda RNF-26 (al menos un caso por RF) y RNF-33 (trazabilidad) para este incremento; no se suman al conteo hasta que Angel confirme que basta esa evidencia. RNF-13 (HTTPS) y RNF-23 (navegadores) quedan sin verificar (2026-11-19).

### 3.4 Resultados de pruebas de hoy

| Ejecución | Aprobadas | Fallidas | Omitidas | Excluidas |
|---|---|---|---|---|
| Base del v0.4.0, sin PostgreSQL | 529 | 0 | 34 | 1 |
| Corrida con una prueba de contrato desactualizada | 745 | 1 | 39 | 1 |
| **Final, sin PostgreSQL** | **746** | **0** | **39** | **1** |

Las 39 omitidas son pruebas de integración que exigen PostgreSQL desechable (26 de rutas, 5 de migración y 8 de catálogo); son las 34 de antes más 5 nuevas de la copia. La excluida es la prueba de navegador de Planear. No hubo corrida con PostgreSQL local hoy: no respondió en `127.0.0.1:55433`.

## 4. Diferencias con la app del incremento anterior

### 4.1 Funcionalidad de v0.5.0 respecto a v0.4.0

- **Planear por chat:** además de agregar paradas, ahora se pueden eliminar por nombre o posición (el origen y el destino no se tocan), reordenarlas y cambiar solo la duración o los tipos de lugares. Una petición no soportada recibe un aviso que enumera lo que sí se puede hacer.
- **Descubrir:** el detalle de una ruta pública tiene el botón «Copiar a mis rutas». Sin sesión pide iniciarla; con sesión crea una copia privada propia sin tocar la original.
- **Mapa:** el detalle muestra el recorrido con marcadores y una línea que une los puntos en el orden del itinerario. La línea no es el trayecto por carretera.

### 4.2 Qué cambió hoy respecto al estado recibido

| Aspecto | Antes de hoy | Resultado de hoy |
|---|---|---|
| Intenciones de M-07 | Agregar, aclarar y no soportada | Cinco intenciones; las nuevas rechazan campos ajenos. |
| Modificar la ruta | Solo agregar paradas | Eliminar, reordenar y cambiar preferencias, todo atómico. |
| Rutas públicas | Solo consulta | Copia a una ruta propia y privada. |
| Detalle público | Texto y paradas | Además, mapa con aviso si no carga. |
| Pruebas | 529 aprobadas sin PostgreSQL | 746 aprobadas sin PostgreSQL. |

### 4.3 Efecto para el usuario y límites

El chat entiende una operación por mensaje (CA-18.4). Cambiar preferencias regenera la propuesta y, tras validarla, reemplaza la ruta y los datos juntos; solo se pregunta confirmación cuando D-03 la exige. Una ruta publicada sin ruta estructurada de v2, por ejemplo creada en v1, muestra «sin ubicaciones» en el mapa aunque tenga paradas. Los datos no copiables dan un error 503 con mensaje claro, no un 400. **Nada de esto se vio funcionar en un navegador.**

## 5. Hallazgos y correcciones de hoy

| Hallazgo | Causa | Corrección |
|---|---|---|
| M1: no se rechazaban campos ajenos en eliminar y reordenar; fechas de la bitácora equivocadas y una línea «M1 hecho» en lo pendiente | Validación incompleta del contrato y anotaciones apresuradas | Se agregaron las listas de campos permitidos, se corrigieron las fechas y la bitácora 02. |
| M4: la prueba de integración «sin migración» dependía del orden de las pruebas | Asumía un esquema que otras pruebas podían dejar cambiado | La prueba quita las columnas explícitamente y las restaura en `finally`. |
| M5 (observación de la autora de M4): una ruta con datos no copiables responde 503 y no 400 | El error nace en la base y no en la petición | Se dejó como está, porque el mensaje es correcto, y se documentó. |
| M6, hallazgo 1: el ajuste diferido de 150 ms, el reloj de 8 s y los eventos de teselas de un detalle anterior tocaban el mapa del siguiente | Los temporizadores usaban la variable global del mapa vigente | Cada mapa actúa solo sobre su propia instancia y solo mientras es el vigente. |
| M6, hallazgo 2 (primera forma): la carga solo esperaba el script de Leaflet y no sus estilos | Se daba por buena la carga al llegar el JavaScript | Se esperan estilos y script; si uno falla o tarda se muestra el aviso. |
| M6, hallazgo 2 (segunda forma, decidida a favor de la revisora por el usuario): tras un fallo de estilos, `window.L` ya existía y el siguiente detalle dibujaba sin estilos | `window.L` se tomaba como carga completa | Una bandera (`leafletCompleto`) exige ambas cargas; si faltan los estilos se piden de nuevo y no se dibuja antes. |
| Prueba de contrato desactualizada tras la corrección anterior | Buscaba un texto del archivo que cambió | Se actualizó la aserción; el código era correcto. |

Los pasos M2 y M3 (de `codex-par`) y M5 pasaron la revisión sin observaciones de código.

## 6. Decisiones aplicadas en la sesión

- **D-V5-1 (P-02):** el mapa usa Leaflet 1.9.4 con teselas de OpenStreetMap, como v1, sin llave. La decide el equipo, no el profesor.
- **D-V5-2:** las coordenadas salen de las que la ruta ya guardó (`resumen`), sin consultar ningún servicio al abrir el detalle. Los puntos inválidos se omiten y se cuentan.
- **D-V5-3:** la edición por chat amplía el contrato existente de M-07; no se crea otro chat.
- **D-V5-4:** las operaciones nuevas pasan por `aplicar()`, que es atómico.
- **D-V5-5:** cambiar preferencias regenera la propuesta y confirma los datos nuevos solo al aceptar.
- **D-V5-6:** copiar es un solo `INSERT ... SELECT` en M-09 y el servicio vive en M-05.
- **D-V5-7:** el endpoint de copiar reutiliza la sesión y el CSRF que ya existen; el dueño sale de la sesión, nunca del cuerpo.
- **Debate 4 (presentación del mapa):** se fusionaron las propuestas del par. Los marcadores se distinguen por tipo y no se numeran; el pie aclara que la línea no es el trayecto por carretera.
- **Un cambio deliberado a la ruta anterior:** una preferencia extraída con ruta vigente se desvía a la operación de cambiar preferencias; quedó anotado en la bitácora 03.

## 7. Lo que falta comprobar

| Pendiente actual | Condición para cerrarlo |
|---|---|
| Navegador de escritorio y móvil (Descubrir con mapa y copiar; Planear con eliminar, reordenar y preferencias) | Revisar a mano en 1280×900 y 375×812: marcadores, línea, encuadre, aviso con la red cortada, botón de copiar con y sin sesión. Chromium sigue bloqueado. Es lo único que puede mover RF-06, 08, 11 y 12. |
| PostgreSQL real para la copia | Levantar una base desechable y correr las 39 integraciones, entre ellas las 5 de `copiar_publica`; el SQL no se ejecutó contra una base. |
| Migración y publicación en Supabase | Respaldo, ensayo previo y regresión; después aplicar. |
| Regresión de v1 y login real | Aislar su base y comprobar guardar, abrir y copiar con sesión real. |
| IA real de Planear | Configurar proveedor y modelo; las pruebas usan IA simulada. |
| P-01 y P-03 | Decisión del profesor sobre publicación, categorías y regiones. |
| CA-18.4 | Limitación: se interpreta una operación por mensaje. |
| CA-08.4 | Parcial: el servidor está probado; conservar el detalle tras el login no se verificó en navegador. |
| RNF-13 y RNF-23 | HTTPS y navegadores: sin verificar (2026-11-19). |
| Tag y publicación | Angel hace los commits, el tag `v0.5.0` y el push. |

## 8. Evidencias y reproducción

- `documentacion/Evidencia_v0.5.0_pruebas.md`: corridas, lo que no se ejecutó, el ensayo del mapa, la matriz RF-prueba (CP-11 a CP-16, CP-27 a CP-32 y CP-34) y los criterios especiales.
- Bitácoras `01`, `02` y `03` de `bitacora_proyecto/`.

La regresión disponible sin PostgreSQL se reproduce desde la raíz con este comando, dividido en líneas para su lectura:

```sh
env -u RUTAMX_TEST_DB_URL \
  PYTHONDONTWRITEBYTECODE=1 \
  venv/bin/python -m pytest base_datos/tests v2/tests \
  -q -p no:cacheprovider \
  -k 'not test_navegador_escritorio_y_movil'
```

Resultado del 19 de noviembre: **746 passed, 39 skipped, 1 deselected**. El ensayo en Node del mapa ejecuta el `descubrir.js` real con un DOM simulado; no es un navegador y no sustituye la revisión visual.

## 9. Siguiente paso

1. Hacer el commit, el tag `v0.5.0` y el push (Angel), y registrar el hash.
2. Revisar a mano `/v2/descubrir` y `/v2/planear` en escritorio y móvil.
3. Levantar PostgreSQL desechable y correr las 39 integraciones.
4. Preparar la exposición (dos clases) y llevar P-01 y P-03 al profesor.
