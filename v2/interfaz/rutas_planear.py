"""M-03: blueprint de Planear; estado de conversación solo en el servidor."""
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from secrets import compare_digest, token_urlsafe
from threading import RLock
import time

from flask import Blueprint, jsonify, render_template, request, session

from v2.integracion.adaptador_ia import AdaptadorIA, crear_adaptador
from v2.integracion.verificador_geografico import VerificadorNominatim
from v2.interfaz.rutas_guardadas import respuesta_sin_sesion, usuario_de_sesion
from v2.negocio.guardado_rutas import GuardadoRutas
from v2.negocio.orquestador import OrquestadorPlaneacion
from v2.utilerias import ErrorValidacion, mensaje_seguro

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


class _AdaptadorDelegado(AdaptadorIA):
    """Envuelve al adaptador real para poder INSTALAR una ruta guardada.

    Con `precargada` puesta, la siguiente extracción y generación devuelven
    esa ruta (así pasa por M-04 y M-05 y se revalida con D-03, sin tocar
    atributos privados). Sin ella, todo se delega tal cual al adaptador real.
    """

    def __init__(self, real):
        self._real = real
        self.precargada = None

    def extraer_datos(self, mensaje, datos_actuales=None):
        if self.precargada is not None:
            return {c: deepcopy(self.precargada[c])
                    for c in ("origen", "destino", "duracion_dias", "intereses")}
        return self._real.extraer_datos(mensaje, datos_actuales)

    def generar_ruta(self, datos):
        if self.precargada is not None:
            return deepcopy(self.precargada)
        return self._real.generar_ruta(datos)

    def interpretar_modificacion(self, instruccion, ruta):
        return self._real.interpretar_modificacion(instruccion, ruta)

    def _solicitar(self, operacion, datos):  # nunca se usa: todo se delega
        raise NotImplementedError


class _Rechazo(Exception):
    """Respuesta de error con su código HTTP, para salir de `responder`."""

    def __init__(self, codigo, datos):
        super().__init__(datos.get("error", ""))
        self.codigo = codigo
        self.datos = datos


@dataclass
class _Conversacion:
    orquestador: OrquestadorPlaneacion
    usada: float
    solicitudes: int = 0
    # Ruta guardada ligada a ESTA conversación y a SU dueño; nunca se hereda
    # entre usuarios ni entre viajes distintos (ver `guardar`).
    guardada: dict = None


def registrar_planear(app, *, fabrica_adaptador=None, verificador=None,
                      demostracion=False, reloj=time.monotonic, guardado=None):
    """Inyección exclusiva del servidor; no existe selector demo en los endpoints.

    Las pruebas pueden usar proveedores explícitos sin cargar entorno/BD reales.
    El estado en memoria requiere un solo proceso; se pierde al reiniciarlo.
    """
    if demostracion and not app.testing:
        raise ValueError("La demostración solo se permite en una app de prueba.")
    fabrica_real = crear_adaptador if fabrica_adaptador is None else fabrica_adaptador
    servicio = GuardadoRutas() if guardado is None else guardado

    def fabrica():
        return _AdaptadorDelegado(fabrica_real())

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
        """`accion(entrada)` devuelve el JSON, o lanza `_Rechazo` con su código."""
        try:
            entrada = obtener()
            with candado:
                if entrada.solicitudes >= MAX_SOLICITUDES:
                    return jsonify(error="Esta conversación llegó a su límite. Inicia una nueva."), 429
                entrada.solicitudes += 1
            return jsonify(accion(entrada))
        except _Rechazo as rechazo:
            return jsonify(**rechazo.datos), rechazo.codigo
        except ErrorValidacion as error:
            return jsonify(error=mensaje_seguro(error)), 400
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
        return responder(lambda e: e.orquestador.procesar(datos["mensaje"]))

    @bp.post("/planear/confirmar")
    def confirmar():
        datos, error = datos_peticion({"acepta"})
        if error:
            return error
        if not isinstance(datos["acepta"], bool):
            return jsonify(error="La confirmación debe indicar sí o no."), 400
        return responder(lambda e: e.orquestador.confirmar(datos["acepta"]))

    @bp.post("/planear/guardar")
    def guardar():
        datos, error = datos_peticion({"nombre"})
        if error:
            return error
        if datos["nombre"] is not None and not isinstance(datos["nombre"], str):
            return jsonify(error="El nombre debe ser texto."), 400
        usuario_id = usuario_de_sesion()
        if usuario_id is None:
            return respuesta_sin_sesion()  # RF-41: pide iniciar sesión

        def accion(entrada):
            ruta = entrada.orquestador.iniciar()["ruta"]
            if ruta is None:
                raise _Rechazo(409, {"error": "Todavía no hay una ruta para guardar."})
            previa = entrada.guardada
            # Solo se actualiza la MISMA fila (D-11) si es del mismo dueño y el
            # mismo viaje; otro usuario o un viaje distinto crea una ruta nueva.
            misma = (previa is not None and previa["usuario_id"] == usuario_id
                     and previa["origen"] == ruta["origen"]
                     and previa["destino"] == ruta["destino"])
            ruta_id = previa["ruta_id"] if misma else None
            fila = servicio.guardar(ruta, usuario_id, ruta_id=ruta_id,
                                    nombre=datos["nombre"] or None)
            entrada.guardada = {"usuario_id": usuario_id, "ruta_id": fila["id"],
                                "origen": ruta["origen"], "destino": ruta["destino"]}
            return {"estado": "guardada", "actualizada": misma,
                    "mensaje": "Ruta actualizada." if misma else "Ruta guardada.",
                    "ruta_guardada": {"id": fila["id"], "nombre": fila["nombre"]}}
        return responder(accion)

    @bp.post("/planear/abrir")
    def abrir_guardada():
        datos, error = datos_peticion({"id"})
        if error:
            return error
        if not isinstance(datos["id"], int) or isinstance(datos["id"], bool):
            return jsonify(error="El identificador de la ruta no es válido."), 400
        usuario_id = usuario_de_sesion()
        if usuario_id is None:
            return respuesta_sin_sesion()

        def accion(entrada):
            ruta = servicio.recuperar(datos["id"], usuario_id)  # solo del dueño
            adaptador = fabrica()
            nuevo = OrquestadorPlaneacion(adaptador, geo)
            nuevo.iniciar()
            adaptador.precargada = ruta
            try:
                vista = nuevo.procesar("Abrir mi ruta guardada.")
                # El usuario ya confirmó esto al crear y guardar la ruta. D-03
                # conoce dos confirmaciones (origen igual a destino y paradas
                # repetidas), así que como máximo se resuelven dos, sin bucle.
                for _ in range(2):
                    if vista["estado"] != "confirmar":
                        break
                    vista = nuevo.confirmar(True)
            finally:
                adaptador.precargada = None
            if vista["estado"] != "propuesta":
                # No se reemplaza la conversación vigente (nada a medias).
                raise _Rechazo(409, {"error": "No se pudo abrir la ruta guardada. " + vista["mensaje"]})
            entrada.orquestador = nuevo  # se INSTALA como la ruta de la conversación
            entrada.guardada = {"usuario_id": usuario_id, "ruta_id": datos["id"],
                                "origen": vista["ruta"]["origen"], "destino": vista["ruta"]["destino"]}
            return {**vista, "ruta_guardada": {"id": datos["id"]}}
        return responder(accion)

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
