// Selector de "Hora de salida" tipo rueda (como el de iOS), con scroll-snap
// nativo — sin librerías. Guarda el valor en formato 24h ("HH:MM") en el
// input oculto `hora_salida`, que es lo que ya lee form.js/main.js.

document.addEventListener("DOMContentLoaded", () => {
  const trigger = document.querySelector("[data-time-trigger]");
  const dialogo = document.querySelector("[data-modal-time]");
  const display = document.querySelector("[data-time-display]");
  const hidden = document.querySelector("[data-time-hidden]");
  const btnConfirmar = document.querySelector("[data-time-confirmar]");
  const btnLimpiar = document.querySelector("[data-time-limpiar]");

  if (!trigger || !dialogo || !hidden) return;

  const columnas = Array.from(dialogo.querySelectorAll("[data-wheel]")).map((col) => ({
    nombre: col.dataset.wheel,
    lista: col.querySelector("[data-wheel-list]"),
    items: Array.from(col.querySelectorAll("li[data-value]")),
  }));

  const ALTO_ITEM = 36;
  // El relleno de arriba/abajo (72px, ver .time-wheel-picker__pad en
  // styles.css) se calculó justo a la mitad del contenedor (180px) menos
  // medio ítem — por diseño, eso hace que centrar el ítem `i` sea
  // simplemente `scrollTop = i * ALTO_ITEM`, sin sumar/restar el relleno.

  function itemActivo(columna) {
    const scrollTop = columna.lista.parentElement.scrollTop;
    const indice = Math.round(scrollTop / ALTO_ITEM);
    const indiceAcotado = Math.max(0, Math.min(indice, columna.items.length - 1));
    return columna.items[indiceAcotado];
  }

  function marcarActivo(columna) {
    const activo = itemActivo(columna);
    columna.items.forEach((li) => li.classList.toggle("is-activo", li === activo));
    return activo;
  }

  function centrarEn(columna, valor) {
    const indice = columna.items.findIndex((li) => li.dataset.value === String(valor));
    if (indice === -1) return;
    columna.lista.parentElement.scrollTop = indice * ALTO_ITEM;
    marcarActivo(columna);
  }

  columnas.forEach((columna) => {
    const contenedor = columna.lista.parentElement;
    let temporizador = null;

    contenedor.addEventListener("scroll", () => {
      marcarActivo(columna);
      clearTimeout(temporizador);
      temporizador = setTimeout(() => {
        const activo = marcarActivo(columna);
        if (activo) contenedor.scrollTop = columna.items.indexOf(activo) * ALTO_ITEM;
      }, 120);
    });

    columna.items.forEach((li, indice) => {
      li.addEventListener("click", () => {
        contenedor.scrollTop = indice * ALTO_ITEM;
        marcarActivo(columna);
      });
    });
  });

  function valoresActuales() {
    const valores = {};
    columnas.forEach((columna) => {
      const activo = itemActivo(columna);
      if (activo) valores[columna.nombre] = activo.dataset.value;
    });
    return valores;
  }

  function a24Horas({ hora, minuto }) {
    return `${hora}:${minuto}`;
  }

  trigger.addEventListener("click", () => {
    if (typeof dialogo.showModal === "function") dialogo.showModal();

    // El diálogo debe estar visible (con layout real) antes de poder
    // hacer scroll dentro de él — si no, scrollTop se queda en 0.
    requestAnimationFrame(() => {
      if (hidden.value) {
        const [hora, minuto] = hidden.value.split(":");
        centrarEn(columnas.find((c) => c.nombre === "hora"), hora);
        centrarEn(columnas.find((c) => c.nombre === "minuto"), minuto);
      } else {
        centrarEn(columnas.find((c) => c.nombre === "hora"), "08");
        centrarEn(columnas.find((c) => c.nombre === "minuto"), "00");
      }
    });
  });

  btnConfirmar.addEventListener("click", () => {
    const valores = valoresActuales();
    if (valores.hora && valores.minuto) {
      hidden.value = a24Horas(valores);
      display.textContent = a24Horas(valores);
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
    }
    dialogo.close();
  });

  if (btnLimpiar) {
    btnLimpiar.addEventListener("click", () => {
      hidden.value = "";
      display.textContent = "Elegir hora";
      hidden.dispatchEvent(new Event("change", { bubbles: true }));
      dialogo.close();
    });
  }
});
