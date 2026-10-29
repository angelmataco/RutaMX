"""Registro y login de cuentas: nombre + apellido + PIN de 4 dígitos.

Sin correo a propósito (proyecto escolar) — ver
bitacora_proyecto/03_DECISIONES_Y_NOTAS.md para el porqué. El PIN nunca
se guarda en texto plano: se hashea con werkzeug.security, que ya viene
con Flask (no es una dependencia nueva).
"""

from werkzeug.security import check_password_hash, generate_password_hash

from app.models import Usuario, db
from app.services import maps_service


def _clave_normalizada(nombre: str, apellido: str) -> str:
    return maps_service._normalizar(f"{nombre} {apellido}")


def registrar_usuario(nombre: str, apellido: str, pin: str) -> Usuario:
    nombre = (nombre or "").strip()
    apellido = (apellido or "").strip()
    pin = (pin or "").strip()

    if not nombre or not apellido:
        raise ValueError("Nombre y apellido son obligatorios.")
    if not (pin.isdigit() and len(pin) == 4):
        raise ValueError("El PIN debe ser de exactamente 4 dígitos.")

    clave = _clave_normalizada(nombre, apellido)
    if Usuario.query.filter_by(clave_normalizada=clave).first():
        raise ValueError("Ya existe una cuenta con ese nombre y apellido.")

    usuario = Usuario(
        nombre=nombre,
        apellido=apellido,
        clave_normalizada=clave,
        pin_hash=generate_password_hash(pin),
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def verificar_login(nombre: str, apellido: str, pin: str) -> Usuario | None:
    clave = _clave_normalizada(nombre or "", apellido or "")
    usuario = Usuario.query.filter_by(clave_normalizada=clave).first()
    if not usuario:
        return None
    if not check_password_hash(usuario.pin_hash, (pin or "").strip()):
        return None
    return usuario
