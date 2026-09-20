# Decisiones y notas — RutaMX

Última actualización: 2026-09-20

El "por qué" detrás de decisiones que no son obvias con solo leer el
código. Se va agregando conforme pasa.

## (Histórico) Selector de hora tipo rueda — REEMPLAZADO por el duration-picker gooey

> Ya no existe: Angel pidió cambiarlo por el efecto `duration-picker` de rare-ui ("se ve más
> pro"). La primera versión se escribía a mano y no le gustó ("no supe cómo poner una hora"),
> así que quedó **híbrido**: el efecto gooey del duration-picker + una ruedita para deslizar la
> hora y los minutos. La regla de "nada con teclado" se mantiene. Lo de abajo es el contexto
> de la decisión anterior.

Angel pidió explícitamente que ningún campo (hora de salida, presupuesto,
horas máximas) obligara a escribir con teclado. El `<input type="time">`
nativo en iOS Safari YA se ve como una rueda, pero en escritorio
(Chrome/Firefox/Safari de Mac) se renderiza como un campo de texto con
flechitas — exactamente lo que no se quería. Por eso se construyó un
selector propio con `<dialog>` + `scroll-snap-type: y mandatory` — mismo
patrón de "usar HTML nativo antes que una librería" que ya se seguía con
los otros modales. Guarda el valor en un input oculto con el mismo
`name="hora_salida"` de siempre, así que ni `form.js` ni `main.js`
necesitaron cambios.

**Formato 24 horas, sin AM/PM:** primera versión tenía 3 columnas (hora
12h, minutos de 5 en 5, AM/PM). Angel pidió cambiarlo a 24 horas — dos
columnas nada más (hora 00-23, minuto 00-59 de 1 en 1) — más simple y sin
la columna extra de AM/PM.

**Bug real encontrado y corregido:** el recuadro verde que resalta la
hora seleccionada tapaba por completo los números en vez de quedar
detrás. Causa: `.time-wheel-picker__highlight` tiene `position:absolute`
mientras que las columnas de números (`.time-wheel-picker__col`) no
tenían ninguna posición especial (`position:static`, el default) — en
CSS, un elemento posicionado siempre se pinta ARRIBA de los elementos no
posicionados dentro del mismo contexto de apilamiento, sin importar el
orden en el HTML. El recuadro, aunque va primero en el markup, tapaba los
números que iban después. Arreglo: darle a `.time-wheel-picker__col`
también `position:relative` + `z-index:1` (y `z-index:0` explícito al
recuadro) para que los números pinten encima. Ojo para el futuro: cuando
se mezcla `position:absolute` con elementos normales en el mismo
contenedor, el orden del DOM NO garantiza el orden de pintado — hay que
fijar el `z-index` a propósito.

(Nota histórica: durante el debugging de este bug, antes de encontrar la
causa real, se llegó a sospechar que era solo un problema de las
capturas de pantalla del navegador de pruebas — resultó ser ambas cosas:
la herramienta de captura sí tiene un problema aparte con currentTarget
de scroll-snap, pero el tapado real de los números SÍ era un bug de CSS
genuino, confirmado porque Angel lo vio con sus propios ojos en la app.)

## Gasto máximo recomendado: por qué automático y por qué estas fórmulas

Angel no quería que el usuario respondiera muchas cosas: por eso comidas
y noches se **deducen solas** (paradas con interés "comida"; noches
simulando el viaje con la hora de salida) y los ajustes manuales quedan
en un desplegable opcional, con "vacío = automático". Nada de marcar
cada parada como "comer/dormir".

Las casetas no se pueden calcular exactas sin datos reales de cada
caseta (cada una cuesta distinto, incluso en la misma carretera). Se
evaluó la API SAKBÉ de INEGI (devuelve el costo de cada caseta de la
ruta; token gratis por correo), pero Angel prefirió no registrarse en
nada por ser proyecto escolar. Por eso: IA con búsqueda web si hay una
conectada, y si no un promedio por km. Ese promedio ($1.1/km) sale de
~$1.5/km en tramos de cuota (fuente: guía de casetas.com.mx, rango
$1–2/km) por ~70% del trayecto por cuota (suposición). La gasolina usa
el precio real de la Magna (Infobae, 18 sep 2026, $23.8/l) y un punto
medio de $25.5/l porque la Premium cuesta ~$5-6 más.

Los imprevistos ($500–$2,000) llegan al tope a las 20 h y no a las 40 h
porque casi nadie hace viajes tan largos (pedido de Angel).

## Sugerencias: por qué lapsos automáticos en vez de "horas máximas"

Angel no quería una pregunta más en el formulario, y "horas máximas de
manejo seguido" casi nadie la llenaba. Ahora la duración del viaje decide
sola cuántos lapsos hay (~3 h cada uno) y la ventana de recomendación
(30 min después de salir a 20 min antes de llegar). El valor de 3 h
(`LAPSO_OBJETIVO_H`) y los 30/20 min están como constantes en
`ai_service.py` por si se quieren afinar.

## Tramos personalizados: por qué "estricto" y por qué dormir es especial

Angel quiso que elegir "comer" en un tramo recomiende SOLO lugares donde se
puede comer, y que en automático salga de todo pero nunca "dormir" si no
aplica (solo si se pasa de las 8 pm). Por eso un tramo personalizado filtra
duro y uno automático solo prioriza, y "dormir" depende de la hora del
reloj. Se eligió que sea un solo toque por tramo (fila de chips al tocar el
tramo) y no un formulario, para no volver invasiva la app. La base tiene 96
de 369 lugares con interés "comida" y 42 con "descanso" (más las ciudades
grandes cuentan como dónde dormir), por eso a veces un tramo estricto sale
vacío y se avisa.

## La IA de "Planear con IA" debe seguir las mismas reglas que la app

Cada vez que cambien las reglas de la app (gasto, tramos, dormir, ventana de
recomendación) hay que reflejarlo en los prompts de `llm_provider.py` **y**
hacerlas cumplir en el servidor (`preparar_objetivos_ia`), porque el modelo
puede equivocarse. Ver regla en `AGENTS.md`.

## Restaurantes y hoteles: por qué primero se re-etiqueta y por qué no se guardan calificaciones

Angel no quiere pagar nada y quiere lugares buenos, no al azar. Se decidió
(2026-09-19): primero revisar las etiquetas de la base actual y después crear
las tablas de restaurantes y hoteles (el análisis de restaurantes sirve a las
dos cosas). Hallazgos que condicionan todo (detalle en
`04_PLAN_RESTAURANTES_Y_HOTELES.md`): las calificaciones no son gratis ni se
pueden guardar (Tripadvisor solo permite guardar el `location_id`); y
OpenStreetMap está mapeado de forma desigual (León 51 restaurantes vs Oaxaca
369), así que **contar restaurantes no mide la gastronomía**: por eso la
etiqueta "comida" se apoya en reconocimientos públicos (UNESCO, Michelin) y en
la decisión del equipo, no en el conteo.

## Gastronomía destacada: por qué aditivo y no se quitó "comida" todavía

Para no dejar los tramos de "Comer" vacíos, primero se AGREGÓ una marca
(`gastronomia_destacada`) en vez de quitar la etiqueta "comida" a los demás
(que es lo que filtra el tramo estricto). Se poda cuando existan los
restaurantes. Criterio de la marca: solo reconocimientos públicos con fuente
(UNESCO Ciudad Creativa de la Gastronomía; Guía Michelin México 2026 con
estrella, o Bib Gourmand con la ciudad confirmada). La lista de "recomendados"
de Michelin (133) no se usó porque no se pudo confirmar la ciudad de cada uno.
Se usaron estrellas, la lista completa de Bib Gourmand con ciudad (Wikipedia)
y Latin America's 50 Best 2025 (Forbes México). Sesgo conocido: estas fuentes
favorecen alta cocina y pocas ciudades (23 de 32 estados quedan sin ningún
lugar destacado), así que no sirven solas para decidir dónde NO hay buena comida.

## Prioridad por reconocimiento: por qué solo si la ruta pasa cerca (40 km)

Angel pidió que lo distinguido (estrella, Michelin, UNESCO) salga primero
"solo si la ruta pasa cerca". El sistema de sugerencias acepta lugares hasta
150 km de la carretera, así que al darles prioridad Guadalajara (a 145 km de
León → Monterrey) subió al primer lugar. Se agregó `RADIO_PRIORIDAD_KM = 40`
(medido con casos reales: Atlixco 30 km, Chocholá 36, Playa del Carmen 39,
Tulum 48). Los restaurantes del futuro solo se recomiendan si el usuario pide una
parada para comer (regla 7b del plan 04); en automático solo ciudades.

## Estrellas: cuántas salen por ruta y por qué hay un tope de 2

Medido con 40 rutas largas al azar entre ciudades grandes (250-1,500 km,
2026-09-19): 42 % no pasa cerca (≤ 40 km) de ningún lugar con estrella, 20 % pasa
por 1, 15 % por 2, 8 % por 3 y 15 % por 4 o más; o sea 38 % tiene 2 o más y 22 %
tiene 3 o más. Se concentran en pocos corredores: la **península de Yucatán**
(Mérida, Chocholá, Tixkokob, Puerto Morelos, Playa del Carmen), **Puebla +
Atlixco**, y Baja California. Podar "comida" NO cambia esto (las 21 estrellas
siguen igual). Con restaurantes el riesgo sube en ciudades con muchas estrellas
(CDMX tiene 11 restaurantes con estrella y 27 Bib Gourmand), por eso el tope de
2 al frente (y ninguna más en la primera vista) es genérico y se aplicará
también a restaurantes. **5 visibles** (decisión de Angel): 5 tarjetas en una
fila en pantallas anchas; en pantallas medianas (3 columnas) quedan 3 + 2.

## Por qué un viaje largo sale con ~9-10 tramos en automático

En automático cada tramo mide ~3 h de camino (`LAPSO_OBJETIVO_H = 3.0` en
`ai_service.py`), sin importar cuánto dure el viaje. Tijuana → Puerto Vallarta
(27.5 h, 2 días) da 9 tramos de 3.0 h; un viaje de 50 h daría 16. Los tramos que
cruzan la noche cuentan como un tramo más (ej. "20:22 – 09:20" es 3 h de camino y
el descanso). Angel no quiso cambiar esto por ahora. Si se quiere menos tramos en
viajes largos, se puede hacer que el largo del tramo crezca con la duración
(p. ej. 4-5 h para viajes de más de 20 h) o poner un tope al automático (p. ej.
8); mientras tanto el usuario puede elegir cuántos tramos (2 a 10, o hasta 30).

## Presupuesto y horas máximas: por qué burbujas y no `<datalist>`

La primera versión usó `<datalist>` (una lista nativa de opciones al
enfocar el campo) — funcional, pero Angel la vio "fea, sin chiste", una
lista plana sin ningún estilo (el navegador no permite personalizar el
aspecto de un `<datalist>` con CSS). Se reemplazó por una fila de
"burbujas" deslizable — el mismo componente visual que ya usan los chips
de "¿Qué buscas?" (`.chip` → aquí `.bubble`, mismo lenguaje visual) — con
una burbuja "Otro" al final que revela el `<input>` normal para un valor
exacto. Presupuesto: $1,000, $3,000, $5,000, $7,000, $9,000 (saltando de
2,000 en 2,000, pedido explícito — la primera versión iba de 1,000 en
1,000 hasta 20,000, pero eran demasiadas burbujas); horas
máximas de 1 a 16.

**Bug de layout al construirlo:** la fila de burbujas, al ser más ancha
que su tarjeta, en vez de scrollear internamente empujaba TODA la página
a desbordarse horizontalmente. Causa clásica de flexbox: un hijo flex
(`.bubble-picker__scroll`) por default no se encoge más allá de su
contenido (`min-width: auto`), así que aunque tenga `overflow-x: auto`,
el contenedor completo crece para dar cabida al contenido en vez de
recortarlo. Arreglo: `min-width: 0` en la cadena de contenedores flex
(`.bubble-picker`, `.bubble-picker__scroll`, y `.field` en general) — con
eso sí respetan su ancho asignado y el scroll queda contenido adentro.

## "Planear con IA": por qué la IA nunca elige el lugar, solo el propósito y la hora

La tentación fácil hubiera sido dejar que la IA "arme el itinerario" y
devuelva nombres de lugares directamente. No se hizo así a propósito:
cualquier proveedor puede alucinar un lugar que suene bien pero no exista
o esté mal ubicado — rompería la regla que ya seguía todo el proyecto
(nunca inventar datos geográficos). En vez de eso, la IA solo decide
*propósito de parada + a qué hora del viaje conviene* (`{proposito,
hora_objetivo}`), y un algoritmo 100% determinista
(`ai_service.asignar_paradas_a_objetivos`) es quien elige el destino real
de la tabla, verificado, sin excepción.

## Por qué la misma lógica de reparto sirve con IA y sin IA

Angel pidió explícitamente que el trabajo hecho para el chat "entrenara"
la app aunque nadie usara el botón de IA. La forma de lograrlo sin
aprendizaje automático real fue separar "quién decide los objetivos" de
"quién los convierte en lugares": la IA los decide conversando
(`llm_provider.generar_opciones_objetivos`), pero una fórmula fija
(`ai_service.generar_objetivos_automaticos`, basada solo en `horas_max` +
`hora_salida`) puede generar objetivos igual de válidos sin ningún
proveedor. Ambos caminos terminan en la misma función de asignación —
por eso agregar el campo "hora de salida" al formulario manual mejora las
sugerencias de cualquiera, use o no la IA.

## Por qué se agregó "hora de salida" y el filtro de hora del día

Sin saber la hora real del reloj en la que caería cada parada, un viaje
de 12h que sale a las 8am terminaría a las 8pm — de día — y no tiene
sentido sugerir "parar a dormir" a media tarde. `hora_salida` es opcional
(si no se da, todo funciona igual que antes, sin este filtro) pero cuando
está, `ai_service.filtrar_objetivos_por_hora_del_dia` reclasifica
objetivos de descanso que caen de día a una visita corta, y viceversa
prioriza descanso si ya es de noche — corre después de generar objetivos
(por IA o por fórmula) y antes de asignar lugares, así protege incluso si
la IA se equivocó en su propuesta.

## Diseño del chat: vidrio esmerilado + respuestas rápidas

El panel usa el elemento `<dialog>` nativo de HTML con
`backdrop-filter: blur()` en vez de una librería de modales — mismo
patrón ya usado para el modal de login, cero dependencias nuevas. Las
preguntas de la IA vienen con hasta 3 respuestas rápidas sugeridas (más
un botón fijo "Otro") en vez de forzar al usuario a escribir todo — pedido
explícito de Angel para que la experiencia no se sintiera tediosa, con un
límite duro de 5 preguntas antes de que la IA tenga que decidir con lo
que ya tiene.

## Geocoding: por qué se cambió el orden de resolución

**Problema:** al pedir una ruta de León a Los Cabos, el mapa quedaba en
blanco. Causa: `obtener_coordenadas()` solo reconocía un catálogo fijo de
18 ciudades (`CIUDADES_DEMO`, de los primeros días del MVP). Ni León ni
Los Cabos estaban ahí, así que ambos caían en la misma coordenada de
respaldo (centro de México) — la app pedía una "ruta" entre un punto y sí
mismo.

**Decisión:** en vez de ampliar el catálogo a mano, se conectó el cálculo
de ruta a la tabla `destinos` (que ya tiene 369 lugares reales,
geocodificados contra Nominatim) y, si el lugar no está ahí, se llama a
Nominatim en vivo. El catálogo de 18 ciudades se dejó como último
respaldo rápido, no se borró.

## Sugerencias: por qué el origen y el destino se tratan distinto

Antes se excluían destinos a menos de 5km en línea recta tanto del origen
como del destino. Angel pidió explícitamente que cerca del **destino** sí
se pudiera sugerir (tiene sentido: llegando a la ciudad, quieres
recomendaciones), pero cerca del **origen** no (es básicamente dentro de
la ciudad de la que sales). Se cambió a un criterio de tiempo real de
manejo (menos de 1 hora desde el origen = descartado) en vez de un radio
fijo en km, porque el tiempo real de carretera representa mejor "qué tan
lejos se siente" que la distancia en línea recta.

## Autocompletado: por qué se dejó de usar `<datalist>` nativo

El `<datalist>` del navegador solo acepta la sugerencia resaltada con
Enter — Tab no está bajo control de JavaScript en ese elemento — y hace
coincidencia literal de caracteres, sin quitar acentos. Por eso escribir
"leon" nunca encontraba "León". Se reemplazó por un dropdown propio en JS
donde si se controla el comportamiento de Tab y la comparación se hace
ignorando acentos y mayúsculas.

## Itinerario: por qué a veces se borraban las paradas y ya no

`calcularRuta()` reiniciaba `estado.itinerario` cada vez que se enviaba el
formulario, sin distinguir si era un viaje nuevo o solo un cambio de
filtros. Ahora solo se reinicia si el origen o destino cambiaron de
verdad; si el usuario solo ajusta los filtros de interés sobre el mismo
viaje, las paradas ya elegidas se conservan.

## Cuentas de usuario: por qué nombre + apellido + PIN y no correo

Angel decidió explícitamente que, por ser proyecto escolar, pedir correo
es de más. Nombre + apellido + PIN de 4 dígitos es suficiente para que
cada quien tenga sus propias rutas guardadas. Si en algún momento se
quiere lanzar la app al público, ahí sí valdría la pena agregar correo
(recuperación de contraseña, evitar duplicados de nombre, etc.) — pero
esa decisión se toma cuando llegue ese momento, no antes.

Consecuencias de esa decisión, aceptadas a propósito:
- Sin correo no hay "olvidé mi contraseña" self-service.
- Nombre + apellido debe ser único; dos personas con el mismo nombre
  exacto no pueden registrarse ambas (normalizado sin acentos/mayúsculas
  con la misma función `_normalizar()` que ya usa el proyecto para
  comparar nombres de destinos).
- El PIN sí se hashea (nunca texto plano) con `werkzeug.security`, que ya
  viene con Flask — no se agregó ninguna dependencia nueva para esto.

**Por qué solo "guardar" pide login y no todo el flujo:** calcular una
ruta y ver sugerencias no tiene nada que proteger — cualquiera puede
planear un viaje. Lo único que tiene dueño es lo que se guarda
permanentemente. Pedir login para "todo" hubiera sido fricción
innecesaria para solo probar la app.

**Por qué `<dialog>` nativo y no una librería de modales:** es un
elemento HTML estándar con `.showModal()`/`.close()` — cero JavaScript
extra para el overlay, cero dependencia nueva. Coherente con el resto del
proyecto (evitar librerías cuando la plataforma ya resuelve el problema).

## Destinos nuevos con IA: por qué es multi-proveedor y no solo Claude

Angel usa Claude, pero Roberto le va a hacer cambios al proyecto con
Codex y probablemente tenga una key distinta (OpenAI, Gemini, la que
sea). Diseñar esto para un solo proveedor hubiera obligado a todo el
equipo a usar la misma IA. Por eso se separó en dos archivos:

- `llm_provider.py` — la única parte que sabe de proveedores. Detecta
  automáticamente cuál está configurado según la variable de entorno
  presente, y expone una sola función (`completar_plantilla_destino`)
  que siempre regresa el mismo formato sin importar cuál se usó.
- `ia_destinos_service.py` — no sabe nada de Claude/OpenAI/Gemini, solo
  recibe el resultado ya parseado y decide qué hacer con él (geocodificar
  de verdad, buscar el estado, insertar en la tabla).

Así, si mañana aparece un cuarto proveedor, solo se agrega una función
más en `llm_provider.py` — el resto del sistema no se entera.

**Por qué las coordenadas nunca vienen de la IA directamente:** cualquier
proveedor puede "alucinar" una coordenada que suene razonable pero esté
mal. Se sigue la misma regla que ya regía para los 369 destinos curados
—nunca inventar datos geográficos— pidiéndole a la IA solo el *nombre*
correcto del lugar, y usando `geocodificar()` (Nominatim) para las
coordenadas de verdad. Si Nominatim no encuentra ese nombre, se descarta
todo el intento en vez de guardar algo a medias.

## La bitácora ahora sí se sube a GitHub

Al principio esta carpeta se creó como algo solo local (en `.gitignore`).
Angel decidió que en realidad sí vale la pena tenerla en GitHub, porque
Roberto le va a hacer cambios al proyecto usando Codex, y estos archivos
sirven como el contexto compartido para que cualquier IA (Claude o Codex)
entienda el proyecto antes de tocar código, sin importar quién la esté
usando. Por eso se agregaron `AGENTS.md` y `CLAUDE.md` en la raíz del
proyecto, que le indican a cualquier agente que lea esta carpeta primero
y la mantenga actualizada después de cada cambio.

## Efectos visuales: por qué reescritos a mano y no instalados

- Los componentes de `efectos visuales rare-ui` son React + Tailwind + `motion`.
  RutaMX no tiene React ni paso de compilación, y meterlos implicaría reestructurar
  el frontend. Se **portó cada efecto a JS/CSS puro** (resortes con `requestAnimationFrame`,
  transiciones CSS, canvas). Consecuencia: no hay librería `motion`.
- Regla: los efectos **envuelven** el flujo, no lo cambian. Cada uno se engancha con una
  llamada (`RutaEfectos.contador.set`, `.eliminar.montar`, `.orbe.montar`);
  el PIN, el gooey y la píldora se auto-montan sobre HTML que ya existía.
- Trampa del contador: al hacer `replaceChildren`, una columna que se saca y se vuelve a
  poner pierde su transición en curso; por eso las columnas se reutilizan por su
  distancia al final del número.
- Trampa del botón de borrar: con `flex-direction: row-reverse` el primer hijo del DOM
  queda a la derecha; el panel tiene `min-width: 0` para que no empuje el bote fuera.
- **Gooey con hover, no con clic:** al hacer clic la página salta a otra sección y el navbar
  (que no es fijo) sale de pantalla, así que la animación nunca se veía. Por eso se dispara al
  pasar el cursor (`mouseenter`), y al salir vuelve a la sección real (`real` vs `activo`).
- **Step-player eliminado** a pedido de Angel; no reintroducirlo.

## Tramos automáticos y "Paradas sugeridas": por qué se igualaron en el frontend

- Son dos cálculos distintos en el backend (distancia vs duración). En vez de tocar
  `lapsos_de_la_ruta` (que también usan el chat de IA y los tests), el frontend pide
  `tramos = paradas_estimadas` cuando está en automático. Si algún día se quiere una sola
  fuente de verdad, la opción es hacer que `routes.py` use `ruta["paradas_estimadas"]` como
  valor por defecto de `tramos`.
- Trampa de CSS: animar `border-radius` desde `999px` a un valor chico parece retrasado, porque
  el navegador recorta el radio a media altura y la esquina no cambia hasta que el número baja
  de ese tope. Partir de un radio real (media altura) evita el "salto".

## Recomendaciones: el filtro de intereses es principal y las 5 primeras van por franjas de horas

- **Regla de Angel (2026-09-19):** lo marcado en "¿Qué buscas?" es el filtro principal y se respeta
  por encima de todo (estrellas, propósito por hora, cercanía). Solo lo pisa un tramo que el usuario
  personalizó a mano (comer / dormir / turismo). Implementado en `ai_service.coincide_intereses`.
- **"Pueblos mágicos" es el `tipo`, no un interés guardado.** Ningún destino tiene ese valor en
  `intereses` (solo naturaleza, playas, comida, descanso, cultura). Cualquier código nuevo que
  compare intereses debe pasar por `_puntos_interes` / `coincide_intereses` (y `_coincide_proposito`).
- **La regla vieja de "máximo 2 estrellas al frente" se abandonó:** ahora la estrella gana **dentro de
  cada franja de horas**; en una ruta con estrellas en las 5 franjas pueden salir 5 estrellas y es a
  propósito (pedido de Angel: "siempre prioridad a lo que tenga estrella").
- **Por qué el frontend repone las recomendadas sin volver al servidor:** cada llamada a
  `/api/sugerencias` recalcula la ruta con OSRM (segundos). Por eso el servidor manda 40 lugares con
  `franja` y `rango_franja`, y `main.js` (`recomendadas()`) elige la mejor de cada franja entre los que
  quedan. Si algún día se quiere una sola fuente de verdad, mover `recomendadas()` al backend.
- Los estados de carga (cuadrícula del mapa, orbe) y "Ver más / Ver menos" usan animaciones en JS
  puro; ningún cambio de hoy tocó el flujo de guardado, PDF, login ni gasto.

## Rediseño: se remapean los tokens en vez de renombrarlos

Al aplicar el diseño de Stitch se dejaron los nombres `--color-crema`,
`--color-terracota`, `--color-verde-oscuro`, etc. y solo cambió su valor. Motivo:
`efectos.css` y los 8 efectos protegidos (bitácora 05) leen esas variables; renombrar
habría obligado a tocar cada efecto. Se sumó `--color-terracota-texto` (`#9f3c16`)
porque el terracota del diseño (`#c85a32`) sobre lino da ~4.2:1, por debajo de AA en
texto pequeño; se usa solo en kickers y etiquetas chicas. Los botones y el resto siguen
con el terracota original del diseño.

## Rediseño: por qué el fondo animado es "barato" y por qué el aro de las ventanas no usa máscara

- **Fondo de líneas (bloque 10 de `efectos.css`):** primero se intentó reinterpretarlo (capas que
  derivan con `transform`, colores por capa, entrada propia) y Angel pidió volver al código original
  del componente, solo con más velocidad y colores de la paleta. **Versión final = el original** (ver
  bitácora 01). Lo que costó, para no repetirlo: animar `pathLength`/`pathOffset` en 72 curvas obliga a
  repintar el SVG en cada cuadro, y con `opacity` por curva (72 capas de composición) el navegador
  integrado dejaba de pintar tarjetas y ventanas. Se resolvió sin cambiar lo que se ve: la opacidad se
  anima como `stroke-opacity = strokeOpacity × [0.3, 0.6, 0.3]` (idéntico, porque la curva solo tiene
  trazo) y el color se anima con `@keyframes fondo-tono` sobre `stroke`. La animación se pausa mientras
  haya un `<dialog>` abierto. No volver a usar `opacity` por curva ni animar más de lo que hace el original. **Regla de Angel: del efecto solo se cambian el color y la velocidad; no agregar entradas, capas ni otro comportamiento.** Se probó una entrada "dibujada desde la izquierda" y se quitó: las curvas entraban juntas, rápidas y encimadas.
- **Luz de las ventanas (bloque 9):** en tarjetas el aro es un `::before` con máscara; en un
  `<dialog>` esa máscara hacía que el navegador dejara de pintar el fondo de la ventana. Por
  eso las ventanas dibujan el aro con capas de `background` y un borde transparente, y el
  chat translúcido lleva solo el resplandor interior (el aro se vería a través del cristal).
- **Al verificar en el navegador integrado:** después de abrir/cerrar ventanas con JS o de
  `scrollIntoView`, el panel a veces no repinta y las capturas salen en blanco o a medias
  hasta que llega un evento real de mouse o scroll. No es un bug de la app: repetir la
  captura tras un `hover` o un scroll.

## Iconos SVG: no deben capturar el mouse (bug del tooltip de la estrella)

Al cambiar los emojis por iconos SVG con `<use>`, el `title` de la estrella de gastronomía
("Guía Michelin México 2026…") dejó de mostrarse: el cursor caía sobre el `<use>` interno del SVG
y Chrome no propaga el tooltip desde ahí hasta el elemento padre que tiene el `title`. Con el
emoji ("★") no pasaba porque era texto. Arreglo: `.icono, .icono * { pointer-events: none }` en
`styles.css`, así el evento llega al `<span>` con el `title` (estrella de la tarjeta, nota amarilla
y estrella del nombre de la parada). Regla: si un icono va dentro de algo con `title`, no debe
recibir eventos de mouse. El tooltip nativo no sale en capturas del navegador integrado; se
verificó con `elementFromPoint` sobre la estrella y la nota.

## Patrón de trabajo con Angel (para quien retome esto, incluido Roberto)

- Verificar todo en la app corriendo de verdad (navegador), no solo con
  tests automatizados — varios bugs reales solo se detectaron probando en
  vivo, no con `pytest`.
- No inventar datos: coordenadas y población siempre verificadas contra
  fuentes reales (Nominatim para coordenadas).
- Explicar el "por qué" de un bug antes o junto con el arreglo, no solo
  aplicar el fix.
- Para cambios grandes o con varios pasos, planear primero y confirmar
  antes de tocar código.
