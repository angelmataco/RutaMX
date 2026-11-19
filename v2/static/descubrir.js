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
  const copiar = dialogo.querySelector('[data-copiar-ruta]');
  const avisoCopia = dialogo.querySelector('[data-copia-estado]');
  const sesionCopia = dialogo.querySelector('[data-copia-sesion]');
  const listaCopia = dialogo.querySelector('[data-copia-lista]');
  const csrf = document.querySelector('meta[name="rutamx-csrf"]').content;
  let rutaActual = null;
  function limpiarCopia() {
    rutaActual = null;
    copiar.hidden = true;
    copiar.disabled = false;
    avisoCopia.textContent = '';
    sesionCopia.hidden = true;
    listaCopia.hidden = true;
  }
  let consulta = 0;
  let consultaDetalle = 0;
  // Mapa del recorrido (RF-11 y RF-12): Leaflet y OpenStreetMap, los mismos que usa v1.
  const bloqueMapa = dialogo.querySelector('[data-mapa-bloque]');
  const avisoMapa = dialogo.querySelector('[data-mapa-estado]');
  const contenedorMapa = dialogo.querySelector('[data-mapa]');
  const pieMapa = dialogo.querySelector('[data-mapa-pie]');
  const LEAFLET_CSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
  const LEAFLET_JS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
  const TESELAS = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  const ESPERA_MAPA_MS = 8000;
  const MENSAJE_MAPA = 'El mapa no pudo cargarse. El resto de la ruta sigue disponible.';
  let mapa = null;
  let cargaLeaflet = null;
  let limpiezaCarga = null;
  let leafletCompleto = false;
  let relojMapa;
  function limpiarMapa() {
    clearTimeout(relojMapa);
    if (mapa) { mapa.remove(); mapa = null; }
    contenedorMapa.replaceChildren();
    contenedorMapa.hidden = true;
    pieMapa.hidden = true;
    avisoMapa.textContent = '';
    bloqueMapa.hidden = true;
  }
  function cargarLeaflet() {
    // window.L solo prueba que el script existe; la carga cuenta como completa cuando también cargaron los estilos.
    if (leafletCompleto && window.L) return Promise.resolve();
    if (cargaLeaflet) return cargaLeaflet;
    cargaLeaflet = new Promise((resolver, rechazar) => {
      const estilos = document.createElement('link');
      estilos.rel = 'stylesheet';
      estilos.href = LEAFLET_CSS;
      const nuevos = [estilos];
      const necesarios = window.L ? 1 : 2;
      let listos = 0;
      const reloj = setTimeout(() => rechazar(new Error('tiempo')), ESPERA_MAPA_MS);
      const falla = (motivo) => { clearTimeout(reloj); rechazar(new Error(motivo)); };
      const listo = () => {
        listos += 1;
        if (listos === necesarios) { clearTimeout(reloj); window.L ? resolver() : rechazar(new Error('sin L')); }
      };
      estilos.onload = listo;
      estilos.onerror = () => falla('estilos');
      if (!window.L) {
        const guion = document.createElement('script');
        guion.src = LEAFLET_JS;
        guion.onload = listo;
        guion.onerror = () => falla('red');
        nuevos.push(guion);
      }
      document.head.append(...nuevos);
      limpiezaCarga = () => { nuevos.forEach((e) => { if (e.remove) e.remove(); }); };
    }).then(() => { leafletCompleto = true; }, (error) => {
      cargaLeaflet = null;
      if (limpiezaCarga) limpiezaCarga();
      throw error;
    });
    return cargaLeaflet;
  }
  function falloDelMapa(instancia) {
    // Un temporizador o evento de un mapa anterior no debe tocar el vigente.
    if (instancia !== undefined && instancia !== mapa) return;
    clearTimeout(relojMapa);
    if (mapa) { mapa.remove(); mapa = null; }
    contenedorMapa.replaceChildren();
    contenedorMapa.hidden = true;
    pieMapa.hidden = true;
    avisoMapa.textContent = MENSAJE_MAPA;
  }
  function etiquetaPunto(punto) {
    const tipo = punto.tipo === 'origen' ? 'Origen' : punto.tipo === 'destino' ? 'Destino' : `Parada ${punto.orden - 1}`;
    const cuerpo = document.createElement('div');
    cuerpo.append(crear('strong', `${tipo}: `), document.createTextNode(punto.nombre));
    return cuerpo;
  }
  function dibujarMapa(puntos, omitidos) {
    const color = getComputedStyle(document.documentElement).getPropertyValue('--color-terracota').trim() || '#c85a32';
    contenedorMapa.hidden = false;
    const propio = window.L.map(contenedorMapa, {scrollWheelZoom: false});
    mapa = propio;
    let cargadas = 0;
    let errores = 0;
    const capa = window.L.tileLayer(TESELAS, {maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'});
    capa.on('tileload', () => { cargadas += 1; if (mapa === propio) clearTimeout(relojMapa); });
    capa.on('tileerror', () => { errores += 1; if (!cargadas && errores >= 3) falloDelMapa(propio); });
    capa.addTo(propio);
    const coordenadas = puntos.map((p) => [p.latitud, p.longitud]);
    window.L.polyline(coordenadas, {color, weight: 3}).addTo(propio);
    puntos.forEach((punto) => {
      const extremo = punto.tipo !== 'parada';
      window.L.circleMarker([punto.latitud, punto.longitud], {
        radius: 7, color, weight: 2, fillColor: color, fillOpacity: extremo ? 0.9 : 0,
      }).bindPopup(etiquetaPunto(punto)).addTo(propio);
    });
    const ajustar = () => {
      if (mapa !== propio) return;
      propio.invalidateSize();
      if (coordenadas.length === 1) propio.setView(coordenadas[0], 10);
      else propio.fitBounds(window.L.latLngBounds(coordenadas), {padding: [24, 24]});
    };
    ajustar();
    setTimeout(ajustar, 150);
    relojMapa = setTimeout(() => { if (!cargadas) falloDelMapa(propio); }, ESPERA_MAPA_MS);
    pieMapa.hidden = false;
    avisoMapa.textContent = omitidos
      ? (omitidos === 1 ? 'Se omitió 1 ubicación sin coordenadas válidas.'
        : `Se omitieron ${omitidos} ubicaciones sin coordenadas válidas.`)
      : '';
  }
  async function mostrarMapa(ruta, actual) {
    const puntos = Array.isArray(ruta.puntos_mapa) ? ruta.puntos_mapa : [];
    bloqueMapa.hidden = false;
    if (!puntos.length) {
      avisoMapa.textContent = 'Esta ruta no tiene ubicaciones para mostrar en el mapa.';
      return;
    }
    avisoMapa.textContent = 'Cargando mapa…';
    try {
      await cargarLeaflet();
      if (actual !== consultaDetalle || !dialogo.open) return;
      dibujarMapa(puntos, Number.isInteger(ruta.puntos_omitidos) ? ruta.puntos_omitidos : 0);
    } catch (error) {
      if (actual === consultaDetalle && dialogo.open) falloDelMapa();
    }
  }
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
    limpiarCopia();
    limpiarMapa();
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
      mostrarMapa(ruta, actual);
      rutaActual = ruta.id;
      copiar.hidden = false;
      avisoDetalle.textContent = ruta.paradas.length ? '' : 'Sin paradas intermedias.';
    } catch (error) {
      if (actual !== consultaDetalle || !dialogo.open) return;
      contenido.replaceChildren();
      avisoDetalle.textContent = errorSeguro(error);
    }
  }
  dialogo.querySelector('[data-cerrar-detalle]').addEventListener('click', () => dialogo.close());
  dialogo.addEventListener('close', () => { ++consultaDetalle; contenido.replaceChildren(); limpiarCopia(); limpiarMapa(); });
  copiar.addEventListener('click', async () => {
    if (rutaActual === null || copiar.disabled) return;
    const id = rutaActual;
    const actual = consultaDetalle;
    copiar.disabled = true;
    sesionCopia.hidden = true;
    listaCopia.hidden = true;
    avisoCopia.textContent = 'Copiando ruta…';
    try {
      const respuesta = await fetch(`/v2/descubrir/rutas/${encodeURIComponent(id)}/copiar`, {
        method: 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: {'X-RutaMX-CSRF': csrf},
      });
      const datos = await respuesta.json();
      if (actual !== consultaDetalle || !dialogo.open) return;
      if (respuesta.status === 401) {
        sesionCopia.hidden = false;
        avisoCopia.textContent = 'Inicia sesión para copiar esta ruta.';
        return;
      }
      if (!respuesta.ok) throw new Error(datos.error || 'No se pudo copiar la ruta. Intenta de nuevo.');
      avisoCopia.textContent = datos.mensaje;
      listaCopia.hidden = false;
    } catch (error) {
      if (actual === consultaDetalle && dialogo.open) avisoCopia.textContent = errorSeguro(error);
    } finally {
      if (actual === consultaDetalle) copiar.disabled = false;
    }
  });
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
