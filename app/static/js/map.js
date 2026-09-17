// Todo lo relacionado al mapa: Leaflet + OpenStreetMap para la base, y
// Leaflet Routing Machine + OSRM para trazar la ruta real por carretera
// pasando por origen, paradas intermedias y destino.
// TODO: cuando se agregue navegación en vivo (tipo Waze/Google Maps), este
// módulo es el punto de partida para mostrar la posición del usuario sobre
// la ruta ya calculada.

const RutaMapa = (() => {
  const CENTRO_MEXICO = [23.6345, -102.5528];
  const COLOR_RUTA = "#c76a4c";
  const OSRM_SERVICE_URL = "https://router.project-osrm.org/route/v1";

  let mapa = null;
  let control = null;
  let capaRespaldo = null;

  function init(elementId) {
    const contenedor = document.getElementById(elementId);
    if (!contenedor || mapa) return;

    mapa = L.map(elementId, { scrollWheelZoom: false }).setView(CENTRO_MEXICO, 5);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(mapa);
  }

  function crearIconoPunto(etiqueta, color) {
    return L.divIcon({
      className: "mapa-marcador",
      html: `<span style="display:flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:${color};color:#fff;font-weight:700;font-size:12px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.25);">${etiqueta}</span>`,
      iconSize: [26, 26],
      iconAnchor: [13, 13],
    });
  }

  function iconoDelPunto(indice, total) {
    if (indice === 0) return crearIconoPunto("A", "#1f3327");
    if (indice === total - 1) return crearIconoPunto("B", COLOR_RUTA);
    return crearIconoPunto(String(indice), COLOR_RUTA);
  }

  function limpiarRespaldo() {
    if (capaRespaldo) {
      mapa.removeLayer(capaRespaldo);
      capaRespaldo = null;
    }
  }

  function dibujarLineaRecta(puntos) {
    limpiarRespaldo();

    const latlngs = puntos.map((p) => [p.lat, p.lon]);
    capaRespaldo = L.layerGroup(
      puntos.map((p, i) =>
        L.marker([p.lat, p.lon], { icon: iconoDelPunto(i, puntos.length) }).bindPopup(p.nombre || "")
      )
    ).addTo(mapa);

    L.polyline(latlngs, { color: COLOR_RUTA, weight: 3, dashArray: "6 8" }).addTo(capaRespaldo);
    mapa.fitBounds(L.latLngBounds(latlngs), { padding: [40, 40] });
  }

  function actualizarRuta(puntos) {
    if (!mapa || !puntos || puntos.length < 2) return;

    limpiarRespaldo();

    const waypoints = puntos.map((p) => L.Routing.waypoint(L.latLng(p.lat, p.lon), p.nombre));

    if (!control) {
      control = L.Routing.control({
        waypoints,
        router: L.Routing.osrmv1({ serviceUrl: OSRM_SERVICE_URL }),
        addWaypoints: false,
        draggableWaypoints: false,
        fitSelectedRoutes: true,
        show: false,
        lineOptions: { styles: [{ color: COLOR_RUTA, weight: 4, opacity: 0.85 }] },
        createMarker: (i, waypoint, total) =>
          L.marker(waypoint.latLng, { icon: iconoDelPunto(i, total) }).bindPopup(waypoint.name || ""),
      })
        .on("routingerror", () => dibujarLineaRecta(puntos))
        .addTo(mapa);
    } else {
      control.setWaypoints(waypoints);
    }
  }

  function invalidarTamano() {
    if (mapa) mapa.invalidateSize();
  }

  return { init, actualizarRuta, invalidarTamano };
})();
