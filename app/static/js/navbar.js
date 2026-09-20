// Navbar fijo que se encoge al bajar: quedan el logo, "RutaMX" y los botones de navegación
// (sin el perfil) sobre fondo translúcido: la marca centrada en el primer tercio de la pantalla
// y los botones en el segundo (en celular, juntos y centrados). Arriba de todo vuelve a su
// tamaño completo. El navbar es `position: fixed`, así que un espaciador (`.navbar-espacio`)
// conserva su altura completa en el flujo: al encogerse no mueve el contenido ni provoca saltos
// de scroll. Lo visual (tamaños, translúcido) vive en styles.css.

const RutaNavbar = (() => {
  const BAJAR_PX = 48; // a partir de aquí se encoge
  const SUBIR_PX = 16; // por debajo de aquí se expande (histéresis: sin parpadeo en el límite)
  const SEPARACION_MOVIL_PX = 36; // hueco entre la marca y los botones en celular

  let barra = null;
  let espacio = null;
  let interior = null;
  let marca = null;
  let enlaces = null;
  let compacto = false;
  let pendiente = false;

  // Mide con las transiciones apagadas (si no, a mitad de una transición se mediría un tamaño
  // intermedio) y deja listas dos cosas:
  //  - la altura del navbar expandido, para el espaciador;
  //  - cuánto hay que desplazar la marca y los botones (--marca-dx / --links-dx) para que en
  //    compacto queden juntos como un solo bloque centrado en la página. Se calcula midiendo
  //    dónde caen "naturalmente" en compacto y moviéndolos desde ahí, así sirve igual con la
  //    cuadrícula de escritorio que con el flex de celular.
  function medir() {
    const estabaCompacto = compacto;
    barra.classList.add("navbar--medir");
    barra.classList.remove("navbar--compacto");
    const alto = barra.offsetHeight;

    barra.classList.add("navbar--compacto");
    barra.style.setProperty("--marca-dx", "0px");
    barra.style.setProperty("--links-dx", "0px");
    const rMarca = marca.getBoundingClientRect();
    const rEnlaces = enlaces.getBoundingClientRect();
    const rInterior = interior.getBoundingClientRect();
    let marcaDx;
    let linksDx;
    if (window.matchMedia("(max-width: 640px)").matches) {
      // Celular: no cabe el reparto en tercios. Marca y botones juntos, centrados como un bloque.
      const estilo = getComputedStyle(interior);
      const izquierda = rInterior.left + parseFloat(estilo.paddingLeft);
      const ancho = rInterior.width - parseFloat(estilo.paddingLeft) - parseFloat(estilo.paddingRight);
      const inicio = izquierda + (ancho - (rMarca.width + SEPARACION_MOVIL_PX + rEnlaces.width)) / 2;
      marcaDx = inicio - rMarca.left;
      linksDx = inicio + rMarca.width + SEPARACION_MOVIL_PX - rEnlaces.left;
    } else {
      // Escritorio: la pantalla en 3 partes iguales; la marca centrada en la línea del primer
      // tercio y los botones en la del segundo. Simétricos respecto al centro de la página.
      const pagina = document.documentElement.clientWidth;
      marcaDx = pagina / 3 - (rMarca.left + rMarca.width / 2);
      linksDx = (pagina * 2) / 3 - (rEnlaces.left + rEnlaces.width / 2);
    }
    barra.style.setProperty("--marca-dx", `${marcaDx.toFixed(2)}px`);
    barra.style.setProperty("--links-dx", `${linksDx.toFixed(2)}px`);

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
    enlaces = barra && barra.querySelector(".navbar__links");
    if (!barra || !espacio || !interior || !marca || !enlaces) return;
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
