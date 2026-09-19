from app.services import gasto_service as g
from app.services import llm_provider


def test_noches_viaje_corto_de_dia_no_duerme():
    assert g.noches_estimadas(8, "08:00") == 0


def test_noches_sale_en_la_tarde_y_llega_pasada_la_noche():
    assert g.noches_estimadas(10, "17:00") == 1


def test_noches_viaje_muy_largo():
    # 50 h saliendo a las 08:00: 13 h el primer día y 14 h por día después.
    assert g.noches_estimadas(50, "08:00") == 3


def test_noches_sin_hora_de_salida_asume_las_8am():
    assert g.noches_estimadas(8) == 0
    assert g.noches_estimadas(8, "basura") == 0


def test_imprevistos_escala_de_500_a_2000():
    assert g.imprevistos(2) == 500
    assert g.imprevistos(4) == 500
    assert g.imprevistos(12) == 1250
    assert g.imprevistos(20) == 2000
    assert g.imprevistos(45) == 2000


def test_gasto_base_solo_gasolina_casetas_e_imprevistos():
    r = g.calcular_gasto(500, 6)
    assert r["comidas"] == 0 and r["hospedaje"] == 0
    assert r["gasolina"] == round(500 / 13 * 25.5)
    assert r["casetas"] == round(500 * g.CASETAS_POR_KM_RESPALDO)
    assert r["total"] == r["gasolina"] + r["casetas"] + r["imprevistos"]


def test_comidas_solo_si_hay_paradas_de_comida():
    paradas = [{"intereses": ["comida", "cultura"]}, {"intereses": ["playas"]}]
    r = g.calcular_gasto(500, 6, {"personas": 2}, paradas)
    assert r["num_comidas"] == 1
    assert r["comidas"] == 150 * 2
    assert r["comidas_automatico"] is True


def test_hospedaje_automatico_segun_hora_de_salida():
    de_dia = g.calcular_gasto(600, 8, {"hora_salida": "08:00"})
    de_tarde = g.calcular_gasto(600, 10, {"hora_salida": "17:00"})
    assert de_dia["hospedaje"] == 0
    assert de_tarde["hospedaje"] == g.COSTO_NOCHE_HOSPEDAJE


def test_ajustes_manuales_reemplazan_lo_automatico():
    r = g.calcular_gasto(600, 10, {"hora_salida": "17:00", "noches": 0, "comidas": 3, "personas": 2})
    assert r["hospedaje"] == 0 and r["noches_automatico"] is False
    assert r["num_comidas"] == 3 and r["comidas"] == 3 * 150 * 2


def test_coche_y_gasolina_cambian_el_costo_de_gasolina():
    normal = g.calcular_gasto(1000, 12)["gasolina"]
    suv_premium = g.calcular_gasto(1000, 12, {"tipo_coche": "suv", "gasolina": "premium"})["gasolina"]
    compacto_magna = g.calcular_gasto(1000, 12, {"tipo_coche": "compacto", "gasolina": "magna"})["gasolina"]
    assert compacto_magna < normal < suv_premium


def test_casetas_sin_ia_usa_promedio_por_km(monkeypatch):
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: False)
    assert g.estimar_casetas("A", "B", 1000) == (1100, "estimado")


def test_casetas_con_ia_usa_el_monto_de_la_ia(monkeypatch):
    g._cache_casetas_ia.clear()
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: True)
    monkeypatch.setattr(llm_provider, "estimar_casetas", lambda *a, **k: 830)
    assert g.estimar_casetas("Uno", "Dos", 1000) == (830, "ia")
    g._cache_casetas_ia.clear()


def test_casetas_con_ia_descarta_respuestas_absurdas(monkeypatch):
    g._cache_casetas_ia.clear()
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: True)
    monkeypatch.setattr(llm_provider, "estimar_casetas", lambda *a, **k: 999999)
    assert g.estimar_casetas("Tres", "Cuatro", 1000) == (1100, "estimado")
    g._cache_casetas_ia.clear()
