// Orquesta el flujo completo: formulario -> ruta -> sugerencias -> itinerario -> guardar.

document.addEventListener("DOMContentLoaded", () => {
  const estado = {
    resumen: null,
    itinerario: [], // lista de { id, nombre }
    ultimoOrigenDestino: null, // { origen, destino } del último viaje calculado
    sugerenciasPool: [], // lugares ya traídos del servidor, listos para mostrarse
    sugerenciasVistosIds: new Set(), // para no repetir con "excluir" al pedir más
    sugerenciasValores: null, // últimos valores del formulario, para "ver más"
  };

  function normalizarClave(texto) {
    return (texto || "").trim().toLowerCase();
  }

  const MOSTRAR_SUGERENCIAS = 4;

  // Mismos valores que app/services/route_service.py — si cambian ahí,
  // cambian aquí también.
  const COSTO_POR_KM = 4.5;
  const COSTO_BASE_HOSPEDAJE = 600;

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
    verMasBtn: document.querySelector("[data-ver-mas]"),
    aventuraParadas: document.querySelector("[data-aventura-paradas]"),
    aventuraDistancia: document.querySelector("[data-aventura-distancia]"),
    aventuraTexto: document.querySelector("[data-aventura-texto]"),
  };

  const tplSugerencia = document.getElementById("tpl-sugerencia");
  const tplParadaItinerario = document.getElementById("tpl-parada-itinerario");

  if (elementos.mapa) {
    RutaMapa.init("mapa");
    RutaMapa.alEncontrarRuta(actualizarStatsPorRutaReal);
  }

  function actualizarStatsPorRutaReal(resumenRuta) {
    if (!estado.resumen || !resumenRuta) return;

    const distanciaKm = Math.round((resumenRuta.totalDistance / 1000) * 10) / 10;
    const tiempoH = Math.round((resumenRuta.totalTime / 3600) * 100) / 100;
    const costoEstimado = Math.round(
      distanciaKm * COSTO_POR_KM + estado.resumen.paradas_estimadas * COSTO_BASE_HOSPEDAJE
    );
    const presupuestoSuficiente = Boolean(estado.resumen.presupuesto) && estado.resumen.presupuesto >= costoEstimado;

    // La ruta real (con las paradas) reemplaza la estimación inicial
    // origen->destino, así "Guardar ruta actual" guarda el dato correcto.
    estado.resumen = {
      ...estado.resumen,
      distancia_km: distanciaKm,
      tiempo_h: tiempoH,
      costo_estimado: costoEstimado,
      presupuesto_suficiente: presupuestoSuficiente,
    };

    renderResumen(estado.resumen);
    renderResumenAventura();
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

      const esMismoViaje =
        estado.ultimoOrigenDestino &&
        normalizarClave(estado.ultimoOrigenDestino.origen) === normalizarClave(valores.origen) &&
        normalizarClave(estado.ultimoOrigenDestino.destino) === normalizarClave(valores.destino);

      estado.resumen = resumen;
      // Solo se reinicia el itinerario si es un viaje nuevo (origen o
      // destino distintos). Si solo cambiaron los filtros de intereses,
      // las paradas ya elegidas se conservan.
      if (!esMismoViaje) {
        estado.itinerario = [];
      }
      estado.ultimoOrigenDestino = { origen: valores.origen, destino: valores.destino };

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

  async function pedirSugerencias(valores, limite, excluirIds) {
    try {
      const query = new URLSearchParams({
        intereses: (valores.intereses || []).join(","),
        origen: valores.origen || "",
        destino: valores.destino || "",
        limite: String(limite),
      });
      if (valores.horasMax) query.set("horas_max", valores.horasMax);
      if (excluirIds.length) query.set("excluir", excluirIds.join(","));

      const respuesta = await fetch(`/api/sugerencias?${query.toString()}`);
      const datos = await respuesta.json();
      return datos.sugerencias || [];
    } catch (err) {
      console.error("Error cargando sugerencias:", err);
      return [];
    }
  }

  async function cargarSugerencias(valores) {
    estado.sugerenciasValores = valores;
    // Las paradas que ya están en el itinerario no deben ofrecerse de
    // nuevo como sugerencia (evita agregarlas dos veces al refrescar
    // filtros sobre el mismo viaje).
    estado.sugerenciasVistosIds = new Set(estado.itinerario.map((parada) => parada.id));
    elementos.sugerenciasContenedor.innerHTML = '<p class="empty-state">Buscando ideas para tu recorrido…</p>';
    elementos.verMasBtn.hidden = true;

    // Se pide un lote grande una sola vez; la grilla solo muestra 4 a la
    // vez y va tomando del resto, así siempre hay con qué reponer.
    estado.sugerenciasPool = await pedirSugerencias(valores, 16, Array.from(estado.sugerenciasVistosIds));
    mostrarSugerencias(tomarDelPool(MOSTRAR_SUGERENCIAS));
  }

  function tomarDelPool(cantidad) {
    const tomados = estado.sugerenciasPool.splice(0, cantidad);
    tomados.forEach((lugar) => estado.sugerenciasVistosIds.add(lugar.id));
    return tomados;
  }

  async function ampliarPool() {
    if (!estado.sugerenciasValores) return;
    const nuevoLote = await pedirSugerencias(estado.sugerenciasValores, 16, Array.from(estado.sugerenciasVistosIds));
    estado.sugerenciasPool.push(...nuevoLote);
  }

  function mostrarSugerencias(lugares) {
    elementos.sugerenciasContenedor.innerHTML = "";

    if (!lugares.length) {
      elementos.sugerenciasContenedor.innerHTML = '<p class="empty-state">No encontramos sugerencias para estos intereses todavía.</p>';
      elementos.verMasBtn.hidden = true;
      return;
    }

    lugares.forEach((lugar) => agregarCardSugerencia(lugar));
    elementos.verMasBtn.hidden = estado.sugerenciasPool.length === 0;
  }

  function agregarCardSugerencia(lugar) {
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
      reponerSugerencia(card);
    });

    nodo.querySelector("[data-descartar]").addEventListener("click", () => {
      reponerSugerencia(card);
    });

    elementos.sugerenciasContenedor.appendChild(nodo);
  }

  async function reponerSugerencia(card) {
    card.remove();

    if (!estado.sugerenciasPool.length) {
      await ampliarPool();
    }

    const [siguiente] = tomarDelPool(1);
    if (siguiente) agregarCardSugerencia(siguiente);

    if (!elementos.sugerenciasContenedor.children.length) {
      elementos.sugerenciasContenedor.innerHTML = '<p class="empty-state">No encontramos más sugerencias para estos intereses.</p>';
    }
    elementos.verMasBtn.hidden = estado.sugerenciasPool.length === 0;
  }

  async function verMasSugerencias() {
    if (estado.sugerenciasPool.length < MOSTRAR_SUGERENCIAS) {
      await ampliarPool();
    }
    mostrarSugerencias(tomarDelPool(MOSTRAR_SUGERENCIAS));
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
    await descargarPdfItinerario();
  }

  async function descargarPdfItinerario() {
    const valores = RutaFormularios.obtenerValores();

    try {
      const respuesta = await fetch("/api/itinerario/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: valores.nombre || `${valores.origen} a ${valores.destino}`,
          origen: valores.origen,
          destino: valores.destino,
          resumen: estado.resumen,
          paradas: estado.itinerario,
        }),
      });

      if (!respuesta.ok) throw new Error("No se pudo generar el PDF");

      const blob = await respuesta.blob();
      const url = URL.createObjectURL(blob);
      const enlace = document.createElement("a");
      enlace.href = url;
      enlace.download = `${valores.nombre || "itinerario"}.pdf`;
      document.body.appendChild(enlace);
      enlace.click();
      enlace.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Error generando el PDF:", err);
      alert("La ruta se guardó, pero no se pudo generar el PDF del itinerario.");
    }
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

  function normalizarAcentos(texto) {
    return normalizarClave(texto)
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "");
  }

  function initAutocompletado(nombres) {
    const MAX_SUGERENCIAS = 8;

    document.querySelectorAll("[data-autocomplete-destino]").forEach((input) => {
      const lista = input.parentElement.querySelector("[data-autocomplete-lista]");
      if (!lista) return;

      let coincidencias = [];
      let indiceActivo = -1;

      function cerrar() {
        lista.hidden = true;
        lista.innerHTML = "";
        coincidencias = [];
        indiceActivo = -1;
      }

      function marcarActivo() {
        Array.from(lista.children).forEach((li, i) => li.classList.toggle("is-activa", i === indiceActivo));
      }

      function elegir(nombre) {
        input.value = nombre;
        cerrar();
      }

      function actualizar() {
        const clave = normalizarAcentos(input.value);
        if (!clave) {
          cerrar();
          return;
        }

        coincidencias = nombres.filter((nombre) => normalizarAcentos(nombre).includes(clave)).slice(0, MAX_SUGERENCIAS);

        if (!coincidencias.length) {
          cerrar();
          return;
        }

        indiceActivo = 0;
        lista.innerHTML = "";
        coincidencias.forEach((nombre) => {
          const item = document.createElement("li");
          item.className = "autocomplete-item";
          item.textContent = nombre;
          item.addEventListener("mousedown", (evento) => {
            evento.preventDefault(); // evita el blur antes del click
            elegir(nombre);
          });
          lista.appendChild(item);
        });
        marcarActivo();
        lista.hidden = false;
      }

      input.addEventListener("input", actualizar);

      input.addEventListener("keydown", (evento) => {
        if (lista.hidden || !coincidencias.length) return;

        if (evento.key === "ArrowDown") {
          evento.preventDefault();
          indiceActivo = (indiceActivo + 1) % coincidencias.length;
          marcarActivo();
        } else if (evento.key === "ArrowUp") {
          evento.preventDefault();
          indiceActivo = (indiceActivo - 1 + coincidencias.length) % coincidencias.length;
          marcarActivo();
        } else if (evento.key === "Enter") {
          // Completa con la sugerencia resaltada en vez de enviar el
          // formulario de inmediato.
          evento.preventDefault();
          elegir(coincidencias[indiceActivo]);
        } else if (evento.key === "Tab") {
          // Completa con la sugerencia resaltada y deja que el Tab
          // continúe moviendo el foco al siguiente campo con normalidad.
          elegir(coincidencias[indiceActivo]);
        } else if (evento.key === "Escape") {
          cerrar();
        }
      });

      input.addEventListener("blur", cerrar);
    });
  }

  async function cargarDatalistDestinos() {
    try {
      const respuesta = await fetch("/api/destinos/nombres");
      const datos = await respuesta.json();
      initAutocompletado(datos.nombres || []);
    } catch (err) {
      console.error("Error cargando el autocompletado de destinos:", err);
    }
  }

  RutaFormularios.init((valores) => calcularRuta(valores));

  if (elementos.guardarRutaBtn) {
    elementos.guardarRutaBtn.addEventListener("click", guardarRuta);
  }

  if (elementos.guardarItinerarioBtn) {
    elementos.guardarItinerarioBtn.addEventListener("click", guardarItinerario);
  }

  if (elementos.verMasBtn) {
    elementos.verMasBtn.addEventListener("click", verMasSugerencias);
  }

  cargarRutasGuardadas();
  cargarDatalistDestinos();
});
