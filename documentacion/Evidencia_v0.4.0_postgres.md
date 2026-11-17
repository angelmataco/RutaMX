# [V2] Evidencia de PostgreSQL del v0.4.0

Última actualización: 2026-11-17 (CDMX)

## Resultado actual de la meta 12: suite corregida en verde

El 2026-11-17 se corrigieron únicamente las pruebas: INSERT con `intereses`
y `resumen` explícitos, esquema anterior restaurado por caso de migración y
comprobación de identidad del contexto Flask en vez de exigir su ausencia.
No cambió código de producción ni `conftest.py`.

Se creó una base nueva propia `rutamx_verde_prueba` en el servidor local de
Angel (`127.0.0.1:55433`, usuario ficticio `rutamx_test`), tras comprobar que
no existía. Comandos ejecutados desde la raíz, ambos con salida **0**:

```sh
RUTAMX_TEST_DB_URL=postgresql://rutamx_test@127.0.0.1:55433/rutamx_verde_prueba PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest base_datos/tests v2/tests -q -p no:cacheprovider -k 'not test_navegador_escritorio_y_movil'
# 563 passed, 1 deselected, 1 warning in 1.26s

env -u RUTAMX_TEST_DB_URL PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest base_datos/tests v2/tests -q -p no:cacheprovider -k 'not test_navegador_escritorio_y_movil'
# 529 passed, 34 skipped, 1 deselected, 1 warning in 1.01s
```

Con PostgreSQL: **0 failed, 0 skipped**, las 34 integraciones pasan, incluidas
las cinco de migración. Sin PostgreSQL: **0 failed**, las 34 integraciones
se omiten. La prueba de navegador de Planear se excluye con `-k` en ambas
corridas; no es una prueba ejecutada ni omitida. Persiste la advertencia de
compatibilidad de dependencias de requests (urllib3/chardet/charset_normalizer).
Las dos corridas se ejecutaron en procesos separados, con variables de entorno
propias; la corrida sin URI no usa la base de la otra.

Revisión independiente del helper de contexto: se dejó un contexto abierto
adrede dentro de `_sin_fuga_de_contexto`, con y sin contexto externo. En ambos
casos lanzó `AssertionError: el script dejó 1 contexto(s) de Flask abierto(s)`
y restauró la identidad previa. No se modificó producción para comprobarlo.

Al terminar se borró exclusivamente `rutamx_verde_prueba` con `DROP DATABASE` y
se comprobó su ausencia en `pg_database`. El servidor de Angel sigue activo;
las bases de ensayos anteriores no se tocaron. No se crearon lanzadores a
disco, procesos de servidor ni otros temporales. No se consultó Supabase.

Esto acredita simulación con PostgreSQL local, **no uso real**. Siguen sin
verificar navegador, Supabase, regresión de v1 y contención concurrente de
`FOR UPDATE`. La corrida depende de una base nueva; el caso del catálogo
«sin migración» aún supone ese orden inicial. No se amplió esta corrección
fuera del reparto aprobado.

## Historial de la meta 11: integración ejecutada con fallos

Servidor levantado por Angel, sin reintentar su arranque: `127.0.0.1:55433`,
usuario ficticio `rutamx_test`. Comprobación con psycopg2 y
`SELECT inet_server_addr()::text, inet_server_port(), current_user`:

```text
Servidor: ('127.0.0.1/32', 55433, 'rutamx_test')
Base propia creada: rutamx_integracion_prueba
```

Se creó esa base con `CREATE DATABASE rutamx_integracion_prueba` tras comprobar
que no existía en `pg_database`. No se usó `rutamx_prueba` ni Supabase.
Las pruebas validan host y sufijo de la URI mediante su fixture. No se cargó
configuración real ni se ejecutó v1. Comando real:

```sh
RUTAMX_TEST_DB_URL=postgresql://rutamx_test@127.0.0.1:55433/rutamx_integracion_prueba PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest base_datos/tests v2/tests -q -p no:cacheprovider -k 'not test_navegador_escritorio_y_movil'
```

Salida real, código **1**:

```text
7 failed, 556 passed, 1 deselected, 1 warning in 1.59s
```

**0 skipped.** Las 34 pruebas de integración antes omitidas se ejecutaron:
30 pasaron y 4 fallaron. Otros 3 fallos son comprobaciones de contexto Flask
que antes pasaban sin integración. La prueba opcional de navegador se excluyó
con `-k`; no es un skip ni una verificación visual. La advertencia es la
compatibilidad de dependencias de requests ya documentada.

## Fallos y causas por lectura del código

| Pruebas fallidas | Causa observada |
|---|---|
| `test_catalogo_repositorio.py::test_integracion_solo_salen_las_publicas_y_filtran` y `::test_integracion_detalle_privado_es_none` | `_insertar`, línea 219, omite `intereses` y `resumen` en INSERT SQL directo. PostgreSQL rechaza primero `intereses` con `NotNullViolation`. Los defaults del ORM no se aplican al SQL directo. No se llega a comprobar el catálogo en esos casos. |
| `test_migracion_catalogo.py::test_integracion_esquema_anterior_gana_las_siete_columnas` y `::test_integracion_fallo_a_la_mitad_deja_el_esquema_intacto` | El esquema ya contiene columnas agregadas por casos previos. `conftest.py:73` solo trunca filas; no restaura el esquema. Las aserciones en líneas 98 y 136 parten de un esquema anterior que ya no existe. |
| `test_publicar_ruta.py::test_abrir_sesion_no_deja_contexto_de_flask_activo`, `::test_abrir_sesion_fallida_tampoco_deja_contexto` y `::test_cada_operacion_real_libera_el_contexto` | `conftest.py:65-69` mantiene un contexto Flask durante toda la sesión cuando se ejecuta integración. `has_app_context()` sigue siendo verdadero por ese contexto externo, incluso si el script libera el suyo. |

No se corrigieron esos archivos: no están reservados en el paso 49. Se dejó
aviso al equipo para proponer su corrección. Estos resultados no prueban por
sí solos un defecto del código de producción, pero impiden declarar verde la
regresión en aquella corrida. De las cinco pruebas de integración de migración, tres pasan y dos
fallan por el estado compartido descrito arriba.

## Comprobación adicional del SQL real

Después de la corrida se recreó únicamente el esquema de la base propia con
una app Flask mínima, URI efectiva comprobada antes de consultas, sin
`instance/config.py`. Desde `venv/bin/python -` con
`PYTHONDONTWRITEBYTECODE=1` se ejecutaron estas operaciones reales:

1. `db.drop_all(); db.create_all()` y `aplicar(db.session)` dos veces.
2. Crear por ORM un usuario ficticio y una ruta `Prueba 100%_literal`, con
   `intereses=[]`, `resumen.rutamx_v2.ruta.duracion_dias=2` y una parada.
3. Reemplazar solo en ese proceso `publicar_ruta._abrir_sesion` por
   `lambda: Session(engine)` del motor local comprobado; llamar
   `publicar(ruta_id, 'Playa', 'Centro', 'Descripción ficticia')`.
4. Con contexto local, `listar_publicas('100%_')` debe devolver una ruta con
   `num_paradas=1`; `listar_publicas('100xZ')` debe dar `[]`;
   `obtener_publica(ruta_id)` debe devolver el detalle.
5. `db.session.remove(); db.drop_all()` sobre la base propia.

Salida real de la comprobación corregida, código **0**:

```text
Publicar: {'ruta_id': 1, 'duracion_dias': 2, 'es_rutamx': False}
SQL real: jsonb_array_length=1; ILIKE ESCAPE literal correcto; FOR UPDATE y #>> ejecutados al publicar
Esquema propio limpiado; servidor activo; base propia vacía
```

Esto ejecuta el SQL del repositorio y de publicación sobre PostgreSQL:
`jsonb_array_length`, `ILIKE ... ESCAPE`, `FOR UPDATE` y `#>>`. No comprueba
contención concurrente del bloqueo ni un flujo en navegador. Usa una sesión
local inyectada; la fábrica de configuración real no se ejercita.

Un primer intento de este lanzador falló por un error propio: se insertó JSON
literal dentro de `text()` y SQLAlchemy interpretó `:2` como parámetro
(`InvalidRequestError: A value is required for bind parameter '2'`). Se corrigió
usando objetos ORM y se recreó el esquema propio antes del intento exitoso.
No fue un rechazo del sistema ni un fallo de la app.

## Limpieza y límites

No se escribieron lanzadores a disco ni se crearon procesos de servidor.
La base propia quedó sin tablas tras la comprobación; permanece creada en el
servidor de Angel, que no se detuvo. No se modificaron otras bases. Las
bitácoras y reporte se consolidan en el paso 4, reservado a Claude.

El ensayo anterior fue **probado en simulación con PostgreSQL local y datos
ficticios**, sin verificar en uso real. Los siete fallos de aquella corrida
quedaron corregidos en la meta 12 (resultado actual al inicio); regresión de
v1 y navegador siguen pendientes.

## Evidencia histórica conservada

Antes de que Angel levantara este servidor, el 2026-11-17 se respetó el bloqueo
previo de PostgreSQL registrado en bitácoras 02/03, sin reintento. La corrida
segura sin `RUTAMX_TEST_DB_URL`, anterior al nuevo test de pantalla, dio
`522 passed, 34 skipped, 1 deselected, 1 warning in 0.99s`, salida 0. No
verificaba SQL real. Ese bloqueo histórico dejó de impedir esta conexión al
servidor aportado por Angel; no implica que se haya resuelto Chromium.
