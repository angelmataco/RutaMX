---
tags: [proyecto, rutamx, problemas]
---
# Problemas resueltos

Parte de [[RutaMX]]. Sale de `bitacora_proyecto/03_DECISIONES_Y_NOTAS.md` del proyecto y del historial de commits.

## 1. El mapa quedaba en blanco al pedir León → Los Cabos
**Causa:** `obtener_coordenadas()` solo conocía un catálogo fijo de 18 ciudades. León y Los Cabos caían en la misma coordenada de respaldo (centro de México) y la app pedía una ruta de un punto a sí mismo.
**Solución:** resolver primero contra la tabla `destinos` (369 lugares geocodificados), luego Nominatim en vivo, y dejar el catálogo de 18 como último respaldo. Ver [[RutaMX - Arquitectura]].

## 2. Las paradas se borraban al cambiar filtros
**Causa:** `calcularRuta()` reiniciaba el itinerario en cada envío del formulario.
**Solución:** solo se reinicia si cambió el origen o el destino.

## 3. El autocompletado no encontraba "León" al escribir "leon"
**Causa:** el `<datalist>` nativo compara caracteres literales y solo acepta la sugerencia con Enter.
**Solución:** dropdown propio en JS que ignora acentos y mayúsculas y controla la tecla Tab.

## 4. El selector de hora tapaba los números
**Causa:** el recuadro resaltado tenía `position: absolute` y las columnas de números no tenían posición, así que se pintaba encima aunque fuera primero en el HTML.
**Solución:** `position: relative` y `z-index: 1` en las columnas, `z-index: 0` en el recuadro. Lección: al mezclar elementos posicionados y normales, el orden del DOM no fija el orden de pintado.

## 5. Las burbujas de presupuesto desbordaban toda la página
**Causa:** un hijo flex no se encoge más allá de su contenido (`min-width: auto`).
**Solución:** `min-width: 0` en la cadena de contenedores flex.

## 6. El tooltip de la estrella de gastronomía desapareció
**Causa:** al cambiar emojis por iconos SVG con `<use>`, el cursor caía en el SVG interno y Chrome no propaga el tooltip al padre con `title`.
**Solución:** `.icono, .icono * { pointer-events: none }`.

## 7. El botón "Iniciar sesión" seguía visible con sesión iniciada
**Causa:** `.btn` define `display: inline-flex`, que le gana al atributo `hidden`.
**Solución:** `.navbar__auth [hidden] { display: none; }`.

## 8. Ojos aplastados en el avatar de la ventana de perfil
**Causa:** `gaze()` mide la forma de la cara al crearse y el monito nacía con la ventana en `display: none`, así que midió cero.
**Solución:** crear el `gaze` al abrir la ventana y destruirlo al cerrarla. Cualquier avatar de Blobatar con gaze debe crearse visible.

## 9. Guadalajara aparecía como primera sugerencia de León → Monterrey
**Causa:** al dar prioridad a lo distinguido, un lugar a 145 km de la carretera (dentro del límite de 150 km) subió al primer lugar.
**Solución:** `RADIO_PRIORIDAD_KM = 40`, medido con casos reales.

## 10. El fondo animado hacía que el navegador dejara de pintar tarjetas
**Causa:** `opacity` por curva en 72 curvas creaba 72 capas de composición, y animar `pathLength` obligaba a repintar el SVG en cada cuadro.
**Solución:** animar `stroke-opacity` y `stroke` con `@keyframes`, y pausar la animación con un `<dialog>` abierto.

## 11. Las ventanas dejaban de pintar su fondo
**Causa:** el aro de luz con máscara (`::before`) dentro de un `<dialog>`.
**Solución:** dibujar el aro con capas de `background` y borde transparente.

## 12. El navbar compacto hacía saltar el contenido
**Causa:** con `position: sticky` el navbar cambia de altura dentro del flujo.
**Solución:** `fixed` más un espaciador que guarda la altura expandida, con histéresis de 48/16 px para que no parpadee.

## 13. El tope entre secciones devolvía la página al mismo punto
**Causa:** `scroll-snap-type: y proximity` tiene una zona de atracción muy grande.
**Solución:** `tope.js`, un imán corto con constantes ajustables.

## 14. El resalte del menú de la píldora salía 8 px más arriba
**Causa:** el resalte se colocaba con el `offsetTop` del `<li>` pero estaba dentro de un contenedor con 8 px de padding.
**Solución:** `top: 8px`, igual al padding.

## 15. Al calcular la ruta la pantalla se quedaba en una animación
**Causa:** el scroll apuntaba a un contenedor cuyo primer hijo era el orbe "Calculando tu ruta…".
**Solución:** quitar el orbe y bajar directo a `#ruta`.

## 16. Efecto gooey que nunca se veía
**Causa:** disparado con clic, la página saltaba de sección y el navbar salía de pantalla.
**Solución:** dispararlo con `mouseenter`.

## 17. Criterios de aceptación que no se podían probar
**Causa:** en el documento de requerimientos v1.0 varios criterios usaban frases sin resultado observable («manejar de forma controlada», «procesar la solicitud»), algunos probaban el inicio de sesión (que ya existe) o sugerían versionado de rutas (fuera del alcance), y siete RF no tenían ningún criterio. RF-22 también contradecía a CA-11.4.
**Solución:** reescribirlos con el resultado exacto esperado, limitarlos al comportamiento de RutaMx, agregar CA-12.5 y alinear RF-22. La cobertura se valida con un script. Detalle en [[RutaMX]].

## [V2] 18. Una excepción que no era de SQLAlchemy salía sin traducir
**Síntoma:** un `RuntimeError` dentro de `crear_ruta`, `obtener_ruta` o `listar_rutas_de_usuario` llegaba a quien llamaba sin ser un `ErrorRepositorio`, contra el contrato "todo fallo es `ErrorRepositorio`".
**Causa:** el módulo solo capturaba `SQLAlchemyError` al traducir.
**Solución:** capturar cualquier excepción, traducirla y conservar la causa con `from`. Lo señaló la revisión de [[Codex CLI|Codex]].
**Prueba:** una prueba que fuerza un `RuntimeError` en las tres operaciones y comprueba el tipo, el mensaje sin detalle interno y la causa conservada.

## [V2] 19. Dos pruebas no probaban lo que decían
**Síntoma:** la de rollback pasaba aunque el módulo nunca llamara a `rollback` (cerrar la sesión también revierte), y la de lectura fallaba al abrir la sesión, no al consultar.
**Solución:** un espía confirma que se llamó `rollback`, y el fallo de lectura se fuerza en `execute` comprobando que las demás rutas quedan intactas.
**Prueba:** se quitó el `rollback` del código a propósito y la prueba falló; después se restauró.

## [V2] 20. El Postgres temporal no arrancaba
**Causa:** la ruta del socket Unix, dentro de la carpeta temporal, superaba el máximo de 103 bytes.
**Solución:** pasar `-k` con un directorio corto para el socket. La receta quedó documentada y se reprodujo desde cero en el proyecto con las pruebas aprobadas (cifra en [[RutaMX]]).

## [V2] 21. Un relevo viejo daba por hechas cosas que el repo no tenía
**Síntoma:** al armar el inventario del plan de incrementos escribí que M-09 tenía seis operaciones y una cifra de pruebas inflada, y un commit que no existe en el repo.
**Causa:** copié cifras de un resumen de sesión anterior sin comprobarlas.
**Solución:** la revisión de [[Codex CLI|Codex]] lo detectó; se contó con `grep` en el repo (tres operaciones) y se corrigió el inventario.
**Prueba:** el plan cita solo lo que se comprobó con comandos reproducibles; lo demás va como «sin verificar».

## [V2] 22. El orquestador perdía los datos extraídos si fallaba la generación
**Síntoma:** en Planear con IA, si la generación de la ruta fallaba, se perdían los datos que la conversación acababa de extraer y había que volver a escribirlos.
**Causa:** [[RutaMX - Arquitectura|M-04]] guardaba los datos nuevos junto con la ruta aceptada y los descartaba al fallar.
**Solución:** se conservan por separado de la ruta aceptada y queda un intento por generar; un mensaje de reintento sin datos nuevos vuelve a intentarlo. Lo señaló la revisión de [[Codex CLI|Codex]].
**Prueba:** pruebas del orquestador que fuerzan el fallo y comprueban que los datos siguen y que el reintento funciona.

## [V2] 23. Tras fallar una confirmación, el siguiente mensaje borraba las paradas
**Síntoma:** en Planear con IA, si fallaba la confirmación de una modificación (por ejemplo agregar una parada), el siguiente mensaje regeneraba la ruta y se perdían las paradas ya agregadas.
**Causa:** [[RutaMX - Arquitectura|M-04]] trataba toda propuesta pendiente como una ruta nueva.
**Solución:** las propuestas pendientes guardan su origen (crear o modificar) y un fallo al confirmar una modificación ya no activa la regeneración. Lo señaló la revisión de [[Codex CLI|Codex]].
**Prueba:** pruebas del orquestador que fuerzan el fallo.

## [V2] 24. Las rutas guardadas por v2 rompían «Mis rutas» de v1
**Síntoma:** al abrir en v1 una ruta guardada por v2 faltaban datos, y guardar de nuevo sin nombre borraba el nombre personalizado.
**Causa:** v1 espera distancia, tiempo y los nombres de origen y destino en `resumen`, y v2 no los escribía; el re-guardado reemplazaba el nombre.
**Solución:** v2 escribe los nombres de origen y destino, conserva el nombre al re-guardar y, con autorización de Angel, v1 redirige a `/v2/rutas` si el resumen trae `rutamx_v2` (6 líneas).
**Prueba:** pruebas del guardado. La redirección solo se comprobó con `node --check`; el clic real está sin verificar (2026-11-12).

## [V2] 25. Abrir una ruta guardada se rechazaba tras la primera confirmación
**Síntoma:** abrir una ruta que requería dos confirmaciones de la regla D-03 fallaba tras resolver la primera.
**Causa:** la apertura resolvía una sola confirmación.
**Solución:** se resuelven hasta dos, porque el usuario ya las confirmó al crear la ruta; si algo falla, no se reemplaza la conversación vigente.
**Prueba:** pruebas de las rutas guardadas con las dos confirmaciones.

## [V2] 26. «Reiniciar filtros» buscaba con los valores anteriores
**Síntoma:** en Descubrir, el botón de reinicio lanzaba la búsqueda antes de que los campos se restablecieran.
**Causa:** la búsqueda se programaba con un microtask, que corre antes del restablecimiento del formulario.
**Solución:** `setTimeout`; además singular en «1 ruta encontrada» y una espera de 250 ms al escribir en el buscador. Lo señaló la revisión de [[Claude Code]].
**Prueba:** ninguna automática: el JavaScript no se ha ejecutado en un navegador, y la prueba de render de la plantilla quedó pendiente (sin verificar (2026-11-12)).

## [V2] 27. El script de publicar dejaba abierto un contexto de Flask
**Síntoma:** cada uso del script dejaba un contexto de la aplicación sin liberar.
**Causa:** el contexto envolvía toda la sesión en vez de solo la obtención de la conexión.
**Solución:** el contexto se usa solo para obtener la conexión y se libera antes de seguir. Lo señaló la revisión de [[Codex CLI|Codex]].
**Prueba:** tres pruebas de que no queda contexto abierto.

## [V2] 28. Pruebas de integración fallaban con PostgreSQL real
**Síntoma:** al correr por primera vez las pruebas de integración contra un PostgreSQL local desechable, varias fallaban aunque con sesión falsa todo estaba en verde (conteos en [[RutaMX]]).
**Causa:** eran defectos de las pruebas, no de la app: un INSERT directo sin `intereses` ni `resumen` (PostgreSQL rechaza el NOT NULL; los defaults del ORM no se aplican al SQL directo); las pruebas de migración suponían un esquema anterior que otras pruebas ya habían modificado; y las de fuga de contexto de [[Flask]] comprobaban `has_app_context()`, que con el contexto de sesión de la integración es verdadero antes y después.
**Solución:** el INSERT incluye esos campos; un fixture restaura el esquema anterior (solo en una base local de prueba); y la prueba de fuga compara la identidad del contexto activo y cierra el que se haya fugado. Lo señaló la revisión de [[Codex CLI|Codex]]: comparar solo `has_app_context()` antes y después no detecta una fuga cuando ya hay contexto externo.
**Prueba:** un script defectuoso que deja su contexto abierto hace fallar las tres pruebas de fuga con y sin contexto externo. Probado en simulación con PostgreSQL local (2026-11-17); un caso de integración sigue dependiendo de correr primero en una base nueva.

## Pendiente conocido
- Supabase responde `tenant/user not found` (proyecto pausado o URL cambiada), así que las pruebas que usan la base fallan; las de v1 hablan con la base real en vez de una aislada. Resultado histórico del 2026-10-29, sin resolver entonces; no se consultó Supabase en esta revisión (2026-11-13).
- `test_registrar_usuario_duplicado_por_acentos_y_mayusculas` falla porque usa el nombre de una cuenta real ("Ángel Mata"); es un fallo del test, no de la app.
- Las pruebas de M-09 usan una base aislada, pero la regresión de v1 sigue sin ella: sin verificar (2026-11-03).
- Con el servidor abierto, la suite completa puede dar `EMAXCONNSESSION` (límite de 15 conexiones de Supabase) en 1 o 2 tests; solos pasan.
- La migración del catálogo no se ha ejecutado en Supabase. El SQL del catálogo, del script de publicar y de `actualizar_ruta` se probó contra un PostgreSQL local desechable (2026-11-17), sin verificar la concurrencia del `FOR UPDATE` ni la base real.
- Las capturas del navegador integrado a veces salen en blanco tras abrir ventanas con JS; no es un bug de la app, se repite la captura tras un `hover` o scroll.

Las decisiones detrás de varios de estos arreglos están en [[RutaMX - Decisiones]].
