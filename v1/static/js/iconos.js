// Iconos a medida de RutaMX. El dibujo vive en templates/partials/iconos_sprite.html;
// aquí solo se arma la etiqueta <svg><use> para usarlos desde JS.
//
//   RutaIconos.html("comer", 16)            -> string con el <svg>
//   RutaIconos.nodo("comer", "Comer", 16)   -> <span> con el icono y el texto (textContent, sin inyección)

window.RutaIconos = (() => {
  function html(nombre, tam = 16) {
    return `<svg class="icono" width="${tam}" height="${tam}" aria-hidden="true" focusable="false"><use href="#i-${nombre}"/></svg>`;
  }

  function nodo(nombre, texto, tam = 16) {
    const span = document.createElement("span");
    span.className = texto ? "icono-texto" : "icono-texto icono-texto--solo";
    span.insertAdjacentHTML("afterbegin", html(nombre, tam));
    if (texto) span.append(document.createTextNode(texto));
    return span;
  }

  return { html, nodo };
})();
