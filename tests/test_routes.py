import pytest

from app import create_app
from app.models import RutaGuardada, Usuario, db
from app.services import llm_provider

NOMBRE_USUARIO_PRUEBA = "Prueba"
APELLIDO_USUARIO_PRUEBA = "Bitacora"


@pytest.fixture
def client():
    app = create_app("development")
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client
    # RutaGuardada y Usuario viven en la base real (Supabase): se limpia
    # lo que haya creado el test para no dejar basura de prueba.
    with app.app_context():
        RutaGuardada.query.filter(RutaGuardada.nombre == "Escapada de prueba").delete()
        Usuario.query.filter(Usuario.nombre == NOMBRE_USUARIO_PRUEBA).delete()
        db.session.commit()


def _registrar_y_loguear(client, apellido=APELLIDO_USUARIO_PRUEBA, pin="1234"):
    return client.post(
        "/api/auth/registro",
        json={"nombre": NOMBRE_USUARIO_PRUEBA, "apellido": apellido, "pin": pin},
    )


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


def test_guardar_ruta_sin_sesion_devuelve_401(client):
    respuesta = client.post(
        "/api/rutas",
        json={"nombre": "Escapada de prueba", "origen": "Ciudad de Mexico", "destino": "Oaxaca de Juarez"},
    )
    assert respuesta.status_code == 401


def test_guardar_y_listar_rutas(client):
    _registrar_y_loguear(client)

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


def test_registro_y_login(client):
    respuesta_registro = _registrar_y_loguear(client)
    assert respuesta_registro.status_code == 201
    assert respuesta_registro.get_json()["usuario"]["nombre"] == NOMBRE_USUARIO_PRUEBA

    client.post("/api/auth/logout")
    respuesta_yo = client.get("/api/auth/yo")
    assert respuesta_yo.get_json()["usuario"] is None

    respuesta_login = client.post(
        "/api/auth/login",
        json={"nombre": NOMBRE_USUARIO_PRUEBA, "apellido": APELLIDO_USUARIO_PRUEBA, "pin": "1234"},
    )
    assert respuesta_login.status_code == 200
    assert respuesta_login.get_json()["usuario"]["nombre"] == NOMBRE_USUARIO_PRUEBA


def test_login_pin_incorrecto(client):
    _registrar_y_loguear(client)
    client.post("/api/auth/logout")

    respuesta = client.post(
        "/api/auth/login",
        json={"nombre": NOMBRE_USUARIO_PRUEBA, "apellido": APELLIDO_USUARIO_PRUEBA, "pin": "0000"},
    )
    assert respuesta.status_code == 401


def test_registro_pin_invalido(client):
    respuesta = client.post(
        "/api/auth/registro",
        json={"nombre": NOMBRE_USUARIO_PRUEBA, "apellido": APELLIDO_USUARIO_PRUEBA, "pin": "12"},
    )
    assert respuesta.status_code == 400


def test_una_cuenta_no_ve_rutas_de_otra(client):
    _registrar_y_loguear(client, apellido="Uno")
    client.post(
        "/api/rutas",
        json={"nombre": "Escapada de prueba", "origen": "Ciudad de Mexico", "destino": "Oaxaca de Juarez"},
    )
    client.post("/api/auth/logout")

    _registrar_y_loguear(client, apellido="Dos")
    datos = client.get("/api/rutas").get_json()
    assert not any(r["nombre"] == "Escapada de prueba" for r in datos["rutas"])


def test_ia_disponible_refleja_configuracion(client, monkeypatch):
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: True)
    assert client.get("/api/ia/disponible").get_json() == {"disponible": True}

    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: False)
    assert client.get("/api/ia/disponible").get_json() == {"disponible": False}


def test_ia_planear_sin_proveedor_da_error(client, monkeypatch):
    monkeypatch.setattr(llm_provider, "hay_proveedor_configurado", lambda: False)

    respuesta = client.post("/api/ia/planear", json={"mensajes": [{"role": "user", "content": "hola"}]})
    assert respuesta.status_code == 200
    assert respuesta.get_json()["tipo"] == "error"


def test_ia_planear_devuelve_opciones_con_proveedor_mockeado(client, monkeypatch):
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
            "personas": 2,
            "horas_max": None,
            "hora_salida": None,
            "intereses": None,
        },
    )
    monkeypatch.setattr(
        llm_provider,
        "generar_opciones_objetivos",
        lambda contexto: {
            "opciones": [
                {"titulo": "Directa", "objetivos": [{"proposito": "comida", "hora_objetivo": 2.0}]},
                {"titulo": "Con más paradas", "objetivos": [{"proposito": "cultura", "hora_objetivo": 1.0}]},
            ]
        },
    )

    respuesta = client.post("/api/ia/planear", json={"mensajes": [{"role": "user", "content": "cdmx a oaxaca"}]})
    datos = respuesta.get_json()
    assert datos["tipo"] == "opciones"
    assert len(datos["opciones"]) == 2


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


def test_enlaces_navegacion_ok(client):
    respuesta = client.post("/api/itinerario/enlaces", json={"origen": "CDMX", "destino": "Oaxaca"})
    assert respuesta.status_code == 200
    assert respuesta.get_json()["enlaces"][0].startswith("https://www.google.com/maps/dir/?api=1&origin=")


def test_enlaces_navegacion_sin_datos(client):
    assert client.post("/api/itinerario/enlaces", json={}).status_code == 400


def test_api_gasto_ok(client):
    respuesta = client.post(
        "/api/gasto",
        json={
            "distancia_km": 600,
            "tiempo_h": 10,
            "ajustes": {"hora_salida": "17:00", "personas": 2},
            "paradas": [{"intereses": ["comida"]}],
        },
    )
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["num_noches"] == 1 and datos["num_comidas"] == 1
    assert datos["total"] > 0


def test_api_gasto_sin_datos(client):
    assert client.post("/api/gasto", json={}).status_code == 400


def test_nombres_de_destinos_ordenados_por_importancia(client):
    from app.models import Destino

    nombres = client.get("/api/destinos/nombres").get_json()["nombres"]
    assert len(nombres) == len(set(nombres))  # sin repetidos

    rango = {"ciudad_principal": 0, "pueblo_magico": 1, "sitio_turistico": 2}
    tipo_de = {}
    with client.application.app_context():
        for d in Destino.query.all():
            tipo_de[d.nombre] = min(tipo_de.get(d.nombre, 3), rango.get(d.tipo, 3))
    rangos = [tipo_de[n] for n in nombres]
    assert rangos == sorted(rangos)  # las ciudades principales van primero
    assert nombres.index("León") < nombres.index(next(n for n in nombres if tipo_de[n] == 2))
