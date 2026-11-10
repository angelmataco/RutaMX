"""Pruebas de M-08 (D-03 a y c, CA-19.3). Transporte falso: sin red."""

import pytest

from v2.integracion import verificador_geografico as vg
from v2.integracion.verificador_geografico import VerificadorNominatim
from v2.negocio.gestor_rutas import ErrorRutaInvalida, GestorRutas
from v2.utilerias import ErrorServicioExterno, ErrorValidacion

OAXACA = {"osm_type": "relation", "osm_id": 1234, "lat": "17.0654", "lon": "-96.7237"}


class RespuestaFalsa:
    def __init__(self, datos=None, error_http=False, json_roto=False):
        self._datos, self._error_http, self._json_roto = datos, error_http, json_roto

    def raise_for_status(self):
        if self._error_http:
            raise RuntimeError("HTTP 503 https://nominatim.example/?q=Oaxaca")

    def json(self):
        if self._json_roto:
            raise ValueError("no es JSON")
        return self._datos


class SesionFalsa:
    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.peticiones = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.peticiones.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta


def verificador(*respuestas):
    sesion = SesionFalsa(*respuestas)
    reloj = {"t": 0.0}
    esperas = []

    def dormir(segundos):
        esperas.append(segundos)
        reloj["t"] += segundos

    v = VerificadorNominatim(sesion, reloj=lambda: reloj["t"], dormir=dormir)
    return v, sesion, esperas


def test_lugar_encontrado_devuelve_id_y_coordenadas_numericas():
    v, sesion, _ = verificador(RespuestaFalsa([OAXACA]))
    assert v.verificar("Oaxaca") == {"id": "relation:1234", "latitud": 17.0654, "longitud": -96.7237}


def test_la_peticion_respeta_las_reglas_de_uso():
    v, sesion, _ = verificador(RespuestaFalsa([OAXACA]))
    v.verificar("  Oaxaca ")
    peticion = sesion.peticiones[0]
    assert peticion["url"] == vg.URL_NOMINATIM
    assert peticion["params"] == {"q": "Oaxaca", "format": "jsonv2", "limit": 1, "countrycodes": "mx"}
    assert peticion["headers"]["User-Agent"] == vg.USER_AGENT
    assert peticion["timeout"] == vg.TIMEOUT_SEGUNDOS
    assert len(sesion.peticiones) == 1  # sin reintentos


def test_user_agent_no_lleva_datos_personales():
    for dato in ("@", "angel", "mata", "gmail"):
        assert dato not in vg.USER_AGENT.casefold()


def test_lugar_que_no_existe_devuelve_none():
    v, _, _ = verificador(RespuestaFalsa([]))
    assert v.verificar("Atlantis") is None


def test_resultado_repetido_sale_de_la_cache_sin_nueva_peticion():
    v, sesion, _ = verificador(RespuestaFalsa([OAXACA]))
    primero = v.verificar("Oaxaca")
    segundo = v.verificar("OAXACA")
    assert primero == segundo and len(sesion.peticiones) == 1
    segundo["latitud"] = 0
    assert v.verificar("oaxaca")["latitud"] == 17.0654  # la cache no se contamina


def test_no_guarda_en_cache_un_lugar_no_encontrado():
    v, sesion, _ = verificador(RespuestaFalsa([]), RespuestaFalsa([OAXACA]))
    assert v.verificar("Oaxaca") is None
    assert v.verificar("Oaxaca")["id"] == "relation:1234"
    assert len(sesion.peticiones) == 2


def test_espera_un_segundo_entre_peticiones():
    v, _, esperas = verificador(RespuestaFalsa([OAXACA]), RespuestaFalsa([OAXACA]))
    v.verificar("Oaxaca")
    assert esperas == []
    v.verificar("Puebla")
    assert esperas == [pytest.approx(vg.INTERVALO_MINIMO_SEGUNDOS)]


@pytest.mark.parametrize("respuesta", [
    RuntimeError("fallo de red"),
    TimeoutError("tiempo agotado"),
    RespuestaFalsa(error_http=True),
    RespuestaFalsa(json_roto=True),
    RespuestaFalsa({"error": "limite"}),
    RespuestaFalsa("texto"),
    RespuestaFalsa([{"osm_type": "relation", "lat": "17", "lon": "-96"}]),
    RespuestaFalsa([{"osm_type": "relation", "osm_id": "x", "lat": "17", "lon": "-96"}]),
    RespuestaFalsa([{"osm_type": "relation", "osm_id": 1, "lat": "abc", "lon": "-96"}]),
    RespuestaFalsa([None]),
])
def test_servicio_caido_o_respuesta_rota_lanza_error_seguro(respuesta):
    v, _, _ = verificador(respuesta)
    with pytest.raises(ErrorServicioExterno) as info:
        v.verificar("Oaxaca")
    texto = str(info.value)
    assert texto == vg.ERROR_SERVICIO
    assert "nominatim" not in texto.casefold() and "Oaxaca" not in texto


def test_nombre_invalido_no_llega_al_servicio():
    v, sesion, _ = verificador()
    for malo in ("", "  ", None, 5):
        with pytest.raises(ErrorValidacion):
            v.verificar(malo)
    assert sesion.peticiones == []


# --- Integración con M-05: el contrato de verificador se cumple de punta a punta ---

def propuesta():
    return {"origen": "Puebla", "destino": "Oaxaca", "duracion_dias": 2, "paradas": []}


PUEBLA = {"osm_type": "relation", "osm_id": 99, "lat": "19.04", "lon": "-98.20"}


def test_m05_acepta_una_ruta_verificada_con_m08():
    v, _, _ = verificador(RespuestaFalsa([PUEBLA]), RespuestaFalsa([OAXACA]))
    ruta = GestorRutas(v).proponer(propuesta())
    assert ruta["origen_lugar"]["id"] == "relation:99"
    assert ruta["destino_lugar"]["latitud"] == 17.0654


def test_m05_rechaza_un_lugar_que_m08_no_identifica():
    v, _, _ = verificador(RespuestaFalsa([PUEBLA]), RespuestaFalsa([]))
    with pytest.raises(ErrorRutaInvalida):
        GestorRutas(v).proponer(propuesta())


def test_m05_no_acepta_la_ruta_si_el_servicio_cae_y_conserva_la_previa():
    v, _, _ = verificador(
        RespuestaFalsa([PUEBLA]), RespuestaFalsa([OAXACA]), RuntimeError("caído"))
    g = GestorRutas(v)
    g.proponer(propuesta())
    antes = g.ruta
    with pytest.raises(ErrorRutaInvalida):
        g.proponer({**propuesta(), "destino": "Mérida"})
    assert g.ruta == antes
