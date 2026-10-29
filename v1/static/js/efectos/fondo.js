// Fondo de líneas que fluyen: el componente background-paths (shadcn / 21st.dev) en JS/SVG/CSS
// puros, sin React ni framer-motion. Se respeta el original:
//   - Dos juegos (position 1 y -1) de 36 curvas con la misma fórmula, viewBox 0 0 696 316,
//     grosor 0.5 + i * 0.03 y strokeOpacity 0.1 + i * 0.03.
//   - Cada curva anima pathLength 0.3 -> 1, pathOffset 0 -> 1 -> 0 y opacity 0.3 -> 0.6 -> 0.3,
//     con ease linear, en bucle y con una duración distinta por curva (base + azar).
//     (La opacidad se anima como stroke-opacity = strokeOpacity * [0.3, 0.6, 0.3]: se ve idéntico,
//     porque la curva solo tiene trazo, y es mucho más barato que `opacity` en 72 elementos.)
// Lo que cambia respecto al original (pedido de Angel):
//   - VELOCIDAD: las curvas dan la vuelta en ~16.5–26 s en lugar de 20–30 s.
//   - COLOR: el original usa un solo color (currentColor); aquí cada curva recorre los tonos de la
//     paleta de la app (efectos.css, --fondo-c0..8), cada una con su propio ritmo y fase.
//
// Se monta solo, sin ganchos en el HTML: crea <div class="fondo-rutas"> al inicio de <body>.
// La animación (@keyframes) y los colores viven en efectos.css.

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.fondo = (() => {
  const NS = "http://www.w3.org/2000/svg";

  // Punto medio pedido por Angel entre la versión anterior (13–22 s, muy rápida) y el original
  // (20–30 s): cada vuelta dura ~16.5–26 s.
  const DURACION_BASE = 16.5; // s (original: 20)
  const DURACION_AZAR = 9.5; // s (original: 10)
  const COLOR_BASE = 40; // s que tarda una curva en recorrer toda la paleta
  const COLOR_AZAR = 30;

  // Misma curva que FloatingPaths del componente original.
  function trazo(i, posicion) {
    const a = 380 - i * 5 * posicion;
    const b = 189 + i * 6;
    return (
      `M-${a} -${b}C-${a} -${b} -${312 - i * 5 * posicion} ${216 - i * 6} ${152 - i * 5 * posicion} ${343 - i * 6}` +
      `C${616 - i * 5 * posicion} ${470 - i * 6} ${684 - i * 5 * posicion} ${875 - i * 6} ${684 - i * 5 * posicion} ${875 - i * 6}`
    );
  }

  // Equivale a <FloatingPaths position={posicion} />
  function flotantes(posicion, cuantas) {
    const svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "fondo-rutas__svg");
    svg.setAttribute("viewBox", "0 0 696 316");
    svg.setAttribute("fill", "none");
    for (let i = 0; i < cuantas; i++) {
      const p = document.createElementNS(NS, "path");
      p.setAttribute("d", trazo(i, posicion));
      p.setAttribute("pathLength", "1"); // como framer-motion: la curva mide 1
      p.setAttribute("stroke-width", (0.5 + i * 0.03).toFixed(2));
      p.style.setProperty("--so", (0.1 + i * 0.03).toFixed(2)); // strokeOpacity del original
      p.style.setProperty("--dur", `${(DURACION_BASE + Math.random() * DURACION_AZAR).toFixed(2)}s`);
      // Color: cada curva arranca en otro punto de la paleta y la recorre a su ritmo.
      const durColor = COLOR_BASE + Math.random() * COLOR_AZAR;
      p.style.setProperty("--dur-color", `${durColor.toFixed(1)}s`);
      p.style.setProperty("--fase-color", `${-(((i / cuantas) * 0.6 + (posicion > 0 ? 0 : 0.3) + Math.random() * 0.1) * durColor).toFixed(1)}s`);
      svg.appendChild(p);
    }
    return svg;
  }

  function montar() {
    if (document.querySelector(".fondo-rutas")) return;
    const contenedor = document.createElement("div");
    contenedor.className = "fondo-rutas";
    contenedor.setAttribute("aria-hidden", "true");
    // En pantallas chicas, la mitad de curvas: menos trabajo para el teléfono.
    const cuantas = window.matchMedia("(max-width: 700px)").matches ? 18 : 36;
    contenedor.append(flotantes(1, cuantas), flotantes(-1, cuantas));
    document.body.prepend(contenedor);
  }

  montar();
  return { montar };
})();
