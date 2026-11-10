"""Pruebas de M-05 (RF-22, 23, 24, 35, 37, 43; D-03 a, b y c; CA-19.3).

Sin base ni red: la fuente geográfica es un verificador falso con datos
ficticios.
"""

from copy import deepcopy

import pytest

from v2.negocio.gestor_rutas import (
    CONFIRMACION_ORIGEN_IGUAL_DESTINO, CONFIRMACION_PARADAS_REPETIDAS,
    ErrorRutaInvalida, ErrorRutaRequiereConfirmacion, GestorRutas, MAX_PARADAS,
    validar_ruta,
)
from v2.utilerias import ErrorValidacion

LUGARES = {
    "Ciudad de México": ("cdmx", 19.43, -99.13),
    "Oaxaca": ("oax", 17.07, -96.72),
    "Puebla": ("pue", 19.04, -98.20),
    "Tehuacán": ("teh", 18.46, -97.39),
    "Mérida": ("mer", 20.97, -89.62),
    "Campeche": ("cam", 19.85, -90.53),
}


class VerificadorFalso:
    """Fuente geográfica de prueba: datos ficticios, sin red."""

    def __init__(self, lugares=None, falla=False):
        self.lugares = dict(LUGARES if lugares is None else lugares)
        self.falla = falla
        self.llamadas = []

    def verificar(self, nombre):
        self.llamadas.append(nombre)
        if self.falla:
            raise ConnectionError("https://geo.example/?key=SECRETA caído")
        datos = self.lugares.get(nombre)
        if not isinstance(datos, tuple):
            return datos  # None, diccionario o basura: tal cual
        return {"id": datos[0], "latitud": datos[1], "longitud": datos[2]}


def gestor(verificador=None):
    return GestorRutas(VerificadorFalso() if verificador is None else verificador)


def propuesta(**cambios):
    base = {
        "origen": "Ciudad de México",
        "destino": "Oaxaca",
        "duracion_dias": 3,
        "intereses": ["comida"],
        "paradas": [
            {"nombre": "Puebla", "descripcion": "Centro histórico"},
            {"nombre": "Tehuacán"},
        ],
    }
    base.update(cambios)
    return base


def validar(entrada, **kw):
    return validar_ruta(entrada, VerificadorFalso(), **kw)


# --- Forma de la propuesta (RF-19, RF-22) ---

def test_propuesta_valida_se_normaliza_y_trae_coordenadas():
    ruta = validar(propuesta(origen="  Ciudad de México "))
    assert ruta["origen"] == "Ciudad de México"
    assert ruta["origen_lugar"] == {"id": "cdmx", "latitud": 19.43, "longitud": -99.13}
    assert ruta["paradas"][1]["nombre"] == "Tehuacán"
    assert ruta["paradas"][1]["descripcion"] == ""
    assert ruta["paradas"][1]["lugar"]["id"] == "teh"


def test_paradas_vacias_son_validas():
    assert validar(propuesta(paradas=[]))["paradas"] == []


def test_intereses_ausentes_quedan_en_lista_vacia():
    datos = propuesta()
    del datos["intereses"]
    assert validar(datos)["intereses"] == []


def test_no_modifica_la_propuesta_original():
    original = propuesta()
    copia = deepcopy(original)
    validar(original)
    assert original == copia


def test_paradas_en_el_limite_pasan_y_una_mas_falla():
    lugares = dict(LUGARES, **{f"P{i}": (f"p{i}", 18.0, -97.0) for i in range(MAX_PARADAS + 1)})
    ok = [{"nombre": f"P{i}"} for i in range(MAX_PARADAS)]
    assert len(validar_ruta(propuesta(paradas=ok), VerificadorFalso(lugares))["paradas"]) == MAX_PARADAS
    with pytest.raises(ErrorRutaInvalida):
        validar_ruta(propuesta(paradas=ok + [{"nombre": "P30"}]), VerificadorFalso(lugares))


@pytest.mark.parametrize("entrada", [
    None, {}, [], "ruta", 5,
    propuesta(origen=None), propuesta(origen="  "), propuesta(destino=""),
    propuesta(duracion_dias=0), propuesta(duracion_dias=-1), propuesta(duracion_dias="3"),
    propuesta(duracion_dias=True), propuesta(duracion_dias=None),
    propuesta(paradas=None), propuesta(paradas="Puebla"),
    propuesta(paradas=["Puebla"]), propuesta(paradas=[{"nombre": ""}]),
    propuesta(paradas=[{"descripcion": "sin nombre"}]),
    propuesta(paradas=[{"nombre": "Puebla", "descripcion": 5}]),
    propuesta(intereses="comida"),
])
def test_propuesta_mal_formada_pide_cambios(entrada):
    with pytest.raises(ErrorRutaInvalida) as info:
        validar(entrada)
    assert "Cambia el origen, el destino o la duración" in str(info.value)


def test_error_de_ruta_invalida_es_un_error_de_validacion():
    assert issubclass(ErrorRutaInvalida, ErrorValidacion)
    assert issubclass(ErrorRutaRequiereConfirmacion, ErrorRutaInvalida)


# --- D-03 (a): origen y destino identificables ---

@pytest.mark.parametrize("campo", ["origen", "destino"])
def test_lugar_inexistente_en_origen_o_destino_se_rechaza(campo):
    with pytest.raises(ErrorRutaInvalida) as info:
        validar(propuesta(**{campo: "Atlantis"}))
    assert "Atlantis" in str(info.value) and "identificar" in str(info.value)


def test_parada_inexistente_se_rechaza():
    with pytest.raises(ErrorRutaInvalida):
        validar(propuesta(paradas=[{"nombre": "Lugar Inventado"}]))


# --- D-03 (c): identificador y coordenadas válidas ---

@pytest.mark.parametrize("lugar", [
    {"id": "", "latitud": 19.0, "longitud": -99.0},
    {"id": None, "latitud": 19.0, "longitud": -99.0},
    {"latitud": 19.0, "longitud": -99.0},
    {"id": "x", "latitud": 91.0, "longitud": -99.0},
    {"id": "x", "latitud": -90.5, "longitud": -99.0},
    {"id": "x", "latitud": 19.0, "longitud": 181.0},
    {"id": "x", "latitud": float("nan"), "longitud": -99.0},
    {"id": "x", "latitud": float("inf"), "longitud": -99.0},
    {"id": "x", "latitud": "19.0", "longitud": -99.0},
    {"id": "x", "latitud": True, "longitud": -99.0},
    {"id": "x", "latitud": 19.0},
])
def test_coordenadas_o_id_invalidos_se_rechazan(lugar):
    verificador = VerificadorFalso(dict(LUGARES, Oaxaca=lugar))
    with pytest.raises(ErrorRutaInvalida):
        validar_ruta(propuesta(), verificador)


def test_coordenadas_en_los_limites_exactos_pasan():
    verificador = VerificadorFalso(dict(LUGARES, Oaxaca={"id": "x", "latitud": 90, "longitud": -180}))
    assert validar_ruta(propuesta(), verificador)["destino_lugar"]["latitud"] == 90.0


def test_respuesta_del_verificador_que_no_es_diccionario_se_rechaza():
    verificador = VerificadorFalso(dict(LUGARES, Oaxaca=["oax", 17, -96]))
    with pytest.raises(ErrorRutaInvalida):
        validar_ruta(propuesta(), verificador)


# --- CA-19.3: sin servicio de validación no se presenta como válida ---

def test_servicio_caido_no_acepta_la_ruta_ni_filtra_detalles():
    with pytest.raises(ErrorRutaInvalida) as info:
        validar_ruta(propuesta(), VerificadorFalso(falla=True))
    texto = str(info.value)
    assert "no está disponible" in texto
    assert "SECRETA" not in texto and "geo.example" not in texto


@pytest.mark.parametrize("verificador", [None, object()])
def test_sin_verificador_falla_de_forma_segura(verificador):
    with pytest.raises(ErrorRutaInvalida) as info:
        validar_ruta(propuesta(), verificador)
    assert "no se presenta como válida" in str(info.value)
    with pytest.raises(ErrorRutaInvalida):
        GestorRutas(verificador).proponer(propuesta())


def test_gestor_por_defecto_no_acepta_nada_sin_fuente_geografica():
    gestor_sin_fuente = GestorRutas()
    with pytest.raises(ErrorRutaInvalida):
        gestor_sin_fuente.proponer(propuesta())
    assert gestor_sin_fuente.ruta is None


# --- D-03 (b): secuencia coherente y confirmaciones ---

def test_origen_igual_destino_pide_confirmacion():
    with pytest.raises(ErrorRutaRequiereConfirmacion) as info:
        validar(propuesta(destino="Ciudad de México"))
    assert info.value.pendiente == CONFIRMACION_ORIGEN_IGUAL_DESTINO
    assert "ida y vuelta" in str(info.value)


def test_origen_igual_destino_confirmado_se_acepta():
    ruta = validar(
        propuesta(destino="Ciudad de México"),
        confirmaciones={CONFIRMACION_ORIGEN_IGUAL_DESTINO})
    assert ruta["destino"] == "Ciudad de México"


def test_origen_y_destino_iguales_por_identificador_aunque_cambie_el_nombre():
    lugares = dict(LUGARES, **{"CDMX": ("cdmx", 19.43, -99.13)})
    with pytest.raises(ErrorRutaRequiereConfirmacion):
        validar_ruta(propuesta(destino="CDMX"), VerificadorFalso(lugares))


def test_parada_repetida_pide_confirmacion():
    paradas = [{"nombre": "Puebla"}, {"nombre": "Tehuacán"}, {"nombre": "Puebla"}]
    with pytest.raises(ErrorRutaRequiereConfirmacion) as info:
        validar(propuesta(paradas=paradas))
    assert info.value.pendiente == CONFIRMACION_PARADAS_REPETIDAS
    assert "Puebla" in str(info.value)


def test_parada_igual_al_origen_o_al_destino_cuenta_como_repetida():
    for nombre in ("Ciudad de México", "Oaxaca"):
        with pytest.raises(ErrorRutaRequiereConfirmacion):
            validar(propuesta(paradas=[{"nombre": nombre}]))


def test_parada_repetida_confirmada_se_acepta_y_mantiene_el_orden():
    paradas = [{"nombre": "Puebla"}, {"nombre": "Tehuacán"}, {"nombre": "Puebla"}]
    ruta = validar(propuesta(paradas=paradas), confirmaciones=[CONFIRMACION_PARADAS_REPETIDAS])
    assert [p["nombre"] for p in ruta["paradas"]] == ["Puebla", "Tehuacán", "Puebla"]


def test_confirmar_una_cosa_no_confirma_la_otra():
    paradas = [{"nombre": "Puebla"}, {"nombre": "Puebla"}]
    with pytest.raises(ErrorRutaRequiereConfirmacion) as info:
        validar(propuesta(destino="Ciudad de México", paradas=paradas),
                confirmaciones={CONFIRMACION_ORIGEN_IGUAL_DESTINO})
    assert info.value.pendiente == CONFIRMACION_PARADAS_REPETIDAS


def test_confirmacion_desconocida_se_rechaza():
    with pytest.raises(ErrorValidacion):
        validar(propuesta(), confirmaciones={"cualquier_cosa"})


# --- GestorRutas: fuente única y atomicidad (RF-24, RF-37) ---

def test_sin_ruta_al_inicio_y_vistas_piden_ruta():
    g = gestor()
    assert g.ruta is None
    for vista in (g.itinerario, g.resumen_chat, g.puntos_mapa):
        with pytest.raises(ErrorValidacion):
            vista()


def test_proponer_guarda_la_ruta_validada():
    g = gestor()
    ruta = g.proponer(propuesta())
    assert g.ruta == ruta
    assert ruta["destino"] == "Oaxaca"


def test_propuesta_invalida_no_cambia_la_ruta_previa():
    g = gestor()
    g.proponer(propuesta())
    antes = g.ruta
    for mala in (propuesta(destino=""), {}, propuesta(destino="Atlantis"),
                 propuesta(destino="Ciudad de México")):
        with pytest.raises(ErrorRutaInvalida):
            g.proponer(mala)
    assert g.ruta == antes


def test_servicio_caido_conserva_la_ruta_previa():
    verificador = VerificadorFalso()
    g = GestorRutas(verificador)
    g.proponer(propuesta())
    antes = g.ruta
    verificador.falla = True
    with pytest.raises(ErrorRutaInvalida):
        g.proponer(propuesta(destino="Mérida"))
    assert g.ruta == antes


def test_propuesta_que_requiere_confirmacion_no_cambia_la_ruta_y_luego_se_acepta():
    g = gestor()
    g.proponer(propuesta())
    antes = g.ruta
    repetida = propuesta(paradas=[{"nombre": "Puebla"}, {"nombre": "Puebla"}])
    with pytest.raises(ErrorRutaRequiereConfirmacion):
        g.proponer(repetida)
    assert g.ruta == antes
    g.proponer(repetida, confirmaciones={CONFIRMACION_PARADAS_REPETIDAS})
    assert len(g.ruta["paradas"]) == 2


def test_propuesta_invalida_sin_ruta_previa_deja_sin_ruta():
    g = gestor()
    with pytest.raises(ErrorRutaInvalida):
        g.proponer({})
    assert g.ruta is None


def test_aplicar_con_falla_a_la_mitad_no_deja_cambios_parciales():
    g = gestor()
    g.proponer(propuesta())
    antes = g.ruta

    def cambio_roto(ruta):
        ruta["destino"] = "Mérida"      # cambio ya hecho en la copia...
        ruta["paradas"].append({"nombre": "Campeche"})
        raise RuntimeError("falla de la IA")  # ...y luego falla

    with pytest.raises(RuntimeError):
        g.aplicar(cambio_roto)
    assert g.ruta == antes


def test_aplicar_con_resultado_invalido_no_deja_cambios_parciales():
    g = gestor()
    g.proponer(propuesta())
    antes = g.ruta

    def cambio_invalido(ruta):
        ruta["destino"] = "Mérida"
        ruta["duracion_dias"] = 0
        return ruta

    with pytest.raises(ErrorRutaInvalida):
        g.aplicar(cambio_invalido)
    assert g.ruta == antes


def test_aplicar_valido_reemplaza_toda_la_ruta_y_revalida_los_lugares():
    g = gestor()
    g.proponer(propuesta())

    def cambio(ruta):
        ruta["destino"] = "Mérida"
        return ruta

    nueva = g.aplicar(cambio)
    assert nueva["destino"] == "Mérida" and g.ruta == nueva
    assert nueva["destino_lugar"]["id"] == "mer"  # coordenadas nuevas, no las viejas


def test_modificar_la_copia_devuelta_no_cambia_la_ruta_guardada():
    g = gestor()
    devuelta = g.proponer(propuesta())
    devuelta["destino"] = "Hackeado"
    devuelta["paradas"].clear()
    leida = g.ruta
    leida["origen"] = "Otro"
    assert g.ruta["destino"] == "Oaxaca"
    assert len(g.ruta["paradas"]) == 2
    assert g.ruta["origen"] == "Ciudad de México"


def test_modificar_la_propuesta_despues_no_cambia_la_ruta_guardada():
    g = gestor()
    datos = propuesta()
    g.proponer(datos)
    datos["paradas"][0]["nombre"] = "Cambiada"
    assert g.ruta["paradas"][0]["nombre"] == "Puebla"


# --- Vistas derivadas (RF-23, RF-43) ---

def test_itinerario_numera_las_paradas_en_orden():
    g = gestor()
    g.proponer(propuesta())
    assert g.itinerario() == [
        {"orden": 1, "nombre": "Puebla", "descripcion": "Centro histórico"},
        {"orden": 2, "nombre": "Tehuacán", "descripcion": ""},
    ]


def test_las_tres_vistas_salen_de_la_misma_ruta():
    g = gestor()
    g.proponer(propuesta())
    puntos = g.puntos_mapa()
    assert [p["nombre"] for p in puntos] == ["Ciudad de México", "Puebla", "Tehuacán", "Oaxaca"]
    assert [p["tipo"] for p in puntos] == ["origen", "parada", "parada", "destino"]
    assert puntos[0]["latitud"] == 19.43 and puntos[-1]["id"] == "oax"
    assert "Ciudad de México a Oaxaca, 3 días" in g.resumen_chat()
    assert "Puebla, Tehuacán" in g.resumen_chat()
    # Una ruta nueva cambia las tres a la vez; no pueden contradecirse.
    g.proponer(propuesta(destino="Mérida", paradas=[{"nombre": "Campeche"}], duracion_dias=1))
    assert [p["nombre"] for p in g.puntos_mapa()] == ["Ciudad de México", "Campeche", "Mérida"]
    assert [p["nombre"] for p in g.itinerario()] == ["Campeche"]
    assert "1 día" in g.resumen_chat() and "Campeche" in g.resumen_chat()


def test_resumen_sin_paradas():
    g = gestor()
    g.proponer(propuesta(paradas=[]))
    assert g.resumen_chat().endswith("Sin paradas intermedias.")
    assert g.itinerario() == []
    assert [p["nombre"] for p in g.puntos_mapa()] == ["Ciudad de México", "Oaxaca"]
