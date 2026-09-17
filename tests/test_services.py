import pytest

from app import create_app
from app.models import Destino
from app.services import ai_service, maps_service, route_service


@pytest.fixture
def app_context():
    app = create_app("development")
    with app.app_context():
        yield


def test_obtener_coordenadas_ciudad_conocida():
    lat, lon = maps_service.obtener_coordenadas("Ciudad de Mexico")
    assert lat == 19.4326
    assert lon == -99.1332


def test_obtener_coordenadas_ciudad_desconocida_usa_respaldo():
    coords = maps_service.obtener_coordenadas("Ciudad Inventada Xyz")
    assert coords == maps_service.COORDENADA_RESPALDO


def test_calcular_ruta_devuelve_campos_esperados():
    resumen = route_service.calcular_ruta("Ciudad de Mexico", "Oaxaca de Juarez", 6500)
    assert resumen["distancia_km"] > 0
    assert resumen["tiempo_h"] > 0
    assert resumen["paradas_estimadas"] >= 1
    assert resumen["costo_estimado"] > 0


def test_sugerir_paradas_sin_intereses_devuelve_lista(app_context):
    sugerencias = ai_service.sugerir_paradas([])
    assert len(sugerencias) > 0
    assert {"id", "nombre", "categoria", "descripcion", "lat", "lon"} <= sugerencias[0].keys()


def test_sugerir_paradas_respeta_limite(app_context):
    sugerencias = ai_service.sugerir_paradas(["playas"], limite=1)
    assert len(sugerencias) == 1


def test_sugerir_paradas_prioriza_intereses(app_context):
    sugerencias = ai_service.sugerir_paradas(["playas"], limite=5)
    nombres = {s["nombre"] for s in sugerencias}

    destinos_playas = {d.nombre for d in Destino.query.all() if "playas" in (d.intereses or [])}
    assert nombres & destinos_playas


def test_sugerir_paradas_respaldo_sin_base_de_datos():
    # Sin contexto de Flask, la consulta a la base falla y debe usar el
    # catálogo de respaldo (LUGARES_DEMO) sin romper el flujo.
    sugerencias = ai_service.sugerir_paradas(["playas"], limite=1)
    assert sugerencias[0]["id"] == "playa_del_carmen"
