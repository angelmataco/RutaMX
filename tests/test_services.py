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
    resumen = route_service.calcular_ruta("Ciudad de Mexico", "Oaxaca de Juarez")
    assert resumen["distancia_km"] > 0
    assert resumen["tiempo_h"] > 0
    assert resumen["paradas_estimadas"] >= 1
    assert resumen["costo_estimado"] > 0
    assert resumen["costo_estimado"] == resumen["gasto"]["total"]
    assert "presupuesto" not in resumen


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
    # límite amplio: con la prioridad a lugares con estrella, los primeros lugares ya no son
    # necesariamente los que salen del reparto por objetivos.
    sugerencias = ai_service.sugerir_paradas([], limite=40, ruta=ruta, horas_max=4, hora_salida="08:00")

    con_proposito = [s for s in sugerencias if s.get("proposito")]
    assert con_proposito  # al menos una parada vino del reparto por objetivos
    ids = [s["id"] for s in con_proposito]
    assert len(ids) == len(set(ids))  # nunca el mismo destino en dos objetivos


def test_enlaces_google_maps_un_tramo():
    from app.services import navegacion_service

    enlaces = navegacion_service.enlaces_google_maps(
        {
            "origen": "CDMX",
            "destino": "Oaxaca",
            "resumen": {"origen": {"lat": 19.4, "lon": -99.1}, "destino": {"lat": 17.06, "lon": -96.7}},
            "paradas": [{"nombre": "Puebla", "lat": 19.04, "lon": -98.2}],
        }
    )
    assert len(enlaces) == 1
    assert "origin=19.4%2C-99.1" in enlaces[0]
    assert "waypoints=19.04%2C-98.2" in enlaces[0]
    assert "destination=17.06%2C-96.7" in enlaces[0]


def test_enlaces_google_maps_divide_en_tramos():
    from app.services import navegacion_service

    paradas = [{"nombre": f"P{i}"} for i in range(12)]
    enlaces = navegacion_service.enlaces_google_maps({"origen": "A", "destino": "B", "paradas": paradas})
    assert len(enlaces) == 2
    assert "origin=P9" in enlaces[1]  # el segundo tramo arranca donde terminó el primero


def test_formato_duracion():
    from app.services.pdf_service import formato_duracion

    assert formato_duracion(9.5) == "9 h 30 min"
    assert formato_duracion(9) == "9 h"
    assert formato_duracion(0.75) == "45 min"


def test_lapsos_viaje_corto_sin_ventana():
    assert ai_service.lapsos_de_la_ruta(0) == []
    assert ai_service.lapsos_de_la_ruta(0.8) == []  # 30 min al salir + 20 min al llegar no dejan ventana


def test_lapsos_cubren_de_30_min_a_20_min_antes_de_llegar():
    lapsos = ai_service.lapsos_de_la_ruta(6)
    assert lapsos[0]["desde_h"] == 0.5
    assert lapsos[-1]["hasta_h"] == round(6 - 20 / 60, 2)
    assert len(lapsos) == 2  # ~3 h por lapso
    # sin huecos ni traslapes entre lapsos
    assert lapsos[0]["hasta_h"] == lapsos[1]["desde_h"]


def test_lapsos_crecen_con_la_duracion():
    assert len(ai_service.lapsos_de_la_ruta(2)) == 1
    assert len(ai_service.lapsos_de_la_ruta(12)) == 4
    assert len(ai_service.lapsos_de_la_ruta(50)) > 10


def test_lapsos_traen_hora_del_reloj():
    lapsos = ai_service.lapsos_de_la_ruta(6, hora_salida="08:00")
    assert lapsos[0]["reloj_desde"] == "08:30"
    assert lapsos[-1]["reloj_hasta"] == "13:40"
    assert all(l["dia"] == 1 and not l["cruza_noche"] for l in lapsos)


def test_lapsos_el_usuario_elige_cuantos_tramos():
    assert len(ai_service.lapsos_de_la_ruta(12, tramos=3)) == 3
    assert len(ai_service.lapsos_de_la_ruta(12, tramos=6)) == 6
    # nunca más tramos de los que caben (mínimo 30 min cada uno)
    assert len(ai_service.lapsos_de_la_ruta(2, tramos=6)) <= 3


def test_lapso_de_noche_pide_hospedaje_y_al_mediodia_comida():
    salida_tarde = ai_service.lapsos_de_la_ruta(10, hora_salida="17:00")
    assert any(l["proposito"] == "descanso" for l in salida_tarde)
    assert any(l["cruza_noche"] for l in salida_tarde)

    salida_manana = ai_service.lapsos_de_la_ruta(9, tramos=3, hora_salida="08:00")
    # tramos: 08:30-11:13, 11:13-13:57, 13:57-16:40 -> la comida cae en el tercero
    assert [l["proposito"] for l in salida_manana] == ["turismo", "turismo", "comida"]


def test_lapsos_de_viaje_largo_cambian_de_dia():
    lapsos = ai_service.lapsos_de_la_ruta(30, hora_salida="08:00")
    assert max(l["dia"] for l in lapsos) >= 2


def test_dormir_solo_aplica_si_el_tramo_termina_despues_de_las_8pm():
    de_dia = ai_service.lapsos_de_la_ruta(6, hora_salida="08:00")
    assert not any(l["permite_dormir"] for l in de_dia)
    assert not any(l["proposito"] == "descanso" for l in de_dia)

    de_tarde = ai_service.lapsos_de_la_ruta(10, hora_salida="17:00")
    assert any(l["permite_dormir"] for l in de_tarde)


def test_usuario_personaliza_el_proposito_de_un_tramo():
    lapsos = ai_service.lapsos_de_la_ruta(9, tramos=3, hora_salida="08:00", propositos={0: "comida", 1: "turismo"})
    assert lapsos[0]["proposito"] == "comida" and lapsos[0]["personalizado"] is True
    assert lapsos[1]["proposito"] == "turismo" and lapsos[1]["personalizado"] is True
    assert lapsos[2]["personalizado"] is False  # sigue en automático


def test_dormir_pedido_donde_no_aplica_se_ignora():
    lapsos = ai_service.lapsos_de_la_ruta(6, hora_salida="08:00", propositos={0: "descanso"})
    assert lapsos[0]["personalizado"] is False and lapsos[0]["proposito"] != "descanso"


def test_encaja_con_lo_pedido_es_estricto():
    from types import SimpleNamespace as D

    fonda = D(intereses=["comida", "cultura"], tipo="pueblo_magico")
    cascada = D(intereses=["naturaleza"], tipo="sitio_turistico")
    ciudad = D(intereses=["cultura"], tipo="ciudad_principal")
    assert ai_service._encaja_con_lo_pedido(fonda, "comida", []) is True
    assert ai_service._encaja_con_lo_pedido(cascada, "comida", []) is False
    assert ai_service._encaja_con_lo_pedido(ciudad, "descanso", []) is True   # hay dónde dormir
    assert ai_service._encaja_con_lo_pedido(cascada, "descanso", []) is False
    assert ai_service._encaja_con_lo_pedido(cascada, "turismo", ["naturaleza", "comida"]) is True
    assert ai_service._encaja_con_lo_pedido(fonda, "turismo", ["naturaleza"]) is False
    assert ai_service._encaja_con_lo_pedido(fonda, "turismo", []) is True  # sin intereses, cualquiera


def test_ia_objetivos_fuera_de_la_ventana_se_descartan():
    objetivos = [
        {"proposito": "cultura", "hora_objetivo": 0.2},   # antes de 30 min
        {"proposito": "cultura", "hora_objetivo": 3.0},
        {"proposito": "cultura", "hora_objetivo": 5.9},   # menos de 20 min antes de llegar (6 h)
    ]
    listos = ai_service.preparar_objetivos_ia(objetivos, 6, "08:00")
    assert [o["hora_objetivo"] for o in listos] == [3.0]


def test_ia_no_puede_proponer_dormir_de_dia():
    listos = ai_service.preparar_objetivos_ia(
        [{"proposito": "descanso", "hora_objetivo": 3.0}], 6, "08:00", ["playas"]
    )
    assert listos[0]["proposito"] == "playas"  # se cambia por turismo
    assert listos[0]["estricto"] is False


def test_ia_dormir_si_hay_noche_en_el_viaje():
    # sale a las 17:00: a ~3.5 h son las 20:30
    listos = ai_service.preparar_objetivos_ia([{"proposito": "descanso", "hora_objetivo": 3.5}], 10, "17:00")
    assert listos[0]["proposito"] == "descanso" and listos[0]["estricto"] is True


def test_ia_sin_hora_de_salida_supone_las_8am_y_no_duerme_de_dia():
    listos = ai_service.preparar_objetivos_ia([{"proposito": "descanso", "hora_objetivo": 4}], 8, None)
    assert listos[0]["proposito"] != "descanso"


def test_ia_comida_es_estricta_y_tiene_ventana():
    listos = ai_service.preparar_objetivos_ia([{"proposito": "comida", "hora_objetivo": 5.0}], 10, "08:00")
    assert listos[0]["estricto"] is True
    assert listos[0]["ventana"] == (3.5, 6.5)


def test_gastronomia_destacada_ciudades_unesco_y_michelin(app_context):
    """Ensenada y Mérida (UNESCO) y Oaxaca (Michelin) están marcadas, con su fuente."""
    reconocidos = {d.nombre: d for d in Destino.query.filter_by(gastronomia_destacada=True).all()}
    for nombre in ("Ensenada", "Mérida", "Oaxaca de Juárez", "Ciudad de México"):
        assert nombre in reconocidos
        assert "comida" in reconocidos[nombre].intereses
        assert reconocidos[nombre].reconocimiento_gastronomico
    # segunda pasada de fuentes: Bib Gourmand y Latin America's 50 Best
    for nombre in ("Tijuana", "Tulum", "Puerto Vallarta", "Atlixco", "Cabo San Lucas", "Puerto Morelos", "Tixkokob"):
        assert nombre in reconocidos, nombre
    assert len(reconocidos) >= 21
    assert "UNESCO" in reconocidos["Mérida"].reconocimiento_gastronomico
    assert "Michelin" in reconocidos["Oaxaca de Juárez"].reconocimiento_gastronomico


def test_para_comer_la_gastronomia_destacada_va_primero():
    from types import SimpleNamespace as D

    comun = D(id=1, nombre="Común", tipo="pueblo_magico", intereses=["comida"], gastronomia_destacada=False,
              reconocimiento_gastronomico=None, lat=0, lon=0, descripcion="", poblacion=None)
    famoso = D(id=2, nombre="Famoso", tipo="ciudad_principal", intereses=["comida"], gastronomia_destacada=True,
               reconocimiento_gastronomico="Guía Michelin", lat=0, lon=0, descripcion="", poblacion=None)
    # el común está exactamente en la hora pedida; el famoso un poco más lejos, pero gana por gastronomía
    asignadas = ai_service.asignar_paradas_a_objetivos(
        [(comun, 3.0), (famoso, 3.6)], [{"proposito": "comida", "hora_objetivo": 3.0}]
    )
    assert asignadas[0]["id"] == 2
    assert asignadas[0]["gastronomia_destacada"] is True


def test_prestigio_ordena_estrella_sobre_bib():
    michelin = {"gastronomia_destacada": True, "reconocimiento_gastronomico": "Guía Michelin México 2026: Pujol (2 estrellas)"}
    una_estrella = {"gastronomia_destacada": True, "reconocimiento_gastronomico": "Guía Michelin México 2026: Alcalde (1 estrella)"}
    solo_bib = {"gastronomia_destacada": True, "reconocimiento_gastronomico": "Guía Michelin México 2026: Bib Gourmand Vica"}
    unesco = {"gastronomia_destacada": True, "reconocimiento_gastronomico": "UNESCO Ciudad Creativa de la Gastronomía (2015)"}
    ninguno = {"gastronomia_destacada": False, "reconocimiento_gastronomico": None}
    assert ai_service.prestigio(michelin) > ai_service.prestigio(una_estrella) > ai_service.prestigio(solo_bib) > 0
    assert ai_service.prestigio(unesco) > ai_service.prestigio(solo_bib)
    assert ai_service.prestigio(ninguno) == 0


def test_linea_de_tiempo_aunque_esten_mas_lejos():
    lugares = [
        {"nombre": "Común", "horas_estimadas": 1, "gastronomia_destacada": False},
        {"nombre": "Bib", "horas_estimadas": 4, "gastronomia_destacada": True, "reconocimiento_gastronomico": "Bib Gourmand X"},
        {"nombre": "Estrella", "horas_estimadas": 5, "gastronomia_destacada": True, "reconocimiento_gastronomico": "Michelin: Y (1 estrella)"},
        {"nombre": "Otro", "horas_estimadas": 2, "gastronomia_destacada": False},
    ]
    orden = [l["nombre"] for l in ai_service._linea_de_tiempo(lugares)]
    assert orden == ["Estrella", "Bib", "Común", "Otro"]  # el resto, en orden de camino (1 h, luego 2 h)


def test_para_cualquier_proposito_gana_el_mas_distinguido():
    from types import SimpleNamespace as D

    comun = D(id=1, nombre="Común", tipo="pueblo_magico", intereses=["cultura"], gastronomia_destacada=False,
              reconocimiento_gastronomico=None, lat=0, lon=0, descripcion="", poblacion=None)
    famoso = D(id=2, nombre="Famoso", tipo="ciudad_principal", intereses=["cultura"], gastronomia_destacada=True,
               reconocimiento_gastronomico="Guía Michelin (1 estrella)", lat=0, lon=0, descripcion="", poblacion=None)
    asignadas = ai_service.asignar_paradas_a_objetivos([(comun, 3.0), (famoso, 3.8)], [{"proposito": "cultura", "hora_objetivo": 3.0}])
    assert asignadas[0]["id"] == 2


def test_prioridad_solo_si_la_ruta_pasa_cerca():
    estrella = "Guía Michelin (1 estrella)"
    cerca = {"gastronomia_destacada": True, "reconocimiento_gastronomico": estrella, "distancia_a_ruta_km": 30}
    lejos = {"gastronomia_destacada": True, "reconocimiento_gastronomico": estrella, "distancia_a_ruta_km": 145}
    sin_dato = {"gastronomia_destacada": True, "reconocimiento_gastronomico": estrella}
    assert ai_service.prioridad(cerca) > 0
    assert ai_service.prioridad(lejos) == 0          # sigue teniendo estrella, pero sin prioridad
    assert ai_service.prioridad(sin_dato) > 0
    orden = [l["nombre"] for l in ai_service._linea_de_tiempo(
        [{"nombre": "Común"}, {**lejos, "nombre": "Lejos"}, {**cerca, "nombre": "Cerca"}]
    )]
    assert orden == ["Cerca", "Común", "Lejos"]


def test_linea_de_tiempo_distinguidos_primero_y_luego_por_horas():
    lugares = [
        {"nombre": "a 6 h", "horas_estimadas": 6.0},
        {"nombre": "a 1 h", "horas_estimadas": 1.0},
        {"nombre": "Estrella a 5 h", "horas_estimadas": 5.0, "gastronomia_destacada": True,
         "reconocimiento_gastronomico": "Michelin (1 estrella)", "distancia_a_ruta_km": 10},
        {"nombre": "a 3.5 h", "horas_estimadas": 3.5},
        {"nombre": "a 2 h", "horas_estimadas": 2.0},
    ]
    assert [l["nombre"] for l in ai_service._linea_de_tiempo(lugares)] == [
        "Estrella a 5 h", "a 1 h", "a 2 h", "a 3.5 h", "a 6 h",
    ]


def test_elegir_con_distinguidos_no_deja_fuera_a_ninguno():
    lugares = [{"id": i, "horas_estimadas": i} for i in range(10)]
    lugares.append({"id": 99, "horas_estimadas": 9, "gastronomia_destacada": True,
                    "reconocimiento_gastronomico": "Michelin (1 estrella)"})
    elegidos = ai_service._elegir_con_distinguidos(lugares, 5)
    assert len(elegidos) == 6 and 99 in [l["id"] for l in elegidos]


def _estrella(nombre, horas, prestigio_txt="Michelin (1 estrella)"):
    return {"nombre": nombre, "horas_estimadas": horas, "gastronomia_destacada": True,
            "reconocimiento_gastronomico": prestigio_txt, "distancia_a_ruta_km": 5}


def test_maximo_dos_estrellas_al_frente_y_ninguna_mas_en_la_primera_pagina():
    lugares = [_estrella("E1", 4.0, "Michelin (2 estrellas)"), _estrella("E2", 2.0), _estrella("E3", 1.0), _estrella("E4", 0.6)]
    lugares += [{"nombre": f"c{i}", "horas_estimadas": 0.7 + i * 0.4} for i in range(10)]
    orden = ai_service._linea_de_tiempo(lugares)
    primera = orden[:ai_service.TAMANO_PAGINA_SUGERENCIAS]
    estrellas_primera = [l["nombre"] for l in primera if l.get("gastronomia_destacada")]
    assert len(estrellas_primera) == 2                      # exclusividad: solo dos estrellas al frente
    assert primera[0]["nombre"] == "E1"                     # la más distinguida (2 estrellas) primero
    assert primera[1]["nombre"] == "E4"                     # a igual puntaje, la más cercana al inicio
    # las otras dos estrellas siguen apareciendo (con su ★), pero después de la primera página
    resto = [l["nombre"] for l in orden[ai_service.TAMANO_PAGINA_SUGERENCIAS:]]
    assert "E2" in resto and "E3" in resto
    # y el resto de la línea de tiempo sigue en orden de horas
    horas = [l["horas_estimadas"] for l in orden[ai_service.TAMANO_PAGINA_SUGERENCIAS:]]
    assert horas == sorted(horas)


def test_con_una_sola_estrella_se_llenan_los_demas_lugares_por_hora():
    lugares = [_estrella("E1", 3.0)] + [{"nombre": f"c{i}", "horas_estimadas": 1 + i} for i in range(8)]
    primera = ai_service._linea_de_tiempo(lugares)[:ai_service.TAMANO_PAGINA_SUGERENCIAS]
    assert [l["nombre"] for l in primera] == ["E1", "c0", "c1", "c2", "c3"]
