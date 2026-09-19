# RutaMX

Aplicación web para planear road trips dentro de México. Proyecto final de
Desarrollo de Aplicaciones y Servicios Virtuales (DASV).

## Estado actual: MVP

Esta primera versión funciona de extremo a extremo (formulario → mapa →
sugerencias → itinerario → guardar):

- **Mapa**: Leaflet + OpenStreetMap para la base, y Leaflet Routing Machine +
  OSRM (servidor demo público, gratis y sin API key) para trazar la ruta
  real por carretera pasando por origen, paradas del itinerario y destino.
- **Gasto máximo recomendado**: `app/services/gasto_service.py` (gasolina,
  casetas, imprevistos y, si aplican, comidas y hospedaje).
- **Cálculo de distancia/tiempo**: `app/services/route_service.py`
  usa la ruta real de OSRM (distancia y tiempo reales de carretera, no
  línea recta); si OSRM no responde, cae a una estimación en línea recta
  para que el flujo no se rompa.
- **Base de datos de destinos** (Postgres en Supabase, ver abajo): catálogo
  de los 32 estados con 369 destinos verificados (`app/models.py`, tablas
  `estados` y `destinos`): mínimo 8 ciudades/pueblos mágicos y mínimo 3
  sitios turísticos por estado, con más en los estados grandes o de
  ciudades muy conocidas.
  Sigue siendo la "plantilla": cada fila exige nombre, estado, tipo,
  coordenadas exactas (verificadas contra Nominatim/OpenStreetMap) y
  descripción.
- **Sugerencias de paradas**: `app/services/ai_service.py` consulta la
  tabla `destinos` y las filtra por cercanía real a la carretera (no en
  línea recta) usando la geometría de OSRM — solo sugiere lugares que de
  verdad quedan en el camino o a una desviación razonable. Si el usuario
  indica cuántas horas máximo quiere manejar seguido, prioriza destinos
  cerca de ese punto del viaje como sugerencia de descanso. Si la base de
  datos no responde, cae a un catálogo fijo de respaldo (`LUGARES_DEMO`).
- **Cuentas de usuario**: nombre + apellido + PIN de 4 dígitos, sin correo
  (proyecto escolar — ver `bitacora_proyecto/03_DECISIONES_Y_NOTAS.md`).
  `app/services/auth_service.py` maneja registro/login, sesión con la
  cookie firmada de Flask. Solo hace falta iniciar sesión para *guardar*
  una ruta — calcular rutas y ver sugerencias sigue abierto sin cuenta.
- **Rutas guardadas**: tabla `rutas_guardadas` en Supabase (`app/models.py`,
  modelo `RutaGuardada`), ligadas a la cuenta que las guardó — ya no se
  pierden al reiniciar el servidor, y cada quien solo ve las suyas.
- **Destinos nuevos con IA**: si alguien escribe un origen/destino que no
  está en la tabla `destinos` (ej. un pueblo pequeño, con o sin errores de
  ortografía), `app/services/ia_destinos_service.py` le pide a la IA que
  identifique el lugar real, busque en internet los datos que faltan, y
  lo inserte con `fuente="ia_generada"` — desde ahí funciona igual que
  cualquiera de los 369 curados (autocompletado, sugerencias, rutas). Ver
  "Conectar tu propia IA" más abajo.
- **"Planear con IA"**: botón en el formulario que abre un chat (panel
  centrado con efecto de vidrio esmerilado) donde describes tu viaje en
  lenguaje natural. La IA hace hasta 5 preguntas de seguimiento (con
  respuestas rápidas sugeridas) y propone 2 itinerarios distintos — pero
  nunca elige el lugar exacto por su cuenta: solo decide propósito de
  parada (comida/descanso/cultura/...) y a qué hora del viaje conviene;
  la asignación al destino real siempre es el mismo algoritmo
  determinista de `ai_service.py`. Ese mismo motor de reparto por
  propósito/hora también mejora las sugerencias **sin usar el botón de
  IA**: si pones horas máximas de manejo + hora de salida en el
  formulario manual, ya reparte paradas de comida/descanso en vez de
  amontonarlas. `app/services/planificador_ia_service.py` orquesta el
  chat, endpoints `GET /api/ia/disponible` y `POST /api/ia/planear`.

Los lugares donde falta una integración real están marcados con
`# TODO: reemplazar ...` en el código.

## Base de datos (Supabase)

El proyecto usa [Supabase](https://supabase.com) (Postgres) para el catálogo
de estados y destinos. Para correr el proyecto localmente:

1. Pide acceso al proyecto de Supabase del equipo (o crea uno nuevo y corre
   el SQL de `estados`/`destinos` que está documentado en el historial del
   proyecto).
2. En Supabase, ve a **Connect** → copia la cadena de conexión del
   **Session pooler** (no la de "Direct connection": esa solo resuelve por
   IPv6 y falla en muchas redes).
3. Crea `instance/config.py` (no se sube a git) con:
   ```python
   SUPABASE_DB_URL = "postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres"
   ```
4. Crea las tablas que falten (no toca las que ya existen):
   ```bash
   python3 -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all()"
   ```
5. Agrega la columna de usuario a las rutas guardadas (migración,
   seguro correrla varias veces):
   ```bash
   python scripts/agregar_usuario_id.py
   ```
6. Carga los datos iniciales (es seguro correrlo varias veces, no duplica filas):
   ```bash
   python scripts/seed_destinos.py
   ```

## Conectar tu propia IA (destinos nuevos)

Esto es opcional — sin ninguna key configurada, la app sigue funcionando
igual que hoy (cae a Nominatim directo para lugares que no estén en la
base, solo que no se guardan). Si quieres que los lugares nuevos se
agreguen para siempre a la base de datos, conecta **una** de estas en tu
`.env` local (nunca se sube a git — cada quien usa la suya, no importa
cuál):

```bash
# Elige una:
ANTHROPIC_API_KEY=...   # console.anthropic.com → API Keys
OPENAI_API_KEY=...      # platform.openai.com → API Keys
GEMINI_API_KEY=...      # aistudio.google.com/apikey
```

Se detecta sola (en ese orden de prioridad) — no hace falta tocar código.
Si tienes varias configuradas y quieres forzar una en específico:

```bash
IA_PROVEEDOR=anthropic   # o: openai / gemini
IA_MODELO=claude-opus-5  # opcional, si no lo pones usa el default de cada proveedor
```

Detalle de cómo funciona: `app/services/llm_provider.py` (conexión con el
proveedor) y `app/services/ia_destinos_service.py` (qué hace con la
respuesta).

## Cómo correrlo

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

La app queda disponible en `http://127.0.0.1:5000`.

## Cómo correr las pruebas

```bash
pytest
```

Algunas pruebas consultan la base de datos real de Supabase y el servicio
de ruteo real (OSRM) — necesitas `instance/config.py` configurado y
conexión a internet para que pasen todas.

## Estructura del proyecto

```
RutaMX/
├── app/
│   ├── __init__.py        # Application factory
│   ├── routes.py          # Endpoints (/, /api/ruta, /api/sugerencias, /api/rutas, /api/auth/*, /api/ia/*)
│   ├── models.py          # Modelos: Estado, Destino, Usuario, RutaGuardada (Supabase)
│   ├── services/
│   │   ├── ai_service.py               # Sugerencias de paradas + reparto por propósito/hora
│   │   ├── route_service.py            # Ruta real (OSRM), distancia/tiempo, corredor
│   │   ├── maps_service.py             # Geocodificación (Nominatim) y catálogo demo
│   │   ├── ia_destinos_service.py      # Genera destinos nuevos con IA e inserta en la tabla
│   │   ├── llm_provider.py             # Conexión con Claude/OpenAI/Gemini (detecta cuál está configurado)
│   │   ├── planificador_ia_service.py  # Orquesta el chat "Planear con IA"
│   │   └── auth_service.py             # Registro/login (nombre + apellido + PIN de 4 dígitos)
│   ├── static/               # CSS, JS, imágenes
│   └── templates/            # HTML (base + partials por sección)
├── scripts/
│   ├── agregar_usuario_id.py  # Migración: agrega usuario_id a rutas_guardadas
│   ├── seed_destinos.py       # Carga inicial de estados y destinos (lote 1)
│   ├── seed_destinos_v2.py    # Lote 2: mínimo 8 ciudades/pueblos + 3 sitios turísticos por estado
│   ├── verify_coordenadas.py  # Verifica/corrige coordenadas contra Nominatim
│   ├── fix_intereses.py       # Corrección 1 de etiquetas de interés
│   ├── fix_intereses_v2.py    # Corrección 2 (mínimo 2 etiquetas por destino)
│   ├── fix_intereses_v3.py    # Corrección 3 (mismo mínimo, para el lote 2)
│   ├── fix_poblacion.py       # Carga población lote 1 (Censo INEGI 2020)
│   └── fix_poblacion_v2.py    # Carga población lote 2 (Censo INEGI 2020)
├── tests/                    # Pruebas de rutas y servicios
├── instance/config.py        # Configuración local (no se sube a git)
├── config.py                  # Configuración general (Dev/Prod)
├── run.py                     # Punto de entrada
└── requirements.txt
```

## Próximos pasos

- Desplegar la app en un hosting público (Render/Railway) para poder
  compartirla con un link.
- Seguir ampliando el catálogo curado de ciudades/pueblos mágicos por estado
  (directo desde el Table Editor de Supabase).
- Decidir si se agrega login (cuentas de usuario) para que cada quien vea
  solo sus propias rutas guardadas.
