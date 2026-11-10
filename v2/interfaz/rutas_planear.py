"""M-03: blueprint de Planear; estado de conversación solo en el servidor."""
from collections import OrderedDict
from dataclasses import dataclass
from secrets import compare_digest, token_urlsafe
from threading import RLock
import time

from flask import Blueprint, jsonify, render_template, request, session

from v2.integracion.adaptador_ia import crear_adaptador
from v2.integracion.verificador_geografico import VerificadorNominatim
from v2.negocio.orquestador import OrquestadorPlaneacion
from v2.utilerias import mensaje_seguro

MAX_CONVERSACIONES = 128
CADUCIDAD_SEGUNDOS = 1800
MAX_SOLICITUDES = 60
MAX_CUERPO = 8192


class _VerificadorCompartido:
    def __init__(self, verificador):
        self._verificador = verificador
        self._candado = RLock()

    def verificar(self, nombre):
        # Un intervalo/caché común para todas las conversaciones de esta app.
        with self._candado:
            return self._verificador.verificar(nombre)


@dataclass
class _Conversacion:
    orquestador: OrquestadorPlaneacion
    usada: float
    solicitudes: int = 0


def registrar_planear(app, *, fabrica_adaptador=None, verificador=None,
                      demostracion=False, reloj=time.monotonic):
    """Inyección exclusiva del servidor; no existe selector demo en los endpoints.

    Las pruebas pueden usar proveedores explícitos sin cargar entorno/BD reales.
    El estado en memoria requiere un solo proceso; se pierde al reiniciarlo.
    """
    if demostracion and not app.testing:
        raise ValueError("La demostración solo se permite en una app de prueba.")
    fabrica = crear_adaptador if fabrica_adaptador is None else fabrica_adaptador
    geo = _VerificadorCompartido(VerificadorNominatim() if verificador is None else verificador)
    conversaciones = OrderedDict()
    candado = RLock()
    bp = Blueprint("planear_v2", __name__, url_prefix="/v2", template_folder="../templates",
                   static_folder="../static", static_url_path="/static")

    def obtener(nueva=False):
        with candado:
            ahora = reloj()
            for identificador, entrada in list(conversaciones.items()):
                if ahora - entrada.usada >= CADUCIDAD_SEGUNDOS:
                    del conversaciones[identificador]
            identificador = session.get("planear_v2_id")
            if nueva:
                conversaciones.pop(identificador, None)
            entrada = None if nueva else conversaciones.get(identificador)
            if entrada is None:
                adaptador = fabrica()
                while len(conversaciones) >= MAX_CONVERSACIONES:
                    conversaciones.popitem(last=False)
                identificador = token_urlsafe(32)
                entrada = _Conversacion(OrquestadorPlaneacion(adaptador, geo), ahora)
                conversaciones[identificador] = entrada
                session["planear_v2_id"] = identificador
            entrada.usada = ahora
            conversaciones.move_to_end(identificador)
            return entrada

    def datos_peticion(claves):
        esperado = session.get("planear_v2_csrf", "")
        recibido = request.headers.get("X-RutaMX-CSRF", "")
        if not esperado or not compare_digest(esperado.encode(), recibido.encode()):
            return None, (jsonify(error="La sesión cambió. Recarga la página e intenta de nuevo."), 403)
        if request.content_length is not None and request.content_length > MAX_CUERPO:
            return None, (jsonify(error="El mensaje es demasiado largo."), 413)
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict) or set(datos) != set(claves):
            return None, (jsonify(error="La solicitud no tiene el formato esperado."), 400)
        return datos, None

    def responder(accion):
        try:
            entrada = obtener()
            with candado:
                if entrada.solicitudes >= MAX_SOLICITUDES:
                    return jsonify(error="Esta conversación llegó a su límite. Inicia una nueva."), 429
                entrada.solicitudes += 1
            return jsonify(accion(entrada.orquestador))
        except Exception as error:
            return jsonify(error=mensaje_seguro(error)), 503

    @bp.get("/planear")
    def pagina():
        if "planear_v2_csrf" not in session:
            session["planear_v2_csrf"] = token_urlsafe(32)
        error = None
        estado = None
        try:
            estado = obtener().orquestador.iniciar()
        except Exception as exc:
            error = "Planear con IA no está configurado. " + mensaje_seguro(exc)
        return render_template("planear_ia.html", estado=estado, error=error,
                               csrf=session["planear_v2_csrf"], demostracion=demostracion)

    @bp.post("/planear/mensaje")
    def mensaje():
        datos, error = datos_peticion({"mensaje"})
        if error:
            return error
        if not isinstance(datos["mensaje"], str):
            return jsonify(error="Escribe un mensaje de texto."), 400
        return responder(lambda o: o.procesar(datos["mensaje"]))

    @bp.post("/planear/confirmar")
    def confirmar():
        datos, error = datos_peticion({"acepta"})
        if error:
            return error
        if not isinstance(datos["acepta"], bool):
            return jsonify(error="La confirmación debe indicar sí o no."), 400
        return responder(lambda o: o.confirmar(datos["acepta"]))

    @bp.post("/planear/reiniciar")
    def reiniciar():
        _, error = datos_peticion(set())
        if error:
            return error
        try:
            return jsonify(obtener(nueva=True).orquestador.iniciar())
        except Exception as exc:
            return jsonify(error=mensaje_seguro(exc)), 503

    @bp.after_request
    def sin_cache(respuesta):
        if request.path.startswith("/v2/planear"):
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    app.register_blueprint(bp)
