// Orquesta el flujo completo: formulario -> ruta -> sugerencias -> itinerario -> guardar.

document.addEventListener("DOMContentLoaded", () => {
  const estado = {
    resumen: null,
    itinerario: [], // lista de { id, nombre }
  };

  const elementos = {
    resultados: document.querySelector("[data-resultados]"),
    mapa: document.querySelector("[data-map]"),
    stats: {
      distancia: document.querySelector('[data-stat="distancia"]'),
      tiempo: document.querySelector('[data-stat="tiempo"]'),
      costo: document.querySelector('[data-stat="costo"]'),
      paradas: document.querySelector('[data-stat="paradas"]'),
    },
    presupuestoNota: document.querySelector("[data-presupuesto-note]"),
    sugerenciasContenedor: document.querySelector("[data-sugerencias]"),
    guardarRutaBtn: document.querySelector("[data-guardar-ruta]"),
    rutasGuardadasSelect: document.querySelector("[data-rutas-guardadas]"),
    itinerarioLista: document.querySelector("[data-itinerario-lista]"),
    itinerarioVacio: document.querySelector("[data-itinerario-vacio]"),
    itemOrigen: document.querySelector("[data-item-origen]"),
    itemDestino: document.querySelector("[data-item-destino]"),
    guardarItinerarioBtn: document.querySelector("[data-guardar-itinerario]"),
    aventuraParadas: document.querySelector("[data-aventura-paradas]"),
    aventuraDistancia: document.querySelector("[data-aventura-distancia]"),
    aventuraTexto: document.querySelector("[data-aventura-texto]"),
  };

  const tplSugerencia = document.getElementById("tpl-sugerencia");
  const tplParadaItinerario = document.getElementById("tpl-parada-itinerario");

  if (elementos.mapa) {
    RutaMapa.init("mapa");
  }

  function formatoMoneda(valor) {
    return new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(valor);
  }

  async function calcularRuta(valores) {
    try {
      const respuesta = await fetch("/api/ruta", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origen: valores.origen,
          destino: valores.destino,
          presupuesto: valores.presupuesto,
        }),
      });

      if (!respuesta.ok) {
        const error = await respuesta.json().catch(() => ({}));
        alert(error.error || "No se pudo calcular la ruta. Revisa el origen y destino.");
        return;
      }

      const resumen = await respuesta.json();
      estado.resumen = resumen;
      estado.itinerario = [];

      elementos.resultados.hidden = false;
      if (elementos.mapa) RutaMapa.invalidarTamano();

      renderResumen(resumen);
      renderItinerarioBase(resumen);

      elementos.resultados.scrollIntoView({ behavior: "smooth" });

      await cargarSugerencias(valores);
    } catch (err) {
      console.error("Error calculando la ruta:", err);
      alert("Ocurrió un error al calcular la ruta. Intenta de nuevo.");
    }
  }

  function renderResumen(resumen) {
    elementos.stats.distancia.textContent = `${resumen.distancia_km} km`;
    elementos.stats.tiempo.textContent = `${resumen.tiempo_h} h`;
    elementos.stats.costo.textContent = formatoMoneda(resumen.costo_estimado);
    elementos.stats.paradas.textContent = resumen.paradas_estimadas;

    if (resumen.presupuesto) {
      elementos.presupuestoNota.textContent = resumen.presupuesto_suficiente
        ? "Tu presupuesto cubre esta estimación y deja margen para experiencias en ruta."
        : "Tu presupuesto es un poco menor al estimado; considera ajustar paradas o gastos.";
    } else {
      elementos.presupuestoNota.textContent = "Agrega un presupuesto para comparar contra el costo estimado.";
    }
  }

  function renderItinerarioBase(resumen) {
    elementos.itemOrigen.hidden = false;
    elementos.itemDestino.hidden = false;
    elementos.itemOrigen.querySelector("[data-item-nombre]").textContent = resumen.origen.nombre;
    elementos.itemDestino.querySelector("[data-item-nombre]").textContent = resumen.destino.nombre;
    renderParadasItinerario();
  }

  async function cargarSugerencias(valores) {
    elementos.sugerenciasContenedor.innerHTML = '<p class="empty-state">Buscando ideas para tu recorrido…</p>';

    try {
      const query = new URLSearchParams({
        intereses: (valores.intereses || []).join(","),
        origen: valores.origen || "",
        destino: valores.destino || "",
      });
      if (valores.horasMax) query.set("horas_max", valores.horasMax);

      const respuesta = await fetch(`/api/sugerencias?${query.toString()}`);
      const datos = await respuesta.json();
      renderSugerencias(datos.sugerencias || []);
    } catch (err) {
      console.error("Error cargando sugerencias:", err);
      elementos.sugerenciasContenedor.innerHTML = '<p class="empty-state">No se pudieron cargar las sugerencias.</p>';
    }
  }

  function renderSugerencias(lugares) {
    elementos.sugerenciasContenedor.innerHTML = "";

    if (!lugares.length) {
      elementos.sugerenciasContenedor.innerHTML = '<p class="empty-state">No encontramos sugerencias para estos intereses todavía.</p>';
      return;
    }

    lugares.forEach((lugar) => {
      const nodo = tplSugerencia.content.cloneNode(true);
      const card = nodo.querySelector("[data-lugar-card]");
      card.dataset.lugarId = lugar.id;
      nodo.querySelector("[data-lugar-categoria]").textContent = lugar.categoria;
      nodo.querySelector("[data-lugar-nombre]").textContent = lugar.nombre;
      nodo.querySelector("[data-lugar-descripcion]").textContent = lugar.descripcion;

      if (typeof lugar.horas_estimadas === "number") {
        const horasEl = nodo.querySelector("[data-lugar-horas]");
        horasEl.textContent = `≈${lugar.horas_estimadas} h de camino`;
        horasEl.hidden = false;
      }

      if (lugar.buena_para_descanso) {
        nodo.querySelector("[data-lugar-descanso]").hidden = false;
      }

      nodo.querySelector("[data-agregar-parada]").addEventListener("click", () => {
        agregarParada(lugar);
        card.remove();
      });

      nodo.querySelector("[data-descartar]").addEventListener("click", () => {
        card.remove();
      });

      elementos.sugerenciasContenedor.appendChild(nodo);
    });
  }

  function agregarParada(lugar) {
    if (!estado.resumen || !lugar) return;
    estado.itinerario.push({ id: lugar.id, nombre: lugar.nombre, lat: lugar.lat, lon: lugar.lon });
    renderParadasItinerario();
  }

  function moverParada(indice, direccion) {
    const nuevoIndice = indice + direccion;
    if (nuevoIndice < 0 || nuevoIndice >= estado.itinerario.length) return;
    const [item] = estado.itinerario.splice(indice, 1);
    estado.itinerario.splice(nuevoIndice, 0, item);
    renderParadasItinerario();
  }

  function eliminarParada(indice) {
    estado.itinerario.splice(indice, 1);
    renderParadasItinerario();
  }

  function renderParadasItinerario() {
    elementos.itinerarioLista.querySelectorAll("[data-item-parada]").forEach((el) => el.remove());

    const hayResumen = Boolean(estado.resumen);
    elementos.itinerarioVacio.hidden = !hayResumen || estado.itinerario.length > 0;
    elementos.itemOrigen.hidden = !hayResumen;
    elementos.itemDestino.hidden = !hayResumen;

    estado.itinerario.forEach((parada, indice) => {
      const nodo = tplParadaItinerario.content.cloneNode(true);
      nodo.querySelector("[data-item-numero]").textContent = indice + 1;
      nodo.querySelector("[data-item-nombre]").textContent = parada.nombre;
      nodo.querySelector("[data-mover-arriba]").addEventListener("click", () => moverParada(indice, -1));
      nodo.querySelector("[data-mover-abajo]").addEventListener("click", () => moverParada(indice, 1));
      nodo.querySelector("[data-eliminar-parada]").addEventListener("click", () => eliminarParada(indice));
      elementos.itinerarioLista.insertBefore(nodo, elementos.itemDestino);
    });

    actualizarMapa();
    renderResumenAventura();
  }

  function actualizarMapa() {
    if (!estado.resumen || !elementos.mapa) return;

    const puntos = [
      { ...estado.resumen.origen },
      ...estado.itinerario,
      { ...estado.resumen.destino },
    ];

    RutaMapa.actualizarRuta(puntos);
  }

  function renderResumenAventura() {
    elementos.aventuraParadas.textContent = estado.itinerario.length;

    if (estado.resumen) {
      elementos.aventuraDistancia.textContent = `${estado.resumen.distancia_km} km`;
      elementos.aventuraTexto.textContent = estado.itinerario.length
        ? `Tu recorrido incluye ${estado.itinerario.length} parada${estado.itinerario.length === 1 ? "" : "s"} intermedia${estado.itinerario.length === 1 ? "" : "s"} y está listo para ajustarlas.`
        : "Agrega paradas desde \"Descubre en el camino\" para completar tu aventura.";
    } else {
      elementos.aventuraDistancia.textContent = "—";
      elementos.aventuraTexto.textContent = "Calcula una ruta y agrega paradas para ver el resumen de tu aventura.";
    }
  }

  async function guardarRuta() {
    if (!estado.resumen) {
      alert("Primero calcula una ruta antes de guardarla.");
      return;
    }

    const valores = RutaFormularios.obtenerValores();

    try {
      const respuesta = await fetch("/api/rutas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: valores.nombre || `${valores.origen} a ${valores.destino}`,
          origen: valores.origen,
          destino: valores.destino,
          presupuesto: valores.presupuesto,
          intereses: valores.intereses,
          resumen: estado.resumen,
          paradas: estado.itinerario,
        }),
      });

      if (!respuesta.ok) throw new Error("No se pudo guardar la ruta");

      await cargarRutasGuardadas();
      alert("Ruta guardada.");
    } catch (err) {
      console.error(err);
      alert("Ocurrió un error al guardar la ruta.");
    }
  }

  async function guardarItinerario() {
    if (!estado.resumen) {
      alert("Primero calcula una ruta antes de guardar el itinerario.");
      return;
    }
    await guardarRuta();
  }

  async function cargarRutasGuardadas() {
    if (!elementos.rutasGuardadasSelect) return;

    try {
      const respuesta = await fetch("/api/rutas");
      const datos = await respuesta.json();
      const rutas = datos.rutas || [];

      elementos.rutasGuardadasSelect.innerHTML = '<option value="">Elige una ruta guardada</option>';
      rutas.forEach((ruta) => {
        const opcion = document.createElement("option");
        opcion.value = ruta.id;
        opcion.textContent = ruta.nombre;
        elementos.rutasGuardadasSelect.appendChild(opcion);
      });
    } catch (err) {
      console.error("Error cargando rutas guardadas:", err);
    }
  }

  RutaFormularios.init((valores) => calcularRuta(valores));

  if (elementos.guardarRutaBtn) {
    elementos.guardarRutaBtn.addEventListener("click", guardarRuta);
  }

  if (elementos.guardarItinerarioBtn) {
    elementos.guardarItinerarioBtn.addEventListener("click", guardarItinerario);
  }

  cargarRutasGuardadas();
});
