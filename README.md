# RutaMX

Aplicación web para planear road trips dentro de México. Proyecto final de
Desarrollo de Aplicaciones y Servicios Virtuales (DASV).

## Estado actual: MVP

Esta primera versión funciona de extremo a extremo (formulario → mapa →
sugerencias → itinerario → guardar):

- **Mapa**: Leaflet + OpenStreetMap para la base, y Leaflet Routing Machine +
  OSRM (servidor demo público, gratis y sin API key) para trazar la ruta
  real por carretera pasando por origen, paradas del itinerario y destino.
- **Cálculo de distancia/tiempo/costo**: todavía es una estimación simulada
  en `app/services/route_service.py` (línea recta, no la distancia real de
  la ruta trazada en el mapa).
- **Base de datos de destinos** (Postgres en Supabase, ver abajo): catálogo
  de los 32 estados y un primer grupo de ciudades principales y pueblos
  mágicos verificados (`app/models.py`, tablas `estados` y `destinos`).
  Sigue siendo la "plantilla": cada fila exige nombre, estado, tipo,
  coordenadas y descripción.
- **Sugerencias de paradas**: por ahora `app/services/ai_service.py` sigue
  usando el catálogo fijo `LUGARES_DEMO`; falta conectarlo a la tabla
  `destinos` y agregar el fallback de IA para pueblos pequeños que no estén
  en la base (ver Próximos pasos).
- **Rutas guardadas**: se guardan en memoria (`app/models.py`), se pierden
  al reiniciar el servidor. Pendiente de mover a una tabla real.

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
4. Carga los datos iniciales (es seguro correrlo varias veces, no duplica filas):
   ```bash
   python scripts/seed_destinos.py
   ```

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

## Estructura del proyecto

```
RutaMX/
├── app/
│   ├── __init__.py        # Application factory
│   ├── routes.py          # Endpoints (/, /api/ruta, /api/sugerencias, /api/rutas)
│   ├── models.py          # Modelos: Estado/Destino (Supabase) y Ruta (memoria)
│   ├── services/           # Lógica de negocio (mapas, ruta, IA)
│   ├── static/              # CSS, JS, imágenes
│   └── templates/           # HTML (base + partials por sección)
├── scripts/
│   └── seed_destinos.py     # Carga inicial de estados y destinos
├── tests/                   # Pruebas de rutas y servicios
├── instance/config.py       # Configuración local (no se sube a git)
├── config.py                 # Configuración general (Dev/Prod)
├── run.py                    # Punto de entrada
└── requirements.txt
```

## Próximos pasos

- Conectar `ai_service.py` a la tabla `destinos` en vez de `LUGARES_DEMO`, y
  agregar el fallback: si el destino que busca el usuario no está en la
  tabla (ej. un pueblo pequeño), generarlo con IA cumpliendo la misma
  plantilla e insertarlo en `destinos` con `fuente="ia_generada"`.
- Seguir ampliando el catálogo curado de ciudades/pueblos mágicos por estado
  (directo desde el Table Editor de Supabase).
- Definir y migrar a una tabla real las rutas guardadas y usuarios.
