"""Persistencia simulada: aislamiento, errores e ida y vuelta sin red."""
from copy import deepcopy
from unittest.mock import Mock

import pytest

from v2.negocio.guardado_rutas import GuardadoRutas, ErrorGuardado


@pytest.fixture
def ruta():
    lugar = {'id': 'ficticio', 'latitud': 1.0, 'longitud': 2.0}
    return {'origen': 'A', 'destino': 'B', 'origen_lugar': lugar,
            'destino_lugar': {**lugar, 'id': 'otro'}, 'duracion_dias': 3,
            'intereses': ['cultura'], 'paradas': [
                {'nombre': 'C', 'descripcion': 'Visita', 'lugar': {**lugar, 'id': 'C'}}]}


class RepositorioFalso:
    def __init__(self):
        self.filas = {}

    def crear_ruta(self, datos, usuario):
        fila = deepcopy({**datos, 'id': len(self.filas) + 1, 'usuario_id': usuario})
        self.filas[fila['id']] = fila
        return deepcopy(fila)

    def actualizar_ruta(self, identificador, datos, usuario):
        if self.obtener_ruta(identificador, usuario) is None:
            return None
        self.filas[identificador] = deepcopy({**datos, 'id': identificador, 'usuario_id': usuario})
        return deepcopy(self.filas[identificador])

    def obtener_ruta(self, identificador, usuario):
        fila = self.filas.get(identificador)
        return deepcopy(fila) if fila and fila['usuario_id'] == usuario else None

    def listar_rutas_de_usuario(self, usuario):
        return deepcopy([f for f in self.filas.values() if f['usuario_id'] == usuario])


def test_ida_y_vuelta_completa_y_actualizacion_misma_fila(ruta):
    repo = RepositorioFalso()
    servicio = GuardadoRutas(repo)
    original = deepcopy(ruta)
    fila = servicio.guardar(ruta, 1)
    assert servicio.recuperar(fila['id'], 1) == original
    ruta['paradas'].insert(0, deepcopy(ruta['paradas'][0]))
    ruta['duracion_dias'] = 4
    nueva = servicio.guardar(ruta, 1, fila['id'], nombre='Mi viaje')
    assert nueva['id'] == fila['id'] and len(repo.filas) == 1
    assert servicio.recuperar(fila['id'], 1) == ruta
    ruta['paradas'].clear()
    assert len(servicio.recuperar(fila['id'], 1)['paradas']) == 2


def test_usuario_ajeno_no_lista_lee_ni_actualiza(ruta):
    repo = RepositorioFalso()
    s = GuardadoRutas(repo)
    fila = s.guardar(ruta, 1)
    assert s.listar(2) == []
    with pytest.raises(ErrorGuardado):
        s.recuperar(fila['id'], 2)
    with pytest.raises(ErrorGuardado):
        s.guardar(ruta, 2, fila['id'])
    assert s.recuperar(fila['id'], 1) == ruta


@pytest.mark.parametrize('operacion', ['guardar', 'listar', 'recuperar'])
def test_fallos_no_filtran_detalle(ruta, operacion):
    repo = Mock()
    for metodo in ('crear_ruta', 'listar_rutas_de_usuario', 'obtener_ruta'):
        getattr(repo, metodo).side_effect = RuntimeError('SECRETO')
    s = GuardadoRutas(repo)
    with pytest.raises(ErrorGuardado) as info:
        if operacion == 'guardar':
            s.guardar(ruta, 1)
        elif operacion == 'listar':
            s.listar(1)
        else:
            s.recuperar(1, 1)
    assert 'SECRETO' not in str(info.value)


@pytest.mark.parametrize('usuario', [None, True, 0, -1, '1'])
def test_sin_usuario_valido_no_escribe(ruta, usuario):
    repo = Mock()
    with pytest.raises(ErrorGuardado):
        GuardadoRutas(repo).guardar(ruta, usuario)
    repo.crear_ruta.assert_not_called()


def test_ruta_v1_sin_contenedor_devuelve_error_seguro():
    repo = Mock()
    repo.obtener_ruta.return_value = {'resumen': {}}
    with pytest.raises(ErrorGuardado, match='compatible'):
        GuardadoRutas(repo).recuperar(1, 1)


def test_resumen_compatible_con_lector_v1_y_ruta_v2_intacta(ruta):
    servicio = GuardadoRutas(RepositorioFalso())
    fila = servicio.guardar(ruta, 1)
    assert fila['resumen']['origen']['nombre'] == ruta['origen']
    assert fila['resumen']['destino']['nombre'] == ruta['destino']
    assert servicio.recuperar(fila['id'], 1) == ruta


def test_actualizar_sin_nombre_conserva_nombre_personalizado(ruta):
    servicio = GuardadoRutas(RepositorioFalso())
    fila = servicio.guardar(ruta, 1, nombre='Vacaciones culturales')
    ruta['duracion_dias'] = 5
    actualizada = servicio.guardar(ruta, 1, ruta_id=fila['id'])
    assert actualizada['nombre'] == 'Vacaciones culturales'
    assert servicio.recuperar(fila['id'], 1) == ruta
