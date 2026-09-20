// Menú "gooey": la opción elegida se separa del resto y queda unida a la barra
// por un cuello que se estira como goma. Adaptado del componente gooey-nav
// (rare-ui). Mejora el <nav class="navbar__links"> con enlaces a secciones;
// sin este script son los enlaces normales.

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.gooey = (() => {
  const RIGIDEZ = 200;
  const AMORTIGUACION = 28;
  const CORTE_CUELLO = 0.22; // el cuello se adelgaza a nada cuando el hueco llega a este tramo
  const ALTO_CUELLO = 100;
  const SEPARACION = 16;
  const RADIO = 10;
  const NS = "http://www.w3.org/2000/svg";

  // Dos curvas cóncavas que se pellizcan hacia el centro, dibujadas en el hueco.
  function trazoCuello(hueco, ancho) {
    if (!Number.isFinite(hueco) || hueco <= 0 || ancho <= 0) return "";
    const cintura = ALTO_CUELLO * (1 - hueco / (ancho * CORTE_CUELLO));
    if (cintura <= 0) return "";
    const inicio = ancho - hueco;
    const medio = inicio + hueco / 2;
    return `M${inicio} 0 Q${medio} ${ALTO_CUELLO - cintura} ${ancho} 0 L${ancho} ${ALTO_CUELLO} Q${medio} ${cintura} ${inicio} ${ALTO_CUELLO} Z`;
  }

  function montar(nav) {
    const enlaces = Array.from(nav.querySelectorAll("a"));
    if (enlaces.length < 2) return null;

    nav.classList.add("gooey");
    const lista = document.createElement("ul");
    lista.className = "gooey__lista";

    const segmentos = enlaces.map((enlace, i) => {
      const li = document.createElement("li");
      li.className = "gooey__seg";
      enlace.classList.add("gooey__item");
      let path = null;
      let degradado = null;
      if (i > 0) {
        const svg = document.createElementNS(NS, "svg");
        svg.setAttribute("class", "gooey__cuello");
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("width", SEPARACION);
        svg.setAttribute("viewBox", `0 0 ${SEPARACION} ${ALTO_CUELLO}`);
        svg.setAttribute("preserveAspectRatio", "none");
        const defs = document.createElementNS(NS, "defs");
        degradado = document.createElementNS(NS, "linearGradient");
        degradado.id = `gooey-cuello-${i}`;
        degradado.setAttribute("x1", "0");
        degradado.setAttribute("x2", "1");
        const izq = document.createElementNS(NS, "stop");
        izq.setAttribute("offset", "0");
        const der = document.createElementNS(NS, "stop");
        der.setAttribute("offset", "1");
        degradado.append(izq, der);
        defs.appendChild(degradado);
        path = document.createElementNS(NS, "path");
        path.setAttribute("fill", `url(#gooey-cuello-${i})`);
        svg.append(defs, path);
        li.appendChild(svg);
        li._paradas = [izq, der];
      }
      li.appendChild(enlace);
      lista.appendChild(li);
      // Cada segmento lleva su propio resorte para el margen izquierdo.
      return { li, path, hueco: i === 0 ? 0 : -1, velocidad: 0, meta: i === 0 ? 0 : -1 };
    });
    nav.replaceChildren(lista);

    let activo = -1;
    let raf = 0;
    let ultimo = 0;

    const abierta = (costura) => costura === 0 || costura === segmentos.length || costura - 1 === activo || costura === activo;

    function aplicarVista() {
      segmentos.forEach((seg) => {
        seg.li.style.marginLeft = `${seg.hueco}px`;
        if (seg.path) seg.path.setAttribute("d", trazoCuello(seg.hueco, SEPARACION));
      });
    }

    function paso(ahora) {
      const dt = Math.min((ahora - ultimo) / 1000, 0.032);
      ultimo = ahora;
      let enMovimiento = false;
      segmentos.forEach((seg) => {
        const fuerza = -RIGIDEZ * (seg.hueco - seg.meta) - AMORTIGUACION * seg.velocidad;
        seg.velocidad += fuerza * dt;
        seg.hueco += seg.velocidad * dt;
        if (Math.abs(seg.hueco - seg.meta) < 0.01 && Math.abs(seg.velocidad) < 0.01) {
          seg.hueco = seg.meta;
          seg.velocidad = 0;
        } else {
          enMovimiento = true;
        }
      });
      aplicarVista();
      raf = enMovimiento ? requestAnimationFrame(paso) : 0;
    }

    function actualizar(reducido) {
      segmentos.forEach((seg, i) => {
        const esActivo = i === activo;
        seg.li.classList.toggle("is-activo", esActivo);
        const enlace = seg.li.querySelector("a");
        if (esActivo) enlace.setAttribute("aria-current", "true");
        else enlace.removeAttribute("aria-current");

        seg.meta = i === 0 ? 0 : abierta(i) ? SEPARACION : -1; // costura cerrada: 1px adentro para que no se vea rendija
        seg.li.style.borderTopLeftRadius = seg.li.style.borderBottomLeftRadius = `${abierta(i) ? RADIO : 0}px`;
        seg.li.style.borderTopRightRadius = seg.li.style.borderBottomRightRadius = `${abierta(i + 1) ? RADIO : 0}px`;

        if (seg.li._paradas) {
          const [izq, der] = seg.li._paradas;
          izq.style.stopColor = i - 1 === activo ? "var(--gooey-activo)" : "var(--gooey-barra)";
          der.style.stopColor = esActivo ? "var(--gooey-activo)" : "var(--gooey-barra)";
        }
      });
      if (reducido) {
        segmentos.forEach((seg) => {
          seg.hueco = seg.meta;
          seg.velocidad = 0;
        });
        aplicarVista();
      } else if (!raf) {
        ultimo = performance.now();
        raf = requestAnimationFrame(paso);
      }
    }

    // "activo" es lo que se ve (y se anima); "real" es la sección donde está la
    // página. Al pasar el cursor por una opción se anima esa; al salir vuelve a la real.
    let real = -1;
    let sobre = false;

    function mostrar(indice) {
      if (indice === activo) return;
      activo = indice;
      actualizar(RutaEfectos.reducirMovimiento());
    }

    function elegir(indice) {
      real = indice;
      if (!sobre) mostrar(indice);
    }

    const indiceDe = (id) => enlaces.findIndex((a) => a.getAttribute("href") === `#${id}`);

    segmentos.forEach((seg, i) => {
      seg.li.addEventListener("mouseenter", () => {
        sobre = true;
        mostrar(i);
      });
      enlaces[i].addEventListener("focus", () => mostrar(i));
      enlaces[i].addEventListener("blur", () => mostrar(sobre ? activo : real));
    });
    lista.addEventListener("mouseleave", () => {
      sobre = false;
      mostrar(real);
    });

    enlaces.forEach((enlace, i) => {
      enlace.addEventListener("click", (evento) => {
        const id = (enlace.getAttribute("href") || "").replace("#", "");
        // Con la sección oculta (aún no hay ruta) se conserva el comportamiento de siempre.
        if (id && RutaEfectos.secciones.irA(id)) {
          evento.preventDefault();
          elegir(i);
          mostrar(i);
        }
      });
    });

    RutaEfectos.secciones.alCambiar((id) => elegir(indiceDe(id)));
    actualizar(true);
    elegir(indiceDe(RutaEfectos.secciones.activa()));
    return { elegir };
  }

  document.addEventListener("DOMContentLoaded", () => {
    const nav = document.querySelector(".navbar__links");
    if (nav) api.instancia = montar(nav);
  });

  const api = { montar, instancia: null };
  return api;
})();
