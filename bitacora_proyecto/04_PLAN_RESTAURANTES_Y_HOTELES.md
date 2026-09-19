# Plan: re-etiquetar la base y agregar restaurantes y hoteles

Última actualización: 2026-09-19

Este es el plan completo (todavía **sin implementar**) de lo que Angel quiere
hacer con más tiempo: (1) revisar las etiquetas de la base actual de destinos,
y (2) crear tablas de restaurantes y hoteles con lugares buenos, para que las
recomendaciones de "comer" y "dormir" cambien. Está aquí para que cualquiera
(Angel, Roberto, Claude, Codex) lo retome sin perder nada de lo hablado.

Leer también `02_LO_QUE_FALTA.md` (pendientes) y `03_DECISIONES_Y_NOTAS.md`.

## 1. Qué quiere Angel (en sus palabras, ordenado)

1. **No pagar nada.** Ninguna API de pago ni tarjeta.
2. **Primero cambiar la base actual (369 destinos), después crear las tablas de
   restaurantes y hoteles.** Para saber si un lugar es realmente bueno en
   comida hay que consultar cuántos restaurantes tiene, así que el análisis de
   restaurantes sirve a los dos pasos.
3. **Calidad, no cosas al azar:** restaurantes y hoteles "buenos" (la idea era
   más de 3.5 estrellas sobre 5).
4. **Cantidad según el tamaño del lugar:** una ciudad grande como León tiene
   muchos más que un pueblo mágico; en los pueblos, 1 o 2 de cada tipo.
5. **También en carretera**, con la misma calidad y que sea **seguro llegar**;
   de esos habrá menos y tienen **menos prioridad** que los que están dentro
   de ciudades y pueblos de la base.
6. **Etiquetas de la base actual:** revisar toda la base. Un lugar puede tener
   **una sola etiqueta** (ya no es obligatorio tener 2 o 3). "Comida" (la doble
   etiqueta, ej. "pueblo mágico + comida") solo si de verdad son muy buenos en
   comida. "Cultura" solo si de verdad hay cultura. Lo que no encaje se queda
   sin esa etiqueta.
7. **Nueva forma de recomendar:** en un tramo de "Comer" salen primero los
   **restaurantes**, pero también **pueblos o ciudades con muy buena comida**,
   dejando claro que lo son ("Pueblo Mágico con muy buena comida"), para quien
   quiera comer y de paso visitar. Igual con hoteles y "Dormir". Los destinos
   generales se quedan como turismo y **siguen saliendo** aunque no sean de
   comida.
8. **Todo debe seguir fluyendo igual que hoy, sin bugs**: tramos, gasto,
   itinerario, PDF, rutas guardadas, enlace de Google Maps, mapa **y la IA de
   "Planear con IA"** tienen que funcionar con las tablas nuevas.

## 2. Lo que se verificó (y limita el plan)

### 2.1 Calificaciones (estrellas/reseñas): no hay forma gratuita y legal de guardarlas

- **Tripadvisor Content API:** 5,000 llamadas gratis al mes, pero pide tarjeta
  ([FAQ](https://tripadvisor-content-api.readme.io/reference/faq)) y su
  [política de caché](https://tripadvisor-content-api.readme.io/reference/caching-policy)
  **no permite guardar** su contenido (solo el `location_id`); además exige
  mostrar su logo ([términos](https://tripadvisor-content-api.readme.io/reference/api-master-terms-new)).
- **Google Places:** exige cuenta de facturación; con calificaciones son unas
  1,000 llamadas gratis al mes
  ([uso y facturación](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing)).
  Por lo que se recuerda también restringe guardar datos (no verificado).
- **Foursquare:** las calificaciones solo están en el plan de pago
  ([cambios](https://docs.foursquare.com/developer/reference/upcoming-changes)).
- **OpenStreetMap (Overpass):** gratis, sin registro, y **sí se puede guardar**
  (licencia ODbL, hay que citar la fuente), pero **no trae reseñas ni
  calificaciones**.

### 2.2 La idea de "abrir las páginas de cada lugar y copiar las estrellas a mano"

Angel propuso que Claude entre a los sitios de cada lugar, vea las estrellas y
las capture en la base, sitio por sitio. Notas honestas:
- **Es muy lento:** ~1,400 lugares (ver cupos abajo), uno por uno.
- **Copiar calificaciones de Google Maps o Tripadvisor va contra sus
  términos** (uno de los dos prohíbe guardarlas; los dos prohíben extraerlas
  automáticamente, por lo que se sabe: verificar antes de hacerlo). Para un
  proyecto escolar que no se publica el riesgo práctico es bajo, pero no es
  cero, y las calificaciones cambian con el tiempo (se quedarían viejas).
- **Alternativa que sí es limpia y gratuita:** que la "calidad" sea una
  **decisión del equipo** (Angel y Roberto marcan los lugares que conocen o
  que verifican), guardada como `fuente = "equipo"`, sin copiar cifras de
  terceros. Y apoyarse en **reconocimientos públicos** (ver 3.1).
- Decisión pendiente de Angel: elegir entre esta alternativa, o copiar
  calificaciones a mano asumiendo el riesgo, o pagar/registrarse más adelante.

### 2.3 Piloto con OpenStreetMap (restaurantes a 4 km del centro, 2026-09-19)

| Lugar | Restaurantes | Con tipo de cocina | Con sitio web |
|---|---|---|---|
| León | 51 | 28 | 2 |
| Oaxaca de Juárez | 369 | 239 | 17 |
| Puebla | 447 | 105 | 19 |
| Ensenada | 58 | 37 | 4 |
| Tequisquiapan | 14 | 5 | 0 |
| Real de Catorce | 4 | 1 | 0 |

**Conclusión clave:** OpenStreetMap está mapeado de forma **desigual**. León
(1.5 millones de habitantes) sale con solo 51 restaurantes y Oaxaca con 369.
**Contar restaurantes NO mide qué tan buena es la gastronomía**: mide qué tanto
lo han mapeado voluntarios. Por eso el conteo solo puede ser una señal de
apoyo, nunca el criterio único de "buena comida".

En Oaxaca (5 km) también salieron 277 lugares de hospedaje; solo el 45 % de
los hoteles trae `stars` y el 46 % sitio web.

### 2.4 Reconocimientos públicos que sí sirven como señal de buena gastronomía

- **UNESCO, Ciudades Creativas en Gastronomía (México):** Ensenada (2015) y
  Mérida (2019) ([Ensenada](https://www.unesco.org/en/creative-cities/ensenada),
  [Mérida](https://www.unesco.org/en/creative-cities/merida)).
- **Guía Michelin México 2025:** destinos CDMX, Baja California, Los Cabos,
  Monterrey y Oaxaca; hubo reconocidos también en Quintana Roo
  ([Michelin](https://guide.michelin.com/mx/es/articulo/michelin-guide-ceremony/guia-michelin-mexico-estrellas-nuevas-2025)).
  Para 2026 la guía amplió sus destinos
  ([HOLA](https://www.hola.com/us-es/lifestyle/20260311888947/guia-michelin-destinos-gastronomicos-mexico-2026/)):
  **falta leer la lista completa**.

## 3. Fase 1 — Re-etiquetar la base actual (PRIMERO)

**Estado (2026-09-19): parte 1 hecha, parte 2 pendiente.**
- ✅ Hecho: marcar gastronomía destacada con UNESCO + Guía Michelin 2026
  (estrellas y Bib Gourmand) + Latin America's 50 Best 2025: **21 lugares**, 5 de
  ellos agregados a la base (ver bitácora 01 y
  `scripts/marcar_gastronomia_destacada.py`).
- ⏳ Falta: revisar cultura/naturaleza/playas/descanso y **podar "comida"** de
  los lugares que no son destacados.

**¿Se puede limpiar ya o hay que esperar a los restaurantes? (respuesta):** se
puede en dos tiempos. Lo **aditivo** (agregar la marca de gastronomía destacada,
dar prioridad) se hizo ya porque no rompe nada. Lo **destructivo** (quitar
"comida" a ~84 lugares) conviene hacerlo **cuando ya existan los restaurantes**:
hoy un tramo de "Comer" filtra por la etiqueta "comida"; si se quitara de golpe
a casi todos, "Comer" quedaría vacío o casi vacío. Con la tabla de restaurantes
lista, "Comer" se llena con restaurantes y ahí sí se puede podar sin riesgo.
Revisar cultura/naturaleza/playas/descanso (que no dependen de restaurantes) sí
se puede hacer antes, con criterios de la sección 3.1.

**Impacto medido de podar "comida" hoy (2026-09-19):** 107 lugares la tienen;
solo los 21 destacados la conservarían y **86 la perderían** (56 ciudades, 20
pueblos mágicos y 10 sitios; entre ellos León, Ciudad Juárez, Zapopan, Saltillo,
Aguascalientes, Hermosillo, Querétaro, Morelia). **23 de 32 estados quedarían
sin ningún lugar de comida** (Guanajuato, Querétaro, Michoacán, Veracruz,
Chiapas, Sonora, etc.), y un tramo de "Comer" en esas rutas saldría vacío. Además
las fuentes (Michelin, 50 Best) están sesgadas hacia alta cocina y hacia unas
pocas ciudades: no reflejan la buena comida tradicional de muchas regiones. Por
eso la poda solo es segura cuando ya existan los restaurantes (Fase 2), o si se
agrega un respaldo para que "Comer" no quede vacío.

Estado actual (369 destinos): 358 tienen 2 etiquetas y 11 tienen 3. Etiquetas:
cultura 310 (84 %), naturaleza 247, comida 96, playas 54, descanso 42. Es
demasiado genérico: 84 % "cultura" no dice nada. Ciudades con "comida": 65 de
161; pueblos mágicos con "comida": 20 de 100.

### Decisión de Angel (2026-09-19): la poda de "comida" ESPERA a los restaurantes

Se acordó **no podar todavía** la etiqueta "comida". Cuando llegue el momento
(después de la Fase 2, con la tabla de restaurantes ya cargada):

- **Se conservan con la etiqueta "comida" estos 21 lugares** (los de gastronomía
  destacada; en la base tienen `gastronomia_destacada = true`). **No se les
  quita nada**: a estos se les **agregan además** sus restaurantes.

| Estado | Lugares que se quedan |
|---|---|
| Baja California | Ensenada, Tijuana, Valle de Guadalupe |
| Baja California Sur | Los Cabos, Cabo San Lucas, San José del Cabo, El Pescadero |
| Ciudad de México | Ciudad de México |
| Jalisco | Guadalajara, Puerto Vallarta |
| Nuevo León | Monterrey, San Pedro Garza García |
| Oaxaca | Oaxaca de Juárez |
| Puebla | Puebla de Zaragoza, Atlixco |
| Quintana Roo | Playa del Carmen, Tulum, Puerto Morelos |
| Yucatán | Mérida, Chocholá, Tixkokob |

- **Regla exacta de la poda (para no equivocarse):** quitar "comida" **solo** de
  los destinos con `gastronomia_destacada = false`. Nunca por nombre a mano. El
  script (`scripts/podar_comida.py`, **por escribir**) debe hacer eso, avisar
  cuántos cambia (hoy serían 86) y no tocar las demás etiquetas.
- **Copia de seguridad:** `scripts/datos/comida_antes_de_podar_2026-09-19.csv`
  guarda, para los 107 lugares que hoy tienen "comida", su estado, tipo,
  etiquetas actuales y si se quedan (SI/NO) y por qué. Sirve para revertir o
  revisar.
- **Antes de podar, ver el riesgo:** 86 lugares la pierden y 23 estados quedan
  sin ninguno (ver más abajo). Se poda cuando ya haya restaurantes en esos
  lugares, o con un respaldo para que "Comer" no quede vacío.
- Posibilidad abierta: agregar lugares con buena comida **regional** que estas
  fuentes no cubren (ej. Michoacán) por decisión del equipo, para no dejar
  estados enteros sin ninguno.

### 3.1 Criterios (que se puedan comprobar, no "a ojo")

| Etiqueta | Se pone solo si… | Fuente de la señal |
|---|---|---|
| **comida** | tiene reconocimiento gastronómico (UNESCO gastronomía, Michelin) **o** una gastronomía regional emblemática confirmada por el equipo. La densidad de restaurantes de OSM solo apoya, corregida por la cobertura del mapa (ver 2.3) | UNESCO, Michelin, equipo, OSM |
| **cultura** | tiene patrimonio o museos reales: sitio UNESCO, zona arqueológica, centro histórico catalogado o varios museos | Wikidata/UNESCO, INAH, OSM (`tourism=museum`, `historic=*`) |
| **naturaleza** | hay un área protegida o atractivo natural real cerca | CONANP / OSM (`boundary=protected_area`, `natural=*`) |
| **playas** | hay playa real a pocos km | OSM (`natural=beach`) |
| **descanso** | tiene oferta real de descanso (spa, resort, balneario…) | OSM (`leisure=*`, `tourism=resort`), a definir |

Un lugar puede quedar con **1 etiqueta** (o incluso más de 3). Se elimina la
regla vieja de "2 o 3 etiquetas por lugar".

### 3.2 Cómo se hace (sin cambiar nada a ciegas)

1. Script `scripts/propuesta_etiquetas.py` que, por cada destino, junta las
   señales y **genera un reporte (CSV)** con: etiquetas actuales, etiquetas
   propuestas y **por qué** (qué señal la respalda). **No modifica la base.**
2. Angel (y Roberto) **revisan el reporte** y corrigen lo que sepan que está mal.
3. Recién entonces otro script aplica los cambios aprobados (los que sean
   dudosos se quedan como estaban, no se inventa).
4. Se registra en `03_DECISIONES_Y_NOTAS.md` el criterio final por etiqueta.
5. Tests: los que dependen de etiquetas (`comida`, `descanso`, `cultura`)
   deben seguir pasando o actualizarse a propósito.

### 3.3 "Doble etiqueta" con comida

Un pueblo mágico o ciudad conserva **"pueblo mágico/ciudad + comida"** solo si
cumple el criterio de comida de arriba. Al recomendarlo en un tramo de
"Comer" se marca claramente ("Pueblo Mágico con muy buena comida").

## 4. Fase 2 — Tablas nuevas de restaurantes y hoteles

### 4.1 Diseño

Tabla nueva (separada de `destinos`, que se queda como catálogo general de
turismo): `establecimientos` con al menos:
`id`, `tipo` (`restaurante` | `hotel`), `nombre`, `lat`, `lon`,
`destino_id` (la ciudad/pueblo de la base a la que pertenece; nulo si está en
carretera), `zona` (`ciudad` | `carretera`), `cocina`, `estrellas`
(hoteles, si OSM la trae), `rango_precio` (nulo si no se sabe),
`fuente` (`osm` | `equipo` | …), `osm_id`, `motivo_calidad` (por qué entró:
reconocimiento, criterio del equipo, estrellas), `calificacion` y
`fuente_calificacion` (**vacíos por ahora**; solo se llenan si algún día hay
una fuente legal y gratuita), `verificado_en`.

### 4.2 Cupos por tamaño (propuesta, falta que Angel la confirme)

| Tipo de lugar | Cuántos hay | Restaurantes + hoteles c/u | Total |
|---|---|---|---|
| Ciudad de más de 500 mil hab. | 25 | 8 + 5 | 325 |
| Ciudad de 100 a 500 mil | 38 | 5 + 3 | 304 |
| Ciudad de menos de 100 mil | 98 | 3 + 2 | 490 |
| Pueblo mágico | 100 | 2 + 1 | 300 |
| Sitio turístico | 108 | ninguno (usa la ciudad cercana) | 0 |

≈ 1,400 lugares. Los cupos son **máximos**: si un lugar pequeño no tiene
candidatos buenos, se queda con menos (nunca se rellena con cosas al azar).

### 4.3 De dónde salen y cómo se eligen

- **Datos base (nombre, coordenadas, cocina, estrellas):** OpenStreetMap
  (Overpass), gratis y guardable, verificando coordenadas como el resto del
  proyecto (regla: no inventar datos).
- **Calidad:** por reconocimiento público (Michelin, UNESCO), estrellas de
  hotel en OSM (p. ej. ≥ 3) y/o **selección del equipo**. Cada fila guarda
  `motivo_calidad`. **Nunca se ponen calificaciones inventadas.**
- **Carga:** script `scripts/cargar_establecimientos.py`, seguro de repetir (no
  duplica), con un reporte previo para revisar antes de insertar.

## 5. Fase 3 — Que TODA la app siga fluyendo igual (requisito de Angel)

Con las tablas nuevas, todo lo que hoy trata paradas como "destinos" debe
aceptar también establecimientos, **sin cambiar el flujo que ya conoce el
usuario**. Lista de lo que hay que revisar y adaptar:

- `ai_service.py`: candidatos de tramos, `_coincide_proposito`,
  `_encaja_con_lo_pedido`, `_sugerir_por_lapsos`, `asignar_paradas_a_objetivos`.
- `gasto_service.py`: `clasificar_parada` (un restaurante es comida, un hotel
  es hospedaje por definición, sin depender de la hora) y, si se tienen
  precios, usarlos en vez de los $150 / $600 fijos.
- `main.js` / plantillas: itinerario (paradas de tipo destino o
  establecimiento), etiquetas 🍽️/🛏️, tarjetas de sugerencia (mostrar cocina y
  "estrellas" solo si hay dato), enlace de Google Maps, mapa y marcadores.
- Rutas guardadas (las paradas se guardan como JSON): que sigan abriéndose las
  ya guardadas (compatibilidad hacia atrás) y las nuevas.
- PDF del itinerario.
- **IA de "Planear con IA"** (`llm_provider.py`, `planificador_ia_service.py`,
  `preparar_objetivos_ia`): un objetivo de "comida" se resuelve con
  restaurantes primero y "descanso" (dormir) con hoteles; conserva el
  respaldo con destinos. Actualizar prompts y reglas del servidor (regla de
  `AGENTS.md`).
- Tests: cada cambio con su prueba; antes de subir, suite completa + prueba en
  el navegador de los flujos principales (ruta, tramos, comer/dormir, guardar y
  reabrir, PDF, IA con proveedor simulado).

## 6. Fase 4 — Restaurantes y hoteles en carretera

- Solo con **criterios de calidad iguales** y **menos prioridad** que los de
  ciudades/pueblos de la base.
- "Seguro llegar" (a definir): sobre o muy cerca (~2 km) de una carretera
  federal principal, fuera de ciudades de la base, con nombre y datos de
  contacto o reconocimiento. **No se puede garantizar seguridad** con datos
  abiertos; se documenta el criterio.
- Cargar por corredor (entre ciudades vecinas) y **guardar en la base** lo que
  se encuentre, para no depender de consultas en vivo (Overpass tiene límites).

## 7. Fase 5 — La nueva forma de recomendar

En un tramo personalizado de **Comer** el orden sería:
1. **Restaurantes** dentro de ciudades/pueblos de la base (mejores primero).
2. **Ciudades y pueblos con muy buena comida** (etiqueta "comida" ya
   verificada), marcados claramente para quien quiere comer y visitar.
3. **Restaurantes en carretera** (menos prioridad).

Igual para **Dormir** con hoteles. En **Automático** sigue saliendo de todo,
incluyendo los destinos generales aunque no sean de comida, y **dormir solo
aplica si el tramo termina después de las 20:00 o cruza la noche** (regla ya
implementada).

## 7b. Regla de prioridad por reconocimiento (definida por Angel, 2026-09-19)

Aplica a **ciudades y pueblos hoy** y a **restaurantes y hoteles cuando existan**:

1. **Ciudades y pueblos distinguidos (estrella ★):** SIEMPRE tienen preferencia
   (en automático y en "Comer"), en la primera página y de ser posible en el
   primer lugar, **solo si la ruta pasa cerca** (≤ 40 km). Llevan la estrella y
   la nota "recomendada a nivel gastronómico por Michelin / UNESCO / …". **Ya
   implementado.**
2. **Restaurantes y hoteles (futuro): solo entran si el usuario lo pide.**
   - Si el usuario **deja todo en automático**, NO se recomiendan restaurantes
     ni hoteles: solo ciudades y pueblos (con la prioridad del punto 1).
   - Si el usuario **pide una parada para comer** (tramo en "Comer"), ahí sí
     entran los restaurantes; igual con hoteles y "Dormir".
   - Dentro de "Comer": primero los restaurantes con estrella / reconocidos
     (que estén a ≤ 40 km de la ruta o dentro de una ciudad de la ruta), luego
     los demás restaurantes buenos, y después las ciudades distinguidas.
3. **Cómo implementarlo sin reescribir nada:** los establecimientos deben
   exponer los mismos campos que ya usa `ai_service.prioridad()`:
   `gastronomia_destacada`, `reconocimiento_gastronomico` y
   `distancia_a_ruta_km`. Así `prestigio()` / `prioridad()` /
   `_distinguidos_primero()` funcionan igual para destinos y para restaurantes.
   Lo nuevo será el filtro "solo con tramo de Comer/Dormir".

## 8. Orden de trabajo (checklist)

- [ ] Fase 0: Angel decide cómo definir "calidad" sin pagar (ver 2.2) y confirma
      los cupos (4.2).
- [x] Fase 1a: gastronomía destacada por UNESCO + Michelin (hecho).
- [ ] Fase 1b: script de propuesta de etiquetas (cultura, naturaleza, playas,
      descanso) → reporte → revisión de Angel → aplicar → tests. La poda de
      "comida" se hace después de la Fase 2.
- [ ] Fase 2: tabla `establecimientos`, carga desde OSM con reporte previo,
      selección de calidad.
- [ ] Fase 3: adaptar toda la app y la IA (sección 5) con pruebas y prueba en
      navegador.
- [ ] Fase 4: restaurantes y hoteles en carretera.
- [x] Prioridad a ciudades distinguidas cerca de la ruta (hecho, ver 7b).
- [ ] Fase 5: nueva forma de recomendar (orden de 7 y regla 7b para restaurantes) y precios reales en el gasto.
- [ ] Actualizar `01_LO_QUE_YA_ESTA_HECHO.md` al terminar cada fase y borrar lo
      hecho de este plan / de `02_LO_QUE_FALTA.md`.

## 9. Decisiones abiertas

1. ¿Cómo se define "bueno" sin pagar? (decisión del equipo + reconocimientos
   públicos vs copiar calificaciones a mano.)
2. ¿Los cupos de 4.2 están bien?
3. ¿Los criterios de etiquetas de 3.1 están bien, o se agregan/quitan?
4. Leer la lista completa de destinos Michelin 2026 y confirmar cuáles de
   nuestros lugares entran.
