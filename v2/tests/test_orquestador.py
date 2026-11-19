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
    o = crear([DATOS, {"origen": "Lugar A", "duracion_dias": 4}], [propuesta(), fallo])
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
    ia = AdaptadorSimulado(extracciones=[DATOS, {"origen": "Lugar A", "duracion_dias": 4}, {}],
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


def con_modificaciones(modificaciones):
    ia = AdaptadorSimulado(extracciones=[DATOS, {}, {}, {}], rutas=[propuesta()],
                          modificaciones=modificaciones)
    o = OrquestadorPlaneacion(ia, GeografiaFalsa())
    o.procesar('Viaje')
    return o


def test_agregar_por_chat_y_posicion_cero():
    o = con_modificaciones([{'accion': 'agregar_parada', 'nombre': 'Lugar D', 'posicion': 0}])
    r = o.procesar('Agrega Lugar D al principio')
    assert r['estado'] == 'propuesta'
    assert [p['nombre'] for p in r['ruta']['paradas']] == ['Lugar D', 'Lugar C']


def test_aclaracion_conserva_intencion_y_ruta():
    o = con_modificaciones([{'accion': 'aclarar', 'pregunta': '¿En dónde?'},
                           {'accion': 'agregar_parada', 'nombre': 'Lugar D'}])
    antes = o.iniciar()['ruta']
    assert o.procesar('Agrega una parada')['estado'] == 'aclarar'
    assert o.iniciar()['ruta'] == antes
    original = o._ia.interpretar_modificacion
    o._ia.interpretar_modificacion = Mock(wraps=original)
    r = o.procesar('Lugar D')
    contexto = o._ia.interpretar_modificacion.call_args.args[0]
    assert 'Agrega una parada' in contexto and 'Lugar D' in contexto
    assert len(r['ruta']['paradas']) == 2


@pytest.mark.parametrize('accion', [{'accion': 'no_soportada'}, RuntimeError('secreto'),
    {'accion': 'agregar_parada', 'nombre': 'Lugar D', 'posicion': 99}])
def test_modificacion_fallida_o_no_soportada_conserva_ruta(accion):
    o = con_modificaciones([accion])
    antes = o.iniciar()['ruta']
    r = o.procesar('Cambia')
    assert r['estado'] in {'error', 'no_soportada'}
    assert r['ruta'] == antes
    assert 'secreto' not in r['mensaje']


def test_modificacion_repetida_confirma_sin_llamar_ia_otra_vez():
    o = con_modificaciones([{'accion': 'agregar_parada', 'nombre': 'Lugar C'}])
    antes = o.iniciar()['ruta']
    assert o.procesar('Agrega Lugar C')['estado'] == 'confirmar'
    assert o.iniciar()['ruta'] == antes
    assert len(o.confirmar(True)['ruta']['paradas']) == 2


def test_fallo_confirmacion_modificacion_no_regenera_en_siguiente_mensaje():
    geo = Mock()
    geo.verificar.side_effect = GeografiaFalsa().verificar
    ia = AdaptadorSimulado(
        extracciones=[DATOS, {}, {}], rutas=[propuesta()],
        modificaciones=[{'accion': 'agregar_parada', 'nombre': 'Lugar C'},
                        {'accion': 'agregar_parada', 'nombre': 'Lugar E'}])
    ia.generar_ruta = Mock(wraps=ia.generar_ruta)
    o = OrquestadorPlaneacion(ia, geo)
    antes = o.procesar('Viaje')['ruta']
    assert o.procesar('Agrega C')['estado'] == 'confirmar'
    geo.verificar.side_effect = RuntimeError('secreto')
    assert o.confirmar(True)['ruta'] == antes
    geo.verificar.side_effect = GeografiaFalsa().verificar
    r = o.procesar('Agrega E')
    assert r['estado'] == 'propuesta'
    assert [p['nombre'] for p in r['ruta']['paradas']] == ['Lugar C', 'Lugar E']
    assert ia.generar_ruta.call_count == 1


@pytest.mark.parametrize('accion', [
    {'accion': 'eliminar_parada', 'nombre': 'Lugar C'},
    {'accion': 'eliminar_parada', 'posicion': 0},
])
def test_eliminar_por_chat_actualiza_itinerario_y_permite_cero_paradas(accion):
    o = con_modificaciones([accion])
    antes = o.iniciar()
    r = o.procesar('Quita la parada')
    assert r['estado'] == 'propuesta' and r['itinerario'] == []
    assert r['ruta']['paradas'] == []
    assert r['datos'] == antes['datos']
    assert r['ruta']['origen'] == antes['ruta']['origen']
    assert r['ruta']['destino'] == antes['ruta']['destino']


def conversacion_con_dos_paradas(acciones, geo=None, **cambios):
    datos = {**DATOS, **{k: v for k, v in cambios.items() if k in DATOS}}
    ia = AdaptadorSimulado(extracciones=[datos, {}, {}, {}],
                          rutas=[propuesta(paradas=[{'nombre': 'Lugar C'}, {'nombre': 'Lugar D'}], **cambios)],
                          modificaciones=acciones)
    ia.generar_ruta = Mock(wraps=ia.generar_ruta)
    ia.interpretar_modificacion = Mock(wraps=ia.interpretar_modificacion)
    o = OrquestadorPlaneacion(ia, geo or GeografiaFalsa())
    o.procesar('Viaje')
    return o


def test_reordenar_por_chat_actualiza_secuencia_sin_generar_otra_ruta():
    o = conversacion_con_dos_paradas([{'accion': 'reordenar_paradas', 'orden': ['Lugar D', 'Lugar C']}])
    r = o.procesar('Invierte las paradas')
    assert r['estado'] == 'propuesta'
    assert [p['nombre'] for p in r['itinerario']] == ['Lugar D', 'Lugar C']
    assert [p['orden'] for p in r['itinerario']] == [1, 2]
    assert o._ia.generar_ruta.call_count == 1


@pytest.mark.parametrize('accion', [
    {'accion': 'eliminar_parada', 'nombre': 'Lugar A'},
    {'accion': 'eliminar_parada', 'nombre': 'Lugar B'},
    {'accion': 'eliminar_parada', 'nombre': 'Ajeno'},
    {'accion': 'eliminar_parada', 'posicion': True},
    {'accion': 'eliminar_parada', 'posicion': -1},
    {'accion': 'eliminar_parada', 'posicion': 99},
    {'accion': 'reordenar_paradas', 'orden': ['Ajeno']},
])
def test_cambios_invalidos_por_chat_conservan_itinerario(accion):
    o = con_modificaciones([accion])
    antes = o.iniciar()
    r = o.procesar('Cambio')
    assert r['estado'] == 'error'
    assert r['ruta'] == antes['ruta'] and r['itinerario'] == antes['itinerario']


def test_reordenar_una_parada_informa_sin_cambios():
    o = con_modificaciones([{'accion': 'reordenar_paradas', 'orden': ['Lugar C']}])
    antes = o.iniciar()['ruta']
    r = o.procesar('Reordena')
    assert r['estado'] == 'propuesta' and r['ruta'] == antes
    assert 'no hay cambios' in r['mensaje']


def test_rf34_enumera_operaciones_y_conserva_ruta():
    o = con_modificaciones([{'accion': 'no_soportada'}])
    antes = o.iniciar()['ruta']
    r = o.procesar('Reserva un hotel')
    assert r['estado'] == 'no_soportada' and r['ruta'] == antes
    for texto in ('no está disponible', 'eliminar', 'reordenarlas', 'duración', 'tipo de lugares'):
        assert texto in r['mensaje']


def test_aclaracion_para_eliminar_conserva_intencion():
    o = con_modificaciones([{'accion': 'aclarar', 'pregunta': '¿Cuál parada?'},
                           {'accion': 'eliminar_parada', 'nombre': 'Lugar C'}])
    antes = o.iniciar()['ruta']
    assert o.procesar('Quita una parada')['estado'] == 'aclarar'
    assert o.iniciar()['ruta'] == antes
    assert o.procesar('Lugar C')['ruta']['paradas'] == []


@pytest.mark.parametrize('accion', [
    {'accion': 'eliminar_parada', 'nombre': 'Lugar C'},
    {'accion': 'reordenar_paradas', 'orden': ['Lugar D', 'Lugar C']},
])
def test_confirmar_operacion_nueva_sin_reconsultar_ia(accion):
    o = conversacion_con_dos_paradas([accion], destino='Lugar A')
    assert o.confirmar(True)['estado'] == 'propuesta'
    antes = o.iniciar()['ruta']
    assert o.procesar('Cambio')['estado'] == 'confirmar'
    assert o.iniciar()['ruta'] == antes
    r = o.confirmar(True)
    assert r['estado'] == 'propuesta' and r['confirmacion'] is None
    assert r['ruta'] != antes
    assert o._ia.interpretar_modificacion.call_count == 1
    assert o._ia.generar_ruta.call_count == 1


def test_cancelar_operacion_nueva_conserva_ruta():
    o = conversacion_con_dos_paradas([{'accion': 'eliminar_parada', 'posicion': 0}], destino='Lugar A')
    o.confirmar(True)
    antes = o.iniciar()['ruta']
    assert o.procesar('Quita primera')['estado'] == 'confirmar'
    assert o.confirmar(False)['ruta'] == antes
    assert o.confirmar(True)['estado'] == 'error'


def test_fallo_en_confirmacion_de_eliminar_no_regenera_despues():
    geo = Mock()
    geo.verificar.side_effect = GeografiaFalsa().verificar
    o = conversacion_con_dos_paradas([
        {'accion': 'eliminar_parada', 'posicion': 0},
        {'accion': 'reordenar_paradas', 'orden': ['Lugar D', 'Lugar C']},
    ], geo, destino='Lugar A')
    o.confirmar(True)
    antes = o.iniciar()['ruta']
    assert o.procesar('Quita primera')['estado'] == 'confirmar'
    geo.verificar.side_effect = RuntimeError('secreto')
    fallo = o.confirmar(True)
    assert fallo['estado'] == 'error' and fallo['ruta'] == antes
    assert 'secreto' not in fallo['mensaje']
    geo.verificar.side_effect = GeografiaFalsa().verificar
    assert o.procesar('Reordena')['estado'] == 'confirmar'
    assert o.confirmar(True)['estado'] == 'propuesta'
    assert o._ia.generar_ruta.call_count == 1


def con_preferencias(cambios, respuesta, extraidos=None, geo=None):
    ia = AdaptadorSimulado(
        extracciones=[DATOS, {} if extraidos is None else extraidos, {}],
        rutas=[propuesta(), respuesta],
        modificaciones=[{'accion': 'cambiar_preferencias', **cambios},
                        {'accion': 'agregar_parada', 'nombre': 'Lugar E'}])
    ia.generar_ruta = Mock(wraps=ia.generar_ruta)
    ia.interpretar_modificacion = Mock(wraps=ia.interpretar_modificacion)
    o = OrquestadorPlaneacion(ia, geo or GeografiaFalsa())
    o.procesar('Viaje')
    return o


@pytest.mark.parametrize('cambios', [
    {'duracion_dias': 5}, {'intereses': ['cultura']},
    {'duracion_dias': 60, 'intereses': ['naturaleza']},
])
def test_preferencias_regeneran_y_actualizan_itinerario(cambios):
    nueva = propuesta(paradas=[{'nombre': 'Lugar D'}], **cambios)
    o = con_preferencias(cambios, nueva)
    r = o.procesar('Cambia las preferencias')
    assert r['estado'] == 'propuesta'
    assert [p['nombre'] for p in r['itinerario']] == ['Lugar D']
    for campo, valor in cambios.items():
        assert r['ruta'][campo] == valor and r['datos'][campo] == valor
    assert r['ruta']['origen'] == DATOS['origen']
    assert r['ruta']['destino'] == DATOS['destino']
    assert o._ia.generar_ruta.call_count == 2


@pytest.mark.parametrize('cambios', [{'duracion_dias': 3}, {'intereses': []},
                                    {'duracion_dias': 3, 'intereses': []}])
def test_preferencias_iguales_no_regeneran(cambios):
    o = con_preferencias(cambios, RuntimeError('No debe llamarse'))
    antes = o.iniciar()
    r = o.procesar('Mismas preferencias')
    assert r['estado'] == 'propuesta'
    assert r['ruta'] == antes['ruta'] and r['datos'] == antes['datos']
    assert r['itinerario'] == antes['itinerario']
    assert o._ia.generar_ruta.call_count == 1


@pytest.mark.parametrize('cambios', [
    {}, {'duracion_dias': 0}, {'duracion_dias': 61}, {'duracion_dias': True},
    {'duracion_dias': '4'}, {'intereses': 'cultura'}, {'intereses': [None]},
    {'duracion_dias': 4, 'origen': 'Otro lugar'},
])
def test_preferencias_invalidas_no_cambian_datos_ni_ruta(cambios):
    o = con_preferencias(cambios, RuntimeError('No debe llamarse'))
    antes = o.iniciar()
    r = o.procesar('Cambia preferencias')
    assert r['estado'] == 'error'
    assert r['ruta'] == antes['ruta'] and r['datos'] == antes['datos']
    assert o._ia.generar_ruta.call_count == 1


@pytest.mark.parametrize('fallo', [RuntimeError('secreto'), {},
    propuesta(duracion_dias=4, destino='Otro'),
    propuesta(duracion_dias=3), propuesta(duracion_dias=4, intereses=['ajenos']),
    propuesta(duracion_dias=4, paradas=None)])
def test_fallo_preferencias_conserva_datos_anteriores_y_no_regenera_luego(fallo):
    o = con_preferencias({'duracion_dias': 4}, fallo)
    antes = o.iniciar()
    r = o.procesar('Cuatro días')
    assert r['estado'] == 'error'
    assert r['ruta'] == antes['ruta'] and r['datos'] == antes['datos']
    assert r['itinerario'] == antes['itinerario'] and 'secreto' not in r['mensaje']
    r = o.procesar('Agrega E')
    assert r['estado'] == 'propuesta'
    assert r['ruta']['duracion_dias'] == 3
    assert o._ia.generar_ruta.call_count == 2


def test_preferencia_extraida_tambien_es_atomica_sin_pasarla_por_modificacion():
    o = con_preferencias({}, RuntimeError('secreto'), extraidos={'duracion_dias': 4})
    antes = o.iniciar()
    r = o.procesar('Cuatro días')
    assert r['estado'] == 'error'
    assert r['ruta'] == antes['ruta'] and r['datos'] == antes['datos']
    o._ia.interpretar_modificacion.assert_not_called()


def test_preferencia_extraida_valida_actualiza_ruta():
    o = con_preferencias({}, propuesta(duracion_dias=4), extraidos={'duracion_dias': 4})
    r = o.procesar('Cuatro días')
    assert r['estado'] == 'propuesta' and r['ruta']['duracion_dias'] == 4
    assert r['datos']['duracion_dias'] == 4


def test_preferencias_con_fallo_geografico_preservan_ambos_estados():
    geo = Mock()
    geo.verificar.side_effect = GeografiaFalsa().verificar
    o = con_preferencias({'duracion_dias': 4}, propuesta(duracion_dias=4), geo=geo)
    antes = o.iniciar()
    geo.verificar.side_effect = RuntimeError('secreto')
    r = o.procesar('Cuatro días')
    assert r['estado'] == 'error'
    assert r['ruta'] == antes['ruta'] and r['datos'] == antes['datos']


@pytest.mark.parametrize('respuesta', [True, False, 'fallo'])
def test_preferencias_pendientes_no_confirman_datos_hasta_aceptar(respuesta):
    geo = Mock()
    geo.verificar.side_effect = GeografiaFalsa().verificar
    repetida = propuesta(duracion_dias=4, paradas=[{'nombre': 'Lugar C'}, {'nombre': 'Lugar C'}])
    o = con_preferencias({'duracion_dias': 4}, repetida, geo=geo)
    antes = o.iniciar()
    pendiente = o.procesar('Cuatro días')
    assert pendiente['estado'] == 'confirmar'
    assert pendiente['datos'] == antes['datos'] and pendiente['ruta'] == antes['ruta']
    if respuesta == 'fallo':
        geo.verificar.side_effect = RuntimeError('secreto')
    r = o.confirmar(respuesta is not False)
    if respuesta is True:
        assert r['estado'] == 'propuesta'
        assert r['ruta']['duracion_dias'] == r['datos']['duracion_dias'] == 4
    else:
        assert r['estado'] == ('cancelado' if respuesta is False else 'error')
        assert r['datos'] == antes['datos'] and r['ruta'] == antes['ruta']
    assert o._ia.generar_ruta.call_count == 2


def test_quitar_intereses_regenera_con_lista_vacia():
    ia = AdaptadorSimulado(
        extracciones=[{**DATOS, 'intereses': ['cultura']}, {}],
        rutas=[propuesta(intereses=['cultura']), propuesta(intereses=[])],
        modificaciones=[{'accion': 'cambiar_preferencias', 'intereses': []}])
    o = OrquestadorPlaneacion(ia, GeografiaFalsa())
    o.procesar('Viaje cultural')
    r = o.procesar('Quita preferencias')
    assert r['estado'] == 'propuesta'
    assert r['datos']['intereses'] == r['ruta']['intereses'] == []
