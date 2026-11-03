"""M-09 Repositorio de rutas: acceso a la base para las rutas del desarrollo nuevo.

(La v1 conserva su propio acceso, `guardar_ruta` y `listar_rutas`; no se toca.)

Operaciones: `crear_ruta`, `obtener_ruta` y `listar_rutas_de_usuario`.

Responsabilidades:
- Guardar y leer rutas asociadas a un dueño (`usuario_id`), con consultas que
  siempre filtran por dueño.
- Integridad mínima antes de escribir (texto obligatorio y paradas como lista).
- Cada escritura controla su propia transacción (commit o rollback).

Lo que NO hace (es de otros módulos): reglas de negocio D-03 (M-05),
autenticación (M-10), actualizar/copiar/borrar rutas.

Transacciones: cada escritura usa una sesión PROPIA (no `db.session`) y hace
commit o rollback por su cuenta. Así nunca confirma cambios pendientes ajenos,
pero tampoco ve datos sin confirmar de otra sesión ni puede revertirse desde una
transacción exterior (a tener en cuenta cuando M-05 orqueste varios cambios).

Devuelve diccionarios, nunca objetos ORM. "No encontrada" es `None`. Todo fallo
se comunica con `ErrorRepositorio`, con un mensaje sin SQL ni detalles internos.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from base_datos.conexion import db
from base_datos.modelos import RutaGuardada

CAMPOS_TEXTO_OBLIGATORIOS = ("nombre", "origen", "destino")


class ErrorRepositorio(Exception):
    """Fallo del repositorio de rutas (datos inválidos o error de la base)."""


def _abrir_sesion():
    """Sesión propia para cada operación.

    Es independiente de `db.session`, así un commit del repositorio nunca
    confirma cambios pendientes de otra parte del programa.
    """
    return Session(db.engine)


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_usuario_id(usuario_id):
    if not _es_entero(usuario_id):
        raise ErrorRepositorio("El identificador de usuario no es válido.")


def _validar_datos_ruta(datos_ruta):
    if not isinstance(datos_ruta, dict):
        raise ErrorRepositorio("Los datos de la ruta deben ser un diccionario.")
    for campo in CAMPOS_TEXTO_OBLIGATORIOS:
        valor = datos_ruta.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorRepositorio(f"El campo '{campo}' es obligatorio y debe tener texto.")
    if not isinstance(datos_ruta.get("paradas"), list):
        raise ErrorRepositorio("El campo 'paradas' es obligatorio y debe ser una lista.")


def _a_diccionario(ruta):
    return {
        "id": ruta.id,
        "nombre": ruta.nombre,
        "origen": ruta.origen,
        "destino": ruta.destino,
        "presupuesto": ruta.presupuesto,
        "intereses": ruta.intereses or [],
        "resumen": ruta.resumen or {},
        "paradas": ruta.paradas or [],
        "usuario_id": ruta.usuario_id,
    }


def crear_ruta(datos_ruta, usuario_id):
    """Guarda una ruta para `usuario_id` y devuelve el diccionario creado."""
    _validar_usuario_id(usuario_id)
    _validar_datos_ruta(datos_ruta)
    try:
        with _abrir_sesion() as sesion:
            try:
                ruta = RutaGuardada(
                    nombre=datos_ruta["nombre"],
                    origen=datos_ruta["origen"],
                    destino=datos_ruta["destino"],
                    presupuesto=datos_ruta.get("presupuesto"),
                    intereses=datos_ruta.get("intereses") or [],
                    resumen=datos_ruta.get("resumen") or {},
                    paradas=datos_ruta["paradas"],
                    usuario_id=usuario_id,  # el dueño sale solo del argumento
                )
                sesion.add(ruta)
                sesion.flush()
                creada = _a_diccionario(ruta)
                sesion.commit()
                return creada
            except Exception:
                sesion.rollback()
                raise
    except Exception as error:
        raise ErrorRepositorio("No se pudo guardar la ruta.") from error


def obtener_ruta(ruta_id, usuario_id):
    """Devuelve la ruta de `usuario_id`, o `None` si no existe o es de otro."""
    _validar_usuario_id(usuario_id)
    if not _es_entero(ruta_id):
        raise ErrorRepositorio("El identificador de la ruta no es válido.")
    try:
        with _abrir_sesion() as sesion:
            ruta = sesion.execute(
                select(RutaGuardada).where(
                    RutaGuardada.id == ruta_id,
                    RutaGuardada.usuario_id == usuario_id,
                )
            ).scalar_one_or_none()
            return _a_diccionario(ruta) if ruta else None
    except Exception as error:
        raise ErrorRepositorio("No se pudo leer la ruta.") from error


def listar_rutas_de_usuario(usuario_id):
    """Devuelve las rutas de `usuario_id` (la más reciente primero)."""
    _validar_usuario_id(usuario_id)
    try:
        with _abrir_sesion() as sesion:
            rutas = sesion.execute(
                select(RutaGuardada)
                .where(RutaGuardada.usuario_id == usuario_id)
                .order_by(RutaGuardada.creado_en.desc(), RutaGuardada.id.desc())
            ).scalars()
            return [_a_diccionario(ruta) for ruta in rutas]
    except Exception as error:
        raise ErrorRepositorio("No se pudieron leer las rutas.") from error
