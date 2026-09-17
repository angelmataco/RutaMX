# RutaMX

Aplicación web para planear road trips dentro de México. Proyecto final de
Desarrollo de Aplicaciones y Servicios Virtuales (DASV).

## Estado actual: MVP

Esta primera versión funciona de extremo a extremo (formulario → mapa →
sugerencias → itinerario → guardar):

- **Mapa**: Leaflet + OpenStreetMap para la base, y Leaflet Routing Machine +
  OSRM (servidor demo público, gratis y sin API key) para trazar la ruta
  real por carretera pasando por origen, paradas del itinerario y destino.
- **Cálculo de distancia/tiempo/costo**: `app/services/route_service.py`
  usa la ruta real de OSRM (distancia y tiempo reales de carretera, no
  línea recta); si OSRM no responde, cae a una estimación en línea recta
  para que el flujo no se rompa.
- **Base de datos de destinos** (Postgres en Supabase, ver abajo): catálogo
  de los 32 estados con 130 ciudades principales, pueblos mágicos y sitios
  turísticos verificados (`app/models.py`, tablas `estados` y `destinos`).
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
- **Rutas guardadas**: tabla `rutas_guardadas` en Supabase (`app/models.py`,
  modelo `RutaGuardada`) — ya no se pierden al reiniciar el servidor.
  Pendiente: asociarlas a un usuario cuando se decida agregar login.

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
5. Carga los datos iniciales (es seguro correrlo varias veces, no duplica filas):
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

Algunas pruebas consultan la base de datos real de Supabase y el servicio
de ruteo real (OSRM) — necesitas `instance/config.py` configurado y
conexión a internet para que pasen todas.

## Estructura del proyecto

```
RutaMX/
├── app/
│   ├── __init__.py        # Application factory
│   ├── routes.py          # Endpoints (/, /api/ruta, /api/sugerencias, /api/rutas)
│   ├── models.py          # Modelos: Estado, Destino, RutaGuardada (Supabase)
│   ├── services/
│   │   ├── ai_service.py      # Sugerencias de paradas (filtro por corredor real)
│   │   ├── route_service.py   # Ruta real (OSRM), distancia/tiempo, corredor
│   │   └── maps_service.py    # Geocodificación (Nominatim) y catálogo demo
│   ├── static/               # CSS, JS, imágenes
│   └── templates/            # HTML (base + partials por sección)
├── scripts/
│   ├── seed_destinos.py       # Carga inicial de estados y destinos
│   ├── verify_coordenadas.py  # Verifica/corrige coordenadas contra Nominatim
│   ├── fix_intereses.py       # Corrección 1 de etiquetas de interés
│   ├── fix_intereses_v2.py    # Corrección 2 (mínimo 2 etiquetas por destino)
│   └── fix_poblacion.py       # Carga población (Censo INEGI 2020)
├── tests/                    # Pruebas de rutas y servicios
├── instance/config.py        # Configuración local (no se sube a git)
├── config.py                  # Configuración general (Dev/Prod)
├── run.py                     # Punto de entrada
└── requirements.txt
```

## Próximos pasos

- **Fallback de IA**: si el destino que busca el usuario no está en la
  tabla `destinos` (ej. un pueblo pequeño), generarlo con IA cumpliendo la
  misma plantilla —nombre, tipo, coordenadas exactas (vía
  `maps_service.geocodificar`), descripción, intereses— e insertarlo en
  `destinos` con `fuente="ia_generada"`.
- Desplegar la app en un hosting público (Render/Railway) para poder
  compartirla con un link.
- Seguir ampliando el catálogo curado de ciudades/pueblos mágicos por estado
  (directo desde el Table Editor de Supabase).
- Decidir si se agrega login (cuentas de usuario) para que cada quien vea
  solo sus propias rutas guardadas.
