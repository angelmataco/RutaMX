// Avatar de la sesión con Blobatar (blobatar.dev). El mismo nombre da siempre el mismo
// monito, así que no se guarda nada. Comportamiento:
//  - Siempre respira, parpadea y mira de reojo (animación "always", poquito).
//  - Con el mouse cerca los ojos lo siguen.
//  - Al picarle se enoja (expresión "mad": se pone rojo) y vuelve a la normalidad.
//  - Al picarle al del navbar se enoja y, cuando termina, se queda quieto mientras la
//    ventana de perfil esté abierta.
//  - Esa ventana tiene su propio monito: sigue al mouse todo el tiempo (con los ojos más
//    exagerados) y se enoja con cada clic, uno a la vez, hasta que la ventana se cierre.
// Los módulos están en static/js/vendor/ (copias de dist/internal.js, gaze.js y
// expression.js de blobatar 2.7.0). `internal` es la API de sus adaptadores: el paquete
// no trae una función animada lista para JS puro.

const RutaAvatar = (() => {
  const ENOJO_MS = 1400; // cuánto dura enojado antes de volver a la normalidad
  const CERCA_PX = 220; // a esta distancia del avatar los ojos empiezan a seguir el mouse

  let carga = null;
  let modulos = null;
  let texto = "";
  let svgBarra = null; // avatar del navbar
  let svgMenu = null; // avatar dentro de la ventana de perfil
  let gazeBarra = null;
  let gazeMenu = null; // solo existe con la ventana abierta (ver menu())
  let objetivo = null; // el <svg> que sigue al mouse ahora (o null)
  let menuAbierto = false;
  let punto = null; // último punto del puntero
  const aplicadas = new WeakMap(); // variables CSS que puso este archivo en cada <svg>
  const enojos = new WeakMap(); // <svg> -> temporizador; existe mientras esté enojado

  function cargar(base) {
    if (!carga) {
      carga = Promise.all([
        import(`${base}blobatar.js`),
        import(`${base}blobatar-expresiones.js`),
        import(`${base}blobatar-gaze.js`),
      ])
        .then(([interno, expresiones, gaze]) => (modulos = { interno, expresiones, gaze }))
        .catch((err) => {
          console.error("No se pudo cargar Blobatar:", err);
          return null;
        });
    }
    return carga;
  }

  function partes(expresion) {
    return modulos.interno._parts(texto, { animate: "always", expression: expresion });
  }

  function marcado(p) {
    const estilo = Object.entries(p.vars).map(([k, v]) => `${k}:${v}`).join(";");
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" aria-hidden="true" style="${estilo}"><g class="${p.cls}">${p.inner}</g></svg>`;
  }

  // Cambia la pose sin reconstruir el DOM: así las variables registradas de motion.css
  // hacen la transición (y las animaciones no se reinician).
  function aplicar(svg, p) {
    const previas = aplicadas.get(svg) || [];
    previas.filter((k) => !(k in p.vars)).forEach((k) => svg.style.removeProperty(k));
    Object.entries(p.vars).forEach(([k, v]) => svg.style.setProperty(k, v));
    aplicadas.set(svg, Object.keys(p.vars));
    svg.querySelector(".mo-root").setAttribute("class", p.cls);
  }

  // Se enoja ENOJO_MS y vuelve a lo normal. Si ya estaba enojado no hace nada. Devuelve
  // una promesa que se cumple (true) al terminar, o nunca si se le corta con calmar().
  function enojar(svg) {
    if (!modulos || !svg || enojos.has(svg)) return Promise.resolve(false);
    svg.getBoundingClientRect(); // si estaba oculto, que ya tenga estilo para hacer la transición
    aplicar(svg, partes(modulos.expresiones.mad));
    return new Promise((terminar) => {
      enojos.set(
        svg,
        setTimeout(() => {
          aplicar(svg, partes());
          enojos.delete(svg);
          terminar(true);
        }, ENOJO_MS)
      );
    });
  }

  function calmar(svg) {
    if (!svg) return;
    clearTimeout(enojos.get(svg));
    enojos.delete(svg);
    aplicar(svg, partes());
  }

  function seguir(svg) {
    if (svg === objetivo) return;
    objetivo = svg;
    if (gazeBarra) gazeBarra.lookAt(svg === svgBarra ? "pointer" : null);
    if (gazeMenu) gazeMenu.lookAt(svg === svgMenu ? "pointer" : null);
  }

  // Quién sigue al mouse: con la ventana abierta, el de la ventana (siempre); si no, el
  // del navbar solo cuando el mouse está cerca.
  function evaluar() {
    if (!svgBarra) return;
    if (menuAbierto) return seguir(svgMenu);
    if (!punto) return seguir(null);
    const r = svgBarra.getBoundingClientRect();
    const distancia = Math.hypot(punto.x - (r.left + r.width / 2), punto.y - (r.top + r.height / 2));
    seguir(distancia < CERCA_PX ? svgBarra : null);
  }

  function alMoverPuntero(evento) {
    punto = { x: evento.clientX, y: evento.clientY };
    evaluar();
  }

  function alSalirPuntero() {
    punto = null;
    evaluar();
  }

  function detener() {
    [gazeBarra, gazeMenu].forEach((g) => g && g.stop());
    gazeBarra = gazeMenu = null;
    [svgBarra, svgMenu].forEach((svg) => svg && calmar(svg));
    if (svgBarra) svgBarra.classList.remove("mo-quieto");
    objetivo = null;
    menuAbierto = false;
    document.removeEventListener("pointermove", alMoverPuntero);
    document.documentElement.removeEventListener("mouseleave", alSalirPuntero);
  }

  async function pintar(nombreCompleto, contBarra, contMenu, base) {
    if (!(await cargar(base))) return;
    detener();
    texto = nombreCompleto;
    const normal = partes();
    contBarra.innerHTML = marcado(normal);
    contMenu.innerHTML = marcado(normal);
    svgBarra = contBarra.querySelector("svg");
    svgMenu = contMenu.querySelector("svg");
    [svgBarra, svgMenu].forEach((svg) => aplicadas.set(svg, Object.keys(normal.vars)));
    // gaze(svg) queda armado pero sin mirar nada hasta que se le diga qué seguir.
    gazeBarra = modulos.gaze.gaze(svgBarra);
    document.addEventListener("pointermove", alMoverPuntero);
    document.documentElement.addEventListener("mouseleave", alSalirPuntero);
  }

  return {
    pintar,
    detener,
    // La ventana de perfil se abre o se cierra.
    // OJO: el seguimiento del monito de la ventana se crea al abrir, con la ventana ya
    // visible. gaze() mide la forma de la cara al crearse; con la ventana oculta mide
    // cero y los ojos quedan aplastados en líneas que casi no se mueven.
    menu(abierto) {
      if (!modulos || !svgBarra) return;
      menuAbierto = abierto;
      if (abierto) {
        gazeMenu = modulos.gaze.gaze(svgMenu);
      } else {
        if (gazeMenu) gazeMenu.stop();
        gazeMenu = null;
        calmar(svgMenu);
        svgBarra.classList.remove("mo-quieto"); // el del navbar vuelve a su vida normal
      }
      evaluar();
    },
    // Clic en el monito del navbar: se enoja y, si la ventana quedó abierta, al terminar
    // se queda quieto hasta que se cierre.
    async pulsarBarra() {
      await carga;
      if (!svgBarra) return;
      svgBarra.classList.remove("mo-quieto");
      if ((await enojar(svgBarra)) && menuAbierto) svgBarra.classList.add("mo-quieto");
    },
    // Clic en el monito de la ventana: se enoja (si ya no lo está) y vuelve a lo normal.
    pulsarMenu() {
      if (menuAbierto) enojar(svgMenu);
    },
  };
})();
