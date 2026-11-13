"""Pruebas de la migración de las columnas del catálogo.

Con sesión falsa se comprueba la forma de las sentencias, la transacción y el
rollback. Las pruebas sobre esquema real (esquema anterior, segunda ejecución,
filas anteriores) usan el PostgreSQL desechable de `RUTAMX_TEST_DB_URL` y se
omiten sin él: NO cuentan como evidencia. La migración NO se ejecuta contra la
base real. Datos ficticios.
"""

import pytest
from sqlalchemy import text

from base_datos.migraciones import agregar_columnas_catalogo as mig
from base_datos.migraciones.agregar_columnas_catalogo import ErrorMigracion, SENTENCIAS, aplicar

COLUMNAS_ESPERADAS = {
    "descripcion", "duracion_dias", "categoria", "region", "visibilidad", "ruta_origen_id", "autor_id",
}


class SesionFalsa:
    def __init__(self, falla_en=None):
        self.ejecutadas, self.commits, self.rollbacks = [], 0, 0
        self.falla_en = falla_en

    def execute(self, sentencia, *a, **k):
        if self.falla_en is not None and len(self.ejecutadas) == self.falla_en:
            raise RuntimeError("fallo de base con detalle interno")
        self.ejecutadas.append(str(sentencia))

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


# --------------------------------------------------------------- forma (sin base)

def test_agrega_exactamente_las_siete_columnas_autorizadas():
    alter = [s for s in SENTENCIAS if s.startswith("ALTER TABLE")]
    assert len(alter) == 7
    for columna in COLUMNAS_ESPERADAS:
        assert sum(f" {columna} " in s for s in alter) == 1


def test_toda_sentencia_es_idempotente():
    assert all("IF NOT EXISTS" in s for s in SENTENCIAS)


def test_visibilidad_es_privada_por_defecto_y_no_nula():
    s = next(s for s in SENTENCIAS if "visibilidad TEXT" in s)
    assert "NOT NULL DEFAULT 'privada'" in s and "'publica'" in s


def test_solo_toca_rutas_guardadas_sin_borrar_nada():
    assert all("rutas_guardadas" in s for s in SENTENCIAS)
    assert not any(p in s.upper() for s in SENTENCIAS for p in ("DROP", "DELETE FROM", "TRUNCATE", "UPDATE"))


def test_aplicar_corre_todo_en_una_transaccion():
    s = SesionFalsa()
    aplicar(s)
    assert len(s.ejecutadas) == len(SENTENCIAS) and s.commits == 1 and s.rollbacks == 0


def test_fallo_revierte_y_no_confirma_con_mensaje_seguro():
    s = SesionFalsa(falla_en=3)
    with pytest.raises(ErrorMigracion) as info:
        aplicar(s)
    assert s.commits == 0 and s.rollbacks == 1
    assert "detalle interno" not in str(info.value)


def test_el_script_sale_con_codigo_1_si_falla(monkeypatch, capsys):
    def falla():
        raise ErrorMigracion("revertida")
    monkeypatch.setattr(mig, "migrar", falla)
    assert mig.principal() == 1
    assert "revertida" in capsys.readouterr().err


def test_el_script_sale_con_codigo_0_si_sale_bien(monkeypatch):
    monkeypatch.setattr(mig, "migrar", lambda: None)
    assert mig.principal() == 0


# ------------------------------------------- esquema real (PostgreSQL desechable)

def _columnas(bd):
    filas = bd.session.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'rutas_guardadas'"
    )).all()
    return {f[0] for f in filas}


def test_integracion_esquema_anterior_gana_las_siete_columnas(bd):
    assert not COLUMNAS_ESPERADAS & _columnas(bd)
    aplicar(bd.session)
    assert COLUMNAS_ESPERADAS <= _columnas(bd)


def test_integracion_segunda_ejecucion_no_falla_ni_duplica(bd):
    aplicar(bd.session)
    antes = _columnas(bd)
    aplicar(bd.session)
    assert _columnas(bd) == antes


def test_integracion_filas_anteriores_se_conservan_y_son_privadas(bd, crear_usuario):
    uid = crear_usuario()
    bd.session.execute(text(
        "INSERT INTO rutas_guardadas (nombre, origen, destino, intereses, resumen, paradas, usuario_id) "
        "VALUES ('Vieja', 'A', 'B', '{}', '{}', '[]', :u)"), {"u": uid})
    bd.session.commit()
    aplicar(bd.session)
    fila = bd.session.execute(text(
        "SELECT nombre, visibilidad, autor_id, duracion_dias FROM rutas_guardadas")).one()
    assert tuple(fila) == ("Vieja", "privada", None, None)


def test_integracion_visibilidad_invalida_se_rechaza(bd, crear_usuario):
    uid = crear_usuario()
    aplicar(bd.session)
    with pytest.raises(Exception):
        bd.session.execute(text(
            "INSERT INTO rutas_guardadas (nombre, origen, destino, intereses, resumen, paradas, "
            "usuario_id, visibilidad) VALUES ('X','A','B','{}','{}','[]', :u, 'secreta')"), {"u": uid})
    bd.session.rollback()


def test_integracion_fallo_a_la_mitad_deja_el_esquema_intacto(bd, monkeypatch):
    monkeypatch.setattr(mig, "SENTENCIAS", mig.SENTENCIAS[:3] + ("ALTER TABLE no_existe ADD COLUMN x INT",))
    with pytest.raises(ErrorMigracion):
        mig.aplicar(bd.session)
    assert not COLUMNAS_ESPERADAS & _columnas(bd)
