// Orquesta el flujo completo: formulario -> ruta -> sugerencias -> itinerario -> guardar.

document.addEventListener("DOMContentLoaded", () => {
  const estado = {
    lapsoActual: null, // null = todo el camino; si no, índice del lapso elegido
    tramosElegidos: null, // null = automático; si no, en cuántos tramos dividir el viaje
    tramosMasAbierto: false, // ¿está abierto el campo de "Más" (11 a 30 tramos)?
    propositos: {}, // { indiceDeTramo: "comida" | "turismo" | "descanso" } de los tramos personalizados
    horaSalidaAsumida: true,
    lapsos: [],
    resumen: null,
    itinerario: [], // lista de { id, nombre }
    ultimoOrigenDestino: null, // { origen, destino } del último viaje calculado
    sugerenciasLista: [], // sugerencias del lote actual, en orden de línea de tiempo
    sugerenciasExpandido: false, // ¿se ven todas o solo las primeras?
    sugerenciasVistosIds: new Set(), // para no repetir con "excluir" al pedir más
    sugerenciasValores: null, // últimos valores del formulario, para "ver más"
  };

  function normalizarClave(texto) {
    return (texto || "").trim().toLowerCase();
  }

  // Cuántas sugerencias se ven de entrada (igual que TAMANO_PAGINA_SUGERENCIAS en
  // ai_service.py) y cuántas se piden en cada lote. El resto se despliega con "Ver más".
  const MOSTRAR_SUGERENCIAS = 5;
  const TAMANO_LOTE = 40; // margen de sobra para reponer recomendadas sin volver a pedir al servidor

  const elementos = {
    resultados: document.querySelector("[data-resultados]"),
    cargandoRuta: document.querySelector("[data-cargando-ruta]"),
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
    tramosMas: document.querySelector("[data-tramos-mas]"),
    tramosMasNumero: document.querySelector("[data-tramos-mas-numero]"),
    tramosMasAplicar: document.querySelector("[data-tramos-mas-aplicar]"),
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
  // (icono comer + "Comer · 13:10", icono dormir + "Dormir · 21:00").
  function marcarTiposDeParadas(detalle) {
    const items = elementos.itinerarioLista.querySelectorAll("[data-item-parada]");
    items.forEach((item, i) => {
      const etiqueta = item.querySelector("[data-item-tipo]");
      const d = detalle && detalle[i];
      const partes = [];
      if (d && d.comida) partes.push(RutaIconos.nodo("comer", "Comer", 14));
      if (d && d.hospedaje) partes.push(RutaIconos.nodo("dormir", "Dormir", 14));
      if (partes.length) {
        etiqueta.replaceChildren();
        partes.forEach((parte, k) => {
          if (k) etiqueta.append(" + ");
          etiqueta.append(parte);
        });
        if (d.hora_llegada) etiqueta.append(` · ${d.hora_llegada}`);
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

  // Al pulsar "Planea mi ruta" la página se abre y baja al instante, sin esperar al
  // servidor: mientras llegan los datos se ve un orbe de "calculando" y se puede seguir
  // navegando. `idCalculo` descarta respuestas viejas si se vuelve a pulsar el botón.
  let idCalculo = 0;
  let orbeCalculando = null;
  let gridMapa = null; // cuadrícula "grid reveal" sobre el mapa mientras se calcula

  function empezarCarga() {
    const yaHabiaResultados = !elementos.resultados.hidden;
    elementos.resultados.hidden = false;
    elementos.resultados.classList.add("is-cargando");
    if (elementos.mapa) RutaMapa.invalidarTamano();
    if (elementos.cargandoRuta) {
      elementos.cargandoRuta.hidden = false;
      if (orbeCalculando) orbeCalculando.destruir();
      orbeCalculando = RutaEfectos.orbe.montar(elementos.cargandoRuta, { estado: "thinking", tamano: 120, etiqueta: "Calculando tu ruta…" });
    }
    if (elementos.mapa) {
      if (gridMapa) gridMapa.quitar();
      gridMapa = RutaEfectos.gridReveal.montar(elementos.mapa, { duracion: 4500, texto: "Trazando tu ruta…" });
    }
    elementos.sugerenciasContenedor.innerHTML = '<div class="cargando-orbe"></div>';
    RutaEfectos.orbe.montar(elementos.sugerenciasContenedor.firstChild, { estado: "thinking", tamano: 120, etiqueta: "Buscando ideas para tu recorrido…" });
    elementos.verMasBtn.hidden = true;
    elementos.resultados.scrollIntoView({ behavior: "smooth" });
    return yaHabiaResultados;
  }

  // `conExito`: llegaron los datos, así que la cuadrícula del mapa se disuelve en ola;
  // si no, se quita de golpe.
  function terminarCarga(conExito = false) {
    elementos.resultados.classList.remove("is-cargando");
    if (gridMapa) {
      if (conExito) gridMapa.revelar();
      else gridMapa.quitar();
      gridMapa = null;
    }
    if (elementos.cargandoRuta) elementos.cargandoRuta.hidden = true;
    if (orbeCalculando) {
      orbeCalculando.destruir();
      orbeCalculando = null;
    }
  }

  async function calcularRuta(valores) {
    const miCalculo = ++idCalculo;
    const yaHabiaResultados = empezarCarga();
    const abortar = () => {
      terminarCarga();
      if (!yaHabiaResultados) elementos.resultados.hidden = true; // no había nada que mostrar todavía
    };
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

      if (miCalculo !== idCalculo) return; // se pulsó de nuevo: manda la respuesta más reciente
      if (!respuesta.ok) {
        const error = await respuesta.json().catch(() => ({}));
        abortar();
        alert(error.error || "No se pudo calcular la ruta. Revisa el origen y destino.");
        return;
      }

      const resumen = await respuesta.json();
      if (miCalculo !== idCalculo) return;
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

      terminarCarga(true);
      if (elementos.mapa) RutaMapa.invalidarTamano();

      renderResumen(resumen);
      renderItinerarioBase(resumen);

      estado.lapsoActual = null; // un viaje nuevo empieza viendo todo el camino
      estado.tramosElegidos = null;
      estado.tramosMasAbierto = false;
      estado.propositos = {};
      await cargarSugerencias(valores);
    } catch (err) {
      console.error("Error calculando la ruta:", err);
      if (miCalculo === idCalculo) {
        abortar();
        alert("Ocurrió un error al calcular la ruta. Intenta de nuevo.");
      }
    }
  }

  function renderResumen(resumen) {
    const gasto = resumen.gasto;
    // Los números del resumen "ruedan" hasta su nuevo valor (efectos/contador.js).
    RutaEfectos.contador.set(elementos.stats.distancia, `${resumen.distancia_km} km`);
    RutaEfectos.contador.set(elementos.stats.tiempo, formatoDuracion(resumen.tiempo_h));
    RutaEfectos.contador.set(elementos.stats.costo, formatoMoneda(gasto ? gasto.total : resumen.costo_estimado));
    RutaEfectos.contador.set(elementos.stats.paradas, String(resumen.paradas_estimadas));

    if (!gasto) {
      elementos.gastoDesglose.hidden = true;
      return;
    }

    const filas = [
      ["gasolina", "Gasolina", gasto.gasolina],
      ["casetas", gasto.casetas_fuente === "ia" ? "Casetas (estimado IA)" : "Casetas (promedio)", gasto.casetas],
    ];
    if (gasto.num_comidas) filas.push(["comer", `Comidas (${gasto.num_comidas})`, gasto.comidas]);
    if (gasto.num_noches) {
      filas.push(["dormir", `Hospedaje (${gasto.num_noches} ${gasto.num_noches === 1 ? "noche" : "noches"})`, gasto.hospedaje]);
    }
    filas.push(["mochila", "Imprevistos y snacks", gasto.imprevistos]);

    elementos.gastoDesglose.innerHTML = "";
    filas.forEach(([icono, texto, monto]) => {
      const li = document.createElement("li");
      const nombre = RutaIconos.nodo(icono, texto, 18);
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
      // En automático, los tramos son las "Paradas sugeridas" del resumen del viaje, para
      // que ambos números coincidan. Si el usuario elige un número, manda el suyo.
      const tramosAUsar = estado.tramosElegidos !== null ? estado.tramosElegidos : estado.resumen && estado.resumen.paradas_estimadas;
      if (tramosAUsar) query.set("tramos", String(tramosAUsar));
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
    elementos.sugerenciasContenedor.innerHTML = '<div class="cargando-orbe"></div>';
    RutaEfectos.orbe.montar(elementos.sugerenciasContenedor.firstChild, {
      estado: "thinking",
      tamano: 120,
      etiqueta: "Buscando ideas para tu recorrido…",
    });
    elementos.verMasBtn.hidden = true;

    // Se pide un lote de una vez; ya viene ordenado como línea de tiempo.
    estado.sugerenciasLista = await pedirSugerencias(valores, TAMANO_LOTE, Array.from(estado.sugerenciasVistosIds));
    estado.sugerenciasExpandido = false;
    renderLapsos();
    renderSugerencias();
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
        return {
          indice: l.indice,
          icono,
          noche: Boolean(l.cruza_noche),
          texto: `${dia}Tramo ${l.indice + 1} · ${l.reloj_desde} – ${l.reloj_hasta}`,
          titulo: `${formatoDuracion(l.desde_h)} a ${formatoDuracion(l.hasta_h)} de camino`,
          personalizado: l.personalizado,
        };
      })
    );

    contenedor.innerHTML = "";
    opciones.forEach(({ indice, texto, titulo, personalizado, icono, noche }) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className =
        "chip" + (indice === estado.lapsoActual ? " is-active" : "") + (personalizado ? " is-personalizado" : "");
      if (icono) boton.append(RutaIconos.nodo(icono, "", 16), " ");
      boton.append(texto);
      if (noche) boton.append(" ", RutaIconos.nodo("noche", "", 16));
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

  // Comer y dormir siempre llevan icono; el turismo solo si el usuario lo eligió.
  // Devuelve el nombre del icono (o null).
  function iconoDeProposito(proposito, personalizado) {
    if (proposito === "comida") return "comer";
    if (proposito === "descanso") return "dormir";
    return personalizado && proposito === "turismo" ? "turismo" : null;
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
      { valor: "comida", texto: "Comer", icono: "comer" },
      { valor: "turismo", texto: "Turismo", icono: "turismo" },
    ];
    if (lapso.permite_dormir) opciones.push({ valor: "descanso", texto: "Dormir", icono: "dormir" });

    elementos.tramoPropositoOpciones.innerHTML = "";
    opciones.forEach(({ valor, texto, icono }) => {
      const activo = valor === null ? !lapso.personalizado : lapso.personalizado && lapso.proposito === valor;
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "chip" + (activo ? " is-active" : "");
      if (icono) boton.append(RutaIconos.nodo(icono, "", 16), " ");
      boton.append(texto);
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

  // Botones rápidos hasta 10 tramos; "Más" abre un campo para elegir de 11 a 30.
  const TRAMOS_RAPIDOS = 10;

  function elegirTramos(cuantos) {
    if (cuantos === estado.tramosElegidos) return;
    estado.tramosElegidos = cuantos;
    estado.lapsoActual = null;
    estado.propositos = {}; // los tramos cambian: se reinician las elecciones
    cargarSugerencias(estado.sugerenciasValores);
  }

  function renderControlDeTramos() {
    elementos.tramosOpciones.innerHTML = "";
    const opciones = [null, ...Array.from({ length: TRAMOS_RAPIDOS - 1 }, (_, i) => i + 2)];
    opciones.forEach((cuantos) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "chip" + (cuantos === estado.tramosElegidos ? " is-active" : "");
      // En automático se ve cuántos tramos salen (igual que "Paradas sugeridas" del resumen).
      boton.textContent = cuantos === null ? (estado.lapsos.length ? `Automático · ${estado.lapsos.length}` : "Automático") : String(cuantos);
      if (cuantos === null) boton.classList.add("chip--automatico");
      boton.addEventListener("click", () => {
        estado.tramosMasAbierto = false;
        elegirTramos(cuantos);
        renderControlDeTramos();
      });
      elementos.tramosOpciones.appendChild(boton);
    });

    const masActivo = estado.tramosElegidos !== null && estado.tramosElegidos > TRAMOS_RAPIDOS;
    const mas = document.createElement("button");
    mas.type = "button";
    mas.className = "chip chip--mas" + (masActivo || estado.tramosMasAbierto ? " is-active" : "");
    mas.textContent = masActivo ? `Más · ${estado.tramosElegidos}` : "Más";
    mas.addEventListener("click", () => {
      estado.tramosMasAbierto = !estado.tramosMasAbierto;
      renderControlDeTramos();
      if (estado.tramosMasAbierto) elementos.tramosMasNumero.focus();
    });
    elementos.tramosOpciones.appendChild(mas);

    elementos.tramosMas.hidden = !(masActivo || estado.tramosMasAbierto);
    if (masActivo) elementos.tramosMasNumero.value = estado.tramosElegidos;

    elementos.tramosNota.hidden = !estado.horaSalidaAsumida;
    elementos.tramosNota.textContent = "Sin hora de salida, los horarios suponen que sales a las 08:00.";
  }

  function aplicarTramosMas() {
    const valor = Math.round(Number(elementos.tramosMasNumero.value));
    if (!Number.isFinite(valor) || valor <= TRAMOS_RAPIDOS) {
      elementos.tramosMasNumero.value = TRAMOS_RAPIDOS + 1;
      return;
    }
    const cuantos = Math.min(valor, 30);
    elementos.tramosMasNumero.value = cuantos;
    elegirTramos(cuantos);
    renderControlDeTramos();
  }

  // ---- Recomendadas (primera vista) y lista completa ("Ver más") ----
  // El servidor manda todas las sugerencias en orden de hora y marca a cada una con su
  // franja de horas del viaje (0-4) y su rango dentro de ella. La primera vista son
  // MOSTRAR_SUGERENCIAS recomendadas: la mejor de cada franja (con prioridad a las de
  // estrella), en orden de hora. "Ver más" muestra todas por hora; "Ver menos" vuelve a
  // las recomendadas, ya sin las que se agregaron o descartaron (entran las siguientes
  // mejores de su misma franja).
  const porRango = (a, b) =>
    (a.rango_franja ?? 99) - (b.rango_franja ?? 99) || (a.rango_global ?? 999) - (b.rango_global ?? 999);
  const porHora = (a, b) => (a.horas_estimadas ?? 0) - (b.horas_estimadas ?? 0);

  function recomendadas() {
    const lista = estado.sugerenciasLista;
    // Sin franjas (respaldo del servidor sin ruta real): las primeras de siempre.
    if (!lista.some((l) => typeof l.franja === "number")) return lista.slice(0, MOSTRAR_SUGERENCIAS);

    const porFranja = new Map();
    lista.forEach((l) => {
      const franja = typeof l.franja === "number" ? l.franja : 0;
      if (!porFranja.has(franja)) porFranja.set(franja, []);
      porFranja.get(franja).push(l);
    });
    const elegidas = [...porFranja.keys()]
      .sort((a, b) => a - b)
      .map((franja) => porFranja.get(franja).slice().sort(porRango)[0]);

    // Si alguna franja se quedó sin lugares, se completa con los siguientes mejores del resto.
    if (elegidas.length < MOSTRAR_SUGERENCIAS) {
      const resto = lista.filter((l) => !elegidas.includes(l)).sort(porRango);
      while (elegidas.length < MOSTRAR_SUGERENCIAS && resto.length) elegidas.push(resto.shift());
    }
    return elegidas.slice(0, MOSTRAR_SUGERENCIAS).sort(porHora);
  }

  function lugaresVisibles() {
    return estado.sugerenciasExpandido ? estado.sugerenciasLista.slice().sort(porHora) : recomendadas();
  }

  async function ampliarLista() {
    if (!estado.sugerenciasValores) return;
    const yaVistos = new Set([...estado.sugerenciasVistosIds, ...estado.sugerenciasLista.map((l) => l.id)]);
    const nuevoLote = await pedirSugerencias(estado.sugerenciasValores, TAMANO_LOTE, Array.from(yaVistos));
    estado.sugerenciasLista.push(...nuevoLote);
  }

  // Animación al reacomodar (Ver más / Ver menos / agregar o descartar): las tarjetas que ya
  // estaban viajan hasta su nuevo lugar y las nuevas entran con un fundido.
  function animarReacomodo(antes) {
    if (!antes || RutaEfectos.reducirMovimiento()) return;
    elementos.sugerenciasContenedor.querySelectorAll("[data-lugar-card]").forEach((card) => {
      const previo = antes.get(card.dataset.lugarId);
      const ahora = card.getBoundingClientRect();
      if (previo) {
        const dx = previo.left - ahora.left;
        const dy = previo.top - ahora.top;
        if (Math.abs(dx) < 1 && Math.abs(dy) < 1) return;
        card.animate(
          [{ transform: `translate(${dx}px, ${dy}px)` }, { transform: "translate(0, 0)" }],
          { duration: 700, easing: "cubic-bezier(0.22, 1, 0.36, 1)" }
        );
      } else {
        card.animate(
          [{ opacity: 0, transform: "translateY(14px) scale(0.96)" }, { opacity: 1, transform: "none" }],
          { duration: 500, easing: "cubic-bezier(0.22, 1, 0.36, 1)", delay: 120, fill: "backwards" }
        );
      }
    });
  }

  function renderSugerencias(animar = false) {
    const contenedor = elementos.sugerenciasContenedor;
    const antes = animar
      ? new Map([...contenedor.querySelectorAll("[data-lugar-card]")].map((c) => [c.dataset.lugarId, c.getBoundingClientRect()]))
      : null;
    contenedor.innerHTML = "";
    contenedor.classList.toggle("is-expandido", estado.sugerenciasExpandido);

    if (!estado.sugerenciasLista.length) {
      contenedor.innerHTML =
        estado.lapsoActual === null
          ? '<p class="empty-state">No encontramos sugerencias para estos intereses todavía.</p>'
          : `<p class="empty-state">${mensajeSinLugaresEnTramo()}</p>`;
      elementos.verMasBtn.hidden = true;
      return;
    }

    lugaresVisibles().forEach((lugar) => agregarCardSugerencia(lugar));
    actualizarBotonVerMas();
    animarReacomodo(antes);
  }

  // "Ver más" (con flechita) muestra todas por hora; "Ver menos" vuelve a las recomendadas.
  function actualizarBotonVerMas() {
    const hayMas = estado.sugerenciasLista.length > recomendadas().length;
    elementos.verMasBtn.hidden = !hayMas && !estado.sugerenciasExpandido;
    elementos.verMasBtn.setAttribute("aria-expanded", String(estado.sugerenciasExpandido));
    elementos.verMasBtn.classList.toggle("is-abierto", estado.sugerenciasExpandido);
    elementos.verMasBtn.querySelector("[data-ver-mas-texto]").textContent = estado.sugerenciasExpandido ? "Ver menos" : "Ver más";
  }

  function mensajeSinLugaresEnTramo() {
    const pedido = estado.propositos[estado.lapsoActual];
    const que = { comida: "lugares para comer", descanso: "lugares para pasar la noche", turismo: "lugares de turismo" }[pedido];
    return que
      ? `No encontramos ${que} en este tramo. Prueba con otro tramo o déjalo en Automático.`
      : "No encontramos sugerencias en este tramo todavía. Prueba con otro tramo.";
  }

  // "Recomendado por la Guía Michelin y la UNESCO" a partir del texto de la base.
  function textoDeReconocimiento(reconocimiento) {
    const fuentes = [];
    if (/michelin/i.test(reconocimiento || "")) fuentes.push("la Guía Michelin");
    if (/unesco/i.test(reconocimiento || "")) fuentes.push("la UNESCO");
    if (/50 best/i.test(reconocimiento || "")) fuentes.push("Latin America's 50 Best");
    if (!fuentes.length) return "Gastronomía reconocida";
    const lista = fuentes.length > 1 ? `${fuentes.slice(0, -1).join(", ")} y ${fuentes[fuentes.length - 1]}` : fuentes[0];
    return `Gastronomía recomendada por ${lista}`;
  }

  const NOMBRES_DE_INTERES = {
    naturaleza: "Naturaleza",
    playas: "Playas",
    comida: "Comida",
    descanso: "Descanso",
    cultura: "Cultura",
    pueblos_magicos: "Pueblos mágicos",
  };

  function agregarCardSugerencia(lugar) {
    const nodo = tplSugerencia.content.cloneNode(true);
    const card = nodo.querySelector("[data-lugar-card]");
    card.dataset.lugarId = lugar.id;
    nodo.querySelector("[data-lugar-categoria]").textContent = lugar.categoria;
    nodo.querySelector("[data-lugar-nombre]").textContent = lugar.nombre;
    nodo.querySelector("[data-lugar-descripcion]").textContent = lugar.descripcion;

    if (typeof lugar.horas_estimadas === "number") {
      nodo.querySelector("[data-lugar-camino]").replaceChildren(RutaIconos.nodo("auto", `≈${formatoDuracion(lugar.horas_estimadas)} de camino`, 16));
      if (lugar.hora_llegada) {
        const llegada = nodo.querySelector("[data-lugar-llegada]");
        llegada.replaceChildren(RutaIconos.nodo("llegada", `Llegas ${lugar.hora_llegada}`, 16));
        llegada.hidden = false;
      }
      nodo.querySelector("[data-lugar-horas]").hidden = false;
    }

    // Los intereses del lugar (los del filtro "¿Qué buscas?" que cumple), para que la franja
    // de abajo nunca quede vacía y se vea por qué se recomienda.
    const contIntereses = nodo.querySelector("[data-lugar-intereses]");
    (lugar.intereses || []).slice(0, 3).forEach((interes) => {
      const chip = document.createElement("span");
      chip.className = "card__interes";
      chip.textContent = NOMBRES_DE_INTERES[interes] || interes;
      contIntereses.appendChild(chip);
    });
    if (!contIntereses.children.length) contIntereses.hidden = true;

    if (lugar.gastronomia_destacada) {
      // Estrellita en la esquina + una línea que dice quién lo recomienda.
      const estrella = nodo.querySelector("[data-lugar-estrella]");
      const detalle = lugar.reconocimiento_gastronomico || "Gastronomía reconocida";
      estrella.title = detalle;
      estrella.hidden = false;
      card.classList.add("tiene-estrella");

      const nota = nodo.querySelector("[data-lugar-gastronomia]");
      nota.replaceChildren(RutaIconos.nodo("estrella", textoDeReconocimiento(lugar.reconocimiento_gastronomico), 16));
      nota.title = detalle;
      nota.hidden = false;
    }

    const nota = nodo.querySelector("[data-lugar-descanso]");
    if (lugar.proposito === "comida") {
      nota.replaceChildren(RutaIconos.nodo("comer", "Buen lugar para comer", 16));
      nota.hidden = false;
    } else if (lugar.proposito === "descanso") {
      nota.replaceChildren(RutaIconos.nodo("dormir", "Buen lugar para pasar la noche", 16));
      nota.hidden = false;
    }

    nodo.querySelector("[data-agregar-parada]").addEventListener("click", () => {
      agregarParada(lugar);
      quitarSugerencia(lugar);
    });

    nodo.querySelector("[data-descartar]").addEventListener("click", () => {
      quitarSugerencia(lugar);
    });

    elementos.sugerenciasContenedor.appendChild(nodo);
    return card;
  }

  // Al agregar a la parada o descartar una sugerencia se quita de la lista y se
  // vuelve a dibujar; si quedan pocas, se trae otro lote.
  async function quitarSugerencia(lugar) {
    estado.sugerenciasVistosIds.add(lugar.id);
    estado.sugerenciasLista = estado.sugerenciasLista.filter((l) => l.id !== lugar.id);
    if (estado.sugerenciasLista.length < MOSTRAR_SUGERENCIAS) await ampliarLista();
    renderSugerencias(true);
  }

  function alternarSugerencias() {
    estado.sugerenciasExpandido = !estado.sugerenciasExpandido;
    renderSugerencias(true);
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
      gastronomia_destacada: lugar.gastronomia_destacada,
      reconocimiento_gastronomico: lugar.reconocimiento_gastronomico,
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
      const nombreEl = nodo.querySelector("[data-item-nombre]");
      if (parada.gastronomia_destacada) nombreEl.append(RutaIconos.nodo("estrella", "", 16), " ");
      nombreEl.append(parada.nombre);
      if (parada.gastronomia_destacada && parada.reconocimiento_gastronomico) nombreEl.title = parada.reconocimiento_gastronomico;
      nodo.querySelector("[data-mover-arriba]").addEventListener("click", () => moverParada(indice, -1));
      nodo.querySelector("[data-mover-abajo]").addEventListener("click", () => moverParada(indice, 1));
      // Confirmación en el mismo botón (efectos/eliminar.js). Se borra por
      // identidad, no por posición, por si otra parada se mueve mientras tanto.
      RutaEfectos.eliminar.montar(nodo.querySelector("[data-eliminar-parada]"), () => {
        const posicion = estado.itinerario.indexOf(parada);
        if (posicion !== -1) eliminarParada(posicion);
      });
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
    RutaEfectos.contador.set(elementos.aventuraParadas, String(estado.itinerario.length));

    if (estado.resumen) {
      RutaEfectos.contador.set(elementos.aventuraDistancia, `${estado.resumen.distancia_km} km`);
      elementos.aventuraTexto.textContent = estado.itinerario.length
        ? `Tu recorrido incluye ${estado.itinerario.length} parada${estado.itinerario.length === 1 ? "" : "s"} intermedia${estado.itinerario.length === 1 ? "" : "s"} y está listo para ajustarlas.`
        : "Agrega paradas desde \"Descubre en el camino\" para completar tu aventura.";
    } else {
      RutaEfectos.contador.set(elementos.aventuraDistancia, "—");
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
        a.append(`Tramo ${i + 1} de ${enlaces.length} `);
        a.insertAdjacentHTML("beforeend", RutaIconos.html("siguiente", 16));
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
    burbuja.querySelector(".ruta-burbuja__trayecto").append(`${ruta.origen} `, RutaIconos.nodo("siguiente", "", 14), ` ${ruta.destino}`);
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
    RutaEfectos.horaSalida.poner(hora); // selector de hora (efectos/duracion.js)
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
    elementos.verMasBtn.addEventListener("click", alternarSugerencias);
  }

  if (elementos.tramosMasAplicar) {
    elementos.tramosMasAplicar.addEventListener("click", aplicarTramosMas);
    elementos.tramosMasNumero.addEventListener("keydown", (evento) => {
      if (evento.key === "Enter") {
        evento.preventDefault();
        aplicarTramosMas();
      }
    });
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
        gastronomia_destacada: p.gastronomia_destacada,
        reconocimiento_gastronomico: p.reconocimiento_gastronomico,
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
