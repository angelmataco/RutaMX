"""M-06: pantalla y lista de rutas guardadas, solo del usuario con sesión (M-10).

La sesión es la misma cookie firmada de v1: `session["usuario_id"]` lo escribe
la autenticación existente (M-10) y aquí solo se lee; v2 no importa nada de v1
para esto. El dueño SIEMPRE sale de la sesión, nunca de lo que mande el
navegador. Guardar y abrir una ruta actúan sobre la conversación y viven en
`rutas_planear.py`; aquí solo está lo que no depende de ella.
"""
from secrets import token_urlsafe

from flask import Blueprint, jsonify, render_template, request, session

from v2.negocio.guardado_rutas import ErrorGuardado, GuardadoRutas
from v2.utilerias import ErrorValidacion, mensaje_seguro

MENSAJE_SESION = "Inicia sesión para guardar y consultar tus rutas."


def usuario_de_sesion():
    """Identificador del usuario con sesión iniciada, o `None` (anónimo)."""
    usuario_id = session.get("usuario_id")
    if isinstance(usuario_id, int) and not isinstance(usuario_id, bool) and usuario_id > 0:
        return usuario_id
    return None


def respuesta_sin_sesion():
    return jsonify(error=MENSAJE_SESION, requiere_sesion=True), 401


def resumir(fila):
    """Datos mínimos de una ruta guardada para la lista (sin `resumen` interno)."""
    contenido = (fila.get("resumen") or {}).get("rutamx_v2")
    compatible = isinstance(contenido, dict) and contenido.get("version") == 1
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "origen": fila["origen"],
        "destino": fila["destino"],
        "paradas": len(fila.get("paradas") or []),
        "compatible": compatible,
    }


def registrar_guardadas(app, *, guardado=None):
    servicio = GuardadoRutas() if guardado is None else guardado
    bp = Blueprint("rutas_guardadas_v2", __name__, url_prefix="/v2",
                   template_folder="../templates")

    @bp.get("/rutas")
    def pagina():
        if "planear_v2_csrf" not in session:
            session["planear_v2_csrf"] = token_urlsafe(32)
        return render_template("rutas_guardadas.html", csrf=session["planear_v2_csrf"],
                               con_sesion=usuario_de_sesion() is not None)

    @bp.get("/rutas/lista")
    def lista():
        usuario_id = usuario_de_sesion()
        if usuario_id is None:
            return respuesta_sin_sesion()
        try:
            filas = servicio.listar(usuario_id)
            return jsonify(rutas=[resumir(f) for f in filas])
        except ErrorValidacion as error:
            # ErrorGuardado ya trae un mensaje seguro; el resto se oculta.
            return jsonify(error=mensaje_seguro(error)), 503
        except Exception as error:
            return jsonify(error=mensaje_seguro(error)), 503

    @bp.after_request
    def sin_cache(respuesta):
        if request.path.startswith("/v2/rutas"):
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    app.register_blueprint(bp)
