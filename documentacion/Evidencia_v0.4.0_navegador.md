# [V2] Verificación de navegador del v0.4.0

Última actualización: 2026-11-17 (CDMX)

## Estado: sin verificar

Actualización de la meta 11 (2026-11-17): Angel levantó PostgreSQL y las
comprobaciones locales de migración y SQL ya se ejecutaron (evidencias
`Evidencia_v0.4.0_migracion.md` y `Evidencia_v0.4.0_postgres.md`). Esto
resuelve el bloqueo de la base para esos ensayos, pero no acredita que se
haya resuelto el rechazo de Chromium. No consta esa resolución: conforme
al paso 3 aprobado, no se reintentó el navegador ni se buscaron alternativas.
No se creó `rutamx_navegador_prueba`, app, lanzadores ni procesos para este
paso; el servidor de Angel permanece activo y no se modificó.

### Antecedente de la meta 10 (antes del servidor de Angel)

No se abrió `/v2/descubrir` en navegador en este paso. El PostgreSQL
desechable requerido por el plan sigue bloqueado por el rechazo previo
registrado en las bitácoras 02 y 03; no se reintentó ni se usó otra base.
El paso 3 también reportó un rechazo actual al intentar su servidor propio.

La bitácora 01 conserva además el error histórico de Chromium:

```text
bootstrap_check_in ... MachPortRendezvousServer: Permission denied (1100)
```

Es el fragmento documentado de una ejecución anterior, no un error generado
hoy ni una transcripción completa del registro de Chromium. No se reintentó
ese arranque ni se instaló otro navegador para eludirlo.

No se arrancó app ni base, no se crearon procesos o temporales y no se
consultó Supabase. No hay capturas ni resultados de consola del navegador.
No se modificaron frontend, efectos protegidos ni configuración real.

## Casos pendientes

| Caso | 1280×900 | 375×812 |
|---|---|---|
| Listado con rutas públicas ficticias y estado vacío | Sin verificar | Sin verificar |
| Búsqueda y filtros combinados | Sin verificar | Sin verificar |
| Reinicio de filtros con valores restablecidos | Sin verificar | Sin verificar |
| Abrir detalle y cerrar con botón/Esc | Sin verificar | Sin verificar |
| Descartar respuestas tardías de listado y detalle | Sin verificar | Sin verificar |
| Consola sin errores y sin desborde horizontal | Sin verificar | Sin verificar |
| Fondo, luz de tarjetas y diálogo modal | Sin verificar | Sin verificar |

## Comprobación distinta: render del servidor

Durante la revisión del paso 1 se leyó la plantilla real y se ejecutó:

```sh
env -u RUTAMX_TEST_DB_URL PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest v2/tests/test_pantalla_descubrir.py -q -p no:cacheprovider
```

Resultado real, salida 0: `7 passed, 1 warning in 0.42s`. Advertencia de
compatibilidad de dependencias de requests. Estas pruebas verifican respuesta
200, anclas, recursos locales, selectores y opciones de categoría/región.
No ejecutan JavaScript ni comprueban apariencia, filtros interactivos o consola.

## Condiciones para completar

Cuando el entorno permita ambos procesos, crear PostgreSQL propio en
`127.0.0.1:55434` con esquema migrado y rutas públicas ficticias. Forzar y
verificar la URI efectiva de SQLAlchemy antes de `db.init_app`; no basta
exportar una variable, porque las fábricas cargan `instance/config.py`.
Si no puede garantizarse ese aislamiento, no ejecutar la app. Servirla en
loopback, revisar ambos tamaños y los casos de la tabla, y detener app y base
con limpieza de sus temporales al terminar. La anfitriona incorpora este
bloqueo a las bitácoras y al reporte en el paso 5.
