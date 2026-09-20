// Píldora flotante de progreso: un anillo que se llena al bajar por la página y
// el nombre de la sección actual; al tocarla se despliega en un menú para
// saltar a otra sección. Adaptado del componente scroll-progress (rare-ui).
// Solo aparece cuando hay al menos 2 secciones visibles (o sea, ya hay ruta).

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.pildora = (() => {
  function montar() {
    const raiz = document.createElement("div");
    raiz.className = "pildora";
    raiz.hidden = true;
    raiz.innerHTML = `
      <div class="pildora__superficie">
        <button type="button" class="pildora__cerrada" aria-label="Ir a otra sección" aria-expanded="false">
          <svg viewBox="0 0 24 24" class="pildora__anillo" aria-hidden="true">
            <circle cx="12" cy="12" r="10" class="pildora__pista" />
            <circle cx="12" cy="12" r="10" pathLength="1" class="pildora__avance" />
          </svg>
          <span class="pildora__etiqueta"></span>
        </button>
        <div class="pildora__abierta" role="group" aria-label="Secciones">
          <span class="pildora__resalte" aria-hidden="true"></span>
          <ul class="pildora__items"></ul>
        </div>
      </div>`;
    document.body.appendChild(raiz);

    const superficie = raiz.querySelector(".pildora__superficie");
    const cerrada = raiz.querySelector(".pildora__cerrada");
    const abierta = raiz.querySelector(".pildora__abierta");
    const items = raiz.querySelector(".pildora__items");
    const resalte = raiz.querySelector(".pildora__resalte");
    const etiqueta = raiz.querySelector(".pildora__etiqueta");
    const avance = raiz.querySelector(".pildora__avance");

    let secciones = [];
    let activaId = null;
    let estaAbierta = false;

    function medir() {
      const capa = estaAbierta ? abierta : cerrada;
      const ancho = capa.offsetWidth;
      const alto = capa.offsetHeight;
      if (!ancho) return;
      superficie.style.width = `${ancho}px`;
      superficie.style.height = `${alto}px`;
      superficie.style.borderRadius = estaAbierta ? "26px" : `${alto / 2}px`;
    }

    function colocarResalte() {
      const li = abierta.querySelector(`li[data-id="${activaId}"]`);
      if (!li) {
        resalte.style.opacity = "0";
        return;
      }
      resalte.style.opacity = "1";
      resalte.style.height = `${li.offsetHeight}px`;
      resalte.style.transform = `translateY(${li.offsetTop}px)`;
    }

    let etiquetaDeseada = "";
    let cambioPendiente = 0;

    function ponerEtiqueta(texto) {
      etiquetaDeseada = texto;
      if (RutaEfectos.reducirMovimiento() || !etiqueta.textContent) {
        etiqueta.textContent = texto;
        medir();
        return;
      }
      if (etiqueta.textContent === texto && !cambioPendiente) return;
      // Cruce suave: se desvanece la anterior, entra la nueva y se reajusta el ancho.
      // Si llegan varios cambios seguidos, al final queda siempre el más reciente.
      etiqueta.classList.add("is-cambiando");
      clearTimeout(cambioPendiente);
      cambioPendiente = setTimeout(() => {
        cambioPendiente = 0;
        etiqueta.textContent = etiquetaDeseada;
        etiqueta.classList.remove("is-cambiando");
        medir();
      }, 110);
    }

    function construirLista() {
      items.replaceChildren();
      secciones.forEach((s) => {
        const li = document.createElement("li");
        li.dataset.id = s.id;
        const boton = document.createElement("button");
        boton.type = "button";
        boton.innerHTML = '<span class="pildora__punto"></span>';
        boton.appendChild(document.createTextNode(s.etiqueta));
        boton.addEventListener("click", () => {
          cambiarApertura(false);
          RutaEfectos.secciones.irA(s.id);
        });
        li.appendChild(boton);
        items.appendChild(li);
      });
    }

    function cambiarApertura(valor) {
      estaAbierta = valor;
      raiz.classList.toggle("is-abierta", valor);
      cerrada.setAttribute("aria-expanded", String(valor));
      abierta.inert = !valor;
      cerrada.inert = valor;
      medir();
      if (valor) {
        colocarResalte();
        const primero = abierta.querySelector(`li[data-id="${activaId}"] button`) || abierta.querySelector("button");
        if (primero) primero.focus({ preventScroll: true });
      }
    }

    function refrescar() {
      const nuevas = RutaEfectos.secciones.disponibles();
      const cambio = nuevas.map((s) => s.id).join() !== secciones.map((s) => s.id).join();
      secciones = nuevas;
      raiz.hidden = secciones.length < 2;
      if (cambio) {
        construirLista();
        if (estaAbierta && secciones.length < 2) cambiarApertura(false);
      }
      activaId = RutaEfectos.secciones.activa();
      const activa = secciones.find((s) => s.id === activaId);
      if (activa) ponerEtiqueta(activa.etiqueta);
      abierta.querySelectorAll("li").forEach((li) => li.classList.toggle("is-activo", li.dataset.id === activaId));
      medir();
      colocarResalte();
    }

    function pintarProgreso() {
      const total = document.documentElement.scrollHeight - window.innerHeight;
      const p = total > 0 ? Math.min(1, Math.max(0, window.scrollY / total)) : 0;
      avance.style.strokeDashoffset = String(1 - p);
    }

    cerrada.addEventListener("click", () => cambiarApertura(true));
    document.addEventListener("pointerdown", (evento) => {
      if (estaAbierta && !raiz.contains(evento.target)) cambiarApertura(false);
    });
    document.addEventListener("keydown", (evento) => {
      if (evento.key === "Escape" && estaAbierta) {
        cambiarApertura(false);
        cerrada.focus({ preventScroll: true });
      }
    });
    window.addEventListener("scroll", pintarProgreso, { passive: true });
    window.addEventListener("resize", () => {
      pintarProgreso();
      refrescar();
    });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(medir).catch(() => {});

    RutaEfectos.secciones.alCambiar(refrescar);
    abierta.inert = true;
    refrescar();
    pintarProgreso();
    return raiz;
  }

  document.addEventListener("DOMContentLoaded", montar);
  return { montar };
})();
