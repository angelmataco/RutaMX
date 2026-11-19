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
    copiar_publica,
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
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

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


def test_detalle_trae_resumen_solo_para_el_mapa(sesion):
    sesion.filas = [fila(resumen={"rutamx_v2": {"ruta": {}}})]
    ruta = obtener_publica(7)
    assert "r.resumen" in sesion.llamadas[0][0]
    assert ruta["resumen"] == {"rutamx_v2": {"ruta": {}}}
    sesion.filas = [fila(resumen=None)]
    assert obtener_publica(7)["resumen"] == {}
    sesion.filas = [fila()]  # sin la columna en la fila: no falla
    assert obtener_publica(7)["resumen"] == {}


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



# ------------------------------------------- copiar (sesión falsa, v0.5.0)

def test_copiar_es_una_sola_sentencia_con_condicion_publica(sesion):
    sesion.filas = [(99,)]
    assert copiar_publica(7, 3) == 99
    assert len(sesion.llamadas) == 1
    consulta, parametros = sesion.llamadas[0]
    assert consulta.lstrip().startswith("INSERT INTO rutas_guardadas")
    assert "SELECT" in consulta and "visibilidad = :publica" in consulta
    assert "ruta_origen_id" in consulta and "RETURNING id" in consulta
    assert parametros == {"id": 7, "usuario_id": 3, "publica": "publica", "privada": "privada"}
    assert sesion.commits == 1


def test_copiar_no_escribe_autor_ni_toca_la_original(sesion):
    sesion.filas = [(99,)]
    copiar_publica(7, 3)
    consulta = sesion.llamadas[0][0].upper()
    assert "AUTOR_ID" not in consulta
    assert "UPDATE" not in consulta and "DELETE" not in consulta


def test_copiar_ruta_inexistente_o_privada_devuelve_none_sin_commit(sesion):
    sesion.filas = []
    assert copiar_publica(7, 3) is None
    assert sesion.commits == 0 and sesion.rollbacks == 1


@pytest.mark.parametrize("ruta_id,usuario_id", [
    (None, 1), ("7", 1), (7.0, 1), (True, 1), (0, 1), (-1, 1),
    (7, None), (7, "1"), (7, 1.0), (7, True), (7, 0), (7, -2),
])
def test_copiar_rechaza_identificadores_invalidos_sin_consultar(sesion, ruta_id, usuario_id):
    with pytest.raises(ErrorRepositorio):
        copiar_publica(ruta_id, usuario_id)
    assert sesion.llamadas == []


def test_copiar_con_columnas_faltantes_da_migracion_pendiente(sesion):
    class Original(Exception):
        pgcode = "42703"

    class ErrorSQL(Exception):
        orig = Original()

    sesion.error = ErrorSQL("detalle interno")
    with pytest.raises(ErrorMigracionPendiente) as info:
        copiar_publica(7, 3)
    assert "detalle interno" not in str(info.value)
    assert sesion.commits == 0 and sesion.rollbacks == 1


def test_copiar_con_otro_error_es_mensaje_seguro_sin_commit(sesion):
    sesion.error = RuntimeError("SELECT secreto FROM tabla")
    with pytest.raises(ErrorRepositorio) as info:
        copiar_publica(7, 3)
    assert str(info.value) == "No se pudo copiar la ruta."
    assert "secreto" not in str(info.value)
    assert not isinstance(info.value, ErrorMigracionPendiente)
    assert sesion.commits == 0 and sesion.rollbacks == 1


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
        "INSERT INTO rutas_guardadas (nombre, origen, destino, intereses, resumen, paradas, usuario_id, visibilidad, "
        "duracion_dias, categoria, region, descripcion, autor_id) VALUES "
        "(:nombre, :origen, :destino, '{}', '{}', CAST(:paradas AS jsonb), :uid, :vis, :dur, :cat, :reg, :desc, :autor)"
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


def _contar(bd, **filtros):
    from sqlalchemy import text
    donde = " AND ".join(f"{c} = :{c}" for c in filtros) or "TRUE"
    return bd.session.execute(text(f"SELECT count(*) FROM rutas_guardadas WHERE {donde}"), filtros).scalar()


def _fila(bd, ruta_id):
    from sqlalchemy import text
    return dict(bd.session.execute(text(
        "SELECT nombre, origen, destino, intereses, resumen, paradas, descripcion, duracion_dias, "
        "categoria, region, usuario_id, visibilidad, autor_id, ruta_origen_id "
        "FROM rutas_guardadas WHERE id = :id"), {"id": ruta_id}).mappings().first())


def test_integracion_copiar_crea_copia_privada_y_no_toca_la_original(bd, crear_usuario):
    _preparar_columnas(bd)
    autor = crear_usuario("Ana")
    otro = crear_usuario("Beto")
    _insertar(bd, autor, nombre="Ruta publica", vis="publica", autor=autor,
              paradas='[{"nombre":"P"}]', desc="Texto ficticio", dur=4, cat="Cultural", reg="Sureste")
    antes = _fila(bd, 1)
    copia_id = copiar_publica(1, otro)
    assert copia_id and copia_id != 1
    assert _fila(bd, 1) == antes
    copia = _fila(bd, copia_id)
    assert copia["usuario_id"] == otro and copia["visibilidad"] == "privada"
    assert copia["autor_id"] is None and copia["ruta_origen_id"] == 1
    for campo in ("nombre", "origen", "destino", "paradas", "descripcion", "duracion_dias", "categoria", "region"):
        assert copia[campo] == antes[campo]


def test_integracion_copiar_dos_veces_crea_dos_copias_independientes(bd, crear_usuario):
    _preparar_columnas(bd)
    uid = crear_usuario("Ana")
    _insertar(bd, uid, nombre="Ruta publica", vis="publica", autor=uid)
    primera, segunda = copiar_publica(1, uid), copiar_publica(1, uid)
    assert primera != segunda
    assert _contar(bd, ruta_origen_id=1) == 2


def test_integracion_copiar_privada_o_inexistente_no_crea_nada(bd, crear_usuario):
    _preparar_columnas(bd)
    uid = crear_usuario("Ana")
    _insertar(bd, uid, nombre="Privada", vis="privada")
    assert copiar_publica(1, uid) is None
    assert copiar_publica(999, uid) is None
    assert _contar(bd) == 1


def test_integracion_copiar_con_fallo_no_deja_copia_parcial(bd, crear_usuario):
    _preparar_columnas(bd)
    uid = crear_usuario("Ana")
    _insertar(bd, uid, nombre="Ruta publica", vis="publica", autor=uid)
    with pytest.raises(ErrorRepositorio):
        copiar_publica(1, 987654)  # usuario inexistente: viola la llave foránea
    bd.session.rollback()
    assert _contar(bd) == 1


def _quitar_columnas_catalogo(bd):
    """Deja la tabla como antes de la migración (solo en la base desechable local).

    `bd` solo trunca datos y el esquema migrado persiste en toda la sesión, así
    que esta prueba lo quita de forma explícita y comprueba que no quedó nada.
    """
    import os
    from urllib.parse import urlparse
    from sqlalchemy import text
    url = urlparse(os.environ["RUTAMX_TEST_DB_URL"])
    assert url.hostname in {"127.0.0.1", "localhost", "::1"}, "la base de prueba no es local"
    assert url.path.lstrip("/").endswith(("_prueba", "_test")), "la base de prueba no es desechable"
    bd.session.execute(text("DROP INDEX IF EXISTS ix_rutas_guardadas_visibilidad"))
    for columna in COLUMNAS_CATALOGO:
        bd.session.execute(text(f"ALTER TABLE rutas_guardadas DROP COLUMN IF EXISTS {columna} CASCADE"))
    bd.session.commit()
    presentes = {f[0] for f in bd.session.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'rutas_guardadas'")).all()}
    assert not set(COLUMNAS_CATALOGO) & presentes


COLUMNAS_CATALOGO = ("ruta_origen_id", "autor_id", "visibilidad", "duracion_dias",
                     "categoria", "region", "descripcion")


def test_integracion_copiar_sin_migracion_da_migracion_pendiente(bd, crear_usuario):
    uid = crear_usuario("Ana")
    _quitar_columnas_catalogo(bd)
    try:
        with pytest.raises(ErrorMigracionPendiente):
            copiar_publica(1, uid)
    finally:
        _preparar_columnas(bd)  # deja el esquema migrado para las demás pruebas
