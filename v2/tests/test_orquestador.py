"""M-04 con IA y geografía simuladas; nombres y coordenadas ficticios."""
from copy import deepcopy
from unittest.mock import Mock

import pytest

from v2.integracion.adaptador_ia import AdaptadorSimulado
from v2.negocio.orquestador import OrquestadorPlaneacion

DATOS = {"origen": "Lugar A", "destino": "Lugar B", "duracion_dias": 3}


class GeografiaFalsa:
    def verificar(self, nombre):
        return {"id": nombre, "latitud": 1.0, "longitud": 2.0}


def propuesta(**cambios):
    return {**DATOS, "paradas": [{"nombre": "Lugar C"}], **cambios}


def crear(extracciones=(), rutas=(), verificador=True):
    return OrquestadorPlaneacion(AdaptadorSimulado(extracciones=extracciones, rutas=rutas),
                                GeografiaFalsa() if verificador else None)


def test_inicio_idempotente_no_llama_ia():
    ia = Mock()
    o = OrquestadorPlaneacion(ia)
    a = o.iniciar()
    assert o.iniciar() == a
    assert a["faltantes"] == ["origen", "destino", "duracion_dias"]
    assert a["ruta"] is None
    ia.extraer_datos.assert_not_called()


def test_conversacion_acumula_y_solo_pide_lo_faltante():
    o = crear([{"origen": "Lugar A"}, {"destino": "Lugar B"}, {"duracion_dias": 3}], [propuesta()])
    a = o.procesar("Salgo de A")
    assert a["estado"] == "faltan_datos"
    assert a["faltantes"] == ["destino", "duracion_dias"]
    assert a["mensaje"] == "Para proponer la ruta necesito: destino, duración en días."
    b = o.procesar("Voy a B")
    assert b["faltantes"] == ["duracion_dias"]
    c = o.procesar("Tres días")
    assert c["estado"] == "propuesta"
    assert c["ruta"]["origen"] == "Lugar A"
    assert c["itinerario"][0]["nombre"] == "Lugar C"
    assert c["mensaje"] == "Lugar A a Lugar B, 3 días. Paradas: Lugar C."


def test_acepta_datos_completos_e_intereses_opcionales():
    o = crear([DATOS], [propuesta(paradas=[])])
    r = o.procesar("A a B en tres días")
    assert r["estado"] == "propuesta" and r["itinerario"] == []
    assert r["faltantes"] == []


def test_intereses_se_conservan():
    datos = {**DATOS, "intereses": ["cultura"]}
    o = crear([datos], [propuesta(intereses=["cultura"])])
    assert o.procesar("Viaje cultural")["ruta"]["intereses"] == ["cultura"]


@pytest.mark.parametrize("respuesta", [{}, propuesta(destino="Lugar equivocado"), propuesta(duracion_dias=2), propuesta(intereses=["otros"])])
def test_no_acepta_respuesta_que_no_cumple_solicitud(respuesta):
    r = crear([DATOS], [respuesta]).procesar("Viaje")
    assert r["estado"] == "error" and r["ruta"] is None


@pytest.mark.parametrize("fallo", [RuntimeError("secreto"), "no JSON", {}, propuesta(paradas=None)])
def test_fallo_de_generacion_conserva_ruta_y_datos_nuevos_del_usuario(fallo):
    o = crear([DATOS, {"duracion_dias": 4}], [propuesta(), fallo])
    anterior = o.procesar("Primer viaje")
    r = o.procesar("Otro viaje de cuatro días")
    assert r["estado"] == "error"
    assert r["ruta"] == anterior["ruta"]
    assert r["datos"] == {**DATOS, "duracion_dias": 4}
    assert r["itinerario"] == anterior["itinerario"]
    assert "secreto" not in r["mensaje"]


def test_fallo_extraccion_conserva_ruta():
    o = crear([DATOS, RuntimeError("secreto")], [propuesta()])
    antes = o.procesar("Viaje")
    despues = o.procesar("Cambio")
    assert despues["ruta"] == antes["ruta"]
    assert despues["estado"] == "error"


def test_sin_verificador_no_presenta_ruta_valida():
    r = crear([DATOS], [propuesta()], verificador=False).procesar("Viaje")
    assert r["estado"] == "error" and r["ruta"] is None
    assert "servicio de lugares" in r["mensaje"]


def test_error_inesperado_no_filtra_detalle():
    ia = Mock()
    ia.extraer_datos.side_effect = RuntimeError("llave-secreta")
    r = OrquestadorPlaneacion(ia).procesar("Viaje")
    assert r["estado"] == "error"
    assert "llave-secreta" not in r["mensaje"]


@pytest.mark.parametrize("mensaje", [None, "", 4, "a" * 1001])
def test_entrada_invalida_no_llama_ia(mensaje):
    ia = Mock()
    assert OrquestadorPlaneacion(ia).procesar(mensaje)["estado"] == "error"
    ia.extraer_datos.assert_not_called()


def test_copias_de_salida_no_alteran_estado():
    o = crear([DATOS], [propuesta()])
    r = o.procesar("Viaje")
    antes = deepcopy(r)
    r["ruta"]["paradas"].clear()
    r["datos"]["origen"] = "Otro"
    r["mensajes"].clear()
    assert o.iniciar()["ruta"] == antes["ruta"]
    assert o.iniciar()["datos"] == antes["datos"]
    assert o.iniciar()["mensajes"] == antes["mensajes"]


def test_confirmacion_igualdad_reintenta_sin_volver_a_llamar_ia():
    datos = {**DATOS, "destino": "Lugar A"}
    o = crear([datos], [propuesta(destino="Lugar A")])
    r = o.procesar("Ida y vuelta")
    assert r["estado"] == "confirmar" and r["ruta"] is None
    assert r["confirmacion"] == "origen_igual_destino"
    r = o.procesar("Sí")
    assert r["estado"] == "propuesta" and r["confirmacion"] is None
    assert r["ruta"]["destino"] == "Lugar A"


def test_dos_confirmaciones_se_piden_por_separado():
    datos = {**DATOS, "destino": "Lugar A"}
    o = crear([datos], [propuesta(destino="Lugar A", paradas=[{"nombre": "Lugar A"}])])
    assert o.procesar("Viaje")["confirmacion"] == "origen_igual_destino"
    assert o.confirmar(True)["confirmacion"] == "paradas_repetidas"
    assert o.confirmar(True)["estado"] == "propuesta"


def test_rechazar_conserva_ruta_anterior():
    o = crear([DATOS, {"destino": "Lugar A"}], [propuesta(), propuesta(destino="Lugar A")])
    antes = o.procesar("Viaje")
    assert o.procesar("Otro")["estado"] == "confirmar"
    r = o.confirmar(False)
    assert r["estado"] == "cancelado"
    assert r["ruta"] == antes["ruta"]


def test_nueva_descripcion_invalida_confirmacion_anterior():
    datos = {**DATOS, "destino": "Lugar A"}
    o = crear([datos, {"origen": "Lugar X"}], [propuesta(destino="Lugar A")])
    assert o.procesar("Viaje")["estado"] == "confirmar"
    o.procesar("Cambio el origen")
    assert o.confirmar(True)["estado"] == "error"
    assert o.iniciar()["ruta"] is None


@pytest.mark.parametrize("acepta", ["sí", 1, None])
def test_confirmacion_no_booleana_se_rechaza(acepta):
    assert crear().confirmar(acepta)["estado"] == "error"


def test_dos_conversaciones_no_comparten_datos():
    a = crear([{"origen": "Lugar A"}])
    b = crear()
    a.procesar("Salgo de A")
    assert b.iniciar()["datos"] == {}


def test_geografia_caida_durante_confirmacion_conserva_ruta():
    geo = Mock()
    geo.verificar.side_effect = GeografiaFalsa().verificar
    ia = AdaptadorSimulado(extracciones=[DATOS, {"destino": "Lugar A"}], rutas=[propuesta(), propuesta(destino="Lugar A")])
    o = OrquestadorPlaneacion(ia, geo)
    antes = o.procesar("Viaje")
    assert o.procesar("Otro")["estado"] == "confirmar"
    geo.verificar.side_effect = RuntimeError("secreto")
    r = o.confirmar(True)
    assert r["estado"] == "error" and r["ruta"] == antes["ruta"]
    assert "secreto" not in r["mensaje"]


def test_corregir_propuesta_pendiente_conserva_datos_no_cambiados():
    datos = {**DATOS, "destino": "Lugar A"}
    o = crear([datos, {"destino": "Lugar B"}], [propuesta(destino="Lugar A"), propuesta()])
    assert o.procesar("Ida y vuelta")["estado"] == "confirmar"
    r = o.procesar("Mejor a Lugar B")
    assert r["estado"] == "propuesta" and r["datos"] == DATOS
    assert o.confirmar(True)["estado"] == "error"


@pytest.mark.parametrize("fallo", [RuntimeError("secreto"), {}, propuesta(destino="Otro"), propuesta(intereses=["otros"])])
def test_reintento_tras_fallo_no_pide_de_nuevo_datos_completos(fallo):
    o = crear([DATOS, {}], [fallo, propuesta()])
    r = o.procesar("De A a B tres días")
    assert r["estado"] == "error" and r["datos"] == DATOS
    assert r["faltantes"] == []
    r = o.procesar("Intenta otra vez")
    assert r["estado"] == "propuesta"
    assert r["datos"] == DATOS and r["faltantes"] == []


def test_reintento_tras_fallo_geografico_conserva_datos_y_ruta_previa():
    geo = Mock()
    geo.verificar.side_effect = GeografiaFalsa().verificar
    ia = AdaptadorSimulado(extracciones=[DATOS, {"duracion_dias": 4}, {}],
                          rutas=[propuesta(), propuesta(duracion_dias=4), propuesta(duracion_dias=4)])
    o = OrquestadorPlaneacion(ia, geo)
    anterior = o.procesar("Viaje")
    geo.verificar.side_effect = RuntimeError("secreto")
    r = o.procesar("Cuatro días")
    assert r["estado"] == "error" and r["ruta"] == anterior["ruta"]
    assert r["datos"]["duracion_dias"] == 4
    geo.verificar.side_effect = GeografiaFalsa().verificar
    r = o.procesar("Intenta otra vez")
    assert r["estado"] == "propuesta" and r["ruta"]["duracion_dias"] == 4
