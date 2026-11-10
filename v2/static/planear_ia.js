/* M-03: el servidor es la autoridad; el navegador solo representa su estado. */
document.addEventListener("DOMContentLoaded", () => {
  const raiz = document.querySelector("[data-planear]");
  if (!raiz) return;
  const mensajes = raiz.querySelector("[data-mensajes]");
  const formulario = raiz.querySelector("[data-formulario]");
  const campo = formulario.querySelector("textarea");
  const enviar = raiz.querySelector("[data-enviar]");
  const reiniciar = raiz.querySelector("[data-reiniciar]");
  const espera = raiz.querySelector("[data-espera]");
  const error = raiz.querySelector("[data-error]");
  const itinerario = raiz.querySelector("[data-itinerario]");
  const vacioInicial = itinerario.firstElementChild.cloneNode(true);
  const dialogo = document.querySelector("[data-confirmacion]");
  const si = dialogo.querySelector("[data-si]");
  const no = dialogo.querySelector("[data-no]");
  const csrf = document.querySelector('meta[name="rutamx-csrf"]').content;
  const tabs = [...raiz.querySelectorAll('[role="tab"]')];
  const movil = matchMedia("(max-width: 899px)");
  let ocupado = false;
  let orbe = null;
  let rutaAnterior = "null";
  let cantidadMensajes = 0;

  function elemento(etiqueta, texto, clase) {
    const el = document.createElement(etiqueta);
    if (texto !== undefined) el.textContent = texto;
    if (clase) el.className = clase;
    return el;
  }

  function vista(id, enfocar = false) {
    tabs.forEach((tab) => {
      const activa = tab.getAttribute("aria-controls") === id;
      tab.setAttribute("aria-selected", String(activa));
      tab.tabIndex = activa ? 0 : -1;
      document.getElementById(tab.getAttribute("aria-controls")).classList.toggle("planear-panel--activo", activa);
      if (activa && enfocar) tab.focus();
    });
    if (id === "itinerario") raiz.querySelector("[data-novedad]").hidden = true;
    window.RutaEfectos?.secciones?.reevaluar();
  }

  tabs.forEach((tab, indice) => {
    tab.addEventListener("click", () => vista(tab.getAttribute("aria-controls")));
    tab.addEventListener("keydown", (evento) => {
      let siguiente;
      if (evento.key === "ArrowRight" || evento.key === "ArrowLeft") siguiente = 1 - indice;
      if (evento.key === "Home") siguiente = 0;
      if (evento.key === "End") siguiente = 1;
      if (siguiente !== undefined) {
        evento.preventDefault();
        vista(tabs[siguiente].getAttribute("aria-controls"), true);
      }
    });
  });
  function roles() {
    tabs.forEach((tab) => {
      const panel = document.getElementById(tab.getAttribute("aria-controls"));
      if (movil.matches) {
        panel.setAttribute("role", "tabpanel");
        panel.setAttribute("aria-labelledby", tab.id);
      } else {
        panel.removeAttribute("role");
        panel.setAttribute("aria-labelledby", panel.id === "ruta" ? "titulo-chat" : "titulo-itinerario");
      }
    });
    window.RutaEfectos?.secciones?.reevaluar();
  }
  movil.addEventListener("change", roles);
  roles();
  document.addEventListener("click", (evento) => {
    const enlace = evento.target.closest('a[href="#ruta"], a[href="#itinerario"], li[data-id="ruta"], li[data-id="itinerario"]');
    if (!enlace || !movil.matches) return;
    vista(enlace.dataset.id || enlace.hash.slice(1));
  }, true);

  function mostrarOcupado(valor) {
    ocupado = valor;
    enviar.disabled = valor;
    reiniciar.disabled = valor;
    si.disabled = valor;
    no.disabled = valor;
    formulario.setAttribute("aria-busy", String(valor));
    espera.hidden = !valor;
    if (valor) {
      orbe = window.RutaEfectos?.orbe?.montar(raiz.querySelector("[data-orbe]"), { tamano: 92, estado: "thinking", etiqueta: "Preparando tu propuesta" });
    } else if (orbe) {
      orbe.destruir();
      orbe = null;
    }
  }

  function pintarItinerario(ruta) {
    const serializada = JSON.stringify(ruta);
    if (serializada === rutaAnterior) return;
    rutaAnterior = serializada;
    if (!ruta) {
      itinerario.replaceChildren(vacioInicial.cloneNode(true));
      raiz.querySelector("[data-actualizado]").hidden = true;
      raiz.querySelector("[data-novedad]").hidden = true;
      return;
    }
    itinerario.replaceChildren();
    itinerario.append(elemento("p", `${ruta.duracion_dias} ${ruta.duracion_dias === 1 ? "día" : "días"}`, "planear-ceja"));
    if (ruta.intereses.length) itinerario.append(elemento("p", ruta.intereses.join(" · "), "card__note"));
    const lista = elemento("ol", undefined, "planear-recorrido");
    function punto(tipo, nombre, descripcion) {
      const li = elemento("li");
      li.append(elemento("small", tipo), elemento("strong", nombre));
      if (descripcion) li.append(elemento("p", descripcion));
      lista.append(li);
    }
    punto("Origen", ruta.origen);
    ruta.paradas.forEach((p, i) => punto(`Parada ${i + 1}`, p.nombre, p.descripcion));
    punto("Destino", ruta.destino);
    itinerario.append(lista);
    if (!ruta.paradas.length) itinerario.append(elemento("p", "Sin paradas intermedias.", "card__note"));
    raiz.querySelector("[data-novedad]").hidden = document.getElementById("itinerario").classList.contains("planear-panel--activo");
    raiz.querySelector("[data-actualizado]").hidden = false;
  }

  function pintar(estado) {
    if (!estado) return;
    if (estado.mensajes.length < cantidadMensajes) {
      mensajes.replaceChildren();
      cantidadMensajes = 0;
    }
    estado.mensajes.slice(cantidadMensajes).forEach((m) => {
      const bloque = elemento("div", undefined, `planear-mensaje${m.rol === "usuario" ? " planear-mensaje--usuario" : ""}`);
      bloque.append(elemento("strong", m.rol === "usuario" ? "Tú" : "RutaMX"), elemento("p", m.texto));
      mensajes.append(bloque);
    });
    cantidadMensajes = estado.mensajes.length;
    mensajes.scrollTop = mensajes.scrollHeight;
    error.hidden = estado.estado !== "error";
    error.textContent = estado.estado === "error" ? estado.mensaje : "";
    pintarItinerario(estado.ruta);
    if (estado.confirmacion) {
      dialogo.querySelector("[data-pregunta]").textContent = estado.mensaje;
      if (!dialogo.open) dialogo.showModal();
      no.focus();
    }
  }

  async function solicitar(accion, datos) {
    if (ocupado) return;
    mostrarOcupado(true);
    error.hidden = true;
    try {
      const respuesta = await fetch(`/v2/planear/${accion}`, {
        method: "POST", headers: { "Content-Type": "application/json", "X-RutaMX-CSRF": csrf },
        body: JSON.stringify(datos), credentials: "same-origin",
      });
      const estado = await respuesta.json();
      if (!respuesta.ok) throw new Error(estado.error || "No se pudo procesar la solicitud. Intenta de nuevo.");
      pintar(estado);
      return true;
    } catch (fallo) {
      error.textContent = fallo instanceof TypeError || fallo instanceof SyntaxError
        ? "No se pudo conectar con RutaMX. Intenta de nuevo; tu itinerario se conserva."
        : fallo.message;
      error.hidden = false;
      if (accion === "mensaje" && !campo.value) campo.value = datos.mensaje;
      return false;
    } finally {
      mostrarOcupado(false);
      if (dialogo.open) no.focus();
      else campo.focus({ preventScroll: true });
    }
  }

  formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();
    if (ocupado || !campo.value.trim()) return;
    const mensaje = campo.value;
    campo.value = "";
    solicitar("mensaje", { mensaje });
  });
  function confirmar(acepta) {
    if (ocupado) return;
    dialogo.close();
    solicitar("confirmar", { acepta });
  }
  si.addEventListener("click", () => confirmar(true));
  no.addEventListener("click", () => confirmar(false));
  dialogo.addEventListener("cancel", (evento) => {
    evento.preventDefault();
    confirmar(false);
  });
  reiniciar.addEventListener("click", () => {
    if (ocupado) return;
    // El itinerario solo se borra cuando el servidor confirma el reinicio.
    solicitar("reiniciar", {}).then((correcto) => { if (correcto) location.reload(); });
  });
  pintar(JSON.parse(document.getElementById("estado-inicial").textContent));
});
