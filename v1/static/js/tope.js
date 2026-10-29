// Tope suave entre secciones: cuando dejas de deslizar cerca del inicio de una sección, de
// arriba de todo o del recuadro del formulario, la página se acomoda sola con un desplazamiento corto, para que la
// sección quede centrada bajo el navbar. Es un imán ligero, no un freno: lejos del inicio
// de una sección no hace nada y el scroll es libre (también dentro de secciones altas).
//
// Por qué no `scroll-snap` de CSS: su zona de atracción la decide el navegador y es muy
// grande (un giro de rueda de 100 px desde el inicio de una sección regresaba solo al
// mismo punto). Aquí la zona es pequeña y se ajusta con FRACCION / MAX_PX.

const RutaTope = (() => {
  const FRACCION = 0.08; // de la altura de la ventana...
  const MAX_PX = 70; // ...con este máximo
  const MIN_PX = 24;
  const HOLGURA_MAX_PX = 20; // espacio máximo sobre el recuadro del formulario al acomodarlo
  const ESPERA_MS = 140; // sin scroll durante este tiempo = "dejó de deslizar"

  let temporizador = 0;
  let tocando = false; // dedo o clic sostenido (arrastrando la barra, tocando la pantalla)

  function topeSuperior() {
    return parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
  }

  // Posiciones de scroll donde una sección queda alineada bajo el navbar.
  function puntos() {
    const tope = topeSuperior();
    const lista = [0];
    document.querySelectorAll(".section").forEach((seccion) => {
      if (!seccion.offsetParent) return; // oculta (display: none)
      lista.push(Math.round(seccion.getBoundingClientRect().top + window.scrollY - tope));
    });
    // El recuadro del formulario ("Planea en minutos") queda completo y sin los textos del hero
    // encima. La holgura solo sirve para centrarlo si sobra espacio, y se limita para que no
    // asome el párrafo de arriba.
    const formulario = document.querySelector(".card--form-hero");
    if (formulario && formulario.offsetParent) {
      const caja = formulario.getBoundingClientRect();
      const holgura = Math.min(HOLGURA_MAX_PX, Math.max(0, (window.innerHeight - tope - caja.height) / 2));
      lista.push(Math.round(caja.top + window.scrollY - tope - holgura));
    }
    return lista;
  }

  function acomodar() {
    if (tocando || document.querySelector("dialog[open]")) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const zona = Math.min(MAX_PX, Math.max(MIN_PX, window.innerHeight * FRACCION));
    const y = window.scrollY;
    let mejor = null;
    puntos().forEach((punto) => {
      const distancia = Math.abs(punto - y);
      if (distancia > 0.5 && distancia <= zona && (mejor === null || distancia < Math.abs(mejor - y))) mejor = punto;
    });
    if (mejor !== null) window.scrollTo({ top: mejor, behavior: "smooth" });
  }

  function alHacerScroll() {
    clearTimeout(temporizador);
    temporizador = setTimeout(acomodar, ESPERA_MS);
  }

  function init() {
    window.addEventListener("scroll", alHacerScroll, { passive: true });
    window.addEventListener("pointerdown", () => (tocando = true), { passive: true });
    window.addEventListener(
      "pointerup",
      () => {
        tocando = false;
        alHacerScroll();
      },
      { passive: true }
    );
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", () => RutaTope.init());
