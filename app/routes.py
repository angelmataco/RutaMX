import io
import re

from flask import Blueprint, jsonify, render_template, request, send_file, session

from app.models import Destino, RutaGuardada, Usuario, guardar_ruta, listar_rutas
from app.services import ai_service, auth_service, gasto_service, llm_provider, navegacion_service, pdf_service, planificador_ia_service, route_service

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/api/ruta", methods=["POST"])
def api_calcular_ruta():
    datos = request.get_json(silent=True) or {}
    origen = (datos.get("origen") or "").strip()
    destino = (datos.get("destino") or "").strip()

    if not origen or not destino:
        return jsonify({"error": "Origen y destino son obligatorios."}), 400

    resumen = route_service.calcular_ruta(origen, destino, datos.get("ajustes"))
    # La geometría completa es para cálculos internos (ver /api/sugerencias);
    # no hace falta mandarla al navegador, que ya traza su propia ruta.
    resumen_publico = {clave: valor for clave, valor in resumen.items() if clave != "geometria"}
    return jsonify(resumen_publico)


@main_bp.route("/api/sugerencias")
def api_sugerencias():
    origen = request.args.get("origen", "").strip()
    destino = request.args.get("destino", "").strip()
    intereses = request.args.get("intereses", "")
    lista_intereses = [i for i in intereses.split(",") if i]

    horas_max = None
    try:
        horas_max = float(request.args.get("horas_max", "")) or None
    except ValueError:
        horas_max = None

    try:
        limite = int(request.args.get("limite", 4))
    except ValueError:
        limite = 4

    excluir = request.args.get("excluir", "")
    ids_excluidos = {int(i) for i in excluir.split(",") if i.isdigit()}

    hora_salida = request.args.get("hora_salida", "").strip() or None

    ruta = route_service.calcular_ruta(origen, destino) if origen and destino else None

    sugerencias = ai_service.sugerir_paradas(
        lista_intereses,
        limite=limite,
        ruta=ruta,
        horas_max=horas_max,
        excluir_ids=ids_excluidos,
        hora_salida=hora_salida,
    )
    return jsonify({"sugerencias": sugerencias})


@main_bp.route("/api/ia/disponible")
def api_ia_disponible():
    return jsonify({"disponible": llm_provider.hay_proveedor_configurado()})


@main_bp.route("/api/ia/planear", methods=["POST"])
def api_ia_planear():
    datos = request.get_json(silent=True) or {}
    mensajes = datos.get("mensajes") or []
    resultado = planificador_ia_service.procesar_turno(mensajes)
    return jsonify(resultado)


@main_bp.route("/api/destinos/nombres")
def api_destinos_nombres():
    # Ordenados por importancia: ciudades principales primero (las más
    # pobladas antes), luego pueblos mágicos y sitios turísticos. El
    # autocompletado respeta este orden, así "León" sale antes que
    # cualquier sitio turístico de León.
    prioridad_tipo = {"ciudad_principal": 0, "pueblo_magico": 1, "sitio_turistico": 2}
    destinos = sorted(
        Destino.query.all(),
        key=lambda d: (prioridad_tipo.get(d.tipo, 3), -(d.poblacion or 0), d.nombre),
    )
    nombres = list(dict.fromkeys(d.nombre for d in destinos))  # sin repetidos, conserva el orden
    return jsonify({"nombres": nombres})


@main_bp.route("/api/auth/registro", methods=["POST"])
def api_auth_registro():
    datos = request.get_json(silent=True) or {}
    try:
        usuario = auth_service.registrar_usuario(
            datos.get("nombre"), datos.get("apellido"), datos.get("pin")
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    session["usuario_id"] = usuario.id
    return jsonify({"usuario": usuario.to_dict()}), 201


@main_bp.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    datos = request.get_json(silent=True) or {}
    usuario = auth_service.verificar_login(
        datos.get("nombre"), datos.get("apellido"), datos.get("pin")
    )
    if not usuario:
        return jsonify({"error": "Nombre, apellido o PIN incorrectos."}), 401

    session["usuario_id"] = usuario.id
    return jsonify({"usuario": usuario.to_dict()})


@main_bp.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    session.pop("usuario_id", None)
    return jsonify({"ok": True})


@main_bp.route("/api/auth/yo")
def api_auth_yo():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"usuario": None})

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        session.pop("usuario_id", None)
        return jsonify({"usuario": None})
    return jsonify({"usuario": usuario.to_dict()})


@main_bp.route("/api/rutas", methods=["GET"])
def api_listar_rutas():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Inicia sesión para ver tus rutas guardadas."}), 401
    return jsonify({"rutas": listar_rutas(usuario_id)})


@main_bp.route("/api/rutas", methods=["POST"])
def api_guardar_ruta():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"error": "Inicia sesión para guardar tu ruta."}), 401

    datos = request.get_json(silent=True) or {}

    nombre = (datos.get("nombre") or "Ruta sin nombre").strip()
    origen = (datos.get("origen") or "").strip()
    destino = (datos.get("destino") or "").strip()
    intereses = datos.get("intereses") or []
    resumen = datos.get("resumen") or {}
    paradas = datos.get("paradas") or []

    if not origen or not destino:
        return jsonify({"error": "Origen y destino son obligatorios."}), 400

    ruta = RutaGuardada(
        nombre=nombre,
        origen=origen,
        destino=destino,
        intereses=intereses,
        resumen=resumen,
        paradas=paradas,
        usuario_id=usuario_id,
    )
    guardar_ruta(ruta)

    return jsonify(ruta.to_dict()), 201


@main_bp.route("/api/itinerario/pdf", methods=["POST"])
def api_pdf_itinerario():
    datos = request.get_json(silent=True) or {}

    origen = (datos.get("origen") or "").strip()
    destino = (datos.get("destino") or "").strip()

    if not origen or not destino:
        return jsonify({"error": "Origen y destino son obligatorios."}), 400

    pdf_bytes = pdf_service.generar_pdf_itinerario(datos)

    nombre_archivo = re.sub(r"[^a-zA-Z0-9_-]+", "_", datos.get("nombre") or "itinerario").strip("_") or "itinerario"

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{nombre_archivo}.pdf",
    )


@main_bp.route("/api/itinerario/enlaces", methods=["POST"])
def api_enlaces_navegacion():
    datos = request.get_json(silent=True) or {}

    if not (datos.get("origen") or "").strip() or not (datos.get("destino") or "").strip():
        return jsonify({"error": "Origen y destino son obligatorios."}), 400

    return jsonify({"enlaces": navegacion_service.enlaces_google_maps(datos)})


@main_bp.route("/api/gasto", methods=["POST"])
def api_gasto():
    """Recalcula el gasto recomendado cuando cambian la distancia real
    (por las paradas) o las paradas mismas."""
    datos = request.get_json(silent=True) or {}
    try:
        distancia_km = float(datos.get("distancia_km"))
        tiempo_h = float(datos.get("tiempo_h"))
    except (TypeError, ValueError):
        return jsonify({"error": "distancia_km y tiempo_h son obligatorios."}), 400

    casetas_por_km = datos.get("casetas_por_km")
    gasto = gasto_service.calcular_gasto(
        distancia_km,
        tiempo_h,
        datos.get("ajustes"),
        datos.get("paradas"),
        casetas_por_km if isinstance(casetas_por_km, (int, float)) else None,
    )
    gasto["casetas_fuente"] = datos.get("casetas_fuente") or "estimado"
    return jsonify(gasto)
