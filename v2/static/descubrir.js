/* M-01: solo presenta datos públicos del servidor. */
document.addEventListener('DOMContentLoaded', () => {
  const raiz = document.querySelector('[data-descubrir]');
  if (!raiz) return;
  const formulario = raiz.querySelector('[data-filtros]');
  const lista = raiz.querySelector('[data-catalogo-lista]');
  const estado = raiz.querySelector('[data-catalogo-estado]');
  const dialogo = document.querySelector('[data-detalle]');
  const contenido = dialogo.querySelector('[data-detalle-contenido]');
  const avisoDetalle = dialogo.querySelector('[data-detalle-estado]');
  let consulta = 0;
  let consultaDetalle = 0;
  let demoraBusqueda;
  function crear(tipo, texto, clase) {
    const elemento = document.createElement(tipo);
    if (texto !== undefined) elemento.textContent = texto;
    if (clase) elemento.className = clase;
    return elemento;
  }
  function errorSeguro(error) {
    return error instanceof TypeError || error instanceof SyntaxError
      ? 'No se pudo conectar con RutaMX. Intenta de nuevo.' : error.message;
  }
  async function obtener(url) {
    const respuesta = await fetch(url, {credentials: 'same-origin', cache: 'no-store'});
    const datos = await respuesta.json();
    if (!respuesta.ok) throw new Error(datos.error || 'No se pudo consultar el catálogo.');
    return datos;
  }
  async function detalle(id) {
    const actual = ++consultaDetalle;
    contenido.replaceChildren();
    avisoDetalle.textContent = 'Cargando detalle…';
    if (!dialogo.open) dialogo.showModal();
    try {
      const datos = await obtener(`/v2/descubrir/rutas/${encodeURIComponent(id)}`);
      if (actual !== consultaDetalle || !dialogo.open) return;
      const ruta = datos.ruta;
      contenido.append(crear('h3', ruta.nombre), crear('p', `${ruta.origen} → ${ruta.destino}`),
        crear('p', `${ruta.duracion_dias} días · ${ruta.autor}`), crear('p', ruta.descripcion));
      const paradas = crear('ol');
      ruta.paradas.forEach((parada) => {
        const punto = crear('li');
        punto.append(crear('strong', parada.nombre), crear('p', parada.descripcion));
        paradas.append(punto);
      });
      contenido.append(paradas);
      avisoDetalle.textContent = ruta.paradas.length ? '' : 'Sin paradas intermedias.';
    } catch (error) {
      if (actual !== consultaDetalle || !dialogo.open) return;
      contenido.replaceChildren();
      avisoDetalle.textContent = errorSeguro(error);
    }
  }
  dialogo.querySelector('[data-cerrar-detalle]').addEventListener('click', () => dialogo.close());
  dialogo.addEventListener('close', () => { ++consultaDetalle; contenido.replaceChildren(); });
  async function buscar() {
    clearTimeout(demoraBusqueda);
    const actual = ++consulta;
    ++consultaDetalle;
    if (dialogo.open) dialogo.close();
    lista.replaceChildren();
    lista.setAttribute('aria-busy', 'true');
    estado.textContent = 'Buscando rutas…';
    const parametros = new URLSearchParams(new FormData(formulario));
    try {
      const datos = await obtener(`/v2/descubrir/rutas?${parametros}`);
      if (actual !== consulta) return;
      datos.rutas.forEach((ruta) => {
        const tarjeta = crear('article', undefined, 'card descubrir-tarjeta');
        tarjeta.append(crear('h3', ruta.nombre), crear('p', `${ruta.origen} → ${ruta.destino}`),
          crear('p', `${ruta.duracion_dias} días · ${ruta.num_paradas} paradas`),
          crear('p', `Por ${ruta.autor}`, 'card__note'));
        const boton = crear('button', 'Ver detalle', 'btn btn--ghost');
        boton.type = 'button';
        boton.setAttribute('aria-label', `Ver detalle de ${ruta.nombre}`);
        boton.addEventListener('click', () => detalle(ruta.id));
        tarjeta.append(boton);
        lista.append(tarjeta);
      });
      estado.textContent = datos.rutas.length
        ? (datos.total === 1 ? '1 ruta encontrada.' : `${datos.total} rutas encontradas.`) : datos.mensaje;
    } catch (error) {
      if (actual !== consulta) return;
      lista.replaceChildren();
      estado.textContent = errorSeguro(error);
    } finally {
      if (actual === consulta) lista.setAttribute('aria-busy', 'false');
    }
  }
  formulario.addEventListener('submit', (evento) => {
    evento.preventDefault();
    if (formulario.reportValidity()) buscar();
  });
  formulario.addEventListener('input', (evento) => {
    // Invalidar inmediatamente: una respuesta anterior no debe pintar mientras
    // el nuevo valor es inválido o antes de la siguiente petición.
    ++consulta;
    clearTimeout(demoraBusqueda);
    if (formulario.checkValidity()) {
      if (evento.target.name === 'q') demoraBusqueda = setTimeout(buscar, 250);
      else buscar();
    }
    else { lista.replaceChildren(); estado.textContent = 'Revisa los filtros antes de buscar.'; lista.setAttribute('aria-busy', 'false'); }
  });
  formulario.addEventListener('reset', () => {
    ++consulta;
    clearTimeout(demoraBusqueda);
    // Una tarea posterior deja terminar el restablecimiento nativo de campos;
    // un microtask puede leer los valores anteriores al reset.
    setTimeout(buscar, 0);
  });
  buscar();
});
