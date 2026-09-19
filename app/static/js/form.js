// Manejo del formulario "Planea en minutos".

const RutaFormularios = (() => {
  const form = document.getElementById("hero-form");

  function camposDe() {
    return {
      origen: form.querySelector('[name="origen"]'),
      destino: form.querySelector('[name="destino"]'),
      nombre: form.querySelector('[name="nombre"]'),
      personas: form.querySelector('[name="personas"]'),
      comidas: document.querySelector('[data-modal-ajustes] [name="comidas"]'),
      noches: document.querySelector('[data-modal-ajustes] [name="noches"]'),
      horasMax: form.querySelector('[name="horas_max"]'),
      horaSalida: form.querySelector('[name="hora_salida"]'),
      chips: Array.from(form.querySelectorAll("[data-interes]")),
    };
  }

  function valorDeAjuste(nombre) {
    const activo = document.querySelector(`[data-ajuste="${nombre}"].is-active`);
    return activo ? activo.dataset.valor : "";
  }

  // Preferencias de gasto tal como las espera el backend (solo lo que se llenó).
  function leerAjustes() {
    const v = leerValores();
    const ajustes = { hora_salida: v.horaSalida };
    if (v.personas) ajustes.personas = Number(v.personas);
    if (v.comidas !== "") ajustes.comidas = Number(v.comidas);
    if (v.noches !== "") ajustes.noches = Number(v.noches);
    if (v.tipoCoche) ajustes.tipo_coche = v.tipoCoche;
    if (v.gasolina) ajustes.gasolina = v.gasolina;
    return ajustes;
  }

  function leerValores() {
    const campos = camposDe();
    return {
      origen: campos.origen.value,
      destino: campos.destino.value,
      nombre: campos.nombre.value,
      personas: campos.personas.value,
      comidas: campos.comidas.value,
      noches: campos.noches.value,
      tipoCoche: valorDeAjuste("tipo_coche"),
      gasolina: valorDeAjuste("gasolina"),
      horasMax: campos.horasMax.value,
      horaSalida: campos.horaSalida.value,
      intereses: campos.chips.filter((c) => c.classList.contains("is-active")).map((c) => c.dataset.interes),
    };
  }

  // "⚙️ Ajustes de gasto" o "⚙️ Ajustes de gasto · 2" según lo que se haya tocado.
  function actualizarBotonAjustes() {
    const boton = document.querySelector("[data-abrir-ajustes-gasto]");
    if (!boton) return;
    const c = camposDe();
    const activos =
      document.querySelectorAll("[data-ajuste].is-active").length +
      (c.comidas.value !== "" ? 1 : 0) +
      (c.noches.value !== "" ? 1 : 0);
    boton.textContent = activos ? `⚙️ Ajustes de gasto · ${activos}` : "⚙️ Ajustes de gasto";
    boton.classList.toggle("is-activo", activos > 0);
  }

  function init(onSubmit) {
    if (!form) return;

    camposDe().chips.forEach((chip) => {
      chip.addEventListener("click", () => chip.classList.toggle("is-active"));
    });

    // Grupos de opciones de una sola elección (coche, gasolina): tocar la
    // activa la desmarca y se vuelve al valor típico.
    document.querySelectorAll("[data-chips-unico]").forEach((grupo) => {
      grupo.querySelectorAll(".chip").forEach((chip) => {
        chip.addEventListener("click", () => {
          const estabaActivo = chip.classList.contains("is-active");
          grupo.querySelectorAll(".chip").forEach((c) => c.classList.remove("is-active"));
          if (!estabaActivo) chip.classList.add("is-active");
        });
      });
    });

    // Botón pequeño "Ajustes de gasto": abre el diálogo y muestra cuántos
    // ajustes hay activos.
    const dialogoAjustes = document.querySelector("[data-modal-ajustes]");
    const botonAjustes = document.querySelector("[data-abrir-ajustes-gasto]");
    if (dialogoAjustes && botonAjustes) {
      botonAjustes.addEventListener("click", () => dialogoAjustes.showModal());
      dialogoAjustes.addEventListener("close", actualizarBotonAjustes);
    }

    form.addEventListener("submit", (evento) => {
      evento.preventDefault();
      if (onSubmit) onSubmit(leerValores());
    });
  }

  return { init, obtenerValores: leerValores, obtenerAjustes: leerAjustes, actualizarBotonAjustes };
})();
