import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app("development")
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


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
