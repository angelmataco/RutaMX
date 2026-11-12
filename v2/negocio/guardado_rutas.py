"""Persistencia M-05/M-09 sin cambios de esquema ni persistencia del chat.

resumen.rutamx_v2 contiene la ruta estructurada completa y una versión de
formato. Los campos comunes siguen disponibles para lectores de v1.
El identificador guardado pertenece al contexto de sesión del llamador.
"""
from copy import deepcopy

from base_datos.repositorios import rutas_repositorio
from v2.utilerias import ErrorValidacion, limpiar_texto


class ErrorGuardado(ErrorValidacion):
    """Mensaje seguro de persistencia para la interfaz."""


def _identificador(valor):
    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        raise ErrorGuardado('El identificador no es válido.')
    return valor


def _ruta_valida(ruta):
    # La validación geográfica corresponde al gestor antes del guardado.
    if not isinstance(ruta, dict):
        raise ErrorGuardado('No hay una ruta válida para guardar.')
    for campo in ('origen', 'destino'):
        limpiar_texto(ruta.get(campo), campo)
    dias = ruta.get('duracion_dias')
    if not isinstance(dias, int) or isinstance(dias, bool) or dias <= 0:
        raise ErrorGuardado('La duración de la ruta no es válida.')
    if (not isinstance(ruta.get('paradas'), list)
            or not isinstance(ruta.get('intereses'), list)
            or not isinstance(ruta.get('origen_lugar'), dict)
            or not isinstance(ruta.get('destino_lugar'), dict)):
        raise ErrorGuardado('La ruta guardada no tiene el formato esperado.')
    return deepcopy(ruta)


class GuardadoRutas:
    """Repositorio inyectable; el dueño siempre procede de M-10."""

    def __init__(self, repositorio=None):
        self._repo = rutas_repositorio if repositorio is None else repositorio

    def guardar(self, ruta, usuario_id, ruta_id=None, nombre=None):
        _identificador(usuario_id)
        copia = _ruta_valida(ruta)
        nombre = limpiar_texto(nombre, 'nombre', obligatorio=False)
        if ruta_id is not None:
            _identificador(ruta_id)
            if not nombre:
                try:
                    anterior = self._repo.obtener_ruta(ruta_id, usuario_id)
                    if anterior is None:
                        raise ErrorGuardado('No se encontró la ruta guardada.')
                    nombre = anterior['nombre']
                except ErrorGuardado:
                    raise
                except Exception:
                    raise ErrorGuardado('No se pudo consultar la ruta guardada.') from None
        nombre = nombre or f"{copia['origen']} a {copia['destino']}"
        datos = {
            'nombre': nombre, 'origen': copia['origen'], 'destino': copia['destino'],
            'intereses': deepcopy(copia['intereses']), 'paradas': deepcopy(copia['paradas']),
            'resumen': {
                'origen': {'nombre': copia['origen']},
                'destino': {'nombre': copia['destino']},
                'rutamx_v2': {'version': 1, 'ruta': copia},
            },
        }
        if ruta_id is not None:
            _identificador(ruta_id)
        try:
            guardada = (self._repo.crear_ruta(datos, usuario_id) if ruta_id is None
                        else self._repo.actualizar_ruta(ruta_id, datos, usuario_id))
            if guardada is None:
                raise ErrorGuardado('No se encontró la ruta guardada.')
            return deepcopy(guardada)
        except ErrorGuardado:
            raise
        except Exception:
            raise ErrorGuardado('No se pudo guardar la ruta. Intenta de nuevo; tu ruta se conserva.') from None

    def listar(self, usuario_id):
        _identificador(usuario_id)
        try:
            return deepcopy(self._repo.listar_rutas_de_usuario(usuario_id))
        except Exception:
            raise ErrorGuardado('No se pudieron consultar tus rutas guardadas.') from None

    def recuperar(self, ruta_id, usuario_id):
        _identificador(usuario_id)
        _identificador(ruta_id)
        try:
            guardada = self._repo.obtener_ruta(ruta_id, usuario_id)
            if guardada is None:
                raise ErrorGuardado('No se encontró la ruta guardada.')
            contenido = guardada.get('resumen', {}).get('rutamx_v2', {})
            if contenido.get('version') != 1:
                raise ErrorGuardado('Esta ruta no tiene un formato compatible con Planear con IA.')
            return _ruta_valida(contenido.get('ruta'))
        except ErrorGuardado:
            raise
        except Exception:
            raise ErrorGuardado('No se pudo recuperar la ruta guardada.') from None
