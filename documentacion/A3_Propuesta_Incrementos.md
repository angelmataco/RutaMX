# [V2] A3: propuesta de incrementos con ficha por incremento

- Fecha: 2026-11-05 (CDMX). Autora: claude-par. Revisora: codex-par. **Propuesta: el usuario decide el número final y cada ficha** (Aceptada / modificada / rechazada).
- Fuente única: `documentacion/RutaMx_Documento_Requerimientos_v2.0.pdf`. Entradas: `A1_Verificacion_Especificacion.md`, `A1_Conteo_Independiente_Codex.md`, `A2_Inventario_Requerimientos.md`. Consigna: `Consigna_Plan_Incremental.md` (prompt A3).

## 1. Restricciones del equipo

| Dato | Respuesta |
|---|---|
| Semanas disponibles hasta la entrega final | 3 semanas (dicho por el usuario, 2026-11-05) |
| Clases restantes | 6 en total: **4 clases de trabajo y 2 de exposición** (dicho por el usuario, 2026-11-05). Los incrementos se construyen en las 4 de trabajo; las 2 de exposición no cuentan para desarrollar |
| Integrantes | 2: Roberto Valderrama y Angel Mata (sec. 1.2 del documento) |
| Número de incrementos que pueden cerrar | Se propone **4** (v0.2.0 a v0.5.0), uno por clase de trabajo, como escenario sujeto a la calibración de la sección 2 |
| Reparto de IA | Claude analiza, planea y documenta; Codex desarrolla y prueba; cada paso lo revisa la otra IA y el equipo decide y verifica (reparto invertido respecto a la consigna, acordado con el usuario) |
| Punto de partida | Incremento 1 = módulo M-09 en `main` (3 operaciones: crear, obtener, listar), tag `v0.1.0` por publicar. v1 es el sitio existente y no cuenta como RF cumplidos (decisión del usuario) |

## 2. Cuántos incrementos caben y por qué

**Propuesta (escenario, no certeza): 4 incrementos de 12, 9, 10 y 13 RF, uno por clase de trabajo.** Cada incremento exige tareas pequeñas con un commit y un push cada una, pruebas normal/límite/error, regresión de los anteriores, contraste con la especificación y tag.

- **Qué se sabe y qué no.** Se sabe: 44 RF y 33 RNF por repartir, 4 clases de trabajo y 2 de exposición, 2 integrantes y reparto de IA (Claude planea, Codex desarrolla, cada paso lo revisa la otra IA). **No se sabe:** la duración de cada clase, cuánto trabajo se hace fuera de clase ni el ritmo real de cada tarea. Por eso el tamaño por incremento es una estimación mía por número de RF y por riesgo, **no una medición**, y 4 incrementos es el escenario más ambicioso razonable, no una garantía.
- **Margen de integración.** En cada clase se reserva el último bloque para regresión, merge y tag; no se planean tareas nuevas en ese bloque. Las clases de exposición quedan libres de desarrollo.
- **Calibración.** Al cerrar el v0.2.0 (el de mayor riesgo) se compara lo planeado con lo hecho y se reajusta el tamaño de los siguientes en el registro de cambios al plan. Si el v0.2.0 no cabe en una clase, el plan pasa al escenario de 3 incrementos.
- **Si algo no cabe**, queda explícito: se recorta primero del v0.5.0 (RF-11 y RF-12, luego RF-34 y las preferencias RF-31 y RF-32) y se registra como pendiente con el incremento donde se atendería, como pide la consigna. Lo anterior no se recorta.
- Se agrupa por flujo de usuario, no por capa técnica (incremento ejecutable de extremo a extremo): Planear (v0.2.0), guardar y recuperar (v0.3.0), Descubrir (v0.4.0) y edición completa, copia y mapa más cierre (v0.5.0). Orden según los cuatro criterios de la consigna: (1) dependencias; (2) prioridad de las HU de la sec. 7 (Alta primero); (3) lo de mayor riesgo técnico primero (M-04 y M-07, sec. 10.4); (4) incremento ejecutable e integrado con el anterior.
- **Alternativa de 3 incrementos** (escenario conservador). Grupos resultantes, con los 44 RF asignados una sola vez: **(A)** v0.2.0 igual que arriba, 12 RF (RF-17 a 24, 35, 36, 37, 43); **(B)** guardar, agregar parada y lo Alto de Descubrir, 14 RF (RF-25, 26, 33, 38 a 42, 44, 01, 02, 03, 09, 10); **(C)** resto de Descubrir, edición restante, copia y mapa, 18 RF (RF-04 a 08, 27 a 32, 34, 13 a 16, 11, 12). Los RNF se reparten igual por flujo y el cierre de pruebas y documentación va en (C). Pierde un tag y la entrega intermedia de Descubrir, y (C) queda muy cargado.

## 3. Asignación de requerimientos funcionales (cada RF en un solo incremento)

| Incremento | RF incluidos | Total |
|---|---|---|
| 1 (v0.1.0, ya en `main`) | Ninguno cerrado; M-09 aporta evidencia parcial a RF-38, 39, 40 y 42 | 0 |
| 2 (v0.2.0) | RF-17, RF-18, RF-19, RF-20, RF-21, RF-22, RF-23, RF-24, RF-35, RF-36, RF-37, RF-43 | 12 |
| 3 (v0.3.0) | RF-25, RF-26, RF-33, RF-38, RF-39, RF-40, RF-41, RF-42, RF-44 | 9 |
| 4 (v0.4.0) | RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08, RF-09, RF-10 | 10 |
| 5 (v0.5.0) | RF-11, RF-12, RF-13, RF-14, RF-15, RF-16, RF-27, RF-28, RF-29, RF-30, RF-31, RF-32, RF-34 | 13 |
| **Total** | | **44** |

Comprobación (se repite en la sección 8): cada RF del 01 al 44 aparece una sola vez en las filas de esta tabla.

## 4. Asignación de requerimientos no funcionales (cada RNF en un solo incremento)

Los RNF son transversales (sec. 6): se asigna cada uno al incremento donde se comprueba por primera vez o donde se cierra. Los de pruebas (RNF-26, 27, 28, 29, 33) se **practican en todos los incrementos** (cada uno agrega pruebas y corre la regresión) y se **cierran** en el v0.5.0. **RNF-32** (instrucciones para configurar y ejecutar, y entorno de pruebas documentado) se escribe en el v0.2.0 porque RNF-06 y RNF-07 (v0.4.0) dependen de ese entorno (sec. 6); se actualiza en cada incremento y se consolida al final.

| Incremento | RNF incluidos |
|---|---|
| 2 (v0.2.0) | RNF-03, RNF-05, RNF-09, RNF-12, RNF-14, RNF-16, RNF-17, RNF-18, RNF-19, RNF-20, RNF-21, RNF-22, RNF-32 |
| 3 (v0.3.0) | RNF-10, RNF-11 |
| 4 (v0.4.0) | RNF-01, RNF-02, RNF-04, RNF-06, RNF-07, RNF-08, RNF-15, RNF-24 |
| 5 (v0.5.0) | RNF-13, RNF-23, RNF-25, RNF-26, RNF-27, RNF-28, RNF-29, RNF-30, RNF-31, RNF-33 |

## 5. Fichas por incremento

### Incremento 2 · v0.2.0: Planear con IA: de la conversación a una ruta estructurada

| Campo | Respuesta |
|---|---|
| Incremento y versión | Incremento 2 · v0.2.0 |
| Objetivo en una frase | El usuario conversa con la IA, esta pide los datos que faltan y le entrega una ruta (origen, destino, paradas) mostrada como itinerario estructurado, sin perder la ruta previa si la IA falla. |
| RF incluidos | RF-17, RF-18, RF-19, RF-20, RF-21, RF-22, RF-23, RF-24, RF-35, RF-36, RF-37, RF-43 (12) |
| HU incluidas (sec. 7) | HU-09, HU-10, HU-11, HU-12, HU-19, HU-20 |
| RNF que se verifican aquí | RNF-03, RNF-05, RNF-09, RNF-12, RNF-14, RNF-16, RNF-17, RNF-18, RNF-19, RNF-20, RNF-21, RNF-22, RNF-32 |
| Criterios de aceptación (sec. 8) | 25 criterios: todos los CA de HU-09, HU-10, HU-11, HU-12, HU-19, HU-20; se prueban todos |
| Módulos involucrados (sec. 10.3) | M-03, M-04, M-05, M-07, M-08, M-11 |
| Depende de | Incremento 1 (M-09 existe, aunque este incremento aún no guarda). Reutiliza la autenticación existente (D-13); el servicio de IA se encapsula en M-07 (RNF-21). |
| Pruebas mínimas: normal, límite y error | Casos de prueba CP-nn de la matriz 9.1 (misma numeración que su RF), p. ej. CP-17, CP-18, CP-19, CP-20 .... Normal: CA-09.1, CA-10.1, CA-11.1 (+4 más). Límite: CA-09.4, CA-10.4, CA-11.4 (+3 más). Error de datos: CA-09.2, CA-10.2, CA-11.2 (+3 más). Error de sistema: CA-09.3, CA-10.3, CA-11.3 (+3 más). Más regresión de los incrementos anteriores (RNF-29). |
| Rama de Git | `incremento-2` |
| Fecha de cierre | Clase 1 de 4 (por confirmar con el calendario real) |
| Por qué se agrupa así | Riesgo técnico más alto del proyecto (M-04 y M-07, sec. 10.4 y 12); sus HU son prioridad Alta (sec. 7) y todo lo demás de Planear parte de la propuesta (HU-11) y de la ruta estructurada (HU-12, D-08). |
| Decisión del equipo y justificación | [Aceptada / modificada / rechazada] · pendiente de que el usuario revise |

### Incremento 3 · v0.3.0: Guardar y recuperar rutas, agregar parada y pedir aclaraciones

| Campo | Respuesta |
|---|---|
| Incremento y versión | Incremento 3 · v0.3.0 |
| Objetivo en una frase | El usuario autenticado guarda su ruta generada (y al volver a guardarla se actualiza esa misma ruta, D-11), la consulta después, se le pide iniciar sesión si no lo está, y puede agregar paradas por chat con aclaración cuando la instrucción es ambigua. |
| RF incluidos | RF-25, RF-26, RF-33, RF-38, RF-39, RF-40, RF-41, RF-42, RF-44 (9) |
| HU incluidas (sec. 7) | HU-13, HU-17, HU-21, HU-22, HU-23 |
| RNF que se verifican aquí | RNF-10, RNF-11 |
| Criterios de aceptación (sec. 8) | 20 criterios: todos los CA de HU-13, HU-17, HU-21, HU-22, HU-23; se prueban todos |
| Módulos involucrados (sec. 10.3) | M-03, M-04, M-05, M-06, M-09, M-10, M-11 |
| Depende de | Incremento 2 (ruta generada y ruta estructurada) e incremento 1 (M-09: crear, obtener y listar). **Incluye agregar a M-09 la operación de actualizar al volver a guardar** (D-11 y CA-21.4: guardar de nuevo actualiza la misma ruta y, si falla, la versión anterior queda intacta); es parte de RF-42 / HU-21, no funcionalidad nueva. Requiere migración de esquema si se agrega algo a `rutas_guardadas`: necesita aprobación explícita de Angel (bitácora 02). |
| Pruebas mínimas: normal, límite y error | Casos de prueba CP-nn de la matriz 9.1 (misma numeración que su RF), p. ej. CP-25, CP-26, CP-33, CP-38 .... Normal: CA-13.1, CA-17.1, CA-21.1 (+2 más). Límite: CA-13.4, CA-17.4, CA-21.4 (+2 más). Error de datos: CA-13.2, CA-17.2, CA-21.2 (+2 más). Error de sistema: CA-13.3, CA-17.3, CA-21.3 (+2 más). Más regresión de los incrementos anteriores (RNF-29). |
| Rama de Git | `incremento-3` |
| Fecha de cierre | Clase 2 de 4 (por confirmar con el calendario real) |
| Por qué se agrupa así | Cierra el flujo extremo a extremo Planear → guardar → consultar con HU de prioridad Alta (HU-21, 22, 23, 13, 17, sec. 7) usando M-09 del incremento 1. |
| Decisión del equipo y justificación | [Aceptada / modificada / rechazada] · pendiente de que el usuario revise |

### Incremento 4 · v0.4.0: Descubrir: catálogo, búsqueda, filtros y detalle de rutas públicas

| Campo | Respuesta |
|---|---|
| Incremento y versión | Incremento 4 · v0.4.0 |
| Objetivo en una frase | Cualquier visitante explora el catálogo de rutas públicas, las busca, las filtra por duración, categoría y región y consulta el detalle de una ruta. |
| RF incluidos | RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07, RF-08, RF-09, RF-10 (10) |
| HU incluidas (sec. 7) | HU-01, HU-02, HU-03, HU-04, HU-05 |
| RNF que se verifican aquí | RNF-01, RNF-02, RNF-04, RNF-06, RNF-07, RNF-08, RNF-15, RNF-24 |
| Criterios de aceptación (sec. 8) | 20 criterios: todos los CA de HU-01, HU-02, HU-03, HU-04, HU-05; se prueban todos |
| Módulos involucrados (sec. 10.3) | M-01, M-02, M-11 |
| Depende de | Incremento 1 (M-09 y la tabla de rutas) e incremento 3 (rutas guardadas/públicas). Depende de aclarar P-01 (cómo se marca una ruta pública) y P-03 (valores de categoría y región) de la sec. 4.3. |
| Pruebas mínimas: normal, límite y error | Casos de prueba CP-nn de la matriz 9.1 (misma numeración que su RF), p. ej. CP-01, CP-02, CP-03, CP-04 .... Normal: CA-01.1, CA-02.1, CA-03.1 (+2 más). Límite: CA-01.4, CA-02.4, CA-03.4 (+2 más). Error de datos: CA-01.2, CA-02.2, CA-03.2 (+2 más). Error de sistema: CA-01.3, CA-02.3, CA-03.3 (+2 más). Más regresión de los incrementos anteriores (RNF-29). |
| Rama de Git | `incremento-4` |
| Fecha de cierre | Clase 3 de 4 (por confirmar con el calendario real) |
| Por qué se agrupa así | Segundo flujo del MVP (sec. 3.2); HU-01 y HU-05 son Alta y HU-02, 03, 04 Media. Va después de Planear porque tiene menos riesgo técnico (criterio 3) y porque el catálogo necesita las rutas que genera y guarda Planear. |
| Decisión del equipo y justificación | [Aceptada / modificada / rechazada] · pendiente de que el usuario revise |

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
| Decisión del equipo y justificación | [Aceptada / modificada / rechazada] · pendiente de que el usuario revise |

## 6. Preguntas para el equipo y para el profesor (no se resuelven en el plan)

1. **P-01 (sec. 4.3): ¿cómo se marca o publica una ruta como pública?** Ningún RF lo describe. El catálogo del v0.4.0 necesita rutas públicas; mientras no se confirme, el plan asume que RutaMx las carga (RF-03 distingue «creada por RutaMx» de «creada por un usuario») y **no agrega** una función de publicar.
2. **P-02 (sec. 4.3): ¿hay proveedor de mapas y credenciales?** Decide si RF-11 y RF-12 (HU-06) entran; ya están al final y son lo primero que se recorta.
3. **P-03 (sec. 4.3): valores de categoría y región** de RF-05; deben definirse al cargar las rutas públicas en el v0.4.0.
4. **Calendario:** confirmado por el usuario: 4 clases de trabajo y 2 de exposición. Falta saber la duración de cada clase y cuánto se trabaja fuera de ella; con eso se calibra el tamaño (sección 2).
5. **Cambios de esquema** de `rutas_guardadas` (por ejemplo la referencia a la ruta de origen al copiar, RF-14, o marcar rutas públicas): requieren la aprobación explícita de Angel antes de ejecutarse (bitácora 02).
6. **Operaciones de M-09:** hoy existen 3 (crear, obtener, listar). El plan agrega **actualizar al volver a guardar** en el v0.3.0 (D-11, sec. 4.2, y CA-21.4) y **copiar** en el v0.5.0 (RF-13, 14, 16). **Eliminar rutas guardadas no se planea:** ningún RF ni decisión de la v2.0 lo pide; si el equipo lo quiere, es un cambio al plan y se registra.

## 7. Riesgos que ve la propuesta (sec. 12 del documento)

- Interpretación no determinista de la IA (riesgo Alto, sec. 10.4 y 12): por eso M-04 va en el v0.2.0 y se prueba con un adaptador de IA simulado de respuestas fijas.
- Atomicidad de los cambios (RF-37, M-05): se hace en el v0.2.0 y se vuelve a ejercer en el v0.3.0 (incluido el re-guardado que conserva la versión anterior si falla, CA-21.4) y v0.5.0.
- Tiempo del proyecto: el v0.5.0 es el recortable; el cierre de RNF de documentación y regresión (RNF-29 a RNF-33) no se recorta.

## 8. Verificación

```sh
# cada RF 01..44 aparece una sola vez en la tabla de la sección 3 (sin duplicados ni faltantes)
awk '/^## 3\./,/^## 4\./' documentacion/A3_Propuesta_Incrementos.md | grep -E '^\| [2-5] ' | grep -o -E 'RF-[0-9]+' | sort | uniq -d | wc -l     # 0
awk '/^## 3\./,/^## 4\./' documentacion/A3_Propuesta_Incrementos.md | grep -E '^\| [2-5] ' | grep -o -E 'RF-[0-9]+' | sort -u | wc -l     # 44
# igual para RNF en la sección 4
awk '/^## 4\./,/^## 5\./' documentacion/A3_Propuesta_Incrementos.md | grep -E '^\| [2-5] ' | grep -o -E 'RNF-[0-9]+' | sort -u | wc -l     # 33
grep -c '\[V2\]' documentacion/A3_Propuesta_Incrementos.md     # >= 1
```

Orden de dependencias comprobado a mano contra la columna «Depende de» de `A2_Inventario_Requerimientos.md`: cada RF queda en un incremento igual o posterior al de los RF de los que depende (por ejemplo RF-13 en el 5 depende de RF-10 en el 4; RF-38 en el 3 depende de RF-21 en el 2).
