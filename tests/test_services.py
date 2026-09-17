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


def test_preparar_corredor_y_distancia_a_corredor():
    # Línea recta norte-sur; un punto muy cerca de la línea debe medir
    # poca distancia perpendicular y un avance mayor que cero.
    geometria = [[19.0, -99.0], [19.5, -99.0], [20.0, -99.0]]
    corredor = route_service.preparar_corredor(geometria)

    distancia_perp, avance_km = route_service.distancia_a_corredor(corredor, (19.5, -99.001))
    assert distancia_perp < 1
    assert avance_km > 0

    # Un punto lejos de la línea debe medir una distancia perpendicular grande.
    distancia_perp_lejos, _ = route_service.distancia_a_corredor(corredor, (19.5, -101.0))
    assert distancia_perp_lejos > 100


def test_sugerir_paradas_filtra_por_corredor_real(app_context):
    ruta = route_service.calcular_ruta("Ciudad de México", "Oaxaca de Juarez")
    sugerencias = ai_service.sugerir_paradas([], limite=10, ruta=ruta)

    nombres = {s["nombre"] for s in sugerencias}
    # El origen y el destino nunca deben sugerirse a sí mismos como parada.
    assert "Ciudad de México" not in nombres
    assert "Oaxaca de Juárez" not in nombres
    # Cada sugerencia trae la hora estimada de avance sobre esa ruta.
    assert all("horas_estimadas" in s for s in sugerencias)


def test_sugerir_paradas_marca_buena_para_descanso(app_context):
    ruta = route_service.calcular_ruta("Ciudad de México", "Cancún")
    sugerencias = ai_service.sugerir_paradas([], limite=8, ruta=ruta, horas_max=4)

    objetivo = 4 * ai_service.FACTOR_DESCANSO
    for lugar in sugerencias:
        if lugar.get("buena_para_descanso"):
            assert abs(lugar["horas_estimadas"] - objetivo) <= ai_service.TOLERANCIA_DESCANSO_HORAS
