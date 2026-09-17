// Manejo del formulario "Planea en minutos".

const RutaFormularios = (() => {
  const form = document.getElementById("hero-form");

  function camposDe() {
    return {
      origen: form.querySelector('[name="origen"]'),
      destino: form.querySelector('[name="destino"]'),
      nombre: form.querySelector('[name="nombre"]'),
      presupuesto: form.querySelector('[name="presupuesto"]'),
      horasMax: form.querySelector('[name="horas_max"]'),
      chips: Array.from(form.querySelectorAll("[data-interes]")),
    };
  }

  function leerValores() {
    const campos = camposDe();
    return {
      origen: campos.origen.value,
      destino: campos.destino.value,
      nombre: campos.nombre.value,
      presupuesto: campos.presupuesto.value,
      horasMax: campos.horasMax.value,
      intereses: campos.chips.filter((c) => c.classList.contains("is-active")).map((c) => c.dataset.interes),
    };
  }

  function init(onSubmit) {
    if (!form) return;

    camposDe().chips.forEach((chip) => {
      chip.addEventListener("click", () => chip.classList.toggle("is-active"));
    });

    form.addEventListener("submit", (evento) => {
      evento.preventDefault();
      if (onSubmit) onSubmit(leerValores());
    });
  }

  return { init, obtenerValores: leerValores };
})();
