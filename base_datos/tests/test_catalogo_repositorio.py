"""Pruebas del repositorio del catálogo (consulta de rutas públicas).

Con sesión falsa: no tocan base ni red. Comprueban el SQL generado (siempre
filtra por visibilidad pública, parámetros enlazados), la validación, lo que se
devuelve (sin `usuario_id`) y el error de migración pendiente. La parte con
PostgreSQL real está al final y se omite sin `RUTAMX_TEST_DB_URL`.
Todos los datos son ficticios.
"""

import pytest

from base_datos.catalogo_valores import CATEGORIAS, LIMITE_RESULTADOS, REGIONES
from base_datos.repositorios import catalogo_repositorio as repo
from base_datos.repositorios.catalogo_repositorio import (
    ErrorMigracionPendiente,
    listar_publicas,
    obtener_publica,
)
from base_datos.repositorios.rutas_repositorio import ErrorRepositorio


class ResultadoFalso:
    def __init__(self, filas):
        self._filas = filas

    def mappings(self):
        return self

    def all(self):
        return list(self._filas)

    def first(self):
        return self._filas[0] if self._filas else None


class SesionFalsa:
    def __init__(self, filas=(), error=None):
        self.filas = list(filas)
        self.error = error
        self.llamadas = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, consulta, parametros=None):
        self.llamadas.append((str(consulta), dict(parametros or {})))
        if self.error:
            raise self.error
        return ResultadoFalso(self.filas)


@pytest.fixture()
def sesion(monkeypatch):
    s = SesionFalsa()
    monkeypatch.setattr(repo, "_abrir_sesion", lambda: s)
    return s


def fila(**cambios):
    datos = {
        "id": 7, "nombre": "Ruta ficticia", "origen": "Ciudad Uno", "destino": "Ciudad Dos",
        "duracion_dias": 3, "categoria": "Playa", "region": "Centro", "num_paradas": 2,
        "es_rutamx": False, "autor_nombre": "Persona", "autor_inicial": "F",
        "descripcion": "Texto ficticio", "paradas": [{"nombre": "A"}, {"nombre": "B"}],
    }
    datos.update(cambios)
    return datos


# ------------------------------------------------------------------ listado

def test_listar_solo_publicas_con_parametros_enlazados(sesion):
    sesion.filas = [fila()]
    rutas = listar_publicas()
    consulta, parametros = sesion.llamadas[0]
    assert "r.visibilidad = :publica" in consulta
    assert parametros["publica"] == "publica"
    assert parametros["limite"] == LIMITE_RESULTADOS
    assert rutas[0]["id"] == 7


def test_listar_no_devuelve_usuario_id_ni_campos_privados(sesion):
    sesion.filas = [fila(usuario_id=99, pin_hash="x")]
    ruta = listar_publicas()[0]
    assert "usuario_id" not in ruta and "pin_hash" not in ruta and "autor_id" not in ruta
    assert ruta["autor"] == {"nombre": "Persona", "inicial_apellido": "F"}


def test_ruta_sin_autor_es_rutamx_y_no_trae_autor(sesion):
    sesion.filas = [fila(es_rutamx=True, autor_nombre=None, autor_inicial=None)]
    ruta = listar_publicas()[0]
    assert ruta["es_rutamx"] is True and ruta["autor"] is None


def test_filtros_agregan_condiciones_y_valores_como_parametros(sesion):
    listar_publicas("playa", 3, "Playa", "Centro")
    consulta, parametros = sesion.llamadas[0]
    for texto in ("ILIKE :q", "r.duracion_dias = :duracion", "r.categoria = :categoria", "r.region = :region"):
        assert texto in consulta
    assert parametros["q"] == "%playa%" and parametros["duracion"] == 3
    assert "playa" not in consulta.lower().replace("ilike", "")


def test_palabra_clave_escapa_comodines_de_like(sesion):
    listar_publicas("100%_\\")
    assert sesion.llamadas[0][1]["q"] == "%100\\%\\_\\\\%"


def test_palabra_clave_vacia_no_agrega_filtro(sesion):
    listar_publicas("   ")
    assert "ILIKE" not in sesion.llamadas[0][0]


def test_intento_de_inyeccion_va_solo_como_parametro(sesion):
    listar_publicas("'; DROP TABLE rutas_guardadas; --")
    consulta, parametros = sesion.llamadas[0]
    assert "DROP" not in consulta and "DROP TABLE" in parametros["q"]


@pytest.mark.parametrize("campos", [
    {"palabra_clave": 5}, {"palabra_clave": "x" * 81}, {"duracion_dias": 0}, {"duracion_dias": -1},
    {"duracion_dias": True}, {"duracion_dias": "3"}, {"categoria": "Inventada"}, {"region": "Marte"},
    {"limite": 0}, {"limite": LIMITE_RESULTADOS + 1}, {"limite": True},
])
def test_listar_rechaza_valores_invalidos_sin_consultar(sesion, campos):
    with pytest.raises(ErrorRepositorio):
        listar_publicas(**campos)
    assert sesion.llamadas == []


def test_valores_del_limite_se_aceptan(sesion):
    listar_publicas("x" * 80, 1, CATEGORIAS[0], REGIONES[-1], limite=LIMITE_RESULTADOS)
    listar_publicas(limite=1)
    assert len(sesion.llamadas) == 2


def test_sin_resultados_devuelve_lista_vacia(sesion):
    assert listar_publicas() == []


# ------------------------------------------------------------------ detalle

def test_detalle_de_ruta_publica(sesion):
    sesion.filas = [fila()]
    ruta = obtener_publica(7)
    consulta, parametros = sesion.llamadas[0]
    assert "r.visibilidad = :publica" in consulta and parametros == {"id": 7, "publica": "publica"}
    assert ruta["descripcion"] == "Texto ficticio"
    assert [p["nombre"] for p in ruta["paradas"]] == ["A", "B"]
    assert "usuario_id" not in ruta


def test_detalle_privado_o_inexistente_es_none(sesion):
    assert obtener_publica(7) is None


@pytest.mark.parametrize("valor", [None, "7", 7.0, True, [7]])
def test_detalle_rechaza_identificador_invalido(sesion, valor):
    with pytest.raises(ErrorRepositorio):
        obtener_publica(valor)
    assert sesion.llamadas == []


def test_descripcion_vacia_es_texto_vacio_y_paradas_none_es_lista(sesion):
    sesion.filas = [fila(descripcion=None, paradas=None)]
    ruta = obtener_publica(7)
    assert ruta["descripcion"] == "" and ruta["paradas"] == []


# ------------------------------------------------------------------- errores

class ErrorBaseFalso(Exception):
    def __init__(self, pgcode=None):
        super().__init__("detalle interno con SQL y credenciales")
        self.orig = type("Orig", (), {"pgcode": pgcode})()


def test_columnas_faltantes_dan_migracion_pendiente(sesion):
    sesion.error = ErrorBaseFalso("42703")
    with pytest.raises(ErrorMigracionPendiente) as info:
        listar_publicas()
    assert "migración" in str(info.value)
    assert "SQL" not in str(info.value) and "credenciales" not in str(info.value)


def test_migracion_pendiente_tambien_en_detalle(sesion):
    sesion.error = ErrorBaseFalso("42703")
    with pytest.raises(ErrorMigracionPendiente):
        obtener_publica(1)


def test_otro_error_de_base_es_mensaje_seguro(sesion):
    sesion.error = ErrorBaseFalso("08006")
    with pytest.raises(ErrorRepositorio) as info:
        listar_publicas()
    assert not isinstance(info.value, ErrorMigracionPendiente)
    assert "SQL" not in str(info.value)


def test_migracion_pendiente_es_un_error_del_repositorio():
    assert issubclass(ErrorMigracionPendiente, ErrorRepositorio)


# ------------------------------------------- integración (PostgreSQL desechable)

def _preparar_columnas(bd):
    from base_datos.migraciones.agregar_columnas_catalogo import aplicar
    aplicar(bd.session)


def _insertar(bd, usuario_id, **valores):
    from sqlalchemy import text
    base = {"nombre": "R", "origen": "A", "destino": "B", "paradas": "[]", "uid": usuario_id,
            "vis": "privada", "dur": 2, "cat": "Playa", "reg": "Centro", "desc": "", "autor": None}
    base.update(valores)
    bd.session.execute(text(
        "INSERT INTO rutas_guardadas (nombre, origen, destino, paradas, usuario_id, visibilidad, "
        "duracion_dias, categoria, region, descripcion, autor_id) VALUES "
        "(:nombre, :origen, :destino, CAST(:paradas AS jsonb), :uid, :vis, :dur, :cat, :reg, :desc, :autor)"
    ), base)
    bd.session.commit()


def test_integracion_sin_migracion_da_migracion_pendiente(bd):
    with pytest.raises(ErrorMigracionPendiente):
        listar_publicas()


def test_integracion_solo_salen_las_publicas_y_filtran(bd, crear_usuario):
    _preparar_columnas(bd)
    uid = crear_usuario("Ana")
    _insertar(bd, uid, nombre="Privada", vis="privada")
    _insertar(bd, uid, nombre="Playa publica", vis="publica", autor=uid, paradas='[{"nombre":"P"}]')
    _insertar(bd, uid, nombre="Cultural oficial", vis="publica", cat="Cultural", dur=5)
    assert {r["nombre"] for r in listar_publicas()} == {"Playa publica", "Cultural oficial"}
    assert [r["nombre"] for r in listar_publicas(categoria="Cultural")] == ["Cultural oficial"]
    assert [r["nombre"] for r in listar_publicas(duracion_dias=5)] == ["Cultural oficial"]
    assert listar_publicas("zzz") == []
    playa = [r for r in listar_publicas() if r["nombre"] == "Playa publica"][0]
    assert playa["num_paradas"] == 1 and playa["autor"]["nombre"] == "Ana" and "usuario_id" not in playa
    assert [r for r in listar_publicas() if r["nombre"] == "Cultural oficial"][0]["es_rutamx"] is True


def test_integracion_detalle_privado_es_none(bd, crear_usuario):
    _preparar_columnas(bd)
    uid = crear_usuario()
    _insertar(bd, uid, nombre="Privada", vis="privada")
    assert obtener_publica(1) is None
