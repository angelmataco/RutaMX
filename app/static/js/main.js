// Orquesta el flujo completo: formulario -> ruta -> sugerencias -> itinerario -> guardar.

document.addEventListener("DOMContentLoaded", () => {
  const estado = {
    lapsoActual: null, // null = todo el camino; si no, índice del lapso elegido
    tramosElegidos: null, // null = automático; si no, en cuántos tramos dividir el viaje
    propositos: {}, // { indiceDeTramo: "comida" | "turismo" | "descanso" } de los tramos personalizados
    horaSalidaAsumida: true,
    lapsos: [],
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

  const elementos = {
    resultados: document.querySelector("[data-resultados]"),
    mapa: document.querySelector("[data-map]"),
    stats: {
      distancia: document.querySelector('[data-stat="distancia"]'),
      tiempo: document.querySelector('[data-stat="tiempo"]'),
      costo: document.querySelector('[data-stat="costo"]'),
      paradas: document.querySelector('[data-stat="paradas"]'),
    },
    gastoDesglose: document.querySelector("[data-gasto-desglose]"),
    gastoIncluye: document.querySelector("[data-gasto-incluye]"),
    sugerenciasContenedor: document.querySelector("[data-sugerencias]"),
    lapsos: document.querySelector("[data-lapsos]"),
    tramosControl: document.querySelector("[data-tramos-control]"),
    tramosOpciones: document.querySelector("[data-tramos-opciones]"),
    tramosNota: document.querySelector("[data-tramos-nota]"),
    tramoProposito: document.querySelector("[data-tramo-proposito]"),
    tramoPropositoTitulo: document.querySelector("[data-tramo-proposito-titulo]"),
    tramoPropositoOpciones: document.querySelector("[data-tramo-proposito-opciones]"),
    guardarRutaBtn: document.querySelector("[data-guardar-ruta]"),
    verRutasBtn: document.querySelector("[data-ver-rutas-guardadas]"),
    modalRutas: document.querySelector("[data-modal-rutas]"),
    rutasContenido: document.querySelector("[data-rutas-contenido]"),
    itinerarioLista: document.querySelector("[data-itinerario-lista]"),
    itinerarioVacio: document.querySelector("[data-itinerario-vacio]"),
    itemOrigen: document.querySelector("[data-item-origen]"),
    itemDestino: document.querySelector("[data-item-destino]"),
    abrirGoogleMapsBtn: document.querySelector("[data-abrir-google-maps]"),
    enlacesTramos: document.querySelector("[data-enlaces-tramos]"),
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

  async function actualizarStatsPorRutaReal(resumenRuta) {
    if (!estado.resumen || !resumenRuta) return;

    const distanciaKm = Math.round((resumenRuta.totalDistance / 1000) * 10) / 10;
    const tiempoH = Math.round((resumenRuta.totalTime / 3600) * 100) / 100;

    // La ruta real (con las paradas) reemplaza la estimación inicial
    // origen->destino, así "Guardar ruta actual" guarda el dato correcto.
    estado.resumen = { ...estado.resumen, distancia_km: distanciaKm, tiempo_h: tiempoH };

    await recalcularGasto();
    renderResumenAventura();
  }

  // El gasto se recalcula en el servidor (una sola fuente de la fórmula)
  // cada vez que cambia algo que lo afecta: distancia real, paradas,
  // personas, hora de salida o los ajustes. De cada parada se deduce sola
  // si es para comer o para dormir.
  async function recalcularGasto() {
    if (!estado.resumen || estado.resumen.distancia_km == null) return;

    const ajustes = RutaFormularios.obtenerAjustes();
    try {
      const respuesta = await fetch("/api/gasto", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          distancia_km: estado.resumen.distancia_km,
          tiempo_h: estado.resumen.tiempo_h,
          ajustes,
          paradas: estado.itinerario,
          casetas_por_km: estado.resumen.casetas_por_km,
          casetas_fuente: estado.resumen.gasto && estado.resumen.gasto.casetas_fuente,
        }),
      });
      if (respuesta.ok) {
        const gasto = await respuesta.json();
        estado.resumen = { ...estado.resumen, gasto, costo_estimado: gasto.total, ajustes };
      }
    } catch (err) {
      console.error("Error recalculando el gasto:", err);
    }

    renderResumen(estado.resumen);
    marcarTiposDeParadas(estado.resumen.gasto && estado.resumen.gasto.paradas_detalle);
  }

  // Etiqueta cada parada del itinerario con lo que el sistema dedujo
  // ("🍽️ Comer · 13:10", "🛏️ Dormir · 21:00").
  function marcarTiposDeParadas(detalle) {
    const items = elementos.itinerarioLista.querySelectorAll("[data-item-parada]");
    items.forEach((item, i) => {
      const etiqueta = item.querySelector("[data-item-tipo]");
      const d = detalle && detalle[i];
      const partes = [];
      if (d && d.comida) partes.push("🍽️ Comer");
      if (d && d.hospedaje) partes.push("🛏️ Dormir");
      if (partes.length) {
        etiqueta.textContent = partes.join(" + ") + (d.hora_llegada ? ` · ${d.hora_llegada}` : "");
        etiqueta.hidden = false;
      } else {
        etiqueta.hidden = true;
      }
    });
  }

  let temporizadorRecalculo = null;
  function programarRecalculoDeGasto() {
    clearTimeout(temporizadorRecalculo);
    temporizadorRecalculo = setTimeout(recalcularGasto, 250);
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
          ajustes: RutaFormularios.obtenerAjustes(),
        }),
      });

      if (!respuesta.ok) {
        const error = await respuesta.json().catch(() => ({}));
        alert(error.error || "No se pudo calcular la ruta. Revisa el origen y destino.");
        return;
      }

      const resumen = await respuesta.json();
      resumen.ajustes = RutaFormularios.obtenerAjustes(); // se guardan con la ruta

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

      estado.lapsoActual = null; // un viaje nuevo empieza viendo todo el camino
      estado.tramosElegidos = null;
      estado.propositos = {};
      await cargarSugerencias(valores);
    } catch (err) {
      console.error("Error calculando la ruta:", err);
      alert("Ocurrió un error al calcular la ruta. Intenta de nuevo.");
    }
  }

  function renderResumen(resumen) {
    const gasto = resumen.gasto;
    elementos.stats.distancia.textContent = `${resumen.distancia_km} km`;
    elementos.stats.tiempo.textContent = formatoDuracion(resumen.tiempo_h);
    elementos.stats.costo.textContent = formatoMoneda(gasto ? gasto.total : resumen.costo_estimado);
    elementos.stats.paradas.textContent = resumen.paradas_estimadas;

    if (!gasto) {
      elementos.gastoDesglose.hidden = true;
      return;
    }

    const filas = [
      ["⛽ Gasolina", gasto.gasolina],
      [gasto.casetas_fuente === "ia" ? "🛣️ Casetas (estimado IA)" : "🛣️ Casetas (promedio)", gasto.casetas],
    ];
    if (gasto.num_comidas) filas.push([`🍽️ Comidas (${gasto.num_comidas})`, gasto.comidas]);
    if (gasto.num_noches) {
      filas.push([`🛏️ Hospedaje (${gasto.num_noches} ${gasto.num_noches === 1 ? "noche" : "noches"})`, gasto.hospedaje]);
    }
    filas.push(["🎒 Imprevistos y snacks", gasto.imprevistos]);

    elementos.gastoDesglose.innerHTML = "";
    filas.forEach(([texto, monto]) => {
      const li = document.createElement("li");
      const nombre = document.createElement("span");
      nombre.textContent = texto;
      const valor = document.createElement("strong");
      valor.textContent = formatoMoneda(monto);
      li.append(nombre, valor);
      elementos.gastoDesglose.appendChild(li);
    });
    elementos.gastoDesglose.hidden = false;

    const incluye = [];
    if (gasto.num_comidas) {
      incluye.push(`${gasto.num_comidas} ${gasto.num_comidas === 1 ? "comida" : "comidas"} para ${gasto.personas} ${gasto.personas === 1 ? "persona" : "personas"}`);
    }
    if (gasto.num_noches) {
      incluye.push(`${gasto.num_noches} ${gasto.num_noches === 1 ? "noche" : "noches"} de hospedaje`);
    }
    elementos.gastoIncluye.textContent = incluye.length
      ? `Incluye ${incluye.join(" y ")}. Puedes cambiarlo en «Ajustes de gasto».`
      : "Sin paradas para comer ni noches en el camino: solo gasolina, casetas e imprevistos. Puedes agregarlas en «Ajustes de gasto».";
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
      if (estado.lapsoActual !== null) query.set("lapso", String(estado.lapsoActual));
      if (estado.tramosElegidos !== null) query.set("tramos", String(estado.tramosElegidos));
      const personalizados = Object.entries(estado.propositos).map(([i, p]) => `${i}:${p}`);
      if (personalizados.length) query.set("propositos", personalizados.join(","));
      if (valores.horaSalida) query.set("hora_salida", valores.horaSalida);
      if (excluirIds.length) query.set("excluir", excluirIds.join(","));

      const respuesta = await fetch(`/api/sugerencias?${query.toString()}`);
      const datos = await respuesta.json();
      // Los lapsos (tramos de tiempo del viaje) los decide el servidor; solo
      // se actualizan cuando se pide "todo el camino".
      estado.lapsos = datos.lapsos || [];
      estado.horaSalidaAsumida = Boolean(datos.hora_salida_asumida);
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
    renderLapsos();
    mostrarSugerencias(tomarDelPool(MOSTRAR_SUGERENCIAS));
  }

  // Controles de los tramos del viaje: cuántos tramos (Automático, 2…6) y
  // una fila de botones, uno por tramo, con su hora del reloj. Los lapsos
  // salen solos de la duración de la ruta (desde 30 min después de salir
  // hasta 20 min antes de llegar) o del número de tramos que pida el usuario.
  function renderLapsos() {
    const contenedor = elementos.lapsos;
    if (!contenedor) return;

    const hayLapsos = estado.lapsos.length > 0;
    elementos.tramosControl.hidden = !hayLapsos;
    if (hayLapsos) renderControlDeTramos();

    if (estado.lapsos.length < 2) {
      contenedor.hidden = true;
      contenedor.innerHTML = "";
      elementos.tramoProposito.hidden = true;
      return;
    }

    const variosDias = estado.lapsos.some((l) => l.dia > 1 || l.cruza_noche);
    const opciones = [{ indice: null, texto: "Todo el camino", titulo: "" }].concat(
      estado.lapsos.map((l) => {
        const icono = iconoDeProposito(l.proposito, l.personalizado);
        const dia = variosDias ? `Día ${l.dia} · ` : "";
        const noche = l.cruza_noche ? " 🌙" : "";
        return {
          indice: l.indice,
          texto: `${icono}${dia}Tramo ${l.indice + 1} · ${l.reloj_desde} – ${l.reloj_hasta}${noche}`,
          titulo: `${formatoDuracion(l.desde_h)} a ${formatoDuracion(l.hasta_h)} de camino`,
          personalizado: l.personalizado,
        };
      })
    );

    contenedor.innerHTML = "";
    opciones.forEach(({ indice, texto, titulo, personalizado }) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className =
        "chip" + (indice === estado.lapsoActual ? " is-active" : "") + (personalizado ? " is-personalizado" : "");
      boton.textContent = texto;
      if (titulo) boton.title = titulo;
      boton.addEventListener("click", () => {
        if (indice === estado.lapsoActual) return;
        estado.lapsoActual = indice;
        cargarSugerencias(estado.sugerenciasValores);
      });
      contenedor.appendChild(boton);
    });
    contenedor.hidden = false;
    renderPropositoDelTramo();
  }

  // 🍽️ comer, 🛏️ dormir; el turismo solo lleva icono si el usuario lo eligió.
  function iconoDeProposito(proposito, personalizado) {
    if (proposito === "comida") return "🍽️ ";
    if (proposito === "descanso") return "🛏️ ";
    return personalizado && proposito === "turismo" ? "🏞️ " : "";
  }

  // Al tocar un tramo aparece esta fila: Automático · Comer · Turismo · Dormir.
  // "Dormir" solo se ofrece si el tramo termina después de las 20:00 o cruza la noche.
  function renderPropositoDelTramo() {
    const lapso = estado.lapsos.find((l) => l.indice === estado.lapsoActual);
    if (!lapso) {
      elementos.tramoProposito.hidden = true;
      return;
    }

    elementos.tramoPropositoTitulo.textContent = `¿Qué buscas en el tramo ${lapso.indice + 1}?`;
    const opciones = [
      { valor: null, texto: "Automático" },
      { valor: "comida", texto: "🍽️ Comer" },
      { valor: "turismo", texto: "🏞️ Turismo" },
    ];
    if (lapso.permite_dormir) opciones.push({ valor: "descanso", texto: "🛏️ Dormir" });

    elementos.tramoPropositoOpciones.innerHTML = "";
    opciones.forEach(({ valor, texto }) => {
      const activo = valor === null ? !lapso.personalizado : lapso.personalizado && lapso.proposito === valor;
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "chip" + (activo ? " is-active" : "");
      boton.textContent = texto;
      boton.addEventListener("click", () => {
        if (activo) return;
        if (valor === null) delete estado.propositos[lapso.indice];
        else estado.propositos[lapso.indice] = valor;
        cargarSugerencias(estado.sugerenciasValores);
      });
      elementos.tramoPropositoOpciones.appendChild(boton);
    });
    elementos.tramoProposito.hidden = false;
  }

  function renderControlDeTramos() {
    elementos.tramosOpciones.innerHTML = "";
    [null, 2, 3, 4, 5, 6].forEach((cuantos) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "chip" + (cuantos === estado.tramosElegidos ? " is-active" : "");
      boton.textContent = cuantos === null ? "Automático" : String(cuantos);
      boton.addEventListener("click", () => {
        if (cuantos === estado.tramosElegidos) return;
        estado.tramosElegidos = cuantos;
        estado.lapsoActual = null;
        estado.propositos = {}; // los tramos cambian: se reinician las elecciones
        cargarSugerencias(estado.sugerenciasValores);
      });
      elementos.tramosOpciones.appendChild(boton);
    });

    elementos.tramosNota.hidden = !estado.horaSalidaAsumida;
    elementos.tramosNota.textContent = "Sin hora de salida, los horarios suponen que sales a las 08:00.";
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
      elementos.sugerenciasContenedor.innerHTML =
        estado.lapsoActual === null
          ? '<p class="empty-state">No encontramos sugerencias para estos intereses todavía.</p>'
          : `<p class="empty-state">${mensajeSinLugaresEnTramo()}</p>`;
      elementos.verMasBtn.hidden = true;
      return;
    }

    lugares.forEach((lugar) => agregarCardSugerencia(lugar));
    elementos.verMasBtn.hidden = estado.sugerenciasPool.length === 0;
  }

  function mensajeSinLugaresEnTramo() {
    const pedido = estado.propositos[estado.lapsoActual];
    const que = { comida: "lugares para comer", descanso: "lugares para pasar la noche", turismo: "lugares de turismo" }[pedido];
    return que
      ? `No encontramos ${que} en este tramo. Prueba con otro tramo o déjalo en Automático.`
      : "No encontramos sugerencias en este tramo todavía. Prueba con otro tramo.";
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
      horasEl.textContent =
        `≈${formatoDuracion(lugar.horas_estimadas)} de camino` + (lugar.hora_llegada ? ` · llegas ${lugar.hora_llegada}` : "");
      horasEl.hidden = false;
    }

    const nota = nodo.querySelector("[data-lugar-descanso]");
    if (lugar.proposito === "comida") {
      nota.textContent = "🍽️ Buen lugar para comer";
      nota.hidden = false;
    } else if (lugar.proposito === "descanso") {
      nota.textContent = "🛏️ Buen lugar para pasar la noche";
      nota.hidden = false;
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
    estado.itinerario.push({
      id: lugar.id,
      nombre: lugar.nombre,
      lat: lugar.lat,
      lon: lugar.lon,
      intereses: lugar.intereses || [],
      horas_estimadas: lugar.horas_estimadas,
      proposito: lugar.proposito,
    });
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
      return false;
    }

    if (typeof RutaAuth !== "undefined" && !RutaAuth.obtenerUsuarioActual()) {
      RutaAuth.abrirModalLogin();
      return false;
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
          intereses: valores.intereses,
          resumen: estado.resumen,
          paradas: estado.itinerario,
        }),
      });

      if (respuesta.status === 401) {
        RutaAuth.abrirModalLogin();
        return false;
      }
      if (!respuesta.ok) throw new Error("No se pudo guardar la ruta");

      alert("Ruta guardada.");
      return true;
    } catch (err) {
      console.error(err);
      alert("Ocurrió un error al guardar la ruta.");
      return false;
    }
  }

  async function guardarItinerario() {
    if (!estado.resumen) {
      alert("Primero calcula una ruta antes de guardar el itinerario.");
      return;
    }
    const guardado = await guardarRuta();
    if (!guardado) return;
    await descargarPdfItinerario();
  }

  async function abrirEnGoogleMaps() {
    if (!estado.resumen) {
      alert("Primero calcula una ruta para abrirla en Google Maps.");
      return;
    }
    const valores = RutaFormularios.obtenerValores();

    try {
      const respuesta = await fetch("/api/itinerario/enlaces", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origen: valores.origen,
          destino: valores.destino,
          resumen: estado.resumen,
          paradas: estado.itinerario,
        }),
      });
      if (!respuesta.ok) throw new Error("No se pudo armar el enlace");
      const { enlaces } = await respuesta.json();

      // Un solo tramo: se abre directo. Varios (más de 9 paradas): se
      // listan para abrirlos en orden.
      elementos.enlacesTramos.innerHTML = "";
      if (enlaces.length === 1) {
        elementos.enlacesTramos.hidden = true;
        window.open(enlaces[0], "_blank", "noopener");
        return;
      }
      enlaces.forEach((enlace, i) => {
        const a = document.createElement("a");
        a.href = enlace;
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = `Tramo ${i + 1} de ${enlaces.length} →`;
        elementos.enlacesTramos.appendChild(a);
      });
      elementos.enlacesTramos.hidden = false;
    } catch (err) {
      console.error("Error armando el enlace de Google Maps:", err);
      alert("No se pudo armar el enlace de Google Maps.");
    }
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

  // ---- "Mis rutas guardadas" (ventana flotante con burbujas) ----

  let reabrirRutasTrasLogin = false;

  function mensajeRutas(titulo, texto, botones = []) {
    const caja = document.createElement("div");
    caja.className = "rutas-vacio";
    caja.innerHTML = `<p class="rutas-vacio__titulo"></p><p class="card__note"></p>`;
    caja.querySelector(".rutas-vacio__titulo").textContent = titulo;
    caja.querySelector(".card__note").textContent = texto;
    if (botones.length) {
      const fila = document.createElement("div");
      fila.className = "rutas-vacio__botones";
      botones.forEach(({ texto: t, clase, alClic }) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `btn ${clase}`;
        btn.textContent = t;
        btn.addEventListener("click", alClic);
        fila.appendChild(btn);
      });
      caja.appendChild(fila);
    }
    return caja;
  }

  function pedirSesion() {
    reabrirRutasTrasLogin = true;
    elementos.modalRutas.close();
  }

  function crearBurbujaRuta(ruta) {
    const resumen = ruta.resumen || {};
    const datos = [];
    if (resumen.distancia_km != null) datos.push(`${resumen.distancia_km} km`);
    if (resumen.tiempo_h != null) datos.push(formatoDuracion(resumen.tiempo_h));
    const numParadas = (ruta.paradas || []).length;
    datos.push(`${numParadas} ${numParadas === 1 ? "parada" : "paradas"}`);

    const burbuja = document.createElement("button");
    burbuja.type = "button";
    burbuja.className = "ruta-burbuja";
    burbuja.innerHTML = `
      <span class="ruta-burbuja__nombre"></span>
      <span class="ruta-burbuja__trayecto"></span>
      <span class="ruta-burbuja__datos"></span>`;
    burbuja.querySelector(".ruta-burbuja__nombre").textContent = ruta.nombre;
    burbuja.querySelector(".ruta-burbuja__trayecto").textContent = `${ruta.origen} → ${ruta.destino}`;
    burbuja.querySelector(".ruta-burbuja__datos").textContent = datos.join(" · ");
    burbuja.addEventListener("click", () => {
      elementos.modalRutas.close();
      abrirRutaGuardada(ruta);
    });
    return burbuja;
  }

  async function abrirRutasGuardadas() {
    if (!elementos.modalRutas) return;
    const cont = elementos.rutasContenido;
    cont.innerHTML = "";

    const haySesion = typeof RutaAuth === "undefined" || Boolean(RutaAuth.obtenerUsuarioActual());
    if (!haySesion) {
      cont.appendChild(
        mensajeRutas("Aún no has iniciado sesión", "Inicia sesión para ver las rutas que planeaste antes.", [
          { texto: "Iniciar sesión", clase: "btn--primary", alClic: () => { pedirSesion(); RutaAuth.abrirModalLogin(); } },
          { texto: "Crear cuenta", clase: "btn--ghost", alClic: () => { pedirSesion(); RutaAuth.abrirModalRegistro(); } },
        ])
      );
      elementos.modalRutas.showModal();
      return;
    }

    cont.appendChild(mensajeRutas("Cargando tus rutas…", ""));
    elementos.modalRutas.showModal();

    try {
      const respuesta = await fetch("/api/rutas");
      cont.innerHTML = "";
      if (respuesta.status === 401) {
        cont.appendChild(mensajeRutas("Tu sesión expiró", "Vuelve a iniciar sesión para ver tus rutas.", [
          { texto: "Iniciar sesión", clase: "btn--primary", alClic: () => { pedirSesion(); RutaAuth.abrirModalLogin(); } },
        ]));
        return;
      }
      const { rutas = [] } = await respuesta.json();
      if (!rutas.length) {
        cont.appendChild(mensajeRutas("Aún no tienes rutas guardadas", "Planea un viaje y toca «Guardar ruta actual» para verlo aquí."));
        return;
      }
      const rejilla = document.createElement("div");
      rejilla.className = "rutas-burbujas";
      rutas.forEach((ruta) => rejilla.appendChild(crearBurbujaRuta(ruta)));
      cont.appendChild(rejilla);
    } catch (err) {
      console.error("Error cargando rutas guardadas:", err);
      cont.innerHTML = "";
      cont.appendChild(mensajeRutas("No se pudieron cargar tus rutas", "Intenta de nuevo en un momento."));
    }
  }

  // Devuelve al formulario las preferencias de gasto con las que se guardó la ruta.
  function restaurarAjustes(form, ajustes) {
    const poner = (nombre, valor) => {
      const campo = document.querySelector(`[name="${nombre}"]`);
      campo.value = valor ?? "";
      campo.dispatchEvent(new Event("input", { bubbles: true }));
    };
    poner("personas", ajustes.personas);
    poner("comidas", ajustes.comidas);
    poner("noches", ajustes.noches);
    document.querySelectorAll("[data-ajuste]").forEach((chip) => {
      chip.classList.toggle("is-active", ajustes[chip.dataset.ajuste] === chip.dataset.valor);
    });
    RutaFormularios.actualizarBotonAjustes();
    const hora = ajustes.hora_salida || "";
    form.querySelector("[data-time-hidden]").value = hora;
    form.querySelector("[data-time-display]").textContent = hora || "Elegir hora";
  }

  // Restaura una ruta guardada: rellena el formulario y muestra mapa,
  // resumen e itinerario tal como se guardaron.
  function abrirRutaGuardada(ruta) {
    const form = document.getElementById("hero-form");
    form.querySelector('[name="origen"]').value = ruta.origen || "";
    form.querySelector('[name="destino"]').value = ruta.destino || "";
    form.querySelector('[name="nombre"]').value = ruta.nombre || "";
    restaurarAjustes(form, (ruta.resumen && ruta.resumen.ajustes) || {});
    form.querySelectorAll("[data-interes]").forEach((chip) => {
      chip.classList.toggle("is-active", (ruta.intereses || []).includes(chip.dataset.interes));
    });

    window.RutaApp.aplicarPlanIA({ resumen: ruta.resumen, paradas: ruta.paradas || [] });
    estado.lapsoActual = null;
    estado.tramosElegidos = null;
    estado.propositos = {};
    cargarSugerencias(RutaFormularios.obtenerValores());
  }

  function normalizarAcentos(texto) {
    return normalizarClave(texto)
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "");
  }

  // ¿`clave` (ya sin acentos ni mayúsculas) aparece en `nombre` como palabra(s)
  // completa(s)? "leon" está en "Centro histórico de León", pero "leo" no.
  function contienePalabraCompleta(nombre, clave) {
    const limpio = (texto) => ` ${normalizarAcentos(texto).replace(/[^a-z0-9ñ]+/g, " ").trim()} `;
    return limpio(nombre).includes(limpio(clave));
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

        // 1) Los nombres que EMPIEZAN con lo escrito (se filtran letra por
        //    letra). `nombres` ya viene ordenado por importancia (ciudades
        //    grandes primero); si lo escrito es exactamente un nombre, ese
        //    sube al primer lugar.
        // 2) Cuando lo escrito ya es una palabra completa (ej. "leon",
        //    "mexico"), se agregan también los nombres que la contienen,
        //    como "Centro histórico de León" o "Ciudad de México".
        const conPrefijo = nombres.filter((nombre) => normalizarAcentos(nombre).startsWith(clave));
        conPrefijo.sort((a, b) => Number(normalizarAcentos(b) === clave) - Number(normalizarAcentos(a) === clave));

        const yaIncluidos = new Set(conPrefijo);
        const conLaPalabra = nombres.filter(
          (nombre) => !yaIncluidos.has(nombre) && contienePalabraCompleta(nombre, clave)
        );

        coincidencias = [...conPrefijo, ...conLaPalabra].slice(0, MAX_SUGERENCIAS);

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

  // Todo fluye: al aplicar ajustes o cambiar personas / hora de salida se
  // recalcula el gasto; la hora de salida también cambia las sugerencias.
  document.addEventListener("ajustes-gasto-aplicados", recalcularGasto);
  document.getElementById("hero-form").addEventListener("change", (evento) => {
    if (evento.target.name === "personas") programarRecalculoDeGasto();
    if (evento.target.name === "hora_salida" && estado.resumen) {
      programarRecalculoDeGasto();
      cargarSugerencias(RutaFormularios.obtenerValores());
    }
  });

  if (elementos.abrirGoogleMapsBtn) {
    elementos.abrirGoogleMapsBtn.addEventListener("click", abrirEnGoogleMaps);
  }

  if (elementos.guardarItinerarioBtn) {
    elementos.guardarItinerarioBtn.addEventListener("click", guardarItinerario);
  }

  if (elementos.verMasBtn) {
    elementos.verMasBtn.addEventListener("click", verMasSugerencias);
  }

  if (elementos.verRutasBtn) {
    elementos.verRutasBtn.addEventListener("click", abrirRutasGuardadas);
  }

  // Si el usuario inició sesión desde la ventana de rutas, se las muestra
  // en cuanto entra.
  if (typeof RutaAuth !== "undefined") {
    RutaAuth.alIniciarSesion(() => {
      if (reabrirRutasTrasLogin) {
        reabrirRutasTrasLogin = false;
        abrirRutasGuardadas();
      }
    });
  }
  cargarDatalistDestinos();

  // Punto de entrada para "Planear con IA" (planificador_ia.js): aplica
  // la opción elegida reusando el mismo render que el flujo manual, para
  // no duplicar lógica de mapa/resumen/itinerario.
  window.RutaApp = {
    aplicarPlanIA(opcion) {
      // Lo que la IA aprendió en la conversación (origen, destino, personas,
      // hora de salida, intereses) pasa al formulario para que todo lo demás
      // (gasto, tramos, sugerencias) siga usándolo.
      const form = document.getElementById("hero-form");
      form.querySelector('[name="origen"]').value = opcion.resumen.origen.nombre;
      form.querySelector('[name="destino"]').value = opcion.resumen.destino.nombre;
      if (opcion.resumen.origen.nombre && opcion.resumen.destino.nombre) {
        form.querySelector('[name="nombre"]').value = `${opcion.resumen.origen.nombre} a ${opcion.resumen.destino.nombre}`;
      }
      form.querySelectorAll("[data-interes]").forEach((chip) => {
        chip.classList.toggle("is-active", (opcion.intereses || []).includes(chip.dataset.interes));
      });
      restaurarAjustes(form, opcion.ajustes || {});

      estado.resumen = opcion.resumen;
      estado.itinerario = opcion.paradas.map((p) => ({
        id: p.id,
        nombre: p.nombre,
        lat: p.lat,
        lon: p.lon,
        intereses: p.intereses || [],
        horas_estimadas: p.horas_estimadas,
        proposito: p.proposito,
      }));
      estado.ultimoOrigenDestino = { origen: opcion.resumen.origen.nombre, destino: opcion.resumen.destino.nombre };

      elementos.resultados.hidden = false;
      if (elementos.mapa) RutaMapa.invalidarTamano();

      renderResumen(estado.resumen);
      renderItinerarioBase(estado.resumen);

      elementos.resultados.scrollIntoView({ behavior: "smooth" });

      // Las sugerencias y los tramos se arman con los datos de este plan.
      estado.lapsoActual = null;
      estado.tramosElegidos = null;
      estado.propositos = {};
      cargarSugerencias(RutaFormularios.obtenerValores());
    },
  };
});
