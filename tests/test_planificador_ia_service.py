import pytest

from app import create_app
from app.services import llm_provider, planificador_ia_service


@pytest.fixture
def app_context():
    app = create_app("development")
    with app.app_context():
        yield


def test_sin_proveedor_configurado_devuelve_error(app_context, monkeypatch):
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: False)

    resultado = planificador_ia_service.procesar_turno([{"role": "user", "content": "hola"}])

    assert resultado["tipo"] == "error"


def test_cuando_faltan_datos_devuelve_pregunta(app_context, monkeypatch):
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: True)
    monkeypatch.setattr(
        llm_provider,
        "extraer_slots_viaje",
        lambda mensajes: {
            "listo": False,
            "pregunta_siguiente": "¿A qué hora sales?",
            "opciones_respuesta": ["8-10am", "12-2pm", "5-7pm"],
            "origen": "Ciudad de Mexico",
            "destino": "Oaxaca de Juarez",
            "personas": None,
            "horas_max": None,
            "hora_salida": None,
            "intereses": None,
        },
    )

    resultado = planificador_ia_service.procesar_turno([{"role": "user", "content": "quiero ir de cdmx a oaxaca"}])

    assert resultado["tipo"] == "pregunta"
    assert resultado["mensaje"] == "¿A qué hora sales?"
    assert resultado["opciones_respuesta"] == ["8-10am", "12-2pm", "5-7pm"]


def test_cuando_esta_listo_devuelve_dos_opciones_con_ruta_real(app_context, monkeypatch):
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: True)
    monkeypatch.setattr(
        llm_provider,
        "extraer_slots_viaje",
        lambda mensajes: {
            "listo": True,
            "pregunta_siguiente": None,
            "opciones_respuesta": None,
            "origen": "Ciudad de Mexico",
            "destino": "Oaxaca de Juarez",
            "personas": 4,
            "horas_max": 4,
            "hora_salida": "08:00",
            "intereses": ["comida"],
        },
    )
    monkeypatch.setattr(
        llm_provider,
        "generar_opciones_objetivos",
        lambda contexto: {
            "opciones": [
                {"titulo": "Ruta directa", "objetivos": [{"proposito": "comida", "hora_objetivo": 3.0}]},
                {"titulo": "Ruta con más paradas", "objetivos": [{"proposito": "cultura", "hora_objetivo": 2.0}]},
            ]
        },
    )

    resultado = planificador_ia_service.procesar_turno(
        [{"role": "user", "content": "quiero ir de cdmx a oaxaca con mis amigos, parando a comer"}]
    )

    assert resultado["tipo"] == "opciones"
    assert len(resultado["opciones"]) == 2
    for opcion in resultado["opciones"]:
        assert "titulo" in opcion
        assert opcion["resumen"]["distancia_km"] > 0
        assert "geometria" not in opcion["resumen"]
        assert len(opcion["paradas"]) >= 1


def test_ia_no_encuentra_origen_destino_devuelve_error(app_context, monkeypatch):
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: True)
    monkeypatch.setattr(
        llm_provider,
        "extraer_slots_viaje",
        lambda mensajes: {
            "listo": True,
            "pregunta_siguiente": None,
            "opciones_respuesta": None,
            "origen": None,
            "destino": None,
            "personas": None,
            "horas_max": None,
            "hora_salida": None,
            "intereses": None,
        },
    )

    resultado = planificador_ia_service.procesar_turno([{"role": "user", "content": "no sé a dónde ir"}])

    assert resultado["tipo"] == "error"
