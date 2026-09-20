// Campo de PIN por casillas: cada dígito "rueda" hacia su casilla mientras un
// cursor se desliza de una a otra. Adaptado del componente otp-input (rare-ui).
//
// Mejora, sin cambiar el contrato con auth.js, los campos <input name="pin">
// de la ventana de login/registro: el input original pasa a ser oculto y
// sigue llevando el valor (así FormData y form.reset() funcionan igual). Si
// este script no carga, queda el campo de texto normal.

window.RutaEfectos = window.RutaEfectos || {};

RutaEfectos.pin = (() => {
  const SOLO_DIGITO = /^[0-9]$/;

  function montar(original) {
    const largo = original.maxLength > 0 ? original.maxLength : 4;
    const formulario = original.form;

    const raiz = document.createElement("div");
    raiz.className = "otp";
    raiz.setAttribute("role", "group");
    raiz.setAttribute("aria-label", `PIN de ${largo} dígitos`);
    const fila = document.createElement("div");
    fila.className = "otp__fila";

    const valores = Array(largo).fill("");
    const casillas = [];
    const celdas = [];

    for (let i = 0; i < largo; i++) {
      const celda = document.createElement("div");
      celda.className = "otp__celda";
      const input = document.createElement("input");
      input.type = "text";
      input.className = "otp__casilla";
      input.inputMode = "numeric";
      input.autocomplete = "off";
      input.required = original.required; // el navegador avisa si falta algún dígito (el input original ya es oculto)
      input.setAttribute("aria-label", `Dígito ${i + 1} de ${largo}`);
      const marca = document.createElement("span");
      marca.className = "otp__marca";
      celda.append(input, marca);
      fila.appendChild(celda);
      casillas.push(input);
      celdas.push(celda);
    }

    const cursor = document.createElement("span");
    cursor.className = "otp__cursor";
    cursor.hidden = true;
    fila.appendChild(cursor);
    raiz.appendChild(fila);

    // El input original sigue en el formulario, pero oculto, con el PIN completo.
    const idOriginal = original.id;
    original.removeAttribute("id"); // que la etiqueta enfoque la primera casilla
    if (idOriginal) casillas[0].id = idOriginal;
    original.type = "hidden";
    original.after(raiz);

    let enfocada = null;

    function moverCursor() {
      const vacio = enfocada !== null && !valores[enfocada];
      cursor.hidden = !vacio;
      if (vacio) {
        const celda = celdas[enfocada];
        cursor.style.transform = `translate(${celda.offsetLeft + celda.offsetWidth / 2 - 1}px, -50%)`;
      }
    }

    function pintar(indice, borrando) {
      const celda = celdas[indice];
      const actual = celda.querySelector(".otp__digito");
      if (valores[indice] && !actual) {
        const digito = document.createElement("span");
        digito.className = "otp__digito";
        digito.textContent = "•";
        celda.querySelector(".otp__marca").appendChild(digito);
      } else if (!valores[indice] && actual) {
        if (borrando && !RutaEfectos.reducirMovimiento()) {
          actual.classList.add("otp__digito--sale");
          actual.addEventListener("animationend", () => actual.remove(), { once: true });
        } else {
          actual.remove();
        }
      }
      celda.dataset.lleno = valores[indice] ? "true" : "false";
      casillas[indice].value = valores[indice];
    }

    function confirmar(borrando = false) {
      casillas.forEach((_, i) => pintar(i, borrando));
      original.value = valores.join("");
      raiz.classList.remove("otp--error");
      moverCursor();
    }

    function enfocar(indice) {
      const casilla = casillas[Math.min(Math.max(indice, 0), largo - 1)];
      casilla.focus();
      casilla.select();
    }

    function rellenar(desde, digitos) {
      const cupo = Math.min(digitos.length, largo - desde);
      for (let i = 0; i < cupo; i++) valores[desde + i] = digitos[i];
      confirmar();
      enfocar(desde + cupo);
    }

    casillas.forEach((casilla, indice) => {
      casilla.addEventListener("input", () => {
        const digitos = casilla.value.split("").filter((c) => SOLO_DIGITO.test(c));
        if (!digitos.length) {
          valores[indice] = "";
          confirmar(true);
          return;
        }
        // Al escribir sobre una casilla llena queda "1" + "2": solo cuenta el nuevo.
        if (digitos.length === 2 && digitos[0] === valores[indice]) digitos.shift();
        if (digitos.length > 1) {
          rellenar(indice, digitos); // pegado o autocompletado de todo el código
          return;
        }
        valores[indice] = digitos[0];
        confirmar();
        enfocar(indice + 1);
      });

      casilla.addEventListener("keydown", (evento) => {
        if (evento.key === "Backspace") {
          evento.preventDefault();
          if (valores[indice]) {
            valores[indice] = "";
            confirmar(true);
          } else if (indice > 0) {
            valores[indice - 1] = "";
            confirmar(true);
            enfocar(indice - 1);
          }
        } else if (evento.key === "ArrowLeft") {
          evento.preventDefault();
          enfocar(indice - 1);
        } else if (evento.key === "ArrowRight") {
          evento.preventDefault();
          enfocar(indice + 1);
        }
      });

      casilla.addEventListener("paste", (evento) => {
        evento.preventDefault();
        const digitos = evento.clipboardData
          .getData("text")
          .split("")
          .filter((c) => SOLO_DIGITO.test(c));
        if (digitos.length) rellenar(indice, digitos);
      });

      // Un clic más allá del primer hueco cae en el hueco: el código queda seguido.
      casilla.addEventListener("pointerdown", (evento) => {
        const primerHueco = valores.findIndex((v) => !v);
        const destino = primerHueco === -1 ? indice : Math.min(indice, primerHueco);
        if (destino !== indice) {
          evento.preventDefault();
          enfocar(destino);
        }
      });

      casilla.addEventListener("focus", () => {
        enfocada = indice;
        casilla.select();
        moverCursor();
      });
    });

    fila.addEventListener("focusout", (evento) => {
      if (!fila.contains(evento.relatedTarget)) {
        enfocada = null;
        moverCursor();
      }
    });

    // form.reset() (lo hace auth.js tras entrar) limpia también las casillas.
    if (formulario) {
      formulario.addEventListener("reset", () => {
        setTimeout(() => {
          valores.fill("");
          confirmar();
        }, 0);
      });

      // Si el servidor rechaza el PIN, auth.js muestra un mensaje de error en
      // este mismo formulario: las casillas se sacuden y se ponen en rojo.
      const mensaje = formulario.querySelector(".empty-state");
      if (mensaje) {
        new MutationObserver(() => {
          if (mensaje.hidden) return;
          raiz.classList.remove("otp--error");
          void raiz.offsetWidth;
          raiz.classList.add("otp--error");
        }).observe(mensaje, { attributes: true, attributeFilter: ["hidden"], childList: true, characterData: true });
      }
    }

    return raiz;
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('.modal-auth input[name="pin"]').forEach(montar);
  });

  return { montar };
})();
