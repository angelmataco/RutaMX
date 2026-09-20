// Selector de "Hora de salida" con efecto gooey: una píldora [ HH Hr. ][ MM Min. ][ ✎ ]
// que al tocar el lápiz se separa en tres piezas con resorte y el lápiz pasa a
// palomita. Al tocar la hora o los minutos se abre una ruedita (scroll-snap, como la
// de iOS) para escoger deslizando: no hay que escribir. Adaptado del componente
// duration-picker (rare-ui) a JS/CSS puro.
//
// Guarda "HH:MM" (24 h) en el input oculto `[data-time-hidden]` (name=hora_salida)
// y dispara `change` en él, que es lo que ya escuchan form.js y main.js.
// Vacío = sin hora. Desde fuera: RutaEfectos.horaSalida.poner("08:30" | "").

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.horaSalida = (() => {
  const RIGIDEZ = 200;
  const AMORTIGUACION = 28;
  const ABIERTO = 8; // px de separación entre piezas al editar
  const MAX = { h: 23, m: 59 };
  const ALTO_ITEM = 36; // debe coincidir con --dur-item en efectos.css
  const INICIAL = { h: 8, m: 0 }; // lo que se propone al abrir sin hora

  const PLUMA =
    "M3.78181 16.3092L3 21L7.69086 20.2182C8.50544 20.0825 9.25725 19.6956 9.84119 19.1116L20.4198 8.53288C21.1934 7.75922 21.1934 6.5049 20.4197 5.73126L18.2687 3.58024C17.495 2.80658 16.2406 2.80659 15.4669 3.58027L4.88841 14.159C4.30447 14.7429 3.91757 15.4947 3.78181 16.3092Z";
  const PALOMITA = "M7.959 20.513L1.592 12.872L3.128 11.592L8.041 17.487L20.947 3.587L22.413 4.948L7.959 20.513Z";

  const pad2 = (n) => String(n).padStart(2, "0");
  const acotar = (n, max) => Math.min(max, Math.max(0, Math.trunc(n) || 0));

  function htmlRueda(campo) {
    const items = Array.from({ length: MAX[campo] + 1 }, (_, i) => `<li data-v="${i}">${pad2(i)}</li>`).join("");
    return `
      <div class="dur__rueda" data-rueda="${campo}" inert>
        <div class="dur__rueda-vista">
          <div class="dur__rueda-banda" aria-hidden="true"></div>
          <div class="dur__rueda-col"><ul><li class="dur__rueda-pad" aria-hidden="true"></li>${items}<li class="dur__rueda-pad" aria-hidden="true"></li></ul></div>
        </div>
        <button type="button" class="dur__rueda-limpiar">Sin hora definida</button>
      </div>`;
  }

  function montar(raiz, hidden) {
    raiz.classList.add("dur");
    raiz.setAttribute("role", "group");

    raiz.innerHTML = `
      <div class="dur__seg dur__seg--h">
        <input class="dur__input" type="text" inputmode="none" placeholder="--" readonly aria-label="Hora de salida, horas (flechas arriba y abajo para cambiar)" data-campo="h" />
        <span class="dur__etiqueta">Hr.</span>
        ${htmlRueda("h")}
      </div>
      <div class="dur__seg dur__seg--m">
        <input class="dur__input" type="text" inputmode="none" placeholder="--" readonly aria-label="Hora de salida, minutos (flechas arriba y abajo para cambiar)" data-campo="m" />
        <span class="dur__etiqueta">Min.</span>
        ${htmlRueda("m")}
      </div>
      <button type="button" class="dur__seg dur__seg--boton" aria-label="Editar hora de salida">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path class="dur__pluma" d="${PLUMA}" />
          <path class="dur__palomita" d="${PALOMITA}" />
        </svg>
      </button>
      <span class="dur__medida" aria-hidden="true"></span>`;

    const inputs = { h: raiz.querySelector('[data-campo="h"]'), m: raiz.querySelector('[data-campo="m"]') };
    const ruedas = {};
    ["h", "m"].forEach((campo) => {
      const el = raiz.querySelector(`[data-rueda="${campo}"]`);
      ruedas[campo] = {
        el,
        col: el.querySelector(".dur__rueda-col"),
        items: Array.from(el.querySelectorAll("li[data-v]")),
        limpiar: el.querySelector(".dur__rueda-limpiar"),
      };
    });
    const boton = raiz.querySelector(".dur__seg--boton");
    const medida = raiz.querySelector(".dur__medida");
    const formulario = hidden.form;

    let editando = false;
    let ruedaAbierta = null; // "h" | "m" | null
    let sucio = false; // ¿el usuario cambió algo mientras editaba?
    let hueco = 0;
    let velocidad = 0;
    let meta = 0;
    let raf = 0;
    let ultimo = 0;

    // ----- resorte de la separación entre piezas -----
    function pintar() {
      const g = Math.min(ABIERTO, Math.max(0, hueco));
      raiz.style.setProperty("--g", `${g}px`);
      raiz.style.setProperty("--abierto", String(g / ABIERTO));
      // Los textos "se mecen" un poco según la velocidad con que se abre/cierra.
      raiz.style.setProperty("--sway", `${Math.max(-3, Math.min(3, (velocidad / 70) * 3))}px`);
    }

    function paso(ahora) {
      const dt = Math.min((ahora - ultimo) / 1000, 0.032);
      ultimo = ahora;
      velocidad += (-RIGIDEZ * (hueco - meta) - AMORTIGUACION * velocidad) * dt;
      hueco += velocidad * dt;
      if (Math.abs(hueco - meta) < 0.01 && Math.abs(velocidad) < 0.5) {
        hueco = meta;
        velocidad = 0;
        pintar();
        raf = 0;
        return;
      }
      pintar();
      raf = requestAnimationFrame(paso);
    }

    function irA(nuevaMeta) {
      meta = nuevaMeta;
      if (RutaEfectos.reducirMovimiento()) {
        hueco = meta;
        velocidad = 0;
        pintar();
        return;
      }
      if (!raf) {
        ultimo = performance.now();
        raf = requestAnimationFrame(paso);
      }
    }

    // ----- ancho de cada campo: se ajusta al texto -----
    function ajustarAncho(input) {
      medida.textContent = input.value || "--";
      input.style.width = `${Math.max(Math.ceil(medida.offsetWidth) + 12, 26)}px`;
    }

    function pintarValores(texto) {
      const [h, m] = texto ? texto.split(":") : ["", ""];
      inputs.h.value = texto ? pad2(Number(h)) : "";
      inputs.m.value = texto ? pad2(Number(m)) : "";
      ajustarAncho(inputs.h);
      ajustarAncho(inputs.m);
    }

    function textoDeCampos() {
      if (inputs.h.value === "" && inputs.m.value === "") return ""; // sin hora
      return `${pad2(acotar(Number(inputs.h.value), MAX.h))}:${pad2(acotar(Number(inputs.m.value), MAX.m))}`;
    }

    // ----- las ruedas -----
    const valorDe = (campo) => (inputs[campo].value === "" ? INICIAL[campo] : acotar(Number(inputs[campo].value), MAX[campo]));

    function marcarActivo(campo, indice) {
      ruedas[campo].items.forEach((li, i) => li.classList.toggle("is-activo", i === indice));
    }

    function centrar(campo, valor, suave = false) {
      const { col } = ruedas[campo];
      const objetivo = acotar(valor, MAX[campo]) * ALTO_ITEM;
      if (suave && !RutaEfectos.reducirMovimiento()) col.scrollTo({ top: objetivo, behavior: "smooth" });
      else col.scrollTop = objetivo;
      marcarActivo(campo, acotar(valor, MAX[campo]));
    }

    function fijarValor(campo, valor) {
      const v = acotar(valor, MAX[campo]);
      inputs[campo].value = pad2(v);
      ajustarAncho(inputs[campo]);
      sucio = true;
      marcarActivo(campo, v);
      return v;
    }

    function abrirRueda(campo) {
      if (!editando || ruedaAbierta === campo) return;
      cerrarRueda();
      ruedaAbierta = campo;
      const { el } = ruedas[campo];
      el.inert = false;
      el.classList.add("is-abierta");
      requestAnimationFrame(() => centrar(campo, valorDe(campo)));
    }

    function cerrarRueda() {
      if (!ruedaAbierta) return;
      const { el } = ruedas[ruedaAbierta];
      el.classList.remove("is-abierta");
      el.inert = true;
      ruedaAbierta = null;
    }

    ["h", "m"].forEach((campo) => {
      const { col, items, limpiar, el } = ruedas[campo];
      let temporizador = 0;

      col.addEventListener("scroll", () => {
        if (ruedaAbierta !== campo) return;
        const indice = acotar(Math.round(col.scrollTop / ALTO_ITEM), MAX[campo]);
        if (pad2(indice) !== inputs[campo].value) fijarValor(campo, indice);
        clearTimeout(temporizador);
        // Al soltar, se acomoda justo en el número más cercano.
        temporizador = setTimeout(() => {
          col.scrollTo({ top: indice * ALTO_ITEM, behavior: RutaEfectos.reducirMovimiento() ? "auto" : "smooth" });
        }, 130);
      });

      items.forEach((li, i) => li.addEventListener("click", () => {
        fijarValor(campo, i);
        centrar(campo, i, true);
      }));

      limpiar.addEventListener("click", () => {
        inputs.h.value = "";
        inputs.m.value = "";
        sucio = true;
        cerrarEdicion(true);
      });

      // Que tocar la rueda no le quite el foco al campo (y así no cierre la edición).
      el.addEventListener("mousedown", (evento) => {
        if (evento.target !== limpiar) evento.preventDefault();
      });
    });

    // ----- editar / guardar -----
    function abrirEdicion(campo = "h") {
      if (editando) return;
      editando = true;
      sucio = false;
      raiz.dataset.editando = "";
      boton.setAttribute("aria-label", "Guardar hora de salida");
      // Sin hora todavía: se propone 08:00 para que la rueda tenga dónde empezar.
      if (inputs.h.value === "" && inputs.m.value === "") {
        inputs.h.value = pad2(INICIAL.h);
        inputs.m.value = pad2(INICIAL.m);
      }
      ajustarAncho(inputs.h);
      ajustarAncho(inputs.m);
      irA(ABIERTO);
      abrirRueda(campo);
    }

    function cerrarEdicion(guardar) {
      if (!editando) return;
      const nuevo = guardar ? textoDeCampos() : hidden.value;
      editando = false;
      cerrarRueda();
      delete raiz.dataset.editando;
      boton.setAttribute("aria-label", "Editar hora de salida");
      pintarValores(nuevo);
      irA(0);
      if (guardar && hidden.value !== nuevo) {
        hidden.value = nuevo;
        hidden.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }

    boton.addEventListener("click", () => (editando ? cerrarEdicion(true) : abrirEdicion()));

    Object.entries(inputs).forEach(([campo, input]) => {
      // Tocar la hora o los minutos abre su ruedita (y la edición, si estaba cerrada).
      input.addEventListener("pointerdown", (evento) => {
        evento.preventDefault(); // sin cursor de texto ni teclado en el celular
        if (!editando) abrirEdicion(campo);
        else if (ruedaAbierta === campo) cerrarRueda();
        else abrirRueda(campo);
      });
      input.addEventListener("keydown", (evento) => {
        // Sin teclear números: Enter guarda, Esc descarta, flechas cambian el valor.
        if (evento.key === "Enter") {
          evento.preventDefault();
          if (editando) cerrarEdicion(true);
          else abrirEdicion(campo);
        } else if (evento.key === "Escape" && editando) {
          evento.preventDefault();
          evento.stopPropagation();
          cerrarEdicion(false);
          boton.focus();
        } else if ((evento.key === "ArrowUp" || evento.key === "ArrowDown") && editando) {
          evento.preventDefault();
          const v = fijarValor(campo, valorDe(campo) + (evento.key === "ArrowUp" ? 1 : -1));
          if (ruedaAbierta === campo) centrar(campo, v, true);
        }
      });
    });

    // Tocar fuera del selector: se guarda solo si el usuario cambió algo (si solo lo abrió, no).
    document.addEventListener("pointerdown", (evento) => {
      if (editando && !raiz.contains(evento.target)) cerrarEdicion(sucio);
    });
    raiz.addEventListener("focusout", (evento) => {
      if (editando && evento.relatedTarget && !raiz.contains(evento.relatedTarget)) cerrarEdicion(sucio);
    });
    // Si se envía el formulario con la edición abierta, primero se guarda lo elegido.
    if (formulario) formulario.addEventListener("submit", () => cerrarEdicion(sucio), true);

    pintar();
    pintarValores(hidden.value);
    // Las fuentes pueden tardar: se remide el ancho cuando ya estén listas.
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(() => !editando && pintarValores(hidden.value)).catch(() => {});
    }

    return {
      // Desde fuera (rutas guardadas, plan de IA): pone la hora sin disparar `change`.
      poner(texto) {
        hidden.value = texto || "";
        if (editando) cerrarEdicion(false);
        pintarValores(hidden.value);
      },
    };
  }

  const api = {
    instancia: null,
    poner(texto) {
      if (api.instancia) api.instancia.poner(texto);
      else {
        const hidden = document.querySelector("[data-time-hidden]");
        if (hidden) hidden.value = texto || "";
      }
    },
  };

  document.addEventListener("DOMContentLoaded", () => {
    const raiz = document.querySelector("[data-hora-salida]");
    const hidden = document.querySelector("[data-time-hidden]");
    if (raiz && hidden) api.instancia = montar(raiz, hidden);
  });

  return api;
})();
