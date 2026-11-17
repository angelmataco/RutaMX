---
tags: [proyecto, rutamx, tecnologias]
---
# Tecnologías usadas

Parte de [[RutaMX]]. Contexto de uso en [[RutaMX - Arquitectura]].

## Backend
| Tecnología | Versión | Para qué se usa |
|---|---|---|
| [[Python]] | venv local | Lenguaje del backend |
| [[Flask]] | 3.0.3 | Servidor web, rutas y sesión con cookie firmada |
| Flask-SQLAlchemy | 3.1.1 | Modelos y acceso a la base |
| psycopg2-binary | 2.9.13 | Conexión con Postgres |
| [[SQLAlchemy]] | 2.0.53 | Viene con Flask-SQLAlchemy; M-09 usa su `Session` propia |
| python-dotenv | 1.0.1 | Variables de entorno desde `.env` |
| requests | 2.32.3 | Llamadas a OSRM y Nominatim |
| [[reportlab]] | 4.2.5 | Itinerario en PDF y, con `scripts/md_a_pdf.py`, los reportes de avance de cada incremento |
| [[pytest]] | 8.3.3 | Pruebas |
| `anthropic`, `openai`, `google-genai` | sin fijar | Un SDK por proveedor de IA; cada persona usa solo el de su key. La v2 (M-07) usa solo `anthropic`, sin versión fijada todavía |
| werkzeug.security | viene con Flask | Hash del PIN de las cuentas |

## Datos y servicios externos
- **Supabase (Postgres)**: estados, destinos, usuarios y rutas guardadas. Usa columnas `ARRAY` y `JSONB`.
- **[[Supabase y Postgres|PostgreSQL]] 16 local** (Homebrew, 16.15): base desechable solo para las pruebas de integración (M-09, la migración del catálogo y el SQL del catálogo y de publicar); no es parte de la app.
- **OSRM** (servidor demo público, gratis y sin key): ruta real por carretera.
- **Nominatim / OpenStreetMap**: geocodificación y verificación de coordenadas; en la v2 también lo usa el verificador geográfico (M-08).
- **Google Maps**: solo como enlace y QR para navegar; no se usa su API.
- **Proveedores de IA** (opcional): Claude, OpenAI o Gemini. Modelos por defecto en `llm_provider.py`: `claude-opus-5`, `gpt-5.1` y `gemini-3-pro`. Se detecta cuál hay por la variable de entorno (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`) o se fuerza con `IA_PROVEEDOR` e `IA_MODELO`.

## Frontend
- **Leaflet + OpenStreetMap** para el mapa y **Leaflet Routing Machine** para trazar la ruta.
- **[[JavaScript y CSS puros]]**, sin framework ni compilación.
- **Plantillas Jinja** de [[Flask]] con parciales por sección.
- **[[Google Fonts]]**: Newsreader (títulos) y Plus Jakarta Sans (texto); requiere internet.
- **Blobatar 2.7 (MIT)**: avatar de sesión, copiado a `static/js/vendor/`.
- **rare-ui** ([[Rare UI]]): de ahí salen los 8 efectos visuales, reescritos a mano en JS/CSS puro (los originales son React + Tailwind + `motion`).
- **Stitch** ([[Google Stitch]]; carpeta de diseño de Angel): fuente de la paleta, el logo y el `DESIGN.md` del rediseño.
- Elemento HTML nativo `<dialog>` para todas las ventanas.

## Herramientas de trabajo
- **[[Git y GitHub]]** (`angelmataco/RutaMX`).
- **[[Claude Code]]** (Angel) y **[[Codex CLI|Codex]]** (Roberto): por eso el proyecto tiene `CLAUDE.md`, `AGENTS.md` y una bitácora compartida.
- **graphify**: grafo de conocimiento en `graphify-out/` (ignorado por git y hoy desactualizado).

## Fuentes de datos citadas en el proyecto
- Censo INEGI 2020 (población de los destinos).
- UNESCO (Ciudades Creativas de la Gastronomía), Guía Michelin México 2026 y Latin America's 50 Best 2025 (gastronomía destacada).
- Guía de casetas.com.mx y Infobae (precios de casetas y gasolina, septiembre 2026).

Las razones de cada elección están en [[RutaMX - Decisiones]]. Otros proyectos en [[Python]]: [[QR WiFi]] y [[Govee Claude]].

## Notas generales de tecnologías
- [[Python]]
- [[Git y GitHub]]
- [[python-dotenv y env|python-dotenv y .env]]
- [[reportlab]]
- [[Claude Code]]
- [[Pruebas con simulación]]
- [[Medir antes de decidir]]
- [[Acceso único al modelo de lenguaje]]
- [[JavaScript y CSS puros]]
- [[Flask]]
- [[Supabase y Postgres]]
- [[Mapas con OSRM, Nominatim y Leaflet]]
- [[SQLAlchemy]]
- [[pytest]]
