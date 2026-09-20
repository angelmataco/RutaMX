// Efecto "contador tipo odómetro": cada dígito es una rueda que gira hasta su
// nuevo valor. Se usa con cualquier texto ("512 km", "$1,234", "6 h 30 min"):
// lo que no es dígito se queda fijo. Adaptado del componente animated-counter
// (rare-ui) a JS/CSS puro.
//
//   RutaEfectos.contador.set(elemento, "$1,234");

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.contador = (() => {
  const CARAS = 10;
  const COPIAS = 3; // la rueda tiene 3 vueltas de 0-9 para poder girar en cualquier sentido
  const ALTO_EM = 1.5;

  const mod = (n, m) => ((n % m) + m) % m;

  function posicionar(col, animar) {
    const rueda = col._rueda;
    if (!animar) rueda.style.transition = "none";
    rueda.style.transform = `translateY(${-col._pos * ALTO_EM}em)`;
    if (!animar) {
      void rueda.offsetHeight; // aplica el salto sin animación antes de devolver la transición
      rueda.style.transition = "";
    }
  }

  function crearColumna() {
    const col = document.createElement("span");
    col.className = "contador__col";
    const medidor = document.createElement("span");
    medidor.className = "contador__medidor";
    medidor.textContent = "0"; // fija el ancho al de un dígito
    const rueda = document.createElement("span");
    rueda.className = "contador__rueda";
    for (let i = 0; i < CARAS * COPIAS; i++) {
      const cara = document.createElement("span");
      cara.textContent = String(i % CARAS);
      rueda.appendChild(cara);
    }
    col.append(medidor, rueda);
    col._rueda = rueda;
    col._pos = CARAS; // copia del medio, mostrando el 0
    // Al terminar de girar se vuelve a la copia del medio, sin que se note.
    rueda.addEventListener("transitionend", (evento) => {
      if (evento.propertyName !== "transform") return;
      col._pos = CARAS + mod(col._pos, CARAS);
      posicionar(col, false);
    });
    posicionar(col, false);
    return col;
  }

  function girar(col, digito, sentido, animar) {
    const actual = mod(col._pos, CARAS);
    if (actual === digito) return;
    const salto = sentido >= 0 ? mod(digito - actual, CARAS) : -mod(actual - digito, CARAS);
    let destino = col._pos + salto;
    if (destino < 0 || destino > CARAS * COPIAS - 1) {
      col._pos = CARAS + actual;
      posicionar(col, false);
      destino = col._pos + salto;
    }
    col._pos = destino;
    // Cascada: cada dígito arranca un poquito después que el de su derecha.
    col._rueda.style.transitionDelay = animar && !RutaEfectos.reducirMovimiento() ? `${col._clave * 0.07}s` : "";
    posicionar(col, animar && !RutaEfectos.reducirMovimiento());
  }

  function set(el, texto) {
    texto = String(texto);
    let estado = el._contador;
    if (!estado) {
      estado = el._contador = { columnas: new Map(), texto: null, digitos: "" };
      el.classList.add("contador");
    }
    if (estado.texto === texto) return;

    const digitos = texto.replace(/\D/g, "");
    const sentido = Number(digitos || 0) >= Number(estado.digitos || 0) ? 1 : -1;
    const primera = estado.texto === null;
    estado.texto = texto;
    estado.digitos = digitos;

    // Texto accesible + la parte animada (que los lectores de pantalla ignoran).
    const sr = document.createElement("span");
    sr.className = "contador__sr";
    sr.textContent = texto;
    const vista = document.createElement("span");
    vista.className = "contador__vista";
    vista.setAttribute("aria-hidden", "true");

    // Las columnas se identifican por su distancia al final: al ganar un
    // dígito las demás se quedan en su lugar en vez de reconstruirse.
    const usadas = new Set();
    let restantes = digitos.length;
    const nuevas = [];
    for (const caracter of texto) {
      if (caracter >= "0" && caracter <= "9") {
        restantes -= 1;
        let col = estado.columnas.get(restantes);
        const esNueva = !col;
        if (esNueva) {
          col = crearColumna();
          estado.columnas.set(restantes, col);
          nuevas.push(col);
        }
        col._clave = restantes;
        usadas.add(restantes);
        vista.appendChild(col);
        col._destino = Number(caracter);
      } else {
        const marca = document.createElement("span");
        marca.className = "contador__marca";
        marca.textContent = caracter;
        vista.appendChild(marca);
      }
    }
    estado.columnas.forEach((_, clave) => {
      if (!usadas.has(clave)) estado.columnas.delete(clave);
    });

    el.replaceChildren(sr, vista);

    // Con las columnas ya en pantalla, se giran hasta su dígito.
    requestAnimationFrame(() => {
      usadas.forEach((clave) => {
        const col = estado.columnas.get(clave);
        if (col) girar(col, col._destino, sentido, true);
      });
    });
    if (primera) el.classList.add("contador--lista");
  }

  return { set };
})();
