// Selector de "burbujas" para personas y horas máximas de manejo — una
// fila de opciones predefinidas (deslizable) en vez de una lista plana de
// <datalist>, con un botón "Otro" para escribir un valor exacto distinto.

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-bubble-picker]").forEach((picker) => {
    const campo = picker.closest(".field");
    const input = campo.querySelector("[data-bubble-input]");
    const burbujas = Array.from(picker.querySelectorAll("[data-bubble-valor]"));
    const btnOtro = picker.querySelector("[data-bubble-otro]");
    if (!input) return;

    function marcar(valor) {
      let coincide = false;
      burbujas.forEach((b) => {
        const esta = b.dataset.bubbleValor === String(valor);
        b.classList.toggle("is-activa", esta);
        if (esta) coincide = true;
      });
      if (btnOtro) btnOtro.classList.toggle("is-activa", !coincide && Boolean(valor));
      input.hidden = !btnOtro || coincide || !valor;
    }

    burbujas.forEach((burbuja) => {
      burbuja.addEventListener("click", () => {
        input.value = burbuja.dataset.bubbleValor;
        marcar(burbuja.dataset.bubbleValor);
        input.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });

    if (btnOtro) {
      btnOtro.addEventListener("click", () => {
        input.hidden = false;
        burbujas.forEach((b) => b.classList.remove("is-activa"));
        btnOtro.classList.add("is-activa");
        input.focus();
      });
    }

    input.addEventListener("input", () => {
      const coincide = burbujas.some((b) => b.dataset.bubbleValor === input.value);
      if (coincide) marcar(input.value);
    });

    // Estado inicial: si el valor por default ya coincide con una
    // burbuja, resaltarla; si no, dejar visible el campo de "otro".
    marcar(input.value);
  });
});
