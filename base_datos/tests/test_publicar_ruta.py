"""Pruebas del script que publica una ruta (sesión falsa, sin tocar la base real).

Comprueban validación, autor (conservar, dueño explícito o RutaMx solo con
--rutamx), duración, transacción con rollback, errores seguros y códigos de
salida. Datos ficticios.
"""

from contextlib import contextmanager

import pytest

from base_datos.catalogo_valores import CATEGORIAS, REGIONES
from base_datos.scripts import publicar_ruta as pub
from base_datos.scripts.publicar_ruta import ErrorPublicacion, principal, publicar, volver_privada


class ResultadoFalso:
    def __init__(self, fila):
        self._fila = fila

    def mappings(self):
        return self

    def first(self):
        return self._fila


class SesionFalsa:
    def __init__(self, fila=None, falla_en_update=None):
        self.fila = fila
        self.falla_en_update = falla_en_update
        self.updates, self.commits, self.rollbacks, self.cerrada = [], 0, 0, False

    def execute(self, sentencia, parametros=None):
        sql = str(sentencia)
        if sql.startswith("SELECT"):
            assert "FOR UPDATE" in sql
            return ResultadoFalso(self.fila)
        if self.falla_en_update:
            raise self.falla_en_update
        self.updates.append((sql, dict(parametros)))
        return ResultadoFalso(None)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


def fila(**cambios):
    datos = {"id": 5, "usuario_id": 10, "autor_id": None, "duracion_v2": "4"}
    datos.update(cambios)
    return datos


@pytest.fixture()
def sesion(monkeypatch):
    s = SesionFalsa(fila())
    monkeypatch.setattr(pub, "_abrir_sesion", lambda: s)
    return s


def publicar_ok(**extra):
    args = dict(ruta_id=5, categoria=CATEGORIAS[0], region=REGIONES[0], descripcion="Texto ficticio")
    args.update(extra)
    return publicar(**args)


# ------------------------------------------------------------------- autor

def test_sin_autor_toma_al_dueno_de_forma_explicita(sesion):
    r = publicar_ok()
    assert sesion.updates[0][1]["autor"] == 10 and r["es_rutamx"] is False


def test_conserva_el_autor_que_ya_tenia(sesion):
    sesion.fila = fila(autor_id=77)
    publicar_ok()
    assert sesion.updates[0][1]["autor"] == 77


def test_rutamx_solo_con_indicador_explicito_y_deja_autor_vacio(sesion):
    sesion.fila = fila(autor_id=77)
    r = publicar_ok(rutamx=True)
    assert sesion.updates[0][1]["autor"] is None and r["es_rutamx"] is True


def test_sin_dueno_ni_autor_exige_rutamx(sesion):
    sesion.fila = fila(usuario_id=None)
    with pytest.raises(ErrorPublicacion, match="--rutamx"):
        publicar_ok()
    assert sesion.updates == [] and sesion.rollbacks == 1


# ---------------------------------------------------------------- duración

def test_duracion_sale_de_la_ruta_guardada(sesion):
    assert publicar_ok()["duracion_dias"] == 4
    assert sesion.updates[0][1]["dur"] == 4


def test_duracion_explicita_tiene_prioridad(sesion):
    publicar_ok(duracion=9)
    assert sesion.updates[0][1]["dur"] == 9


@pytest.mark.parametrize("valor", [None, "", "0", "-2", "abc"])
def test_sin_duracion_valida_en_la_ruta_pide_duracion(sesion, valor):
    sesion.fila = fila(duracion_v2=valor)
    with pytest.raises(ErrorPublicacion, match="--duracion"):
        publicar_ok()
    assert sesion.updates == []


# --------------------------------------------------------------- validación

@pytest.mark.parametrize("campos", [
    {"categoria": "Inventada"}, {"categoria": None}, {"region": "Marte"}, {"region": ""},
    {"descripcion": "   "}, {"descripcion": None}, {"descripcion": "x" * 501},
    {"ruta_id": 0}, {"ruta_id": -1}, {"ruta_id": True}, {"ruta_id": "5"},
    {"duracion": 0}, {"duracion": True},
])
def test_valores_invalidos_fallan_sin_abrir_la_base(monkeypatch, campos):
    monkeypatch.setattr(pub, "_abrir_sesion", lambda: pytest.fail("no debe abrir la base"))
    with pytest.raises(ErrorPublicacion):
        publicar_ok(**campos)


def test_limites_validos_se_aceptan(sesion):
    publicar_ok(descripcion="x" * 500, duracion=1)
    assert sesion.commits == 1


def test_el_mensaje_de_categoria_lista_las_opciones(monkeypatch):
    monkeypatch.setattr(pub, "_abrir_sesion", lambda: pytest.fail("no debe abrir la base"))
    with pytest.raises(ErrorPublicacion) as info:
        publicar_ok(categoria="Otra")
    assert all(c in str(info.value) for c in CATEGORIAS)


# --------------------------------------------------------------- transacción

def test_ruta_inexistente_falla_y_revierte(sesion):
    sesion.fila = None
    with pytest.raises(ErrorPublicacion, match="No existe"):
        publicar_ok()
    assert sesion.commits == 0 and sesion.rollbacks == 1 and sesion.cerrada


def test_exito_confirma_una_vez_y_cierra(sesion):
    publicar_ok()
    assert sesion.commits == 1 and sesion.rollbacks == 0 and sesion.cerrada
    assert sesion.updates[0][1]["vis"] == "publica" and sesion.updates[0][1]["desc"] == "Texto ficticio"


class ErrorBaseFalso(Exception):
    def __init__(self, pgcode):
        super().__init__("detalle interno con SQL")
        self.orig = type("Orig", (), {"pgcode": pgcode})()


def test_falta_la_migracion_da_mensaje_claro(sesion):
    sesion.falla_en_update = ErrorBaseFalso("42703")
    with pytest.raises(ErrorPublicacion, match="migración"):
        publicar_ok()
    assert sesion.commits == 0 and sesion.rollbacks == 1


def test_otro_error_de_base_no_filtra_detalles(sesion):
    sesion.falla_en_update = ErrorBaseFalso("08006")
    with pytest.raises(ErrorPublicacion) as info:
        publicar_ok()
    assert "detalle interno" not in str(info.value) and "SQL" not in str(info.value)
    assert sesion.commits == 0


# ------------------------------------------------------------------- privada

def test_volver_privada_solo_cambia_la_visibilidad(sesion):
    volver_privada(5)
    sql, params = sesion.updates[0]
    assert params == {"vis": "privada", "id": 5} and "categoria" not in sql and sesion.commits == 1


def test_volver_privada_de_ruta_inexistente_falla(sesion):
    sesion.fila = None
    with pytest.raises(ErrorPublicacion):
        volver_privada(5)
    assert sesion.updates == []


@pytest.mark.parametrize("valor", [0, -3, True, None])
def test_volver_privada_valida_el_id(monkeypatch, valor):
    monkeypatch.setattr(pub, "_abrir_sesion", lambda: pytest.fail("no debe abrir la base"))
    with pytest.raises(ErrorPublicacion):
        volver_privada(valor)


# ------------------------------------------------------------- línea de comandos

def test_cli_publica_y_sale_con_0(sesion, capsys):
    codigo = principal(["5", "--categoria", "Playa", "--region", "Centro", "--descripcion", "Texto"])
    assert codigo == 0 and "es pública" in capsys.readouterr().out


def test_cli_rutamx(sesion, capsys):
    principal(["5", "--categoria", "Playa", "--region", "Centro", "--descripcion", "T", "--rutamx"])
    assert sesion.updates[0][1]["autor"] is None


def test_cli_privada(sesion, capsys):
    assert principal(["5", "--privada"]) == 0 and "privada" in capsys.readouterr().out


def test_cli_privada_no_se_combina_con_datos_de_publicacion(sesion, capsys):
    assert principal(["5", "--privada", "--categoria", "Playa"]) == 1
    assert sesion.updates == []


@pytest.mark.parametrize("argv", [
    [], ["abc"], ["5"], ["5", "--categoria", "Playa"], ["5", "--categoria", "Nada", "--region", "Centro", "--descripcion", "T"],
    ["5", "--categoria", "Playa", "--region", "Centro", "--descripcion", "T", "--duracion", "x"],
])
def test_cli_argumentos_invalidos_salen_con_1_y_mensaje(monkeypatch, capsys, argv):
    monkeypatch.setattr(pub, "_abrir_sesion", lambda: pytest.fail("no debe abrir la base"))
    assert principal(argv) == 1
    assert capsys.readouterr().err


def test_cli_ruta_inexistente_sale_con_1(sesion, capsys):
    sesion.fila = None
    assert principal(["5", "--categoria", "Playa", "--region", "Centro", "--descripcion", "T"]) == 1
    assert "No existe" in capsys.readouterr().err


def test_cli_sin_poder_abrir_la_base_sale_con_1_sin_detalles(monkeypatch, capsys):
    def falla():
        raise RuntimeError("postgresql://usuario:clave@host/db")
    monkeypatch.setattr(pub, "_abrir_sesion", falla)
    assert principal(["5", "--categoria", "Playa", "--region", "Centro", "--descripcion", "T"]) == 1
    err = capsys.readouterr().err
    assert "clave" not in err and "postgresql" not in err


# ------------------------------------------------- contexto de Flask (sin fugas)

def _app_falsa():
    from flask import Flask

    from base_datos.conexion import iniciar_base_datos

    app = Flask("prueba_publicar")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    iniciar_base_datos(app)
    return app


def _contexto_activo():
    """El contexto de Flask que está arriba de la pila (o None si no hay)."""
    from flask import has_app_context
    from flask.globals import app_ctx

    return app_ctx._get_current_object() if has_app_context() else None


@contextmanager
def _sin_fuga_de_contexto():
    """Falla si lo de adentro deja un contexto de Flask abierto.

    No exige que no haya contexto: con las pruebas de integración la sesión
    mantiene uno externo (`conftest.py`), y ahí `has_app_context()` es True
    antes y después aunque el script deje otro encima. Por eso se compara la
    identidad del contexto activo, y se cierran los que se hayan fugado para
    no contaminar las demás pruebas.
    """
    from flask.globals import app_ctx

    antes = _contexto_activo()
    yield
    fugados = 0
    while _contexto_activo() is not antes and fugados < 10:
        app_ctx._get_current_object().pop()
        fugados += 1
    assert fugados == 0, f"el script dejó {fugados} contexto(s) de Flask abierto(s)"


def test_abrir_sesion_no_deja_contexto_de_flask_activo(monkeypatch):
    monkeypatch.setattr("base_datos.conexion.crear_app_minima", _app_falsa)
    with _sin_fuga_de_contexto():
        sesion = pub._abrir_sesion()
        sesion.close()


def test_abrir_sesion_fallida_tampoco_deja_contexto(monkeypatch):
    from sqlalchemy.orm import Session

    monkeypatch.setattr("base_datos.conexion.crear_app_minima", _app_falsa)
    monkeypatch.setattr(Session, "__init__", lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("sin sesión")))
    with _sin_fuga_de_contexto():
        with pytest.raises(RuntimeError):
            pub._abrir_sesion()


def test_cada_operacion_real_libera_el_contexto(monkeypatch):
    monkeypatch.setattr("base_datos.conexion.crear_app_minima", _app_falsa)
    for _ in range(3):
        with _sin_fuga_de_contexto():
            with pytest.raises(ErrorPublicacion):
                volver_privada(5)  # sqlite no tiene la tabla: falla, pero sin dejar contexto
