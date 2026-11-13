"""Publica (o vuelve privada) una ruta guardada en el catálogo de Descubrir.

Herramienta administrativa de línea de comandos: NO es una función de la app
(P-01 sigue abierta ante el profesor; esta es la propuesta pendiente de
aprobación de Angel). Requiere que ya se haya corrido la migración
`base_datos/migraciones/agregar_columnas_catalogo.py`.

Uso:
    python base_datos/scripts/publicar_ruta.py 12 --categoria Playa --region Sureste \\
        --descripcion "Costa de Oaxaca en cinco días"
    python base_datos/scripts/publicar_ruta.py 12 --categoria Cultural --region Centro \\
        --descripcion "..." --rutamx          # autor vacío: aparece como RutaMx
    python base_datos/scripts/publicar_ruta.py 12 --privada      # la saca del catálogo

Autor: si la ruta ya tiene autor_id se conserva; si no, se toma al dueño de la
ruta como autor, de forma explícita. Solo `--rutamx` deja el autor vacío, y es
la única forma de que una ruta aparezca como de RutaMx.

Duración: sale de la ruta guardada por v2 (`resumen.rutamx_v2.ruta.duracion_dias`);
si la ruta no la trae (por ejemplo, una de v1) hay que indicarla con `--duracion`.

Sale con código 1 y un mensaje claro si algo no es válido, la ruta no existe o
falta la migración. Corre en una transacción: o se aplica todo o nada.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import text

from base_datos.catalogo_valores import (
    CATEGORIAS,
    REGIONES,
    VISIBILIDAD_PRIVADA,
    VISIBILIDAD_PUBLICA,
)

LIMITE_DESCRIPCION = 500
CODIGO_COLUMNA_INEXISTENTE = "42703"

_BUSCAR = text(
    "SELECT id, usuario_id, autor_id, "
    "resumen #>> '{rutamx_v2,ruta,duracion_dias}' AS duracion_v2 "
    "FROM rutas_guardadas WHERE id = :id FOR UPDATE"
)
_PUBLICAR = text(
    "UPDATE rutas_guardadas SET visibilidad = :vis, categoria = :cat, region = :reg, "
    "descripcion = :desc, duracion_dias = :dur, autor_id = :autor WHERE id = :id"
)
_PRIVADA = text("UPDATE rutas_guardadas SET visibilidad = :vis WHERE id = :id")


class ErrorPublicacion(Exception):
    """Dato inválido, ruta inexistente o migración pendiente (mensaje seguro)."""


def _abrir_sesion():
    from sqlalchemy.orm import Session

    from base_datos.conexion import crear_app_minima, db

    app = crear_app_minima()
    # El contexto de Flask solo hace falta para obtener el engine; se libera
    # antes de devolver la sesión (las consultas siguientes no lo necesitan).
    with app.app_context():
        engine = db.engine
    return Session(engine)


def _entero_positivo(valor, nombre):
    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        raise ErrorPublicacion(f"{nombre} debe ser un número entero mayor que cero.")
    return valor


def _validar_publicacion(ruta_id, categoria, region, descripcion, duracion):
    _entero_positivo(ruta_id, "El id de la ruta")
    if categoria not in CATEGORIAS:
        raise ErrorPublicacion(f"Categoría no válida. Opciones: {', '.join(CATEGORIAS)}.")
    if region not in REGIONES:
        raise ErrorPublicacion(f"Región no válida. Opciones: {', '.join(REGIONES)}.")
    if not isinstance(descripcion, str) or not descripcion.strip():
        raise ErrorPublicacion("La descripción es obligatoria.")
    if len(descripcion.strip()) > LIMITE_DESCRIPCION:
        raise ErrorPublicacion(f"La descripción no puede pasar de {LIMITE_DESCRIPCION} caracteres.")
    if duracion is not None:
        _entero_positivo(duracion, "La duración")


def _duracion_de(fila, duracion):
    if duracion is not None:
        return duracion
    try:
        valor = int(fila["duracion_v2"])
    except (TypeError, ValueError):
        valor = 0
    if valor <= 0:
        raise ErrorPublicacion("La ruta no trae su duración en días: indícala con --duracion.")
    return valor


def _traducir(error):
    codigo = getattr(getattr(error, "orig", None), "pgcode", None)
    if codigo == CODIGO_COLUMNA_INEXISTENTE:
        return ErrorPublicacion(
            "Falta la migración del catálogo: corre base_datos/migraciones/agregar_columnas_catalogo.py primero."
        )
    return ErrorPublicacion("No se pudo actualizar la ruta.")


def _ejecutar(operacion):
    """Corre `operacion(sesion)` en una transacción propia (todo o nada)."""
    sesion = _abrir_sesion()
    try:
        resultado = operacion(sesion)
        sesion.commit()
        return resultado
    except ErrorPublicacion:
        sesion.rollback()
        raise
    except Exception as error:
        sesion.rollback()
        raise _traducir(error) from error
    finally:
        sesion.close()


def publicar(ruta_id, categoria, region, descripcion, duracion=None, rutamx=False):
    """Pone la ruta como pública y devuelve un resumen de lo aplicado."""
    _validar_publicacion(ruta_id, categoria, region, descripcion, duracion)

    def operacion(sesion):
        fila = sesion.execute(_BUSCAR, {"id": ruta_id}).mappings().first()
        if fila is None:
            raise ErrorPublicacion(f"No existe la ruta {ruta_id}.")
        if rutamx:
            autor = None
        elif fila["autor_id"] is not None:
            autor = fila["autor_id"]
        elif fila["usuario_id"] is not None:
            autor = fila["usuario_id"]
        else:
            raise ErrorPublicacion("La ruta no tiene dueño ni autor: usa --rutamx si es de RutaMx.")
        dias = _duracion_de(fila, duracion)
        sesion.execute(_PUBLICAR, {
            "vis": VISIBILIDAD_PUBLICA, "cat": categoria, "reg": region,
            "desc": descripcion.strip(), "dur": dias, "autor": autor, "id": ruta_id,
        })
        return {"ruta_id": ruta_id, "duracion_dias": dias, "es_rutamx": autor is None}

    return _ejecutar(operacion)


def volver_privada(ruta_id):
    """Saca la ruta del catálogo (no borra nada más)."""
    _entero_positivo(ruta_id, "El id de la ruta")

    def operacion(sesion):
        if sesion.execute(_BUSCAR, {"id": ruta_id}).mappings().first() is None:
            raise ErrorPublicacion(f"No existe la ruta {ruta_id}.")
        sesion.execute(_PRIVADA, {"vis": VISIBILIDAD_PRIVADA, "id": ruta_id})
        return {"ruta_id": ruta_id}

    return _ejecutar(operacion)


def _parser():
    p = argparse.ArgumentParser(description="Publica o vuelve privada una ruta guardada.")
    p.add_argument("ruta_id", type=int)
    p.add_argument("--categoria")
    p.add_argument("--region")
    p.add_argument("--descripcion")
    p.add_argument("--duracion", type=int)
    p.add_argument("--rutamx", action="store_true", help="autor vacío: aparece como RutaMx")
    p.add_argument("--privada", action="store_true", help="vuelve la ruta privada")
    return p


def principal(argv=None):
    """Devuelve el código de salida: 0 bien, 1 error."""
    try:
        args = _parser().parse_args(argv)
    except SystemExit as salida:
        return 0 if salida.code == 0 else 1  # --help sale bien; un argumento inválido, no
    try:
        if args.privada:
            if args.categoria or args.region or args.descripcion or args.duracion or args.rutamx:
                raise ErrorPublicacion("--privada no se combina con los datos de publicación.")
            volver_privada(args.ruta_id)
            print(f"Listo: la ruta {args.ruta_id} ahora es privada.")
        else:
            r = publicar(args.ruta_id, args.categoria, args.region, args.descripcion,
                         args.duracion, args.rutamx)
            autor = "RutaMx" if r["es_rutamx"] else "su autor"
            print(f"Listo: la ruta {r['ruta_id']} es pública ({r['duracion_dias']} días, autor: {autor}).")
    except ErrorPublicacion as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("Error: no se pudo abrir la base de datos (revisa la configuración).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(principal())
