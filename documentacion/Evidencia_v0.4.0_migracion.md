# [V2] Evidencia v0.4.0: ensayo de migración y publicación (paso 1 de la meta 11)

Fecha: 2026-11-17 (CDMX). Estado: **probado en una base PostgreSQL desechable local** (no es uso real; no se tocó Supabase).

## Historial

El mismo día, en la meta 10, el sistema rechazó levantar un PostgreSQL desde
esta sesión y el ensayo quedó sin verificar. Después Angel lo levantó él mismo
(`initdb` y `pg_ctl` desde `!`) en `127.0.0.1:55433`, con datos en
`/tmp/pg_rutamx`. Este ensayo usa ese servidor, sin volver a arrancarlo.

## Cómo se aisló

Los scripts de migración y publicación obtienen su conexión con
`crear_app_minima`, que carga `.env` e `instance/config.py` (posible base
real). Para evitarlo se usó un lanzador temporal (en el scratchpad de la
sesión, ya borrado) que, antes de cualquier consulta:

1. reemplaza `base_datos.conexion.crear_app_minima` por una app con la URI
   `postgresql://rutamx_test@127.0.0.1:55433/rutamx_prueba`;
2. comprueba la URI efectiva del motor de SQLAlchemy (host 127.0.0.1,
   puerto 55433, base `rutamx_prueba`) y se detiene si no coincide.

Nunca se cargó `instance/config.py` ni se usó Supabase. Datos ficticios (una
usuaria «Ana Ficticia» y dos rutas inventadas, una de 4 días y otra de 2).

## Lo que se corrió y salió (salida real)

Comando: `env -u RUTAMX_TEST_DB_URL PYTHONDONTWRITEBYTECODE=1 venv/bin/python -W ignore <lanzador> <raíz del proyecto>`.

```text
URI efectiva verificada: host=127.0.0.1 puerto=55433 base=rutamx_prueba
Columnas antes: ['id', 'nombre', 'origen', 'destino', 'presupuesto', 'intereses', 'resumen', 'paradas', 'usuario_id', 'creado_en']
ANTES de migrar: ErrorMigracionPendiente -> El catálogo necesita la migración de la base de datos (columnas nuevas) y todavía no se ha aplicado.
Listo: rutas_guardadas tiene las columnas del catálogo.
Migracion, corrida 1: codigo 0
Listo: rutas_guardadas tiene las columnas del catálogo.
Migracion, corrida 2: codigo 0
Columnas despues: [... 'creado_en', 'descripcion', 'duracion_dias', 'categoria', 'region', 'visibilidad', 'ruta_origen_id', 'autor_id']
Filas previas conservadas: (2, 'privada', 'privada')
Catalogo antes de publicar: []
Publicar (categoria invalida): codigo 1      (Error: Categoría no válida. Opciones: Playa, Cultural, Naturaleza, Gastronomía, Pueblo Mágico.)
Publicar (ruta inexistente): codigo 1        (Error: No existe la ruta 999.)
Publicar ruta 1: codigo 0                    (Listo: la ruta 1 es pública (4 días, autor: su autor).)
Catálogo (servicio) tras publicar: una ruta, id 1 «Ruta ficticia de playa», 4 días, 2 paradas, Playa, Sureste, autor «Ana F.», es_rutamx False
Filtro categoria=Playa: [1]
Filtro categoria=Cultural: []
Busqueda 'playa': [1]
Busqueda con comodin '%': []
Detalle ruta 1: con descripción y las 2 paradas ordenadas
Detalle ruta privada 2: RutaNoEncontrada - No se encontró la ruta.
Volver privada ruta 1: codigo 0
Catálogo tras volver privada: []
```

## Qué demuestra y qué no

- **Probado en base desechable local:** antes de migrar el catálogo responde «migración pendiente»; la migración corre dos veces sin error (idempotente), agrega las 7 columnas y conserva las filas previas como privadas; `publicar_ruta.py` valida categoría y ruta inexistente (código 1), publica con `FOR UPDATE` y `#>>` reales y toma la duración de `resumen`; el catálogo (`jsonb_array_length`, `ILIKE ... ESCAPE`, filtros) devuelve solo la ruta pública, una privada responde como inexistente y `--privada` la saca del catálogo; el comodín `%` se escapa y no devuelve todo.
- **Sin verificar:** la migración en Supabase (la ejecuta Angel, con respaldo), la regresión de v1, el navegador y cualquier uso real.
- Las pruebas de integración de `base_datos/tests` corren aparte (paso 2 de la meta 11, en otra base).
