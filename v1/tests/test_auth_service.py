import pytest

from app import create_app
from app.models import Usuario, db
from app.services import auth_service

NOMBRE = "Prueba"
APELLIDO = "AuthService"


@pytest.fixture
def app_context():
    app = create_app("development")
    with app.app_context():
        yield
    with app.app_context():
        Usuario.query.filter(Usuario.nombre == NOMBRE).delete()
        db.session.commit()


def test_registrar_usuario_ok(app_context):
    usuario = auth_service.registrar_usuario(NOMBRE, APELLIDO, "1234")
    assert usuario.id is not None
    assert usuario.pin_hash != "1234"  # nunca en texto plano


def test_registrar_usuario_pin_invalido(app_context):
    with pytest.raises(ValueError):
        auth_service.registrar_usuario(NOMBRE, APELLIDO, "12a4")
    with pytest.raises(ValueError):
        auth_service.registrar_usuario(NOMBRE, APELLIDO, "12345")


def test_registrar_usuario_duplicado_por_acentos_y_mayusculas(app_context):
    auth_service.registrar_usuario("Ángel", "Mata", "1111")
    with pytest.raises(ValueError):
        auth_service.registrar_usuario("angel", "MATA", "2222")
    Usuario.query.filter(Usuario.nombre == "Ángel").delete()
    db.session.commit()


def test_verificar_login_correcto_e_incorrecto(app_context):
    auth_service.registrar_usuario(NOMBRE, APELLIDO, "1234")

    assert auth_service.verificar_login(NOMBRE, APELLIDO, "1234") is not None
    assert auth_service.verificar_login(NOMBRE, APELLIDO, "0000") is None
    assert auth_service.verificar_login("Nadie", "Inexistente", "1234") is None
