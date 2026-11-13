"""M-01: pantalla y endpoints de Descubrir (catálogo de rutas públicas).

Abierto a visitantes: no pide sesión y no lee `session`. Solo habla con M-02
(`Catalogo`), que ya entrega datos públicos; aquí no hay SQL ni reglas del
catálogo. Cada error se convierte en un mensaje seguro: los de validación dan
400, la ruta privada o inexistente da el mismo 404 y los fallos del catálogo
(incluida la migración pendiente) dan 503 sin afectar el resto de v2.
"""
import re

from flask import Blueprint, jsonify, render_template, request

from base_datos.catalogo_valores import CATEGORIAS, REGIONES
from v2.negocio.catalogo import Catalogo, ErrorCatalogo, RutaNoEncontrada
from v2.utilerias import ErrorValidacion, mensaje_seguro

MENSAJE_SIN_RESULTADOS = "No hay rutas que coincidan con tu búsqueda. Cambia las palabras o reinicia los filtros."
_DURACION = re.compile(r"^\d{1,3}$")
_IDENTIFICADOR = re.compile(r"^\d{1,9}$")


def _duracion_de(texto):
    """La duración llega como texto en la URL; vacía significa «sin filtro»."""
    texto = (texto or "").strip()
    if not texto:
        return None
    if not _DURACION.match(texto):
        raise ErrorValidacion("El dato «duración» debe ser un número entero.")
    return int(texto)


def registrar_descubrir(app, *, catalogo=None):
    servicio = Catalogo() if catalogo is None else catalogo
    bp = Blueprint("descubrir_v2", __name__, url_prefix="/v2/descubrir",
                   template_folder="../templates")

    @bp.get("")
    def pagina():
        return render_template("descubrir.html", categorias=CATEGORIAS, regiones=REGIONES)

    @bp.get("/rutas")
    def lista():
        try:
            rutas = servicio.listar(
                palabra_clave=request.args.get("q"),
                duracion_dias=_duracion_de(request.args.get("duracion")),
                categoria=request.args.get("categoria"),
                region=request.args.get("region"),
            )
        except ErrorValidacion as error:
            return jsonify(error=mensaje_seguro(error)), 400
        except Exception as error:
            return jsonify(error=mensaje_seguro(error)), 503
        respuesta = {"rutas": rutas, "total": len(rutas)}
        if not rutas:
            respuesta["mensaje"] = MENSAJE_SIN_RESULTADOS
        return jsonify(respuesta)

    @bp.get("/rutas/<ruta_id>")
    def detalle(ruta_id):
        if not _IDENTIFICADOR.match(ruta_id):
            return jsonify(error="El identificador de la ruta no es válido."), 400
        try:
            return jsonify(ruta=servicio.detalle(int(ruta_id)))
        except RutaNoEncontrada as error:
            return jsonify(error=mensaje_seguro(error)), 404
        except ErrorValidacion as error:
            return jsonify(error=mensaje_seguro(error)), 400
        except ErrorCatalogo as error:
            return jsonify(error=mensaje_seguro(error)), 503
        except Exception as error:
            return jsonify(error=mensaje_seguro(error)), 503

    @bp.after_request
    def sin_cache(respuesta):
        respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    app.register_blueprint(bp)
