// Navbar fijo que se encoge al bajar: quedan el logo y "RutaMX" (sin los botones ni el perfil)
// sobre fondo translúcido, con la marca centrada en el primer tercio de la pantalla; en el
// segundo tercio aparece la píldora de progreso (efectos/pildora.js). Arriba de todo vuelve a su
// tamaño completo y la píldora desaparece. El navbar es `position: fixed`, así que un espaciador (`.navbar-espacio`)
// conserva su altura completa en el flujo: al encogerse no mueve el contenido ni provoca saltos
// de scroll. Lo visual (tamaños, translúcido) vive en styles.css.

const RutaNavbar = (() => {
  const BAJAR_PX = 48; // a partir de aquí se encoge
  const SUBIR_PX = 16; // por debajo de aquí se expande (histéresis: sin parpadeo en el límite)

  let barra = null;
  let espacio = null;
  let interior = null;
  let marca = null;
  let compacto = false;
  let pendiente = false;

  // Mide con las transiciones apagadas (si no, a mitad de una transición se mediría un tamaño
  // intermedio) y deja listas dos cosas:
  //  - la altura del navbar expandido, para el espaciador;
  //  - cuánto hay que desplazar la marca (--marca-dx) para que en compacto su centro quede en
  //    el primer tercio de la pantalla. Se calcula midiendo dónde cae "naturalmente" en compacto
  //    y moviéndola desde ahí, así sirve igual con la cuadrícula de escritorio que con el flex
  //    de celular.
  function medir() {
    const estabaCompacto = compacto;
    barra.classList.add("navbar--medir");
    barra.classList.remove("navbar--compacto");
    const alto = barra.offsetHeight;

    barra.classList.add("navbar--compacto");
    barra.style.setProperty("--marca-dx", "0px");
    const rMarca = marca.getBoundingClientRect();
    const pagina = document.documentElement.clientWidth;
    barra.style.setProperty("--marca-dx", `${(pagina / 3 - (rMarca.left + rMarca.width / 2)).toFixed(2)}px`);

    if (!estabaCompacto) barra.classList.remove("navbar--compacto");
    barra.offsetHeight; // fuerza el estilo antes de reactivar las transiciones
    barra.classList.remove("navbar--medir");
    espacio.style.setProperty("--navbar-alto", `${alto}px`);
  }

  function fijar(nuevo) {
    if (nuevo === compacto) return;
    compacto = nuevo;
    barra.classList.toggle("navbar--compacto", compacto);
    // La ventana de perfil vive en la parte que se oculta: se cierra al encogerse.
    if (compacto && typeof RutaAuth !== "undefined") RutaAuth.cerrarMenu();
    // La píldora de progreso se cierra al volver al navbar completo.
    document.dispatchEvent(new CustomEvent("navbar:compacto", { detail: compacto }));
  }

  function alHacerScroll() {
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(() => {
      pendiente = false;
      const y = window.scrollY;
      if (y > BAJAR_PX) fijar(true);
      else if (y < SUBIR_PX) fijar(false);
    });
  }

  function init() {
    barra = document.querySelector("[data-navbar]");
    espacio = document.querySelector("[data-navbar-espacio]");
    interior = barra && barra.querySelector(".navbar__inner");
    marca = barra && barra.querySelector(".navbar__brand");
    if (!barra || !espacio || !interior || !marca) return;
    medir();
    window.addEventListener("scroll", alHacerScroll, { passive: true });
    window.addEventListener("resize", medir);
    // Las fuentes web cambian la altura del navbar cuando terminan de cargar.
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(medir);
    alHacerScroll(); // por si la página se recarga ya con scroll
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", () => RutaNavbar.init());
