"""M-08 Verificador geográfico: único módulo que conoce al proveedor de lugares.

Implementa el contrato que M-05 usa para D-03 (a y c): `verificar(nombre)`
devuelve `{"id": str, "latitud": float, "longitud": float}`, `None` si el
lugar no se puede identificar, o lanza `ErrorServicioExterno` si el servicio
no responde. El proveedor es Nominatim (OpenStreetMap), el mismo que ya usa
el proyecto para coordenadas.

Reglas de uso de Nominatim que se respetan: `User-Agent` que identifica la
aplicación (genérico, sin datos personales), como máximo una petición por
segundo, resultados en caché dentro de la instancia y sin reintentos
automáticos. Solo se envía el nombre del lugar que escribió el usuario.
La búsqueda se limita a México (`countrycodes=mx`) porque RutaMX planea
roadtrips por México; un lugar ambiguo se resuelve con el primer resultado
del proveedor (el de mayor importancia).

No importa nada de v1. El transporte es inyectable para probar sin red.
"""

import time

from v2.utilerias import ErrorServicioExterno, limpiar_texto

URL_NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "RutaMX-v2 (proyecto escolar)"
PAIS = "mx"
TIMEOUT_SEGUNDOS = 10
INTERVALO_MINIMO_SEGUNDOS = 1.0
ERROR_SERVICIO = "No se pudo consultar el servicio de lugares. Intenta de nuevo."


class VerificadorNominatim:
    def __init__(self, sesion=None, *, reloj=time.monotonic, dormir=time.sleep):
        if sesion is None:
            import requests
            sesion = requests.Session()
        self._sesion = sesion
        self._reloj = reloj
        self._dormir = dormir
        self._ultima = None
        self._cache = {}

    def _respetar_intervalo(self):
        if self._ultima is not None:
            falta = INTERVALO_MINIMO_SEGUNDOS - (self._reloj() - self._ultima)
            if falta > 0:
                self._dormir(falta)
        self._ultima = self._reloj()

    def verificar(self, nombre):
        nombre = limpiar_texto(nombre, "lugar")
        llave = nombre.casefold()
        if llave in self._cache:
            return dict(self._cache[llave])
        self._respetar_intervalo()
        try:
            respuesta = self._sesion.get(
                URL_NOMINATIM,
                params={"q": nombre, "format": "jsonv2", "limit": 1, "countrycodes": PAIS},
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT_SEGUNDOS,
            )
            respuesta.raise_for_status()
            resultados = respuesta.json()
        except Exception:
            # Sin detalle del transporte: puede incluir la URL o el texto buscado.
            raise ErrorServicioExterno(ERROR_SERVICIO) from None
        if not isinstance(resultados, list):
            raise ErrorServicioExterno(ERROR_SERVICIO)
        if not resultados:
            return None
        lugar = self._normalizar(resultados[0])
        self._cache[llave] = lugar
        return dict(lugar)

    @staticmethod
    def _normalizar(crudo):
        try:
            return {
                "id": f"{crudo['osm_type']}:{int(crudo['osm_id'])}",
                "latitud": float(crudo["lat"]),
                "longitud": float(crudo["lon"]),
            }
        except (KeyError, TypeError, ValueError):
            # Respuesta incompleta: M-05 la rechazará por falta de id o coordenadas.
            raise ErrorServicioExterno(ERROR_SERVICIO) from None
