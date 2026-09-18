# Lo que ya está hecho — RutaMX

Última actualización: 2026-09-18

RutaMX es una app web para planear road trips por México. Flujo completo
funcionando de punta a punta: formulario → cálculo de ruta → mapa →
sugerencias de paradas → armar itinerario → guardar → descargar PDF.

## Mapa y ruta

- Mapa con Leaflet + OpenStreetMap.
- Ruta real por carretera (no línea recta) con Leaflet Routing Machine +
  OSRM (servidor demo gratuito, sin API key).
- Distancia, tiempo y costo estimado calculados con la ruta real de OSRM;
  si OSRM no responde, cae a una estimación en línea recta para que no se
  rompa el flujo.
- **Geocoding real arreglado**: antes el cálculo de ruta solo reconocía 18
  ciudades hardcodeadas y cualquier otra (ej. León, Los Cabos) caía en la
  misma coordenada de respaldo, dando un mapa en blanco. Ahora resuelve en
  orden: tabla `destinos` (369 lugares) → Nominatim (geocoding real) →
  catálogo de 18 ciudades → respaldo.
- Mapa agrandado (llena toda su tarjeta, sin espacio en blanco).

## Destinos nuevos generados con IA (multi-proveedor)

- Cuando alguien escribe un origen/destino que no está en los 369
  destinos curados (ej. "Manuel Doblado", con o sin errores de
  ortografía), `app/services/ia_destinos_service.py` le pide a la IA
  configurada que identifique el lugar real, busque en internet los datos
  necesarios (estado, tipo, descripción, intereses, población) y lo
  inserte en `destinos` con `fuente="ia_generada"`.
- Las coordenadas nunca se toman de lo que "sepa" la IA — siempre se
  verifican con `geocodificar()` (Nominatim), igual que los 369 curados.
- Pasa **una sola vez por lugar**: la siguiente vez que alguien lo
  escriba, ya está en la tabla y no se vuelve a llamar a la IA.
- Desde que se inserta, funciona exactamente igual que los curados:
  aparece en el autocompletado, en sugerencias de paradas para rutas
  futuras que pasen cerca, y en el cálculo de rutas.
- **Multi-proveedor de verdad**: `app/services/llm_provider.py` detecta
  solo con qué variable de entorno esté configurada
  (`ANTHROPIC_API_KEY` → `OPENAI_API_KEY` → `GEMINI_API_KEY`) cuál usar —
  Angel puede tener la de Claude, Roberto la que tenga, sin tocar código.
  Sin ninguna key configurada, la app sigue funcionando igual que antes
  (cae a Nominatim directo, solo que ese lugar no se guarda para
  siempre).

## Base de datos de destinos (Supabase / Postgres)

- Catálogo de los 32 estados con 369 destinos verificados: mínimo 8
  ciudades/pueblos mágicos y mínimo 3 sitios turísticos por estado.
- Cada destino tiene nombre, estado, tipo, coordenadas verificadas contra
  Nominatim, descripción e intereses asociados.
- Rutas guardadas también viven en Supabase (tabla `rutas_guardadas`), ya
  no se pierden al reiniciar el servidor.

## Sugerencias de paradas (IA / lógica de ruta)

- Filtra destinos por cercanía real a la carretera (usando la geometría de
  OSRM), no en línea recta.
- Si el usuario indica horas máximas de manejo seguido, prioriza destinos
  cerca de ese punto del viaje como sugerencia de descanso.
- Se descartan destinos a menos de 1 hora real de manejo del origen (están
  prácticamente en la misma ciudad de la que sales); ya NO se descartan
  los que están cerca del destino (ahí sí tiene sentido sugerir cosas).
- "Ver más recomendaciones" trae tandas de 16 en vez de 8.
- Sin filtros de interés marcados da recomendaciones generales; si luego
  seleccionas uno o más filtros y vuelves a dar "Planea mi ruta", se
  filtran de acuerdo a eso.
- Si cambias los filtros y vuelves a calcular la ruta (mismo origen y
  destino), las paradas que ya habías agregado al itinerario **ya no se
  borran** — antes sí se perdían.

## Autocompletado de Origen/Destino

- Dropdown propio en JS (no el `<datalist>` nativo del navegador) para los
  campos Origen y Destino, alimentado por los 369 destinos de la base.
- Ignora acentos y mayúsculas (escribir "leon" sí encuentra "León").
- Se puede aceptar la sugerencia resaltada con **Tab** (y de paso sigue
  moviendo el foco al siguiente campo) o con **Enter**.
- Flechas arriba/abajo para navegar entre sugerencias, Escape para cerrar.

## Itinerario y guardado

- Armar itinerario agregando/quitando/reordenando paradas sugeridas.
- La parada de ORIGEN tiene un color distinto (dorado claro) al de
  DESTINO (terracota) y a las paradas normales (verde), para diferenciarlas
  a simple vista.
- "Guarda tu plan" (guardar ruta + selector de rutas guardadas) vive junto
  a "Resumen de aventura" en la sección de itinerario — antes estaba en la
  sección del mapa, donde no encajaba bien.
- Descarga de itinerario en PDF con el branding de la app (ReportLab,
  backend).

## Calidad / pruebas

- 21 tests automatizados (`pytest -q`), cubren cálculo de ruta, geocoding,
  sugerencias, guardado de rutas y generación de PDF.
- Grafo de conocimiento del proyecto generado con graphify
  (`graphify-out/`), se actualiza con `/graphify update`.

## Commits recientes (los últimos 3, de la sesión más reciente)

1. Autocompletado propio con Tab/Enter y sin distinguir acentos.
2. Arreglo: las paradas ya no se borran al cambiar solo los filtros.
3. Arreglo raíz del geocoding (tabla + Nominatim) + mapa más grande + tandas
   de 16 + colores de origen/destino + reubicación de "Guarda tu plan".
