"""Pruebas de M-11 Utilerías (RNF-12, RNF-14, RNF-19). Sin base ni red."""

import pytest

from v2 import utilerias as u


# --- mensaje_seguro (RNF-14) ---

def test_error_propio_muestra_su_mensaje():
    assert u.mensaje_seguro(u.ErrorValidacion("Falta el destino.")) == "Falta el destino."


def test_error_ajeno_se_oculta_tras_mensaje_generico():
    error = RuntimeError("psycopg2: password authentication failed for user postgres")
    texto = u.mensaje_seguro(error)
    assert texto == u.MENSAJE_ERROR_GENERICO
    assert "psycopg2" not in texto and "password" not in texto


def test_error_propio_con_mensaje_vacio_usa_el_generico():
    assert u.mensaje_seguro(u.ErrorRutaMX("  ")) == u.MENSAJE_ERROR_GENERICO


def test_mensaje_por_defecto_personalizado():
    assert u.mensaje_seguro(ValueError("x"), por_defecto="No se pudo guardar.") == "No se pudo guardar."


def test_los_errores_derivan_de_errorrutamx():
    assert issubclass(u.ErrorValidacion, u.ErrorRutaMX)
    assert issubclass(u.ErrorServicioExterno, u.ErrorRutaMX)


# --- limpiar_texto (RNF-12) ---

def test_texto_normal_se_recorta_y_colapsa_espacios():
    assert u.limpiar_texto("  Ciudad   de \n México ", "origen") == "Ciudad de México"


def test_texto_quita_caracteres_de_control():
    assert u.limpiar_texto("Le\x00ón\x07", "destino") == "León"


@pytest.mark.parametrize("valor", [None, "", "   ", "\x00\x01"])
def test_texto_obligatorio_vacio_falla(valor):
    with pytest.raises(u.ErrorValidacion):
        u.limpiar_texto(valor, "origen")


@pytest.mark.parametrize("valor", [None, "", "  "])
def test_texto_opcional_vacio_devuelve_none(valor):
    assert u.limpiar_texto(valor, "intereses", obligatorio=False) is None


@pytest.mark.parametrize("valor", [5, 3.2, ["a"], {"a": 1}, True])
def test_texto_que_no_es_cadena_falla(valor):
    with pytest.raises(u.ErrorValidacion):
        u.limpiar_texto(valor, "origen")


def test_texto_en_el_limite_pasa_y_uno_mas_falla():
    assert u.limpiar_texto("a" * 10, "x", maximo=10) == "a" * 10
    with pytest.raises(u.ErrorValidacion):
        u.limpiar_texto("a" * 11, "x", maximo=10)


def test_mensaje_de_error_nombra_el_campo_sin_datos_internos():
    with pytest.raises(u.ErrorValidacion) as info:
        u.limpiar_texto("", "destino")
    assert "destino" in str(info.value)


# --- validar_entero_positivo (RNF-12) ---

def test_entero_valido_en_los_limites():
    assert u.validar_entero_positivo(1, "duracion") == 1
    assert u.validar_entero_positivo(u.DURACION_MAXIMA_DIAS, "duracion") == u.DURACION_MAXIMA_DIAS


@pytest.mark.parametrize("valor", [0, -3, u.DURACION_MAXIMA_DIAS + 1])
def test_entero_fuera_de_rango_falla(valor):
    with pytest.raises(u.ErrorValidacion):
        u.validar_entero_positivo(valor, "duracion")


@pytest.mark.parametrize("valor", [True, False, "3", 2.0, None, [1]])
def test_entero_con_tipo_incorrecto_falla(valor):
    with pytest.raises(u.ErrorValidacion):
        u.validar_entero_positivo(valor, "duracion")


# --- validar_lista_de_textos (RNF-12) ---

def test_lista_vacia_es_valida():
    assert u.validar_lista_de_textos([], "paradas", 5) == []


def test_lista_se_limpia_elemento_por_elemento():
    assert u.validar_lista_de_textos([" Puebla ", "Oaxaca"], "paradas", 5) == ["Puebla", "Oaxaca"]


def test_lista_excedida_falla_en_el_limite():
    assert len(u.validar_lista_de_textos(["a"] * 3, "paradas", 3)) == 3
    with pytest.raises(u.ErrorValidacion):
        u.validar_lista_de_textos(["a"] * 4, "paradas", 3)


@pytest.mark.parametrize("valor", ["Puebla", None, 5, {"a": "b"}])
def test_lista_que_no_es_lista_falla(valor):
    with pytest.raises(u.ErrorValidacion):
        u.validar_lista_de_textos(valor, "paradas", 5)


def test_lista_con_elemento_invalido_falla():
    with pytest.raises(u.ErrorValidacion):
        u.validar_lista_de_textos(["Puebla", 7], "paradas", 5)
    with pytest.raises(u.ErrorValidacion):
        u.validar_lista_de_textos(["Puebla", "  "], "paradas", 5)


# --- constantes (RNF-19) ---

def test_constantes_de_configuracion_existen_y_son_coherentes():
    assert u.LONGITUD_MAXIMA_TEXTO > 0
    assert u.LONGITUD_MAXIMA_MENSAJE >= u.LONGITUD_MAXIMA_TEXTO
    assert u.DURACION_MAXIMA_DIAS >= 1
