// Efectos visuales (solo frontend): sección de la página en la que está el
// usuario. La comparten el menú "gooey" del navbar y la píldora de progreso.
// Las secciones de resultados (#ruta, #descubre, #itinerario) están ocultas
// hasta que se calcula una ruta, así que solo cuentan las que se ven.

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.reducirMovimiento = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

RutaEfectos.secciones = (() => {
  const TODAS = [
    { id: "inicio", etiqueta: "Inicio" },
    { id: "ruta", etiqueta: "Ruta" },
    { id: "descubre", etiqueta: "Descubre" },
    { id: "itinerario", etiqueta: "Itinerario" },
  ];
  const MARGEN_SUPERIOR = 140; // una sección "empieza" cuando su borde sube de aquí
  const oyentes = [];
  let activaId = null;
  let bloqueadoHasta = 0;
  let pendiente = false;

  const visible = (el) => el && el.getClientRects().length > 0;

  function disponibles() {
    return TODAS.filter((s) => visible(document.getElementById(s.id)));
  }

  function calcularActiva() {
    const lista = disponibles();
    if (!lista.length) return null;
    const alFinal = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
    if (alFinal) return lista[lista.length - 1].id;
    let activa = lista[0].id;
    lista.forEach((s) => {
      if (document.getElementById(s.id).getBoundingClientRect().top <= MARGEN_SUPERIOR) activa = s.id;
    });
    return activa;
  }

  function actualizar(forzar = false) {
    if (!forzar && Date.now() < bloqueadoHasta) return;
    const nueva = calcularActiva();
    if (nueva === activaId && !forzar) return;
    activaId = nueva;
    oyentes.forEach((cb) => cb(activaId));
  }

  function programar() {
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(() => {
      pendiente = false;
      actualizar();
    });
  }

  window.addEventListener("scroll", programar, { passive: true });
  window.addEventListener("resize", () => actualizar(true));
  document.addEventListener("DOMContentLoaded", () => {
    // Los resultados aparecen/desaparecen quitando el atributo hidden.
    const resultados = document.querySelector("[data-resultados]");
    if (resultados) {
      new MutationObserver(() => actualizar(true)).observe(resultados, { attributes: true, attributeFilter: ["hidden"] });
    }
    actualizar(true);
  });

  return {
    disponibles,
    activa: () => activaId,
    alCambiar: (cb) => oyentes.push(cb),
    reevaluar: () => actualizar(true),
    // Mientras una animación de scroll está en curso, no se cambia la activa.
    bloquear(ms) {
      bloqueadoHasta = Date.now() + ms;
      setTimeout(() => actualizar(true), ms + 20);
    },
    irA(id) {
      const el = document.getElementById(id);
      if (!visible(el)) return false;
      this.bloquear(RutaEfectos.reducirMovimiento() ? 0 : 750);
      activaId = id;
      oyentes.forEach((cb) => cb(activaId));
      el.scrollIntoView({ behavior: RutaEfectos.reducirMovimiento() ? "auto" : "smooth", block: "start" });
      return true;
    },
  };
})();
