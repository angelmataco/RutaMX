"""M-05: copiar una ruta pública como base de una ruta propia (RF-13, 14 y 16).

El dueño de la copia siempre llega desde la sesión (M-10), nunca del cuerpo de
la petición. La copia la hace M-09 en una sola sentencia atómica; aquí solo se
validan los identificadores y los datos copiables, y se traducen los fallos a
mensajes seguros sin detalles de la base.
"""
from base_datos.repositorios import catalogo_repositorio
from base_datos.repositorios.catalogo_repositorio import ErrorMigracionPendiente
from v2.utilerias import ErrorRutaMX, ErrorValidacion, limpiar_texto

MENSAJE_NO_ENCONTRADA = "No se encontró la ruta."
MENSAJE_FALLO = "No se pudo copiar la ruta. Intenta de nuevo."
MENSAJE_MIGRACION = "La copia necesita la migración de la base de datos; todavía no se ha aplicado."
MENSAJE_DATOS = "La ruta no tiene datos válidos para copiarse."


class ErrorCopia(ErrorRutaMX):
    """Fallo seguro de la copia; el mensaje se puede mostrar al usuario."""


class RutaNoEncontrada(ErrorCopia):
    """Igual para rutas privadas e inexistentes."""


def _identificador(valor, mensaje):
    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        raise ErrorValidacion(mensaje)
    return valor


def _datos_copiables(detalle):
    # CA-07.2: no se crea nada si la ruta pública llegó con datos inválidos.
    try:
        for campo in ("nombre", "origen", "destino"):
            limpiar_texto(detalle.get(campo), campo)
        paradas = detalle.get("paradas")
        if not isinstance(paradas, list):
            raise ErrorValidacion(MENSAJE_DATOS)
        for parada in paradas:
            if not isinstance(parada, dict):
                raise ErrorValidacion(MENSAJE_DATOS)
            limpiar_texto(parada.get("nombre"), "parada")
    except ErrorValidacion:
        raise ErrorCopia(MENSAJE_DATOS) from None
    except AttributeError:
        raise ErrorCopia(MENSAJE_DATOS) from None


class CopiaRutas:
    """Repositorio inyectable con obtener_publica y copiar_publica."""

    def __init__(self, repositorio=None):
        self._repo = catalogo_repositorio if repositorio is None else repositorio

    def copiar(self, ruta_id, usuario_id):
        _identificador(ruta_id, "El identificador de la ruta no es válido.")
        _identificador(usuario_id, "El identificador de usuario no es válido.")
        try:
            detalle = self._repo.obtener_publica(ruta_id)
            if detalle is None:
                raise RutaNoEncontrada(MENSAJE_NO_ENCONTRADA)
            _datos_copiables(detalle)
            copia_id = self._repo.copiar_publica(ruta_id, usuario_id)
            if copia_id is None:
                # Dejó de ser pública entre la lectura y la copia.
                raise RutaNoEncontrada(MENSAJE_NO_ENCONTRADA)
            return {"id": copia_id, "nombre": limpiar_texto(detalle["nombre"], "nombre")}
        except ErrorCopia:
            raise
        except ErrorMigracionPendiente:
            raise ErrorCopia(MENSAJE_MIGRACION) from None
        except Exception:
            raise ErrorCopia(MENSAJE_FALLO) from None
