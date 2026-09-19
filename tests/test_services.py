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
    assert lat == pytest.approx(19.4326, abs=0.05)
    assert lon == pytest.approx(-99.1332, abs=0.05)


def test_obtener_coordenadas_destino_real_sin_estar_en_catalogo_demo(app_context):
    # León y Los Cabos no están en el catálogo demo de 18 ciudades, pero
    # sí en la tabla `destinos` o vía Nominatim: no deben caer ambos en
    # la misma coordenada de respaldo (el bug original reportado).
    coords_leon = maps_service.obtener_coordenadas("Leon")
    coords_cabos = maps_service.obtener_coordenadas("Los Cabos")
    assert coords_leon != coords_cabos
    assert coords_leon != maps_service.COORDENADA_RESPALDO
    assert coords_cabos != maps_service.COORDENADA_RESPALDO


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


class _DestinoFalso:
    """Doble simple de `Destino` para probar asignación sin tocar la BD."""

    def __init__(self, id_, nombre, intereses):
        self.id = id_
        self.nombre = nombre
        self.intereses = intereses
        self.tipo = "pueblo_magico"
        self.descripcion = "Descripción de prueba."
        self.lat = 20.0
        self.lon = -100.0


def test_asignar_paradas_a_objetivos_no_repite_destinos():
    candidatos = [
        (_DestinoFalso(1, "Comedero Uno", ["comida"]), 4.0),
        (_DestinoFalso(2, "Comedero Dos", ["comida"]), 4.5),
        (_DestinoFalso(3, "Posada de Descanso", ["descanso"]), 8.0),
    ]
    objetivos = [{"proposito": "comida", "hora_objetivo": 4.0}, {"proposito": "descanso", "hora_objetivo": 8.0}]

    asignadas = ai_service.asignar_paradas_a_objetivos(candidatos, objetivos)

    assert len(asignadas) == 2
    ids = {lugar["id"] for lugar in asignadas}
    assert len(ids) == 2  # nunca el mismo destino en dos objetivos
    comida = next(l for l in asignadas if l["proposito"] == "comida")
    assert comida["id"] == 1  # el más cercano a la hora objetivo, entre los dos con el mismo interés


def test_asignar_paradas_a_objetivos_omite_si_no_hay_candidato():
    candidatos = [(_DestinoFalso(1, "Único Lugar", ["comida"]), 4.0)]
    objetivos = [{"proposito": "comida", "hora_objetivo": 4.0}, {"proposito": "playas", "hora_objetivo": 8.0}]

    asignadas = ai_service.asignar_paradas_a_objetivos(candidatos, objetivos)

    assert len(asignadas) == 1
    assert asignadas[0]["proposito"] == "comida"


def test_filtrar_objetivos_por_hora_del_dia_reclasifica_descanso_de_dia():
    objetivos = [{"proposito": "descanso", "hora_objetivo": 4.0}]  # sale 8am + 4h = 12pm, pleno día
    filtrados = ai_service.filtrar_objetivos_por_hora_del_dia(objetivos, "08:00", ["cultura"])
    assert filtrados[0]["proposito"] == "cultura"


def test_filtrar_objetivos_por_hora_del_dia_prioriza_descanso_de_noche():
    objetivos = [{"proposito": "comida", "hora_objetivo": 14.0}]  # sale 8am + 14h = 10pm, de noche
    filtrados = ai_service.filtrar_objetivos_por_hora_del_dia(objetivos, "08:00")
    assert filtrados[0]["proposito"] == "descanso"


def test_filtrar_objetivos_por_hora_del_dia_sin_hora_salida_no_cambia_nada():
    objetivos = [{"proposito": "descanso", "hora_objetivo": 4.0}]
    filtrados = ai_service.filtrar_objetivos_por_hora_del_dia(objetivos, None)
    assert filtrados == objetivos


def test_generar_objetivos_automaticos_sin_horas_max_devuelve_vacio():
    assert ai_service.generar_objetivos_automaticos(10, None) == []


def test_generar_objetivos_automaticos_genera_comida_y_descanso():
    objetivos = ai_service.generar_objetivos_automaticos(12, 4)
    assert len(objetivos) == 2
    assert objetivos[0]["proposito"] == "comida"
    assert objetivos[1]["proposito"] == "descanso"


def test_sugerir_paradas_con_hora_salida_reparte_por_proposito(app_context):
    ruta = route_service.calcular_ruta("Ciudad de México", "Cancún")
    sugerencias = ai_service.sugerir_paradas([], limite=6, ruta=ruta, horas_max=4, hora_salida="08:00")

    con_proposito = [s for s in sugerencias if s.get("proposito")]
    assert con_proposito  # al menos una parada vino del reparto por objetivos
    ids = [s["id"] for s in con_proposito]
    assert len(ids) == len(set(ids))  # nunca el mismo destino en dos objetivos
