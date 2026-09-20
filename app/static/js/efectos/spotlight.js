// Luz que sigue al cursor sobre tarjetas y ventanas: un aro brillante en el borde
// y un resplandor suave por dentro, que se acercan al puntero. Adaptado del componente
// spotlight-card (GlowCard) a JS/CSS puro; los colores salen de la paleta de la app.
//
// Este script solo mide dónde está el puntero respecto a cada superficie y lo deja en
// variables CSS (--mx, --my, --xp, --spot-on). Todo lo visual vive en efectos.css.
// Se aplica solo, sin ganchos en el HTML: también a las tarjetas que arma main.js después.

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.spotlight = (() => {
  // Debe coincidir con la lista de "Luz que sigue al cursor" en efectos.css.
  const SUPERFICIES = ".card, .ruta-burbuja, .modal-auth, .modal-ajustes, .modal-rutas, .modal-ia, .navbar__menu";

  let ultimo = null; // último PointerEvent, para pintar una vez por cuadro
  let pendiente = false;

  // Con una ventana (<dialog>) abierta, la luz es solo de esa ventana y de lo que lleva
  // dentro: la página de atrás queda apagada aunque el cursor pase por encima.
  function pintar() {
    pendiente = false;
    const ventana = document.querySelector("dialog[open]");
    const punto = ultimo ? { x: ultimo.clientX, y: ultimo.clientY } : null;
    const xp = punto ? (punto.x / window.innerWidth).toFixed(3) : "0.5";
    document.querySelectorAll(SUPERFICIES).forEach((el) => {
      const activa = punto && (!ventana || ventana.contains(el));
      if (!activa) {
        el.style.setProperty("--spot-on", "0");
        return;
      }
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return; // oculta (display: none)
      el.style.setProperty("--mx", `${(punto.x - r.left).toFixed(1)}px`);
      el.style.setProperty("--my", `${(punto.y - r.top).toFixed(1)}px`);
      el.style.setProperty("--xp", xp);
      el.style.setProperty("--spot-on", "1");
    });
  }

  function apagar() {
    ultimo = null;
    pintar();
  }

  function alMoverse(e) {
    ultimo = e;
    if (!pendiente) {
      pendiente = true;
      requestAnimationFrame(pintar);
    }
  }

  document.addEventListener("pointermove", alMoverse, { passive: true });
  document.addEventListener("pointerdown", alMoverse, { passive: true });
  document.documentElement.addEventListener("pointerleave", apagar);
  // En pantallas táctiles la luz no debe quedarse pegada donde soltaste el dedo.
  document.addEventListener("pointerup", (e) => e.pointerType === "touch" && apagar());
  document.addEventListener("pointercancel", apagar);

  // Al abrir o cerrar una ventana se recalcula al momento (sin esperar a que se mueva el mouse):
  // al abrirla se apaga la luz de la página de atrás; al cerrarla, vuelve a la normalidad.
  new MutationObserver(() => {
    if (!pendiente) {
      pendiente = true;
      requestAnimationFrame(pintar);
    }
  }).observe(document.body, { subtree: true, attributes: true, attributeFilter: ["open"] });

  return { apagar };
})();
