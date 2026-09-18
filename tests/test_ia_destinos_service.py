import pytest

from app import create_app
from app.models import Destino, db
from app.services import ia_destinos_service, llm_provider, maps_service

NOMBRE_PRUEBA = "Manuel Doblado"


@pytest.fixture
def app_context():
    app = create_app("development")
    with app.app_context():
        yield
    with app.app_context():
        Destino.query.filter(Destino.nombre == NOMBRE_PRUEBA).delete()
        db.session.commit()


def _respuesta_ia_valida():
    return {
        "encontrado": True,
        "nombre": NOMBRE_PRUEBA,
        "estado": "Guanajuato",
        "tipo": "pueblo_magico",
        "descripcion": "Pueblo agrícola en el Bajío guanajuatense.",
        "intereses": ["cultura", "comida"],
        "poblacion": 12000,
    }


def test_generar_destino_con_ia_inserta_con_coordenadas_reales(app_context, monkeypatch):
    monkeypatch.setattr(llm_provider, "completar_plantilla_destino", lambda nombre: _respuesta_ia_valida())

    destino = ia_destinos_service.generar_destino_con_ia("manuel doblad0")  # con typo a propósito

    assert destino is not None
    assert destino.nombre == NOMBRE_PRUEBA
    assert destino.fuente == "ia_generada"
    assert destino.tipo == "pueblo_magico"
    # Las coordenadas deben venir de geocodificar() (Nominatim), no de la
    # respuesta simulada de la IA (que ni siquiera trae lat/lon).
    assert destino.lat is not None and destino.lon is not None
    assert -35 < destino.lat < 35  # rango plausible de latitud en México/Nominatim


def test_generar_destino_con_ia_sin_proveedor_configurado_devuelve_none(app_context, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("IA_PROVEEDOR", raising=False)

    assert llm_provider.completar_plantilla_destino("cualquier lugar") is None
    assert ia_destinos_service.generar_destino_con_ia("cualquier lugar") is None


def test_generar_destino_con_ia_no_encontrado_devuelve_none(app_context, monkeypatch):
    monkeypatch.setattr(
        llm_provider,
        "completar_plantilla_destino",
        lambda nombre: {"encontrado": False},
    )
    assert ia_destinos_service.generar_destino_con_ia("asdkjqwoiej") is None


def test_obtener_coordenadas_solo_llama_ia_la_primera_vez(app_context, monkeypatch):
    llamadas = {"total": 0}

    def _fake_completar(nombre):
        llamadas["total"] += 1
        return _respuesta_ia_valida()

    monkeypatch.setattr(llm_provider, "completar_plantilla_destino", _fake_completar)

    coords_1 = maps_service.obtener_coordenadas(NOMBRE_PRUEBA)
    assert llamadas["total"] == 1

    coords_2 = maps_service.obtener_coordenadas(NOMBRE_PRUEBA)
    assert llamadas["total"] == 1  # ya estaba en la tabla, no se volvió a llamar a la IA
    assert coords_1 == coords_2
