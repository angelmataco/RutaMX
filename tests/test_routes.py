import pytest

from app import create_app
from app.models import RutaGuardada, db


@pytest.fixture
def client():
    app = create_app("development")
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client
    # RutaGuardada vive en la base real (Supabase): se limpia lo que haya
    # creado el test para no dejar basura de prueba en la tabla.
    with app.app_context():
        RutaGuardada.query.filter(RutaGuardada.nombre == "Escapada de prueba").delete()
        db.session.commit()


def test_index_ok(client):
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert b"RutaMX" in respuesta.data


def test_calcular_ruta_ok(client):
    respuesta = client.post(
        "/api/ruta",
        json={"origen": "Ciudad de Mexico", "destino": "Oaxaca de Juarez", "presupuesto": 6500},
    )
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["distancia_km"] > 0
    assert datos["tiempo_h"] > 0
    assert "costo_estimado" in datos


def test_calcular_ruta_sin_datos(client):
    respuesta = client.post("/api/ruta", json={})
    assert respuesta.status_code == 400


def test_sugerencias_ok(client):
    respuesta = client.get("/api/sugerencias?intereses=naturaleza,comida")
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert len(datos["sugerencias"]) > 0


def test_sugerencias_respeta_limite(client):
    respuesta = client.get("/api/sugerencias?limite=2")
    datos = respuesta.get_json()
    assert len(datos["sugerencias"]) == 2


def test_sugerencias_excluir_no_repite(client):
    primera = client.get("/api/sugerencias?limite=4").get_json()["sugerencias"]
    ids_primera = [str(l["id"]) for l in primera]

    segunda = client.get(f"/api/sugerencias?limite=4&excluir={','.join(ids_primera)}").get_json()["sugerencias"]
    ids_segunda = {l["id"] for l in segunda}

    assert not ids_segunda & {l["id"] for l in primera}


def test_destinos_nombres_ok(client):
    respuesta = client.get("/api/destinos/nombres")
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert len(datos["nombres"]) > 0


def test_guardar_y_listar_rutas(client):
    respuesta = client.post(
        "/api/rutas",
        json={
            "nombre": "Escapada de prueba",
            "origen": "Ciudad de Mexico",
            "destino": "Oaxaca de Juarez",
            "presupuesto": 6500,
            "intereses": ["comida"],
            "resumen": {"distancia_km": 500},
            "paradas": [],
        },
    )
    assert respuesta.status_code == 201

    respuesta_lista = client.get("/api/rutas")
    datos = respuesta_lista.get_json()
    assert any(r["nombre"] == "Escapada de prueba" for r in datos["rutas"])


def test_pdf_itinerario_ok(client):
    respuesta = client.post(
        "/api/itinerario/pdf",
        json={
            "nombre": "Escapada de prueba",
            "origen": "Ciudad de Mexico",
            "destino": "Oaxaca de Juarez",
            "resumen": {"distancia_km": 461.1, "tiempo_h": 5.71, "costo_estimado": 3171, "presupuesto": 6500, "presupuesto_suficiente": True},
            "paradas": [{"nombre": "Puebla de Zaragoza"}],
        },
    )
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/pdf"
    assert respuesta.data[:4] == b"%PDF"


def test_pdf_itinerario_sin_datos(client):
    respuesta = client.post("/api/itinerario/pdf", json={})
    assert respuesta.status_code == 400
