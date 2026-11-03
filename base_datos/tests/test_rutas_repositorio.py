"""Pruebas de M-09 Repositorio de rutas (crear, obtener, listar).

Las de validación no tocan la base. Las de integración usan el PostgreSQL
desechable de `RUTAMX_TEST_DB_URL` (ver conftest.py); sin él se omiten.
Todos los datos son ficticios.
"""

import copy

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from base_datos.modelos import RutaGuardada
from base_datos.repositorios import rutas_repositorio as repo
from base_datos.repositorios.rutas_repositorio import (
    ErrorRepositorio,
    crear_ruta,
    listar_rutas_de_usuario,
    obtener_ruta,
)

RUTA_FICTICIA = {
    "nombre": "Ruta de prueba",
    "origen": "Ciudad Uno",
    "destino": "Ciudad Dos",
    "presupuesto": 1500.0,
    "intereses": ["playas", "comida"],
    "resumen": {"distancia_km": 120},
    "paradas": [{"nombre": "Parada B"}, {"nombre": "Parada A"}, {"nombre": "Parada C"}],
}


def ruta(**cambios):
    datos = copy.deepcopy(RUTA_FICTICIA)
    datos.update(cambios)
    return datos


def quitar(campo):
    datos = copy.deepcopy(RUTA_FICTICIA)
    del datos[campo]
    return datos


def contar_rutas(bd):
    return bd.session.query(RutaGuardada).count()


# ---------------------------------------------------------------- validación
# PR-02 (parte unitaria): no necesitan base de datos.

@pytest.mark.parametrize("campo", ["nombre", "origen", "destino"])
@pytest.mark.parametrize("valor", [None, "", "   ", 123, ["x"]])
def test_crear_rechaza_texto_obligatorio_invalido(campo, valor):
    with pytest.raises(ErrorRepositorio):
        crear_ruta(ruta(**{campo: valor}), usuario_id=1)


@pytest.mark.parametrize("campo", ["nombre", "origen", "destino", "paradas"])
def test_crear_rechaza_campo_obligatorio_omitido(campo):
    with pytest.raises(ErrorRepositorio):
        crear_ruta(quitar(campo), usuario_id=1)


@pytest.mark.parametrize("valor", [None, "texto", {"a": 1}, 5])
def test_crear_rechaza_paradas_que_no_son_lista(valor):
    with pytest.raises(ErrorRepositorio):
        crear_ruta(ruta(paradas=valor), usuario_id=1)


@pytest.mark.parametrize("datos", [None, "ruta", [1, 2]])
def test_crear_rechaza_datos_que_no_son_diccionario(datos):
    with pytest.raises(ErrorRepositorio):
        crear_ruta(datos, usuario_id=1)


@pytest.mark.parametrize("usuario_id", [None, "1", 1.5, True])
def test_usuario_id_invalido_se_rechaza_en_las_tres_operaciones(usuario_id):
    with pytest.raises(ErrorRepositorio):
        crear_ruta(ruta(), usuario_id=usuario_id)
    with pytest.raises(ErrorRepositorio):
        obtener_ruta(1, usuario_id)
    with pytest.raises(ErrorRepositorio):
        listar_rutas_de_usuario(usuario_id)


@pytest.mark.parametrize("ruta_id", [None, "1", 2.5, True])
def test_obtener_rechaza_ruta_id_invalido(ruta_id):
    with pytest.raises(ErrorRepositorio):
        obtener_ruta(ruta_id, 1)


# --------------------------------------------------------------- integración

def test_pr01_crear_devuelve_diccionario_asociado_al_usuario(bd, crear_usuario):
    usuario_a = crear_usuario()
    creada = crear_ruta(ruta(), usuario_a)

    assert isinstance(creada, dict)
    assert isinstance(creada["id"], int)
    assert creada["usuario_id"] == usuario_a
    assert creada["nombre"] == "Ruta de prueba"
    fila = bd.session.get(RutaGuardada, creada["id"])
    assert fila.usuario_id == usuario_a


def test_el_dueno_sale_del_argumento_no_de_los_datos(bd, crear_usuario):
    usuario_a = crear_usuario()
    usuario_b = crear_usuario()
    creada = crear_ruta(ruta(usuario_id=usuario_b), usuario_a)
    assert creada["usuario_id"] == usuario_a


def test_paradas_vacias_se_aceptan(bd, crear_usuario):
    usuario_a = crear_usuario()
    creada = crear_ruta(ruta(paradas=[]), usuario_a)
    assert creada["paradas"] == []


def test_conserva_contenido_y_orden_de_las_paradas(bd, crear_usuario):
    usuario_a = crear_usuario()
    creada = crear_ruta(ruta(), usuario_a)
    recuperada = obtener_ruta(creada["id"], usuario_a)
    assert recuperada["paradas"] == RUTA_FICTICIA["paradas"]


def test_pr02_datos_invalidos_no_dejan_filas(bd, crear_usuario):
    usuario_a = crear_usuario()
    for datos in (ruta(nombre="  "), quitar("origen"), ruta(paradas="x")):
        with pytest.raises(ErrorRepositorio):
            crear_ruta(datos, usuario_a)
    assert contar_rutas(bd) == 0


def test_usuario_inexistente_falla_sin_filas(bd):
    with pytest.raises(ErrorRepositorio):
        crear_ruta(ruta(), usuario_id=999999)
    assert contar_rutas(bd) == 0


def test_pr03_fallo_en_el_commit_hace_rollback_y_no_deja_filas(
    bd, crear_usuario, monkeypatch
):
    usuario_a = crear_usuario()
    llamadas = []

    class SesionQueFallaAlConfirmar(Session):
        def commit(self):
            raise OperationalError("commit", {}, Exception("fallo forzado"))

        def rollback(self):
            llamadas.append("rollback")
            super().rollback()

    monkeypatch.setattr(repo, "_abrir_sesion", lambda: SesionQueFallaAlConfirmar(bd.engine))

    with pytest.raises(ErrorRepositorio) as info:
        crear_ruta(ruta(), usuario_a)
    assert "fallo forzado" not in str(info.value)  # sin detalles internos
    assert "rollback" in llamadas  # se revirtió de forma explícita
    monkeypatch.undo()

    assert contar_rutas(bd) == 0
    # Cada operación abre una sesión nueva: el servicio sigue funcionando.
    assert crear_ruta(ruta(), usuario_a)["id"]
    assert contar_rutas(bd) == 1


def test_error_que_no_es_de_sqlalchemy_tambien_sale_como_error_del_repositorio(
    bd, crear_usuario, monkeypatch
):
    usuario_a = crear_usuario()
    creada = crear_ruta(ruta(), usuario_a)

    class SesionConFalloInesperado(Session):
        def commit(self):
            raise RuntimeError("falla inesperada")

    monkeypatch.setattr(repo, "_abrir_sesion", lambda: SesionConFalloInesperado(bd.engine))
    with pytest.raises(ErrorRepositorio) as info:
        crear_ruta(ruta(nombre="Otra"), usuario_a)
    assert "falla inesperada" not in str(info.value)
    assert isinstance(info.value.__cause__, RuntimeError)  # la causa se conserva

    def _abrir():
        raise RuntimeError("falla inesperada")

    monkeypatch.setattr(repo, "_abrir_sesion", _abrir)
    with pytest.raises(ErrorRepositorio):
        obtener_ruta(creada["id"], usuario_a)
    with pytest.raises(ErrorRepositorio):
        listar_rutas_de_usuario(usuario_a)
    monkeypatch.undo()
    assert contar_rutas(bd) == 1


def test_no_confirma_cambios_pendientes_ajenos(bd, crear_usuario):
    from base_datos.modelos import Usuario

    usuario_a = crear_usuario()
    bd.session.add(
        Usuario(
            nombre="Pendiente",
            apellido="Ajeno",
            clave_normalizada="pendienteajeno",
            pin_hash="hash-ficticio",
        )
    )  # sin commit
    crear_ruta(ruta(), usuario_a)
    bd.session.rollback()
    assert bd.session.query(Usuario).filter_by(clave_normalizada="pendienteajeno").count() == 0


def test_pr06_listar_devuelve_solo_las_rutas_del_dueno(bd, crear_usuario):
    usuario_a = crear_usuario()
    usuario_b = crear_usuario()
    crear_ruta(ruta(nombre="A1"), usuario_a)
    crear_ruta(ruta(nombre="A2"), usuario_a)
    crear_ruta(ruta(nombre="B1"), usuario_b)

    de_a = listar_rutas_de_usuario(usuario_a)
    assert {r["nombre"] for r in de_a} == {"A1", "A2"}
    assert all(r["usuario_id"] == usuario_a for r in de_a)
    assert all(isinstance(r, dict) and "id" in r for r in de_a)
    assert [r["nombre"] for r in listar_rutas_de_usuario(usuario_b)] == ["B1"]


def test_pr07_otro_usuario_obtiene_none_y_la_ruta_queda_intacta(bd, crear_usuario):
    usuario_a = crear_usuario()
    usuario_b = crear_usuario()
    creada = crear_ruta(ruta(), usuario_a)

    assert obtener_ruta(creada["id"], usuario_b) is None
    assert obtener_ruta(creada["id"], usuario_a) == creada


def test_obtener_ruta_inexistente_devuelve_none(bd, crear_usuario):
    assert obtener_ruta(424242, crear_usuario()) is None


def test_pr08_datos_secundarios_incompletos_no_impiden_recuperar(bd, crear_usuario):
    usuario_a = crear_usuario()
    creada = crear_ruta(
        {"nombre": "Mínima", "origen": "X", "destino": "Y", "paradas": []},
        usuario_a,
    )
    recuperada = obtener_ruta(creada["id"], usuario_a)
    assert recuperada["nombre"] == "Mínima"
    assert recuperada["presupuesto"] is None
    assert recuperada["intereses"] == []
    assert recuperada["resumen"] == {}
    assert recuperada["paradas"] == []


def _fallo_al_ejecutar_la_consulta(monkeypatch, bd):
    class SesionQueFallaAlConsultar(Session):
        def execute(self, *args, **kwargs):
            raise OperationalError("select", {}, Exception("detalle interno"))

    monkeypatch.setattr(repo, "_abrir_sesion", lambda: SesionQueFallaAlConsultar(bd.engine))


def test_pr09_fallo_de_lectura_en_obtener_es_error_controlado(
    bd, crear_usuario, monkeypatch
):
    usuario_a = crear_usuario()
    usuario_b = crear_usuario()
    creada = crear_ruta(ruta(nombre="A1"), usuario_a)
    otra_de_a = crear_ruta(ruta(nombre="A2"), usuario_a)
    de_b = crear_ruta(ruta(nombre="B1"), usuario_b)

    _fallo_al_ejecutar_la_consulta(monkeypatch, bd)
    with pytest.raises(ErrorRepositorio) as info:
        obtener_ruta(creada["id"], usuario_a)
    assert "detalle interno" not in str(info.value)
    monkeypatch.undo()

    # Las demás rutas y datos siguen intactos.
    assert obtener_ruta(creada["id"], usuario_a) == creada
    assert obtener_ruta(otra_de_a["id"], usuario_a) == otra_de_a
    assert obtener_ruta(de_b["id"], usuario_b) == de_b
    assert contar_rutas(bd) == 3


def test_pr09_fallo_de_lectura_en_listar_es_error_controlado(
    bd, crear_usuario, monkeypatch
):
    usuario_a = crear_usuario()
    usuario_b = crear_usuario()
    crear_ruta(ruta(nombre="A1"), usuario_a)
    crear_ruta(ruta(nombre="A2"), usuario_a)
    crear_ruta(ruta(nombre="B1"), usuario_b)

    _fallo_al_ejecutar_la_consulta(monkeypatch, bd)
    with pytest.raises(ErrorRepositorio):
        listar_rutas_de_usuario(usuario_a)
    monkeypatch.undo()

    assert len(listar_rutas_de_usuario(usuario_a)) == 2
    assert len(listar_rutas_de_usuario(usuario_b)) == 1
    assert contar_rutas(bd) == 3


def test_listar_devuelve_la_mas_reciente_primero(bd, crear_usuario):
    usuario_a = crear_usuario()
    crear_ruta(ruta(nombre="Primera"), usuario_a)
    crear_ruta(ruta(nombre="Segunda"), usuario_a)
    crear_ruta(ruta(nombre="Tercera"), usuario_a)
    nombres = [r["nombre"] for r in listar_rutas_de_usuario(usuario_a)]
    assert nombres == ["Tercera", "Segunda", "Primera"]


@pytest.mark.parametrize("identificador", [0, -1])
def test_identificadores_cero_o_negativos(bd, crear_usuario, identificador):
    usuario_a = crear_usuario()
    assert obtener_ruta(identificador, usuario_a) is None
    assert listar_rutas_de_usuario(identificador) == []
    with pytest.raises(ErrorRepositorio):
        crear_ruta(ruta(), identificador)  # no hay usuario con ese id
    assert contar_rutas(bd) == 0


def test_pr10_usuario_sin_rutas_recibe_lista_vacia(bd, crear_usuario):
    assert listar_rutas_de_usuario(crear_usuario()) == []
