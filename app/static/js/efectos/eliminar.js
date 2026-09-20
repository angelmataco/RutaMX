// Botón de borrar que pide confirmación en el mismo lugar, sin ventana
// emergente: el bote abre la tapa y aparecen ✓ (borrar) y ✕ (cancelar).
// Adaptado del componente delete-button (rare-ui) a JS/CSS puro.
//
//   RutaEfectos.eliminar.montar(botonOriginal, () => borrarLoQueSea());
//
// Reemplaza al botón original y llama al callback ya confirmado.

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.eliminar = (() => {
  const RETRASO_CONFIRMACION_MS = 550; // deja ver el ✓ antes de que desaparezca el elemento

  const SVG = {
    bote:
      '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<g class="del__tapa"><path d="M4 6.5H20"/><path d="M9.5 6.5V4.5C9.5 4 9.9 3.5 10.5 3.5H13.5C14.1 3.5 14.5 4 14.5 4.5V6.5"/></g>' +
      '<g class="del__cuerpo"><path d="M5.5 6.5L6.8 19.2C6.9 20.2 7.7 21 8.7 21H15.3C16.3 21 17.1 20.2 17.2 19.2L18.5 6.5"/>' +
      '<line x1="10" y1="10" x2="10" y2="17" stroke-width="1.6"/><line x1="14" y1="10" x2="14" y2="17" stroke-width="1.6"/></g></svg>',
    palomita:
      '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.5 12.8Q8 15.5 9.8 18.2C12.2 13.5 15.5 8.5 20 5.2"/></svg>',
    tache:
      '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6L18 18M18 6L6 18"/></svg>',
    hecho:
      '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path class="del__trazo" pathLength="1" d="M4.5 12.8Q8 15.5 9.8 18.2C12.2 13.5 15.5 8.5 20 5.2"/></svg>',
  };

  function crearBoton(clase, etiqueta, html) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = clase;
    b.setAttribute("aria-label", etiqueta);
    b.innerHTML = html;
    return b;
  }

  function montar(original, alConfirmar) {
    const titulo = original.getAttribute("title") || "Eliminar";

    const raiz = document.createElement("span");
    raiz.className = "del";
    raiz.dataset.estado = "cerrado";

    const caja = document.createElement("span");
    caja.className = "del__caja";

    const disparador = crearBoton("del__disparador", titulo, SVG.bote);
    disparador.setAttribute("aria-expanded", "false");

    const panel = document.createElement("span");
    panel.className = "del__panel";
    const confirmar = crearBoton("del__circulo del__circulo--si", "Confirmar: eliminar", SVG.palomita);
    const cancelar = crearBoton("del__circulo", "Cancelar", SVG.tache);
    panel.append(confirmar, cancelar);
    panel.inert = true; // cerrado: sus botones no reciben foco

    const aviso = document.createElement("span");
    aviso.className = "contador__sr";
    aviso.setAttribute("role", "status");
    aviso.setAttribute("aria-live", "polite");

    caja.append(disparador, panel); // con row-reverse el bote queda a la derecha
    raiz.append(caja, aviso);

    let cerrarPorFuera = null;

    function abrir() {
      raiz.dataset.estado = "abierto";
      disparador.setAttribute("aria-expanded", "true");
      panel.inert = false;
      cerrarPorFuera = (evento) => {
        if (!raiz.contains(evento.target)) resolver(false, false); // clic afuera: no le quita el foco a lo que se tocó
      };
      document.addEventListener("pointerdown", cerrarPorFuera);
    }

    function cerrar() {
      panel.inert = true;
      disparador.setAttribute("aria-expanded", "false");
      document.removeEventListener("pointerdown", cerrarPorFuera);
      cerrarPorFuera = null;
    }

    function resolver(confirmado, devolverFoco = true) {
      cerrar();
      if (confirmado) {
        raiz.dataset.estado = "borrado";
        raiz.classList.add("del--bloqueado");
        aviso.textContent = "Eliminado";
        setTimeout(alConfirmar, RETRASO_CONFIRMACION_MS);
      } else {
        raiz.dataset.estado = "cerrado";
        // Pequeño "rebote" del bote al cancelar.
        disparador.classList.remove("del__disparador--rebote");
        void disparador.offsetWidth;
        disparador.classList.add("del__disparador--rebote");
        aviso.textContent = "Conservado";
        if (devolverFoco) disparador.focus();
      }
    }

    disparador.addEventListener("click", () => {
      if (raiz.dataset.estado === "abierto") resolver(false);
      else if (raiz.dataset.estado === "cerrado") abrir();
    });
    confirmar.addEventListener("click", () => resolver(true));
    cancelar.addEventListener("click", () => resolver(false));
    raiz.addEventListener("keydown", (evento) => {
      if (evento.key === "Escape" && raiz.dataset.estado === "abierto") {
        evento.stopPropagation(); // que no cierre también una ventana <dialog> de atrás
        resolver(false);
      }
    });

    disparador.insertAdjacentHTML("beforeend", SVG.hecho.replace("<svg", '<svg class="del__hecho"'));
    original.replaceWith(raiz);
    return raiz;
  }

  return { montar };
})();
