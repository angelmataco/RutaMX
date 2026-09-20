// Orbe de puntos animado (canvas) con estados. Se usa como indicador de
// "la IA está pensando". Adaptado del componente matrix-orb (rare-ui).
//
//   const orbe = RutaEfectos.orbe.montar(contenedor, { estado: "thinking", tamano: 64 });
//   orbe.destruir();   // (se detiene solo si el contenedor sale de la página)

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.orbe = (() => {
  const TAU = Math.PI * 2;
  const ESTADOS = ["idle", "listening", "thinking"];
  const ETIQUETAS = { idle: "En espera", listening: "Escuchando", thinking: "Pensando…" };
  const ESCALA = { idle: 0.88, listening: 1, thinking: 0.92 };
  const RIGIDEZ = 180;
  const AMORTIGUACION = 26;
  const ATAQUE = 0.22;
  const SUELTA = 0.08;
  const MEZCLA = 0.16;
  const ORBITADORES = [
    { radio: 0.62, velocidad: 2.2, fase: 0, dispersion: 0.42 },
    { radio: 0.4, velocidad: -1.7, fase: 2.1, dispersion: 0.36 },
    { radio: 0.8, velocidad: 1.15, fase: 4, dispersion: 0.34 },
  ];

  function envolvente(t) {
    const lenta = 0.5 + 0.5 * Math.sin(t * 0.62 + 0.4);
    const rapida = 0.5 + 0.5 * Math.sin(t * 1.9 + 1.1);
    return 0.22 + 0.78 * (0.45 + 0.55 * lenta) * rapida;
  }

  function intensidad(estado, d, nx, ny, t, amplitud) {
    if (estado === "listening") {
      const onda = 0.5 + 0.5 * Math.sin(d * 4.2 - t * 3);
      return 0.32 + amplitud * (0.34 + 0.38 * onda);
    }
    if (estado === "thinking") {
      let calor = 0;
      for (const o of ORBITADORES) {
        const a = t * o.velocidad + o.fase;
        const dx = nx - Math.cos(a) * o.radio;
        const dy = ny - Math.sin(a) * o.radio;
        calor += Math.exp(-(dx * dx + dy * dy) / (o.dispersion * o.dispersion));
      }
      return 0.26 + 0.8 * Math.min(1, calor);
    }
    return 0.62 + 0.12 * Math.sin(t * 1.05 - d * 2.4);
  }

  function montar(contenedor, { estado = "thinking", tamano = 64, color, puntos = 11, etiqueta } = {}) {
    color = color || getComputedStyle(document.documentElement).getPropertyValue("--color-terracota").trim() || "#c76a4c";

    const raiz = document.createElement("div");
    raiz.className = "orbe";
    const canvas = document.createElement("canvas");
    canvas.setAttribute("aria-hidden", "true");
    canvas.style.width = canvas.style.height = `${tamano}px`;
    raiz.appendChild(canvas);
    let texto = null;
    if (etiqueta !== null) {
      texto = document.createElement("span");
      texto.className = "orbe__texto";
      texto.setAttribute("role", "status");
      texto.setAttribute("aria-live", "polite");
      raiz.appendChild(texto);
    }
    contenedor.appendChild(raiz);

    const ctx = canvas.getContext("2d");
    const dpr = Math.min(window.devicePixelRatio || 1, 4);
    const buffer = Math.round(tamano * dpr);
    canvas.width = canvas.height = buffer;
    ctx.scale(buffer / tamano, buffer / tamano);
    ctx.fillStyle = color;

    const rejilla = Math.max(3, Math.round(puntos));
    const mitad = (rejilla - 1) / 2;
    const espaciado = (tamano * 0.74) / (rejilla - 1);
    const radioMax = espaciado * 0.6;
    const centro = tamano / 2;
    const pesos = { idle: 0, listening: 0, thinking: 0 };
    let actual = estado;
    pesos[actual] = 1;

    function etiquetar() {
      raiz.dataset.estado = actual;
      if (texto) texto.textContent = (etiqueta && etiqueta[actual]) || (typeof etiqueta === "string" ? etiqueta : ETIQUETAS[actual]);
    }
    etiquetar();

    function dibujar(t, amplitud, escala) {
      ctx.clearRect(0, 0, tamano, tamano);
      for (let iy = 0; iy < rejilla; iy++) {
        for (let ix = 0; ix < rejilla; ix++) {
          const nx = (ix - mitad) / mitad;
          const ny = (iy - mitad) / mitad;
          const d = Math.hypot(nx, ny);
          if (d > 1.12) continue; // 1.12 (y no la esquina, 1.41) redondea el contorno
          let mezclado = 0;
          for (const e of ESTADOS) {
            if (pesos[e] < 0.001) continue;
            mezclado += pesos[e] * intensidad(e, d, nx, ny, t, amplitud);
          }
          const radio = radioMax * Math.exp(-d * d * 1.7) * Math.min(1, Math.max(0, mezclado)) * escala;
          if (radio * dpr < 0.5) continue; // menos de medio píxel se ve como neblina
          ctx.beginPath();
          ctx.arc(centro + (ix - mitad) * espaciado * escala, centro + (iy - mitad) * espaciado * escala, radio, 0, TAU);
          ctx.fill();
        }
      }
    }

    let raf = 0;
    let detenido = false;

    if (RutaEfectos.reducirMovimiento()) {
      dibujar(0, envolvente(0), ESCALA[actual]); // un solo cuadro, sin movimiento
    } else {
      let t = 0;
      let amplitud = 0;
      let escala = ESCALA[actual];
      let velocidad = 0;
      let ultimo = performance.now();
      const cuadro = (ahora) => {
        if (detenido || !canvas.isConnected) return; // si lo quitan de la página, se apaga solo
        const dt = Math.min((ahora - ultimo) / 1000, 0.05);
        ultimo = ahora;
        t += dt;
        const objetivo = envolvente(t);
        amplitud += (objetivo - amplitud) * (1 - Math.pow(1 - (objetivo > amplitud ? ATAQUE : SUELTA), dt * 60));
        const paso = 1 - Math.pow(1 - MEZCLA, dt * 60);
        for (const e of ESTADOS) pesos[e] += ((e === actual ? 1 : 0) - pesos[e]) * paso;
        velocidad += (-RIGIDEZ * (escala - ESCALA[actual]) - AMORTIGUACION * velocidad) * dt;
        escala += velocidad * dt;
        dibujar(t, amplitud, escala);
        raf = requestAnimationFrame(cuadro);
      };
      raf = requestAnimationFrame(cuadro);
    }

    return {
      elemento: raiz,
      cambiarEstado(nuevo) {
        if (!ESTADOS.includes(nuevo)) return;
        actual = nuevo;
        etiquetar();
        if (RutaEfectos.reducirMovimiento()) {
          for (const e of ESTADOS) pesos[e] = e === actual ? 1 : 0;
          dibujar(0, envolvente(0), ESCALA[actual]);
        }
      },
      destruir() {
        detenido = true;
        cancelAnimationFrame(raf);
        raiz.remove();
      },
    };
  }

  return { montar };
})();
