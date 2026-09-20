# Efectos visuales protegidos (rare-ui) — NO SE TOCAN

Última actualización: 2026-09-20

**Regla de Angel:** el rediseño de toda la interfaz (base de Stitch, 2026-09-20) ya se
hizo respetando estos efectos, y cualquier rediseño futuro también debe respetarlos. Los efectos de este documento, sacados de la carpeta
`efectos visuales rare-ui`, **se quedan siempre**. El rediseño puede cambiar
colores, tipografías, espaciados, layout y estilos de todo lo demás, pero **no
puede quitar, reemplazar, simplificar ni desactivar estos efectos**.

Aplica a cualquier IA (Claude, Codex) y a cualquier skill que toque el frontend.
Si una decisión de diseño choca con un efecto de aquí, **se conserva el efecto** y
se adapta el diseño alrededor; si de verdad hay que cambiarlo, se le pregunta a
Angel antes.

## Qué se puede y qué no

**Se puede cambiar (apariencia):** colores (los efectos usan las variables
`--color-*` de `styles.css`, así que un cambio de paleta los recolorea solo),
tamaños, tipografía, bordes, sombras, posición general en la página.

**No se puede:**
- Borrar o reemplazar `app/static/js/efectos/` ni `app/static/css/efectos.css`.
- Quitar sus `<script>` / `<link>` de `base.html` (ni cambiar su orden: `secciones.js`
  antes que `gooey.js` y `pildora.js`; todos antes de `main.js`).
- Renombrar o quitar los ganchos HTML de la tabla de abajo (ids, atributos `data-*`,
  clases). Los scripts los buscan por nombre.
- Sustituir el efecto por otra cosa "equivalente" (un `confirm()` en vez del botón de
  borrar, cuatro `<input>` normales en vez del PIN, etc.).
- Quitar el soporte de `prefers-reduced-motion` (bloque al final de `efectos.css`).

## Los 8 efectos de rare-ui

Origen: componentes de `efectos visuales rare-ui` (React/Tailwind/Motion), **reescritos
a JS/CSS puro** porque RutaMX no tiene React ni build. La carpeta original no se modificó.

| # | Efecto (rare-ui) | Archivo | Qué hace | Ganchos que NO se pueden quitar |
|---|---|---|---|---|
| 1 | animated-counter | `contador.js` | Los números ruedan dígito por dígito (odómetro). | `[data-stat="distancia\|tiempo\|costo\|paradas"]`, `[data-aventura-paradas]`, `[data-aventura-distancia]`; `main.js` los escribe con `RutaEfectos.contador.set(...)` |
| 2 | delete-button | `eliminar.js` | Borrar parada con confirmación ✓/✕ en el mismo botón. | `[data-eliminar-parada]` dentro de `#tpl-parada-itinerario`; `main.js` lo monta con `RutaEfectos.eliminar.montar(...)` |
| 3 | otp-input | `pin.js` | PIN en 4 casillas (a todo lo ancho de la ventana) con dígito rodando, cursor deslizante y sacudida al error. | `.modal-auth` con `input[name="pin"]` (login y registro) y `.empty-state` de error en cada formulario |
| 4 | gooey-nav | `gooey.js` | Menú del navbar; la opción se separa con un cuello elástico al pasar el cursor por encima. | `<nav class="navbar__links">` con enlaces `<a href="#ruta">`, `#descubre`, `#itinerario` |
| 5 | scroll-progress | `pildora.js` + `secciones.js` | Píldora flotante (esquina inferior derecha) con anillo de progreso y menú de secciones. | Ids de sección `#inicio` (hero), `#ruta`, `#descubre`, `#itinerario`; contenedor `[data-resultados]` |
| 6 | duration-picker | `duracion.js` | Selector de **Hora de salida**: píldora `[HH Hr.][MM Min.][✎]` que se separa con resorte al editar; al tocar hora o minutos se abre una **ruedita** para deslizar (no se escribe). | `[data-hora-salida]` (contenedor) y `[data-time-hidden]` (`<input type="hidden" name="hora_salida">`) en `hero.html`; `main.js` usa `RutaEfectos.horaSalida.poner(...)` |
| 8 | grid-reveal | `gridreveal.js` | Cuadrícula que se parte mientras carga la ruta y se disuelve en ola sobre el **mapa**. | `[data-map]` (`#mapa`) y el flujo `empezarCarga`/`terminarCarga` de `calcularRuta` en `main.js` |
| 7 | matrix-orb | `orbe.js` | Orbe de puntos animado como indicador de "pensando". | `[data-sugerencias]` (carga de sugerencias) y `[data-chat-transcript]` del chat de IA (`mostrarPensando` en `planificador_ia.js`) |

**Se sumaron dos efectos más, pedidos por Angel (también protegidos):**

| # | Efecto | Archivo | Qué hace | Ganchos que NO se pueden quitar |
|---|---|---|---|---|
| 9 | spotlight-card | `spotlight.js` + bloque 9 de `efectos.css` | Aro y resplandor que siguen al cursor en tarjetas y ventanas, en terracota→ocre. | La lista `SUPERFICIES` de `spotlight.js` debe coincidir con el selector `:is(...)` del bloque 9 (`.card`, `.ruta-burbuja`, `.modal-auth`, `.modal-ajustes`, `.modal-rutas`, `.modal-ia`). Toda ventana nueva que se sume debe agregarse a ambas listas. |
| 10 | background-paths | `fondo.js` + bloque 10 de `efectos.css` | Líneas que fluyen detrás de toda la página, con los colores de la app. | El script crea `.fondo-rutas` solo, con 2 SVG de 36 curvas cada uno que animan `pathLength`, `pathOffset` y `stroke-opacity` como el original. Las secciones (`.hero`, `.section--*`) deben seguir transparentes o translúcidas para que se vea. No usar `opacity` por curva ni animar `transform` de capas: ver bitácora 03. |

Además, los **iconos a medida** (sprite en `partials/iconos_sprite.html`) son parte del
diseño: nada de emojis en la app. Los dibujos de `eliminar.js` y `duracion.js` conservan
sus clases (`del__tapa`, `del__trazo`, `dur__pluma`, `dur__palomita`).

Si el rediseño cambia la estructura de una sección, hay que **mover** el gancho a la
estructura nueva, no eliminarlo.

## Detalles de cada efecto que hay que respetar

- **Contador:** rueda **lento a propósito** (1.6 s + cascada por dígito, pedido de Angel): no acelerarlo. Cada valor se pinta con `RutaEfectos.contador.set(elemento, texto)`, nunca
  con `textContent` directo. El texto real queda en un `.contador__sr` para lectores de pantalla.
- **Borrar:** se borra por identidad del objeto (no por índice) tras 550 ms de animación.
  Antes de este efecto borraba al primer clic; confirmar es ahora el comportamiento correcto.
- **PIN:** el `<input name="pin">` original se conserva (oculto) porque `auth.js` lo lee con
  `FormData`. No usar `type="password"` con otro nombre ni sacarlo del `<form>`.
- **Gooey:** la animación se ve al **pasar el cursor** (al salir vuelve a la sección real
  de la página); el clic también la dispara. Pedido explícito de Angel: no depender del clic,
  porque al hacer clic la página salta de sección y la animación no se alcanza a ver. Las variables `--gooey-barra` y `--gooey-activo` definen sus colores.
  En ≤640 px el menú pasa a su propia fila (evita desborde horizontal).
- **Píldora:** vive abajo a la **derecha** y es grande (pedido de Angel); crece hacia
  arriba/izquierda al abrirse. Solo aparece con ≥ 2 secciones visibles (o sea, con ruta calculada). Si se
  agrega otra sección a la página, hay que sumarla a la lista de `secciones.js`.
- **Hora de salida:** la ruedita de minutos va de **10 en 10** (00 a 50; pedido de Angel), no de uno en uno. El fondo es el **naranja de la app** (pedido de Angel; no volver al verde). Guarda `HH:MM` (24 h) en el input oculto y dispara `change` en él (así
  `main.js` recalcula gasto y sugerencias). No volver a la rueda anterior ni a un `<input type="time">`.
  Enter debe guardar sin enviar el formulario de la ruta. **No se escribe a mano** (pedido de Angel):
  la hora y los minutos se eligen con la ruedita (`.dur__rueda`) o con las flechas ↑↓.
- **Botones de sesión del navbar:** resalte gooey al pasar el cursor (regla `.navbar__auth .btn:hover`
  en `efectos.css`); se quedan en su posición, solo cambian de forma/color con rebote. Es parte del efecto gooey.
- **Grid reveal:** cubre el mapa (~4.5 s estimados) desde que se pulsa "Planea mi ruta" hasta que llega la ruta,
  y **la página no debe congelarse** mientras: los resultados se abren y se baja al instante (pedido de Angel).
- **Botones de sesión:** el radio base es `18px`, no `999px` (ver bug corregido en la bitácora 01).
- **Orbe:** también se muestra como "Calculando tu ruta…" arriba de los resultados. Tamaño grande a propósito (120 px en sugerencias, 92 px en el chat de IA): es el
  efecto favorito de Angel, no se achica. Se apaga solo si su contenedor sale del DOM; usa `--color-terracota`.

## Cómo comprobar que un rediseño no los rompió

1. Levantar la app y calcular una ruta (ej. Ciudad de México → Oaxaca de Juárez).
2. **Contador:** los 4 números del resumen ruedan al calcular y al agregar paradas.
3. **Borrar:** agregar una parada, tocar el bote → tapa abierta con ✓ y ✕; ✓ la elimina.
4. **PIN:** "Iniciar sesión" → 4 casillas del ancho del campo; escribir dígitos los hace rodar; un PIN
   incorrecto sacude las casillas.
5. **Gooey:** al pasar el cursor por una opción se separa del resto; sin cursor, marca la sección actual.
6. **Píldora:** aparece abajo a la derecha tras calcular; al tocarla se despliega y salta.
7. **Hora de salida:** tocar el lápiz separa las piezas y abre la ruedita de horas; deslizar, tocar los
   minutos (otra ruedita) y la palomita deja `HH:MM`.
8. **Botón Iniciar sesión:** al pasar el cursor se pinta de terracota con rebote.
9. **Orbe:** se ve mientras cargan las sugerencias y la ruta.
10. **Grid reveal:** al pulsar "Planea mi ruta" la página baja de inmediato y el mapa muestra la cuadrícula
    hasta que llega la ruta; se puede deslizar mientras carga.
11. Consola del navegador sin errores y sin scroll horizontal en 375 px.
12. `pytest -q` (123 tests) sigue pasando.
13. **Luz de tarjetas:** al mover el cursor cerca del borde de una tarjeta o ventana se ilumina el aro; con una ventana abierta solo brilla la ventana, no las tarjetas de atrás.
14. **Fondo:** líneas que crecen y se desplazan como el original, cambiando entre los tonos de la paleta; con una ventana abierta se pausan.
15. Ninguna tarjeta ni ventana pierde su fondo blanco (si pasa, revisar el fondo animado y la máscara del aro).

**Step-player: quitado a propósito (2026-09-19).** A Angel no le gustó; se eliminó
(`stepplayer.js`, su CSS y sus enganchos en `main.js`). No volver a agregarlo.

Historial de cómo se hicieron y por qué así: ver la sección "Efectos visuales" en
`01_LO_QUE_YA_ESTA_HECHO.md` y `03_DECISIONES_Y_NOTAS.md`.
