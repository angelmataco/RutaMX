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

  let mensajes = [];
  let enviando = false;

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

  function agregarBurbuja(texto, rol) {
    const burbuja = document.createElement("div");
    burbuja.className = `chat-burbuja chat-burbuja--${rol === "user" ? "usuario" : "ia"}`;
    burbuja.textContent = texto;
    transcript.appendChild(burbuja);
    transcript.scrollTop = transcript.scrollHeight;
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

  function renderOpciones(opciones) {
    contenedorOpciones.innerHTML = "";
    contenedorOpciones.hidden = false;

    opciones.forEach((opcion) => {
      const tarjeta = document.createElement("article");
      tarjeta.className = "card opcion-ia-card";

      const paradasHtml = opcion.paradas
        .map(
          (parada) =>
            `<li><span class="tag tag--horas">≈${parada.horas_estimadas ?? "?"} h</span> <strong>${parada.nombre}</strong> <span class="opcion-ia-card__proposito">(${parada.proposito})</span></li>`
        )
        .join("");

      tarjeta.innerHTML = `
        <h4 class="card__title">${opcion.titulo}</h4>
        <p class="card__subtitle">${opcion.resumen.distancia_km} km · ${opcion.resumen.tiempo_h} h</p>
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

    try {
      const respuesta = await fetch("/api/ia/planear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensajes }),
      });
      const datos = await respuesta.json();

      if (datos.tipo === "pregunta") {
        mensajes.push({ role: "assistant", content: datos.mensaje });
        agregarBurbuja(datos.mensaje, "ia");
        agregarRespuestasRapidas(datos.opciones_respuesta);
      } else if (datos.tipo === "opciones") {
        agregarBurbuja("¡Listo! Aquí tienes dos opciones distintas para tu viaje:", "ia");
        renderOpciones(datos.opciones);
      } else {
        agregarBurbuja(datos.mensaje || "Ocurrió un error, intenta de nuevo.", "ia");
      }
    } catch (err) {
      console.error("Error en el chat de IA:", err);
      agregarBurbuja("Ocurrió un error de conexión. Intenta de nuevo.", "ia");
    } finally {
      enviando = false;
    }
  }

  botonAbrir.addEventListener("click", () => {
    if (typeof dialogo.showModal === "function") dialogo.showModal();
  });

  form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    const texto = input.value;
    input.value = "";
    enviarMensaje(texto);
  });

  verificarDisponibilidad();
});
