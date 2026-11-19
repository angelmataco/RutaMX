"""M-05: copiar una ruta pública. Repositorio falso; sin base, red ni .env."""
import pytest

from base_datos.repositorios.catalogo_repositorio import ErrorMigracionPendiente
from v2.negocio.copia_rutas import (
    CopiaRutas, ErrorCopia, MENSAJE_DATOS, MENSAJE_FALLO, MENSAJE_MIGRACION,
    MENSAJE_NO_ENCONTRADA, RutaNoEncontrada,
)
from v2.utilerias import ErrorValidacion


def detalle(**cambios):
    datos = {"id": 7, "nombre": " Ruta ficticia ", "origen": "Ciudad Uno", "destino": "Ciudad Dos",
             "duracion_dias": 3, "paradas": [{"nombre": "Parada A"}, {"nombre": "Parada B"}]}
    datos.update(cambios)
    return datos


class RepoFalso:
    def __init__(self, ruta=None, copia_id=99, error_lectura=None, error_copia=None):
        self.ruta = ruta
        self.copia_id = copia_id
        self.error_lectura = error_lectura
        self.error_copia = error_copia
        self.copias = []

    def obtener_publica(self, ruta_id):
        if self.error_lectura:
            raise self.error_lectura
        return self.ruta

    def copiar_publica(self, ruta_id, usuario_id):
        self.copias.append((ruta_id, usuario_id))
        if self.error_copia:
            raise self.error_copia
        return self.copia_id


def test_copia_devuelve_id_y_nombre_limpio():
    repo = RepoFalso(detalle())
    assert CopiaRutas(repo).copiar(7, 3) == {"id": 99, "nombre": "Ruta ficticia"}
    assert repo.copias == [(7, 3)]


def test_ruta_sin_paradas_se_puede_copiar():
    repo = RepoFalso(detalle(paradas=[]))
    assert CopiaRutas(repo).copiar(7, 3)["id"] == 99


@pytest.mark.parametrize("ruta_id,usuario_id", [
    (None, 1), ("7", 1), (7.0, 1), (True, 1), (0, 1), (-3, 1),
    (7, None), (7, "1"), (7, True), (7, 0), (7, -1),
])
def test_identificadores_invalidos_no_consultan_ni_copian(ruta_id, usuario_id):
    repo = RepoFalso(detalle())
    with pytest.raises(ErrorValidacion):
        CopiaRutas(repo).copiar(ruta_id, usuario_id)
    assert repo.copias == []


def test_ruta_inexistente_o_privada_no_se_copia():
    repo = RepoFalso(None)
    with pytest.raises(RutaNoEncontrada, match=MENSAJE_NO_ENCONTRADA):
        CopiaRutas(repo).copiar(7, 3)
    assert repo.copias == []


def test_deja_de_ser_publica_entre_lectura_y_copia():
    repo = RepoFalso(detalle(), copia_id=None)
    with pytest.raises(RutaNoEncontrada, match=MENSAJE_NO_ENCONTRADA):
        CopiaRutas(repo).copiar(7, 3)


@pytest.mark.parametrize("cambios", [
    {"nombre": ""}, {"nombre": None}, {"nombre": 5}, {"origen": "  "}, {"destino": None},
    {"paradas": None}, {"paradas": "A"}, {"paradas": ["A"]}, {"paradas": [None]},
    {"paradas": [{}]}, {"paradas": [{"nombre": ""}]}, {"paradas": [{"nombre": 3}]},
])
def test_datos_invalidos_se_rechazan_sin_copiar(cambios):
    repo = RepoFalso(detalle(**cambios))
    with pytest.raises(ErrorCopia, match=MENSAJE_DATOS):
        CopiaRutas(repo).copiar(7, 3)
    assert repo.copias == []


def test_detalle_que_no_es_diccionario_se_rechaza_sin_copiar():
    repo = RepoFalso(["no es un diccionario"])
    with pytest.raises(ErrorCopia, match=MENSAJE_DATOS):
        CopiaRutas(repo).copiar(7, 3)
    assert repo.copias == []


@pytest.mark.parametrize("origen_fallo", ["lectura", "copia"])
def test_fallo_del_repositorio_es_mensaje_seguro(origen_fallo):
    error = RuntimeError("INSERT secreto https://privado")
    repo = RepoFalso(detalle(), **{f"error_{origen_fallo}": error})
    with pytest.raises(ErrorCopia) as info:
        CopiaRutas(repo).copiar(7, 3)
    assert str(info.value) == MENSAJE_FALLO
    assert info.value.__suppress_context__
    assert "secreto" not in str(info.value)


def test_migracion_pendiente_tiene_mensaje_propio():
    repo = RepoFalso(detalle(), error_copia=ErrorMigracionPendiente("columna interna"))
    with pytest.raises(ErrorCopia) as info:
        CopiaRutas(repo).copiar(7, 3)
    assert str(info.value) == MENSAJE_MIGRACION
    assert "interna" not in str(info.value)


def test_el_servicio_por_defecto_usa_el_repositorio_del_catalogo():
    from base_datos.repositorios import catalogo_repositorio
    assert CopiaRutas()._repo is catalogo_repositorio
