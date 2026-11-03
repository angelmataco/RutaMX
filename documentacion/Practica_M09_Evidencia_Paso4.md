# [V2] Práctica M-09 — Evidencia del Paso 4 (pruebas)

Módulo: M-09 Repositorio de rutas (`crear_ruta`, `obtener_ruta`, `listar_rutas_de_usuario`).
Fecha de ejecución: 2026-11-03. Datos 100 % ficticios.

## Casos de prueba (mínimo normal, límite y error)

| Caso | Datos de entrada | Resultado esperado | Resultado real obtenido | Estado |
|---|---|---|---|---|
| Normal / CA-21.1 (PR-01) | Ruta ficticia válida y usuario A | Devuelve un diccionario con `id`; la fila queda con `usuario_id` = A | `test_pr01_crear_devuelve_diccionario_asociado_al_usuario` aprobada | Pasa |
| Normal / CA-22.1 (PR-06) | A con 2 rutas, B con 1 | `listar_rutas_de_usuario(A)` devuelve solo las 2 de A | `test_pr06_listar_devuelve_solo_las_rutas_del_dueno` aprobada | Pasa |
| Límite / CA-22.4 (PR-10) | Usuario sin rutas | Lista vacía, sin excepción | `test_pr10_usuario_sin_rutas_recibe_lista_vacia` aprobada | Pasa |
| Límite / CA-21.1 | `paradas` = lista vacía; ids 0 y -1 | La lista vacía se acepta; los ids 0 y -1 dan `None`/`[]`, y crear con ellos falla sin filas | `test_paradas_vacias_se_aceptan`, `test_identificadores_cero_o_negativos[0]` y `[-1]` aprobadas | Pasa |
| Error / CA-21.2 (PR-02) | Nombre con espacios, `origen` omitido, `paradas` no lista | `ErrorRepositorio` y ninguna fila nueva | `test_pr02_datos_invalidos_no_dejan_filas` y 34 pruebas de validación aprobadas | Pasa |
| Error / CA-21.3 (PR-03) | Fallo forzado en el `commit` | `rollback` explícito, `ErrorRepositorio` sin detalle interno, 0 filas | `test_pr03_fallo_en_el_commit_hace_rollback_y_no_deja_filas` aprobada | Pasa |
| Error / PNF-11 (PR-07) | B pide una ruta de A | `None`; la ruta de A no cambia | `test_pr07_otro_usuario_obtiene_none_y_la_ruta_queda_intacta` aprobada | Pasa |
| Error / CA-22.3 (PR-09) | Fallo al ejecutar la consulta en obtener y en listar | `ErrorRepositorio`; las demás rutas siguen intactas | Dos pruebas `test_pr09_*` aprobadas | Pasa |
| Error / contrato | Fallo que no es de SQLAlchemy (`RuntimeError`) | Sale como `ErrorRepositorio`, con la causa conservada | `test_error_que_no_es_de_sqlalchemy_...` aprobada | Pasa |

Cobertura adicional: PR-08 (datos secundarios incompletos), dueño que sale del argumento y no de los datos, orden y contenido de las paradas, ruta inexistente → `None`, cambios pendientes ajenos no se confirman, usuario inexistente (clave foránea) sin filas, listado con la más reciente primero.

## Evidencia de ejecución

| Elemento | Registro |
|---|---|
| Entorno | Python 3.13.5 · PostgreSQL 16.15 (Homebrew) desechable en `127.0.0.1:54329`, base `rutamx_prueba`, creada con `initdb` en una carpeta temporal. No es Supabase. |
| Comando | `RUTAMX_TEST_DB_URL=postgresql://rutamx_test@127.0.0.1:54329/rutamx_prueba venv/bin/python -m pytest base_datos/tests -q` |
| Salida observada | `53 passed in 0.18s` |
| Sin la variable de entorno | `34 passed, 19 skipped` (las 19 de integración se omiten con aviso; no cuentan como evidencia de persistencia ni de atomicidad). |
| Protecciones comprobadas | Con un host no local o con una base cuyo nombre no termina en `_prueba` / `_test`, la corrida se detiene antes de borrar nada. |
| Comprobación de que la prueba detecta el defecto | Se quitó temporalmente el `rollback` del código: la prueba PR-03 falló (1 failed, 52 passed). Se restauró y volvieron las 53. |

## Error y corrección realizada

| Hallazgo | Origen | Corrección |
|---|---|---|
| Una excepción que no fuera de SQLAlchemy salía sin traducir a `ErrorRepositorio` | Revisión de Codex (bloqueante) | Las tres operaciones traducen cualquier excepción, conservando la causa; prueba nueva. |
| PR-09 simulaba el fallo al abrir la sesión, no al consultar | Revisión de Codex (importante) | El fallo ahora ocurre en `execute` y se verifica que las demás rutas siguen intactas. |
| PR-03 no probaba que se llamara `rollback` | Revisión de Codex (importante) | Un espía confirma la llamada explícita. |
| La protección de la base solo revisaba el host | Revisión de Codex (importante) | Además exige que el nombre de la base termine en `_prueba` o `_test`. |
| El Postgres temporal no arrancó la primera vez | Sesión de trabajo | La ruta del socket Unix superaba el máximo de 103 bytes; se usó un directorio corto para el socket. |

## Commits y salida completa

| Dato | Valor |
|---|---|
| Commit del código y las pruebas | `2cf75cf` — https://github.com/angelmataco/RutaMX/commit/2cf75cf636b584f136c9b31b6fd9042ed05cc8f5 |
| Commit de la documentación | `d8b7c97` — https://github.com/angelmataco/RutaMX/commit/d8b7c978296da54fbaa4d099c175458ba3571562 |
| Salida completa de pytest (con y sin la base) | `documentacion/Practica_M09_salida_pytest.txt` (rutas de este equipo reemplazadas por `...`) |

## Cómo recrear y retirar el PostgreSQL temporal

Reproduce el entorno de la evidencia. Es una base local, desechable y sin contraseña (`--auth=trust`, solo escucha en `127.0.0.1`). Host local y nombre terminado en `_prueba` reducen errores de selección, pero no garantizan que una base sea desechable: no apuntar nunca la variable a una base con datos reales.

```bash
brew install postgresql@16
PG=/opt/homebrew/opt/postgresql@16/bin
DATOS=$(mktemp -d)                      # carpeta temporal del clúster
mkdir -p /tmp/rutamx_pg                 # socket en ruta corta (límite de 103 bytes)

$PG/initdb -D "$DATOS" -U rutamx_test --auth=trust -E UTF8
$PG/pg_ctl -D "$DATOS" -o "-p 54329 -c listen_addresses=127.0.0.1 -k /tmp/rutamx_pg" -l "$DATOS/log.txt" -w start
$PG/createdb -h 127.0.0.1 -p 54329 -U rutamx_test rutamx_prueba

RUTAMX_TEST_DB_URL=postgresql://rutamx_test@127.0.0.1:54329/rutamx_prueba \
  venv/bin/python -m pytest base_datos/tests -q          # esperado: 53 passed

# Retirar el entorno
$PG/pg_ctl -D "$DATOS" stop
rm -rf "$DATOS" /tmp/rutamx_pg
```

## Estado de las tareas del plan M-09 (T-01 a T-12)

El incremento aceptado es **crear, obtener y listar**. No se cierran las 12 tareas como conjunto terminado.

| Tarea | Estado | Nota |
|---|---|---|
| T-01 Revisar el diseño de persistencia (H-2 a H-6) | Parcial | H-2 y H-6 resueltas por decisión del equipo; falta la revisión de Roberto del diseño (H-4). |
| T-02 Aprobar el cambio de columnas | Parcial | Angel aprobó el cambio (2026-11-03); su ejecución queda diferida. |
| T-03 Base de prueba aislada | Hecha | `base_datos/tests/conftest.py`, con PostgreSQL temporal en lugar de Docker. |
| T-04 Migración `ALTER TABLE` | Diferida | Incremento de migración. |
| T-05 Extender el modelo | Diferida | Sin `autor_id` ni `visibilidad`. |
| T-06 Pruebas de M-09 | Parcial | Cubre PR-01, 02, 03, 06 a 10; faltan PR-04, 05 y 11 a 15. |
| T-07 Crear y actualizar | Parcial | Crear hecho; actualizar (CA-21.4/D-11) diferido. |
| T-08 Obtener y listar | Hecha | Con aislamiento por usuario. |
| T-09 Copia atómica | Diferida | Depende de P-01. |
| T-10 Regresión de la v1 | Diferida | Sin verificar (2026-11-03). |
| T-11 Prueba en la app corriendo | Diferida | Sin verificar (2026-11-03). |
| T-12 Bitácora y commit | Hecha para este incremento | Commits `2cf75cf` y `d8b7c97`, más el ajuste del marcador `[V2]`. |

## Riesgo transaccional para M-05

La sesión propia evita confirmar cambios ajenos, pero sus commits no participan en una transacción exterior. La atomicidad actual acredita **una** creación individual. Antes de que M-05 orqueste varias escrituras debe definirse la unidad transaccional.

## Funciones o partes que cada integrante puede explicar

A completar por el equipo (cada quien debe poder explicar su parte con sus palabras):

| Integrante | Parte sugerida |
|---|---|
| Angel | `crear_ruta` y el manejo de transacciones (`_abrir_sesion`, commit, rollback); prueba PR-03. |
| Roberto | `obtener_ruta` y `listar_rutas_de_usuario` (filtro por dueño, `None` y lista vacía); pruebas PR-06, PR-07, PR-10. |

## Limitaciones declaradas

- Cobertura parcial de HU-21, HU-22 y PNF-11 (solo creación, lectura y listado).
- CA-21.4 y D-11 (actualizar la misma ruta), copia de rutas, `autor_id` y `visibilidad`: diferidos.
- Regresión de la v1 y verificación en navegador: no realizadas.
- La sesión propia no ve datos sin confirmar de otra sesión ni se revierte desde una transacción exterior (a considerar en M-05).
