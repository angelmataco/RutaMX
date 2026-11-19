"""M-01: pantalla y endpoints de Descubrir (catálogo de rutas públicas).

Consulta abierta a visitantes; copiar exige sesión y CSRF. Habla con M-02
(`Catalogo`) y M-05 (`CopiaRutas`); aquí no hay SQL ni reglas del
catálogo. Cada error se convierte en un mensaje seguro: los de validación dan
400, la ruta privada o inexistente da el mismo 404 y los fallos del catálogo
(incluida la migración pendiente) dan 503 sin afectar el resto de v2.
"""
import re
from secrets import compare_digest, token_urlsafe

from flask import Blueprint, jsonify, render_template, request, session

from base_datos.catalogo_valores import CATEGORIAS, REGIONES
from v2.negocio.catalogo import Catalogo, ErrorCatalogo, RutaNoEncontrada
from v2.negocio.copia_rutas import CopiaRutas, RutaNoEncontrada as CopiaNoEncontrada
from v2.interfaz.rutas_guardadas import usuario_de_sesion, respuesta_sin_sesion
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


def registrar_descubrir(app, *, catalogo=None, copia=None):
    servicio = Catalogo() if catalogo is None else catalogo
    servicio_copia = CopiaRutas() if copia is None else copia
    bp = Blueprint("descubrir_v2", __name__, url_prefix="/v2/descubrir",
                   template_folder="../templates")

    @bp.get("")
    def pagina():
        if "planear_v2_csrf" not in session:
            session["planear_v2_csrf"] = token_urlsafe(32)
        return render_template("descubrir.html", categorias=CATEGORIAS, regiones=REGIONES,
                               csrf=session["planear_v2_csrf"])

    @bp.post("/rutas/<ruta_id>/copiar")
    def copiar(ruta_id):
        usuario_id = usuario_de_sesion()
        if usuario_id is None:
            return respuesta_sin_sesion()
        esperado = session.get("planear_v2_csrf", "")
        recibido = request.headers.get("X-RutaMX-CSRF", "")
        if not esperado or not compare_digest(esperado.encode(), recibido.encode()):
            return jsonify(error="La sesión de la página venció. Recarga e intenta de nuevo."), 403
        if not _IDENTIFICADOR.fullmatch(ruta_id):
            return jsonify(error="El identificador de la ruta no es válido."), 400
        try:
            copia_creada = servicio_copia.copiar(int(ruta_id), usuario_id)
            return jsonify(ruta=copia_creada, mensaje="Ruta copiada a mis rutas."), 201
        except CopiaNoEncontrada as error:
            return jsonify(error=mensaje_seguro(error)), 404
        except ErrorValidacion as error:
            return jsonify(error=mensaje_seguro(error)), 400
        except Exception as error:
            return jsonify(error=mensaje_seguro(error)), 503

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
