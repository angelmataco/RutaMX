// Estado de carga "grid reveal": una cuadrícula gris que se va partiendo en cuadritos
// mientras algo carga y, cuando llega, se deshace en una ola que deja ver lo de abajo.
// Adaptado del componente grid-reveal (rare-ui) a canvas puro. En RutaMX cubre el mapa
// mientras se calcula la ruta.
//
//   const g = RutaEfectos.gridReveal.montar(contenedor, { duracion: 4500, texto: "Trazando tu ruta…" });
//   g.revelar();   // ya llegó lo que se esperaba: la cuadrícula se disuelve y se quita sola
//   g.quitar();    // cancelar sin animación (por ejemplo, si hubo un error)
//
// `duracion` es el tiempo estimado de espera (ms): la cuadrícula avanza a ese ritmo y nunca
// llega al final por sí sola, así que siempre queda margen para la llegada real.

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.gridReveal = (() => {
  const CELDAS = 180;
  const CELDAS_INICIALES = 4;
  const AGUANTE = 0.9; // sin datos, nunca pasa de aquí
  const TOPE_ESPERA = 0.72; // mientras espera, deja de partirse aquí para que la llegada tenga a dónde ir
  const ULTIMO_CORTE = 0.92;
  const MORPH = 0.055; // lo que tarda una celda en separarse (en unidades de progreso)
  const CANAL_DESDE = 0.35;
  const CANAL_HASTA = 0.75;
  const DURACION_OLA_MS = 950;

  const acotar01 = (n) => (n > 0 ? (n < 1 ? n : 1) : 0);
  const mezclar = (a, b, t) => a + (b - a) * t;
  const salidaSuave = (t) => 1 - Math.pow(1 - t, 3);
  const suavizar = (a, b, x) => {
    const t = acotar01((x - a) / (b - a));
    return t * t * (3 - 2 * t);
  };
  // nunca llega a su techo: si tarda más de lo estimado, sigue avanzando despacito
  const autoRitmo = (transcurrido, duracion) => AGUANTE * (1 - Math.exp(-transcurrido / (duracion > 0 ? duracion : 1)));
  const azar = (x, y, z) => {
    const n = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
    return n - Math.floor(n);
  };

  function crearCelda(x, y, w, h, padre) {
    return { x, y, w, h, tono: azar(x + 3.1, y + 1.7, w * 31.7), retardo: 0, corteEn: 0, padre, hijos: null };
  }

  // Partir siempre la celda más grande mantiene los cuadros cuadrados y el conteo sube de uno en uno.
  function construirArbol(aspecto) {
    const raiz = crearCelda(0, 0, 1, 1, null);
    const hojas = [raiz];
    const ramas = [];
    while (hojas.length < CELDAS) {
      let elegida = 0;
      let mayor = -1;
      hojas.forEach((c, i) => {
        const area = c.w * aspecto * c.h * (1 + 0.12 * azar(c.x, c.y, 7.3));
        if (area > mayor) {
          mayor = area;
          elegida = i;
        }
      });
      const padre = hojas.splice(elegida, 1)[0];
      const ancha = padre.w * aspecto >= padre.h;
      const mitad = ancha ? padre.w / 2 : padre.h / 2;
      const a = ancha ? crearCelda(padre.x, padre.y, mitad, padre.h, padre) : crearCelda(padre.x, padre.y, padre.w, mitad, padre);
      const b = ancha ? crearCelda(padre.x + mitad, padre.y, mitad, padre.h, padre) : crearCelda(padre.x, padre.y + mitad, padre.w, mitad, padre);
      padre.hijos = [a, b];
      ramas.push(padre);
      hojas.push(a, b);
    }
    const apertura = CELDAS_INICIALES - 1;
    const resto = Math.max(1, ramas.length - apertura);
    // los primeros cortes van antes de cero: esas celdas ya están separadas en el primer cuadro
    ramas.forEach((c, i) => {
      c.corteEn = i < apertura ? -MORPH : (ULTIMO_CORTE * (i - apertura + 1)) / resto;
    });
    // El retardo de la ola final depende de la posición (diagonal) más un poco de azar.
    hojas.forEach((c) => {
      const diagonal = (c.x + c.w / 2 + c.y + c.h / 2) / 2;
      c.retardo = (0.7 * diagonal + 0.3 * azar(c.x, c.y, 3.9)) * 0.6;
    });
    return { raiz, ramas };
  }

  // Un gris cálido (a juego con la paleta crema de RutaMX) que respira despacito.
  function tinte(tono, reloj) {
    const g = 226 + tono * 13 + Math.sin(reloj * 1.5 + tono * 6.28) * 3;
    return [Math.round(g), Math.round(g - 4), Math.round(g - 15)];
  }

  function montar(contenedor, { duracion = 4500, texto = "" } = {}) {
    const marco = document.createElement("div");
    marco.className = "grid-reveal";
    const canvas = document.createElement("canvas");
    canvas.setAttribute("aria-hidden", "true");
    marco.appendChild(canvas);
    let pie = null;
    if (texto) {
      pie = document.createElement("div");
      pie.className = "grid-reveal__pie";
      pie.setAttribute("role", "status");
      pie.textContent = texto;
      marco.appendChild(pie);
    }
    contenedor.appendChild(marco);

    const ctx = canvas.getContext("2d");
    const rect0 = marco.getBoundingClientRect();
    const { raiz, ramas } = construirArbol(rect0.width > 0 && rect0.height > 0 ? rect0.width / rect0.height : 1.6);
    const escena = { ancho: 0, alto: 0, escala: 1, reloj: 0, corte: 0, ola: -1 };
    let listo = false;
    let inicioOla = 0;
    let raf = 0;
    let terminado = false;

    function dibujar() {
      const { ancho, alto, corte, ola } = escena;
      ctx.clearRect(0, 0, ancho, alto);
      if (!ancho) return;
      const revelando = ola >= 0;
      const suave = 1 - suavizar(CANAL_DESDE, CANAL_HASTA, corte);
      const canal = escena.escala * suave;
      const redondeado = suave > 0.01 && typeof ctx.roundRect === "function";

      // Los canales se hunden en este color en vez de dejar ver lo de abajo.
      if (!revelando) {
        const [r, g, b] = tinte(raiz.tono, escena.reloj);
        ctx.fillStyle = `rgb(${Math.round(r * 0.92)},${Math.round(g * 0.92)},${Math.round(b * 0.92)})`;
        ctx.fillRect(0, 0, ancho, alto);
      }

      const pintar = (p, celda) => {
        // Se ajusta a píxeles enteros para que las celdas vecinas no dejen rendija.
        const x = Math.round(p.x);
        const y = Math.round(p.y);
        const w = Math.round(p.x + p.w) - x;
        const h = Math.round(p.y + p.h) - y;
        const izq = x <= 0 ? 0 : canal;
        const arr = y <= 0 ? 0 : canal;
        const anchoUtil = w - izq - (x + w >= ancho ? 0 : canal);
        const altoUtil = h - arr - (y + h >= alto ? 0 : canal);
        if (anchoUtil <= 0 || altoUtil <= 0) return;
        let alfa = 1;
        if (revelando) {
          alfa = 1 - suavizar(celda.retardo, celda.retardo + 0.4, ola);
          if (alfa <= 0.003) return;
        }
        const [r, g, b] = tinte(p.tono, escena.reloj);
        ctx.globalAlpha = alfa;
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        if (redondeado) {
          const radio = Math.min(anchoUtil, altoUtil) * 0.12 * suave;
          ctx.beginPath();
          ctx.roundRect(x + izq, y + arr, anchoUtil, altoUtil, radio);
          ctx.fill();
        } else {
          ctx.fillRect(x + izq, y + arr, anchoUtil, altoUtil);
        }
        ctx.globalAlpha = 1;
      };

      const recorrer = (celda, p) => {
        if (!celda.hijos || corte < celda.corteEn) {
          pintar(p, celda);
          return;
        }
        // Los hijos parten del rectángulo del padre y se separan hasta el suyo.
        const t = salidaSuave(acotar01((corte - celda.corteEn) / MORPH));
        celda.hijos.forEach((hijo) => {
          recorrer(hijo, {
            x: mezclar(p.x, hijo.x * ancho, t),
            y: mezclar(p.y, hijo.y * alto, t),
            w: mezclar(p.w, hijo.w * ancho, t),
            h: mezclar(p.h, hijo.h * alto, t),
            tono: mezclar(p.tono, hijo.tono, t),
          });
        });
      };
      recorrer(raiz, { x: 0, y: 0, w: ancho, h: alto, tono: raiz.tono });
    }

    function medir() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const r = marco.getBoundingClientRect();
      const w = Math.max(1, Math.round(r.width * dpr));
      const h = Math.max(1, Math.round(r.height * dpr));
      escena.escala = dpr;
      if (w === escena.ancho && h === escena.alto) return;
      escena.ancho = w;
      escena.alto = h;
      canvas.width = w;
      canvas.height = h;
      dibujar(); // cambiar el tamaño del canvas lo borra: se pinta de nuevo
    }
    medir();
    const observador = typeof ResizeObserver === "function" ? new ResizeObserver(medir) : null;
    if (observador) observador.observe(marco);

    function limpiar() {
      terminado = true;
      cancelAnimationFrame(raf);
      if (observador) observador.disconnect();
      marco.remove();
    }

    if (RutaEfectos.reducirMovimiento()) {
      // Sin movimiento: una sola imagen fija y se quita en cuanto llega lo esperado.
      escena.corte = TOPE_ESPERA;
      dibujar();
      return {
        revelar: limpiar,
        quitar: limpiar,
      };
    }

    let ultimo = 0;
    let transcurrido = 0;
    let suavizado = 0;
    function cuadro(ahora) {
      if (terminado) return;
      if (!marco.isConnected) return limpiar(); // si lo quitan de la página, se apaga solo
      raf = requestAnimationFrame(cuadro);
      if (!ultimo) ultimo = ahora;
      const dt = Math.min((ahora - ultimo) / 1000, 0.05);
      ultimo = ahora;
      transcurrido += dt;
      escena.reloj = transcurrido;

      const objetivo = listo ? 1 : autoRitmo(transcurrido * 1000, duracion);
      suavizado += (objetivo - suavizado) * (1 - Math.exp(-dt * 5.5));
      const querido = Math.min(suavizado, listo ? 1 : TOPE_ESPERA);
      escena.corte += (querido - escena.corte) * (1 - Math.exp(-dt * 4));

      // Con todas las celdas ya separadas, arranca la ola que las disuelve.
      if (listo && escena.ola < 0 && escena.corte > 0.985) {
        escena.ola = 0;
        inicioOla = ahora;
        if (pie) pie.classList.add("is-saliendo");
      }
      if (escena.ola >= 0) {
        escena.ola = Math.min(1, (ahora - inicioOla) / DURACION_OLA_MS);
        if (escena.ola >= 1) return limpiar();
      }
      dibujar();
    }
    raf = requestAnimationFrame(cuadro);

    return {
      revelar() {
        listo = true;
      },
      quitar: limpiar,
    };
  }

  return { montar };
})();
