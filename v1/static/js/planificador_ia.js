// Chat "Planear con IA": conversa con el usuario, deja que el backend
// (llm_provider + planificador_ia_service) decida qué preguntar y qué
// dos opciones de itinerario proponer, y al elegir una la entrega al
// flujo normal vía window.RutaApp.aplicarPlanIA (definido en main.js).

document.addEventListener("DOMContentLoaded", () => {
  const botonAbrir = document.querySelector("[data-abrir-planificador-ia]");
  const dialogo = document.querySelector("[data-modal-ia]");
  const transcript = document.querySelector("[data-chat-transcript]");
  const contenedorOpciones = document.querySelector("[data-chat-opciones]");
  const form = document.querySelector("[data-chat-form]");
  const input = document.querySelector("[data-chat-input]");

  if (!botonAbrir || !dialogo || !transcript || !form || !input) return;

  const SALUDO =
    "¡Hola! Cuéntame cómo te imaginas tu road trip — de dónde a dónde, a qué hora sales, cuántos van y qué te gustaría hacer en el camino — y te propongo un itinerario.";
  // Velocidad de "escritura": ~20 ms por letra, pero ningún mensaje tarda
  // más de ~2.5 s en salir completo, aunque sea largo.
  const MS_POR_LETRA = 20;
  const MS_MAXIMO_MENSAJE = 2500;
  const reducirMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let mensajes = [];
  let enviando = false;
  let saludado = false;

  async function verificarDisponibilidad() {
    try {
      const respuesta = await fetch("/api/ia/disponible");
      const datos = await respuesta.json();
      botonAbrir.hidden = !datos.disponible;
    } catch (err) {
      console.error("Error consultando disponibilidad de IA:", err);
      botonAbrir.hidden = true;
    }
  }

  const pausa = (ms) => new Promise((resolver) => setTimeout(resolver, ms));

  function agregarBurbuja(texto, rol) {
    const burbuja = document.createElement("div");
    burbuja.className = `chat-burbuja chat-burbuja--${rol === "user" ? "usuario" : "ia"}`;
    burbuja.textContent = texto;
    transcript.appendChild(burbuja);
    transcript.scrollTop = transcript.scrollHeight;
  }

  // Burbuja de la IA que se va escribiendo letra por letra.
  async function escribirBurbuja(texto) {
    if (reducirMovimiento) {
      agregarBurbuja(texto, "ia");
      return;
    }
    const burbuja = document.createElement("div");
    burbuja.className = "chat-burbuja chat-burbuja--ia is-escribiendo";
    transcript.appendChild(burbuja);

    const letras = Array.from(texto); // respeta emojis
    const retraso = Math.min(MS_POR_LETRA, MS_MAXIMO_MENSAJE / letras.length);
    for (let i = 1; i <= letras.length; i++) {
      burbuja.textContent = letras.slice(0, i).join("");
      transcript.scrollTop = transcript.scrollHeight;
      await pausa(retraso);
    }
    burbuja.classList.remove("is-escribiendo");
  }

  // Los tres puntitos mientras la IA "piensa" (esperando al servidor).
  function mostrarPensando() {
    const burbuja = document.createElement("div");
    burbuja.className = "chat-burbuja chat-burbuja--ia chat-burbuja--orbe";
    transcript.appendChild(burbuja);
    RutaEfectos.orbe.montar(burbuja, { estado: "thinking", tamano: 92, etiqueta: "Pensando…" });
    transcript.scrollTop = transcript.scrollHeight;
    return burbuja;
  }

  function agregarRespuestasRapidas(opciones) {
    if (!opciones || !opciones.length) return;
    const contenedor = document.createElement("div");
    contenedor.className = "chat-respuestas-rapidas";

    [...opciones.slice(0, 3), "Otro"].forEach((texto) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "chat-opcion-respuesta";
      boton.textContent = texto;
      boton.addEventListener("click", () => {
        contenedor.remove();
        if (texto === "Otro") {
          input.focus();
          return;
        }
        enviarMensaje(texto);
      });
      contenedor.appendChild(boton);
    });

    transcript.appendChild(contenedor);
    transcript.scrollTop = transcript.scrollHeight;
  }

  // "descanso" en el sistema significa dormir; se muestra tal cual se entiende.
  function nombreDeProposito(proposito) {
    return { comida: "comer", descanso: "dormir" }[proposito] || proposito;
  }

  function renderOpciones(opciones) {
    contenedorOpciones.innerHTML = "";
    contenedorOpciones.hidden = false;

    opciones.forEach((opcion) => {
      const tarjeta = document.createElement("article");
      tarjeta.className = "card opcion-ia-card";

      const paradasHtml = opcion.paradas
        .map(
          (parada) =>
            `<li><span class="tag tag--horas">≈${parada.horas_estimadas != null ? formatoDuracion(parada.horas_estimadas) : "?"}${parada.hora_llegada ? ` · ${parada.hora_llegada}` : ""}</span> <strong title="${parada.reconocimiento_gastronomico || ""}">${parada.gastronomia_destacada ? RutaIconos.html("estrella", 14) + " " : ""}${parada.nombre}</strong> <span class="opcion-ia-card__proposito">(${nombreDeProposito(parada.proposito)})</span></li>`
        )
        .join("");

      tarjeta.innerHTML = `
        <h4 class="card__title">${opcion.titulo}</h4>
        <p class="card__subtitle">${opcion.resumen.distancia_km} km · ${formatoDuracion(opcion.resumen.tiempo_h)}${
          opcion.resumen.gasto
            ? ` · gasto máx. ≈ ${new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(opcion.resumen.gasto.total)}`
            : ""
        }</p>
        <ul class="opcion-ia-card__paradas">${paradasHtml}</ul>
        <button type="button" class="btn btn--primary btn--block" data-usar-opcion>Usar esta opción</button>
      `;

      tarjeta.querySelector("[data-usar-opcion]").addEventListener("click", () => {
        if (window.RutaApp) window.RutaApp.aplicarPlanIA(opcion);
        dialogo.close();
      });

      contenedorOpciones.appendChild(tarjeta);
    });
  }

  async function enviarMensaje(texto) {
    if (enviando || !texto.trim()) return;
    enviando = true;

    agregarBurbuja(texto, "user");
    mensajes.push({ role: "user", content: texto });

    const pensando = mostrarPensando();
    try {
      const respuesta = await fetch("/api/ia/planear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensajes }),
      });
      const datos = await respuesta.json();
      pensando.remove();

      if (datos.tipo === "pregunta") {
        mensajes.push({ role: "assistant", content: datos.mensaje });
        await escribirBurbuja(datos.mensaje);
        agregarRespuestasRapidas(datos.opciones_respuesta);
      } else if (datos.tipo === "opciones") {
        await escribirBurbuja("¡Listo! Aquí tienes dos opciones distintas para tu viaje:");
        renderOpciones(datos.opciones);
      } else {
        await escribirBurbuja(datos.mensaje || "Ocurrió un error, intenta de nuevo.");
      }
    } catch (err) {
      console.error("Error en el chat de IA:", err);
      pensando.remove();
      await escribirBurbuja("Ocurrió un error de conexión. Intenta de nuevo.");
    } finally {
      enviando = false;
    }
  }

  botonAbrir.addEventListener("click", () => {
    if (typeof dialogo.showModal === "function") dialogo.showModal();
    // El saludo se escribe solo la primera vez; después la conversación
    // se conserva tal cual.
    if (!saludado) {
      saludado = true;
      enviando = true; // no dejar mandar mensajes mientras se escribe el saludo
      escribirBurbuja(SALUDO).finally(() => {
        enviando = false;
        input.focus();
      });
    }
  });

  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const texto = input.value;
    input.value = "";
    enviarMensaje(texto);
  });

  verificarDisponibilidad();
});
