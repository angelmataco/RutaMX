# Decisiones y notas — RutaMX

Última actualización: 2026-09-19

El "por qué" detrás de decisiones que no son obvias con solo leer el
código. Se va agregando conforme pasa.

## Selector de hora tipo rueda: por qué construirlo a mano en vez de usar `<input type="time">`

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
