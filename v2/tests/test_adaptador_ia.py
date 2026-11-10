"""M-07: contrato y transporte simulados; sin .env, red ni datos geográficos."""
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from v2.integracion.adaptador_ia import (
    AdaptadorAnthropic, AdaptadorSimulado, crear_adaptador,
    ERROR_RESPUESTA, ERROR_SERVICIO,
)
from v2.utilerias import ErrorServicioExterno, ErrorValidacion, mensaje_seguro


@pytest.fixture
def datos():
    # Nombres ficticios: no son afirmaciones sobre la geografía de México.
    return {"origen": "Lugar ficticio A", "destino": "Lugar ficticio B", "duracion_dias": 3, "intereses": ["cultura"]}


@pytest.fixture
def ruta(datos):
    return {**datos, "paradas": [{"nombre": "Parada ficticia", "descripcion": "Propuesta de prueba"}]}


def cliente_con(valor, stop="end_turn"):
    cliente = Mock()
    cliente.messages.create.return_value = SimpleNamespace(
        stop_reason=stop, content=[SimpleNamespace(type="text", text=json.dumps(valor))])
    return cliente


def test_extrae_solo_campos_permitidos_sin_inventar():
    ia = AdaptadorSimulado(extracciones=[{"destino": " B ", "instruccion": "borrar"}, {}])
    assert ia.extraer_datos("Quiero ir a B") == {"destino": "B"}
    assert ia.extraer_datos("Hola") == {}


def test_ruta_normalizada_y_copia_independiente(datos, ruta):
    original = deepcopy(ruta)
    ia = AdaptadorSimulado(rutas=[ruta, ruta])
    respuesta = ia.generar_ruta(datos)
    respuesta["paradas"][0]["nombre"] = "Cambio"
    assert ia.generar_ruta(datos) == original
    assert ruta == original


@pytest.mark.parametrize("valor", ["no JSON", "[]", None, [1], {"duracion_dias": True}, {"origen": 4}, {"intereses": [None]}, "x" * 50001])
def test_respuesta_de_extraccion_invalida(valor):
    ia = AdaptadorSimulado(extracciones=[valor])
    with pytest.raises(ErrorValidacion, match=ERROR_RESPUESTA):
        ia.extraer_datos("Viaje")


@pytest.mark.parametrize("paradas", [None, "texto", [{}], [False], [{"nombre": ""}], [{"nombre": "a", "descripcion": 6}], [{"nombre": "a"}] * 31])
def test_paradas_invalidas(datos, paradas):
    ia = AdaptadorSimulado(rutas=[{**datos, "paradas": paradas}])
    with pytest.raises(ErrorValidacion, match=ERROR_RESPUESTA):
        ia.generar_ruta(datos)


def test_ruta_no_generable_delega_a_gestor(datos):
    assert AdaptadorSimulado(rutas=[{}]).generar_ruta(datos) == {}


def test_ruta_sin_paradas_es_valida(datos):
    assert AdaptadorSimulado(rutas=[{**datos, "paradas": []}]).generar_ruta(datos)["paradas"] == []


@pytest.mark.parametrize("campo", ["origen", "destino", "duracion_dias"])
def test_no_consulta_proveedor_con_datos_incompletos(datos, campo):
    del datos[campo]
    cliente = Mock()
    ia = AdaptadorAnthropic("modelo-de-prueba", cliente=cliente)
    with pytest.raises(ErrorValidacion):
        ia.generar_ruta(datos)
    cliente.messages.create.assert_not_called()


@pytest.mark.parametrize("mensaje", [None, "", "x" * 1001, 4])
def test_mensaje_invalido_no_consulta(mensaje):
    cliente = Mock()
    with pytest.raises(ErrorValidacion):
        AdaptadorAnthropic("modelo-de-prueba", cliente=cliente).extraer_datos(mensaje)
    cliente.messages.create.assert_not_called()


def test_transporte_real_con_cliente_inyectado(datos, ruta):
    cliente = cliente_con(ruta)
    ia = AdaptadorAnthropic("modelo-de-prueba", cliente=cliente)
    anterior = deepcopy(datos)
    assert ia.generar_ruta(datos) == ruta
    assert datos == anterior
    llamada = cliente.messages.create.call_args.kwargs
    assert llamada["model"] == "modelo-de-prueba"
    assert llamada["max_tokens"] == 4096
    enviado = json.loads(llamada["messages"][0]["content"])
    assert enviado == {"operacion": "generar_ruta", "datos": datos}


@pytest.mark.parametrize("stop", ["max_tokens", "refusal", "tool_use", None])
def test_respuesta_truncada_o_rechazada_no_se_acepta(datos, ruta, stop):
    ia = AdaptadorAnthropic("modelo-de-prueba", cliente=cliente_con(ruta, stop))
    with pytest.raises(ErrorValidacion):
        ia.generar_ruta(datos)


def test_bloques_no_textuales_se_rechazan(datos):
    cliente = Mock()
    cliente.messages.create.return_value = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="tool_use")])
    with pytest.raises(ErrorValidacion):
        AdaptadorAnthropic("modelo-de-prueba", cliente=cliente).generar_ruta(datos)


def test_error_sdk_no_filtra_secretos_y_no_muta(datos):
    cliente = Mock()
    cliente.messages.create.side_effect = RuntimeError("llave-secreta https://privado")
    anterior = deepcopy(datos)
    with pytest.raises(ErrorServicioExterno) as info:
        AdaptadorAnthropic("modelo-de-prueba", cliente=cliente).generar_ruta(datos)
    assert mensaje_seguro(info.value) == ERROR_SERVICIO
    assert info.value.__suppress_context__
    assert datos == anterior


def test_simulado_fallo_y_agotamiento(datos):
    ia = AdaptadorSimulado(rutas=[RuntimeError("secreto")])
    for _ in range(2):
        with pytest.raises(ErrorServicioExterno, match=ERROR_SERVICIO):
            ia.generar_ruta(datos)


def test_config_no_habilita_simulado_ni_lee_entorno_real():
    with pytest.raises(ErrorServicioExterno, match="IA_V2_MODELO"):
        crear_adaptador({})
    with pytest.raises(ErrorServicioExterno, match="llave"):
        crear_adaptador({"IA_V2_MODELO": "modelo-prueba"})
    with pytest.raises(ErrorServicioExterno, match="proveedor"):
        crear_adaptador({"IA_V2_PROVEEDOR": "simulado"})


def test_fabrica_sdk_con_limite_y_sin_reintentos(monkeypatch):
    import sys
    constructor = Mock()
    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(Anthropic=constructor))
    ia = crear_adaptador({"IA_V2_MODELO": "modelo-prueba", "ANTHROPIC_API_KEY": "llave-ficticia"})
    assert isinstance(ia, AdaptadorAnthropic)
    constructor.assert_called_once_with(api_key="llave-ficticia", timeout=30.0, max_retries=0)
    constructor.return_value.messages.create.assert_not_called()
