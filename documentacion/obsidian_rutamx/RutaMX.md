---
tags: [proyecto, python, flask, escuela, mapas, ia]
estado: En progreso
---
# RutaMX

**Estado:** En progreso. El MVP (versión 1) funciona de punta a punta (formulario → mapa → sugerencias → itinerario → guardar). La versión 2 sigue su plan de incrementos: v0.1.0 (M-09), v0.2.0 (Planear con IA), v0.3.0 (guardar y recuperar rutas) y v0.4.0 (Descubrir) están probados en simulación, incluidas las pruebas de integración contra un [[Supabase y Postgres|PostgreSQL]] local desechable (2026-11-17), y siguen sin verificar en navegador, con una IA real y en Supabase. Faltan los tags `v0.2.0` a `v0.4.0`, el push de los commits locales, ejecutar la migración del catálogo en Supabase, restaurantes y hoteles, calibrar el tiempo de viaje, desplegar y probar en teléfono real. Ver "Lo que falta" más abajo.

Aplicación web para planear road trips dentro de México. Es el proyecto final de la materia *Desarrollo de Aplicaciones y Servicios Virtuales* (tercer semestre), hecho en equipo con Roberto Valderrama. Tú escribes origen y destino, la app traza la ruta real por carretera, te sugiere paradas que de verdad quedan en el camino, calcula un gasto máximo recomendado y arma un itinerario que puedes guardar, exportar a PDF o abrir en Google Maps.

## Qué hace hoy
- **Mapa y ruta real** con Leaflet + OpenStreetMap y OSRM (distancia y tiempo de carretera, no en línea recta).
- **Base de destinos**: 369 en el catálogo inicial y 374 tras las cinco altas de gastronomía (fotografías de esas fechas; no se recontó la base, sin verificar (2026-11-13)), verificados en los 32 estados (mínimo 8 ciudades/pueblos mágicos y 3 sitios turísticos por estado), con coordenadas comprobadas contra Nominatim.
- **Sugerencias de paradas** filtradas por cercanía real a la carretera y por lo que marques en "¿Qué buscas?". La primera vista son 5 recomendadas repartidas por franjas de horas del viaje; "Ver más" muestra todas.
- **Tramos con propósito** (comer, dormir, turismo) y con hora del reloj; el viaje se divide solo en tramos de ~3 h.
- **Gasto máximo recomendado**: gasolina, casetas, imprevistos y, si aplican, comidas y hospedaje, deducidos solos.
- **Cuentas sin correo**: nombre + apellido + PIN de 4 dígitos. Solo hace falta iniciar sesión para guardar rutas.
- **Rutas guardadas** en Supabase, cada quien ve solo las suyas.
- **Itinerario en PDF** y navegación en vivo delegada a Google Maps (enlace + QR).
- **Destinos nuevos con IA**: si escribes un lugar que no está en la base, una IA (Claude, OpenAI o Gemini) lo identifica y se guarda.
- **"Planear con IA"**: chat que arma 2 itinerarios a partir de una conversación.
- **Rediseño visual** propio (paleta lino/terracota/agave, iconos SVG a medida, sin emojis) y 8 efectos de rare-ui portados a JS/CSS puro.
- **Avatar de sesión** con Blobatar que sigue el mouse.

## [V2] Versión 2: M-09 y los incrementos v0.2.0 a v0.4.0
**Incremento v0.1.0, M-09 Repositorio de rutas** (capa de datos): 3 de sus 5 operaciones (crear, obtener y listar rutas por usuario), en `base_datos/repositorios/rutas_repositorio.py`. Probado en simulación (2026-11-03), con pruebas contra un [[Supabase y Postgres|PostgreSQL]] desechable y sin tocar Supabase. En ese corte (2026-11-03) faltaban actualizar y copiar una ruta y las columnas nuevas de `rutas_guardadas` (aprobadas el 2026-11-03). Hoy: actualizar se agregó en el v0.3.0, copiar sigue pendiente (v0.5.0) y las columnas están en una migración que se ensayó en PostgreSQL local y no se ha ejecutado en Supabase.

**Incremento v0.2.0, Planear con IA** (2026-11-10): seis módulos nuevos en `v2/`: M-11 utilerías, M-07 adaptador de IA, M-05 gestor de rutas con la regla D-03, M-08 verificador geográfico con Nominatim (agregado fuera de la tabla del plan, por indicación de Angel), M-04 orquestador y M-03 la pantalla `/v2/planear`. Estado: probado en simulación (2026-11-10), con IA simulada y una sola consulta real a Nominatim; sin verificar en navegador (Chromium bloqueado por el sandbox) y sin verificar con IA real (falta llave y modelo). La app normal muestra «Planear con IA no está configurado» sin esa configuración. Detalle en [[RutaMX - Arquitectura]].

**Incremento v0.3.0, guardar y recuperar rutas** (2026-11-12): M-09 suma `actualizar_ruta` (misma fila, solo del dueño); M-07 interpreta modificaciones del chat (agregar parada, pedir aclaración); M-05 y M-04 las aplican; un servicio de guardado sin migración de esquema (los datos de v2 van dentro de `resumen`); y las pantallas «Guardar ruta» y «Mis rutas guardadas» en `/v2/rutas`. El dueño sale siempre de la sesión de v1. Un cambio autorizado por Angel en v1 (`abrirRutaGuardada`, 6 líneas en `v1/static/js/main.js`) redirige a `/v2/rutas` cuando la ruta la guardó v2. Estado: probado en simulación (2026-11-12); persistencia real, login real y navegador sin verificar (2026-11-12). Commits locales, sin push ni tag.

**Incremento v0.4.0, Descubrir** (2026-11-12): catálogo público `/v2/descubrir` (visible sin sesión) para buscar, filtrar por duración, categoría y región, y ver el detalle de una ruta; solo aparecen las rutas con `visibilidad = 'publica'`, y del autor solo nombre e inicial del apellido. Incluye la migración de las siete columnas autorizadas el 2026-11-03 (ensayada en PostgreSQL local, no ejecutada en Supabase) y un script administrativo para publicar o volver privada una ruta; no hay botón de publicar en la app. Las listas de categorías y regiones y la publicación por script son una **propuesta del equipo**: P-01 y P-03 siguen abiertas ante el profesor. Estado: probado en simulación en el catálogo, el servicio y los endpoints (2026-11-12) y, con un PostgreSQL local desechable, en el SQL real, la migración (dos corridas sin error, filas anteriores conservadas) y la publicación de una ruta ficticia (2026-11-17); los filtros dinámicos y el reinicio de la pantalla (RF-06 y RF-08) solo están programados, porque el navegador no se probó. Sin verificar (2026-11-17): la migración en Supabase, el navegador, la regresión de v1 y la concurrencia del `FOR UPDATE`. En la base real no se publicaron rutas en estas sesiones; si ya hay rutas públicas allí, sin verificar (2026-11-17). Commit local `4204079` (2026-11-13), sin push, sin tag. Detalle en [[RutaMX - Arquitectura]] y [[RutaMX - Decisiones]].

Avance medido en el reporte `documentacion/Reporte_Avance_Incremento_v0.4.0.md`: 25 de 44 requerimientos funcionales completos en simulación (56.8%), 2 solo programados, 4 parciales y 13 sin iniciar; ninguno verificado en uso real.

Los commits y las entradas nuevas de la versión 2 llevan el marcador `[V2]` (regla del profesor).

**Plan de incrementos** (aprobado por Angel y Roberto el 2026-11-05, en `documentacion/plan_incrementos.md` con los anexos A1 a A4): el incremento 1 es M-09 (tag `v0.1.0`) y los otros cuatro reparten los 44 RF y 33 RNF así: v0.2.0 Planear con IA (12 RF), v0.3.0 guardar y recuperar (9), v0.4.0 Descubrir (10) y v0.5.0 edición restante, copiar, mapa y cierre (13, el recortable). Todo requerimiento sigue «Pendiente» hasta verificarse en uso real; RF-18, RF-24 y RF-37 se cierran por completo hasta el v0.5.0. Siguen abiertas ante el profesor P-01, P-02 y P-03; el v0.4.0 avanzó con una propuesta del equipo para P-01 y P-03. Detalle en [[RutaMX - Arquitectura]], [[RutaMX - Decisiones]] y [[RutaMX - Problemas resueltos]].

## Datos rápidos
- Repositorio: `angelmataco/RutaMX` en GitHub. 59 commits en GitHub, del 2026-09-17 al 2026-11-10 (contados con `git rev-list --count origin/main`), más diez locales (siete del 2026-11-12 y tres del 2026-11-13) que aún no se suben (69 en la copia local, contados con `git rev-list --count HEAD`): los 32 de septiembre, el del crédito y la licencia, 4 del 2026-10-13 hechos desde la MacBook Air (documentos de requerimientos, diseño modular, bitácora y un merge), 2 del 2026-10-15 también desde la Air (la práctica de persistencia y su PDF con el formato azul original), 5 del 2026-10-29 (reorganización del repo y plan de M-09), 4 del 2026-11-03 (M-09 y su documentación), 2 del 2026-11-05 (el plan de incrementos y el registro de su publicación) y 9 del 2026-11-10 (los módulos del v0.2.0, su demostración, el reporte de avance y los PDF); los siete locales del 2026-11-12 (el código del v0.3.0, el ajuste de v1 que redirige las rutas de v2, los reportes de avance y el script `scripts/md_a_pdf.py`) y los tres del 2026-11-13 (el código del v0.4.0, su documentación y el registro de ese commit); los de M-09 en adelante llevan el marcador `[V2]`. Una sola rama, `main`, y el tag `v0.1.0` (sobre el último commit de M-09, `d74a1ba`; el commit del plan es `3e11b46`); no hay tags `v0.2.0`, `v0.3.0` ni `v0.4.0`.
- Backend: ~2,800 líneas de [[Python]] en `app/` (hoy `v1/`; cifra de antes de la reorganización). Frontend: ~2,300 líneas de JS (sin contar los efectos; `main.js` tiene ~1,300) y ~3,800 de CSS (`styles.css` ~2,600 y `efectos.css` ~1,200), sin framework ni paso de compilación.
- Pruebas: 123 tests con `pytest`: servicios (55), rutas (34), gasto (21), planificador IA (5), destinos IA (4) y autenticación (4) (algunos tocan la base real y el servicio de ruteo, así que necesitan internet).
- Esos 123 son la cifra histórica de v1; su regresión con v2 no se ha corrido porque sus pruebas escriben en Supabase.
- Pruebas de `base_datos/tests/` (2026-11-17): sin PostgreSQL 140 pasan y 34 se omiten con aviso; con un [[Supabase y Postgres|PostgreSQL]] desechable local 174 pasan y 0 se omiten (simulación local, no uso real).
- Pruebas de v2 (2026-11-17): 389 pasan y 1 se excluye con `-k` (el caso opcional de navegador, que no se ejecutó) en `v2/tests/`, con IA y geografía simuladas, sin red ni base; incluyen las 7 de la plantilla real de Descubrir.
- Suma de v2 y `base_datos` (2026-11-17): sin PostgreSQL 529 pasan, 34 se omiten y 1 se excluye (el caso de navegador, con `-k`); con PostgreSQL local, en una base nueva, 563 pasan, 0 se omiten y 1 se excluye. Al correr por primera vez las integraciones fallaron 7 pruebas por defectos de las propias pruebas y se corrigieron el mismo día (ver [[RutaMX - Problemas resueltos]]).
- Estructura de la app: `routes.py` con 15 endpoints, 10 servicios en `v1/services/`, 4 modelos. El más grande es `services/ai_service.py`, con 888 líneas (contadas en GitHub el 2026-10-18).
- Estructura: `v1/`, `v2/` y `base_datos/` (ver [[RutaMX - Arquitectura]]). Se corre con `python run.py` y queda en `http://127.0.0.1:5000`.
- Documentos de la materia (propuesta inicial, requerimientos y diseño modular): en GitHub los PDF están en la carpeta `documentacion/` del repo. El plan de implementación del módulo M-09 (versión 1.1, entregado a la clase) está ahí mismo, en `RutaMx_Plan_de_Implementacion_M09.pdf`.
- El proyecto tiene su propia **bitácora** en `bitacora_proyecto/` (qué está hecho, qué falta, decisiones) pensada para que Claude y [[Codex CLI|Codex]] la lean antes de tocar código.

## Lo que falta (resumen)
Detalle y razones en [[RutaMX - Decisiones]]. Lo principal:
1. **Re-etiquetar la base y agregar restaurantes y hoteles** (sin pagar nada). Plan parcial: está hecha la lectura de estrellas y Bib Gourmand y el marcado gastronómico de los destinos, pero faltan la poda de etiquetas y la tabla de establecimientos.
2. **Calibrar el tiempo de viaje contra Google Maps**: León → Cabo San Lucas sale ~50 h en la app y ~44 h en Google.
3. **Probar la IA con una key real**: el chat de "Planear con IA" de v1, la generación de destinos y la pantalla `/v2/planear` solo se han probado con IA simulada. Para v2 faltan `ANTHROPIC_API_KEY` e `IA_V2_MODELO`.
4. **Desplegar en un hosting público** (Render o Railway) para compartirla con un link.
5. **Probar en teléfono real** el navbar compacto, el tope entre secciones y el fondo animado.
6. Iconos para los 6 intereses de "¿Qué buscas?" (hoy solo texto) y una pasada de accesibilidad.
7. Un test falla por usar el nombre de una cuenta real ("Ángel Mata"); hay que cambiarlo a un nombre ficticio.
8. [V2] Cerrar los incrementos v0.2.0 a v0.4.0: verificación visual en navegador (escritorio y 375 px), regresión de v1, push de los commits locales y los tags `v0.2.0`, `v0.3.0` y `v0.4.0`. Después sigue el v0.5.0 (edición completa por chat, copiar rutas, mapa y cierre), que necesita la respuesta a P-02. M-09 suma copiar en el v0.5.0.
9. [V2] Endurecer `/v2/planear`: la `SECRET_KEY` por defecto de desarrollo, el reinicio de conversación sin tope y fijar la versión del SDK `anthropic`; la conversación vive en memoria de un solo proceso.
10. [V2] Descubrir: consultar P-01 y P-03 con el profesor (hoy hay una propuesta del equipo), ejecutar con respaldo la migración de `rutas_guardadas` en Supabase (la hace Angel; ya se ensayó en PostgreSQL local, 2026-11-17), publicar al menos una ruta con el script en la base real y probar la concurrencia del `FOR UPDATE`: sin verificar (2026-11-17).

## Documento de requerimientos
Práctica de historias de usuario, criterios y trazabilidad. **El PDF es la fuente**; aquí solo el resumen. Decisiones en [[RutaMX - Decisiones]], módulos propuestos en [[RutaMX - Arquitectura]] y el problema de los criterios en [[RutaMX - Problemas resueltos]].

| Versión | Fecha | Qué cambió | Estado |
|---|---|---|---|
| 1.0 | 2026-09-28 | Problema, alcance, 44 RF, 33 RNF, 23 historias, 92 criterios, riesgos, bitácora de IA | Entregado |
| 2.0 | 2026-10-08 | Corrige ambigüedades, prioriza historias (12 Alta, 10 Media, 1 Baja), 93 criterios, matriz de trazabilidad y 11 módulos | Pendiente de validación de Roberto |

Archivos en `documentacion/` del repo (agregados a GitHub el 2026-10-13): `RutaMx_Documento_Requerimientos.pdf` (v1.0, sin modificar) y `RutaMx_Documento_Requerimientos_v2.0.pdf` (vigente). Con cada versión nueva se agrega una fila a la tabla. Hecho con [[Claude Code]].

### Diseño modular y arquitectura inicial
Segunda práctica, basada en el documento v2.0: `RutaMx_Diseno_Modular_Arquitectura_Inicial_Actualizado.pdf` (8 páginas, Universidad Iberoamericana León, asignatura "Desarrollo de aplicaciones y servicios virtuales"). **Solo diseño: no incluye implementación.** Roles que declara: Roberto Valderrama, arquitectura / diseño y análisis; Angel Mata, operación de IA y validación técnica. **El PDF es la fuente**; el resumen está en [[RutaMX - Arquitectura]] (sección "Diseño modular") y las decisiones en [[RutaMX - Decisiones]]. Se pensó para un MVP de 8 semanas con 2 integrantes. Su bitácora de revisión con IA aparece en la última tabla del PDF; **no pude leer su contenido** (la página 8 termina en la cabecera de la tabla).

## Mapa de notas
- [[RutaMX - Arquitectura]]: capas, endpoints, servicios, base de datos y flujo de una ruta.
- [[RutaMX - Tecnologías]]: [[Flask]], Supabase, OSRM, Leaflet, proveedores de IA y más.
- [[RutaMX - Decisiones]]: el porqué de las decisiones y lo pendiente.
- [[RutaMX - Problemas resueltos]]: bugs reales que se encontraron y cómo se arreglaron.

## Relacionado
- [[QR WiFi]]: otro proyecto en [[Python]] de la bóveda.
- [[Govee Claude]]: otro proyecto en Python hecho con apoyo de [[Claude Code]].

## Tecnologías relacionadas
Notas generales en la carpeta `Tecnologías`:
- [[Python]]
- [[Google Fonts]]
- [[Git y GitHub]]
- [[python-dotenv y env|python-dotenv y .env]]
- [[reportlab]]
- [[Claude Code]]
- [[Codex CLI]]: Roberto trabaja con Codex; por eso el repo tiene `AGENTS.md`.
- [[Pruebas con simulación]]
- [[Medir antes de decidir]]
- [[Acceso único al modelo de lenguaje]]
- [[JavaScript y CSS puros]]
- [[Rare UI]]
- [[Google Stitch]]: la carpeta de diseño fuente de la paleta, el logo y el `DESIGN.md` del rediseño.
- [[Flask]]
- [[Supabase y Postgres]]
- [[SQLAlchemy]]: la `Session` propia de M-09.
- [[Mapas con OSRM, Nominatim y Leaflet]]
- [[pytest]]

## Historial de cambios
- 2026-10-04: nota creada a partir del código, el README y la bitácora del proyecto. Estado: En progreso. Último commit revisado: `ce92ca3` (2026-09-20).
- 2026-10-04: se agregó la sección "Tecnologías relacionadas" con enlaces a las notas generales de la carpeta `Tecnologías`.
- 2026-10-07: auditoría contra GitHub: 32 commits (último `ce92ca3`), 123 tests, 15 endpoints y 10 servicios coinciden con la nota. Se agregó el enlace a [[Rare UI]]. Hallazgo: el repo es público, usa efectos de Rare UI portados y no tenía el enlace de crédito a rareui.com que pide su licencia ni `LICENSE` propia.
- 2026-10-07: se agregó al repo el crédito a [[Rare UI]] (pie de página, README y bitácora) y el `LICENSE` (MIT); commit `ea8ba56`. Queda pendiente decidir si el repo se hace privado, porque la licencia de Rare UI prohíbe redistribuir los efectos portados.
- 2026-10-08: se documentó el documento de requerimientos v2.0 (sección nueva, decisiones, módulos propuestos y problema de criterios en las notas del proyecto). Pendiente de validación de Roberto.
- 2026-10-10: enlazada la nota de tecnología [[Google Stitch]], que ya se mencionaba en [[RutaMX - Tecnologías]] sin nota propia.
- 2026-10-13: auditoría contra GitHub: la cifra de commits pasó de 33 a 37 (4 nuevos del 2026-10-13 desde la MacBook Air: carpeta `documentacion` con los requerimientos, diseño modular y arquitectura inicial, bitácora y un merge). **No revisé su contenido**, así que las notas de arquitectura y decisiones podrían estar desactualizadas.
- 2026-10-13: revisados los 4 commits nuevos. Los requerimientos v2.0 y su bitácora ya estaban documentados (2026-10-08); lo nuevo es el PDF de **diseño modular y arquitectura inicial** (sección en [[RutaMX]], resumen en [[RutaMX - Arquitectura]] y [[RutaMX - Decisiones]]) y que los PDF están en `documentacion/` del repo. Corregida la ruta `info_proyecto/`. Pendiente: no pude leer la bitácora de IA del final del PDF.
- 2026-10-14: enlazada la nota nueva [[Codex CLI]] (Roberto trabaja con Codex); sin cambios en el proyecto.
- 2026-10-17: enlazada la nota nueva [[Google Fonts]] (usa o menciona esa fuente); sin cambios en el proyecto.
- 2026-10-29: reorganización del repo en `v1/`, `v2/` y `base_datos/` (rama `reorganizacion`, sin mezclar a `main`), plan de implementación de M-09 v1.1 entregado y Supabase caído. Rutas viejas corregidas en [[RutaMX - Arquitectura]]; decisiones en [[RutaMX - Decisiones]] y pendiente en [[RutaMX - Problemas resueltos]].
- 2026-11-03: primer módulo de la versión 2, M-09 (crear, obtener y listar), probado en simulación; la rama `reorganizacion` se mezcló en `main` y se borró; regla del marcador `[V2]`. Cifra de commits y pruebas actualizada; notas de arquitectura, decisiones, problemas y tecnologías al día. Enlazadas [[SQLAlchemy]] y la nota nueva [[pytest]].
- 2026-11-05: plan de incrementos aprobado por Angel y Roberto y publicado (commit `3e11b46`, tag `v0.1.0`); cifra de commits actualizada, decisiones del plan en [[RutaMX - Decisiones]] y un problema nuevo en [[RutaMX - Problemas resueltos]]. Sin cambios de código.
- 2026-11-10: incremento v0.2.0 (Planear con IA) con seis módulos nuevos en `v2/`, probado en simulación, y auditoría de las bitácoras del proyecto (cifras, estados y pendientes conciliados con el código y `git log`). Cifras de commits y pruebas actualizadas; notas de arquitectura, decisiones, problemas y tecnologías al día.
- 2026-11-12: revisión del primer módulo (M-09) contra el repo, sin cambios de código; corregidos el diseño "sin implementar", el campo "personas" que ya no aplica, un problema nuevo (M-04) y las notas de Tecnologías (M-07 y M-08).
- 2026-11-13: incrementos v0.3.0 (guardar y recuperar rutas) y v0.4.0 (Descubrir) documentados a partir del repo y de `git log`: estado, cifras de commits y pruebas, avance medido, decisiones, problemas resueltos y pendientes reemplazados donde estaban. Sin cambios de código; el v0.4.0 sigue sin commit.
- 2026-11-17: el v0.4.0 se ensayó contra un PostgreSQL local desechable (migración, publicación, SQL y pruebas de integración); las 7 pruebas que fallaban se corrigieron y la suite quedó en verde en simulación local. Navegador, Supabase, regresión de v1 y concurrencia siguen sin verificar. Estado, cifras y pendientes reemplazados donde estaban; borradores de [[RutaMX - Arquitectura]], [[RutaMX - Decisiones]] y [[RutaMX - Problemas resueltos]] al día.
