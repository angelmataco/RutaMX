import io
import re

from flask import Blueprint, jsonify, render_template, request, send_file

from app.models import RutaGuardada, guardar_ruta, listar_rutas
from app.services import ai_service, pdf_service, route_service

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/api/ruta", methods=["POST"])
def api_calcular_ruta():
    datos = request.get_json(silent=True) or {}
    origen = (datos.get("origen") or "").strip()
    destino = (datos.get("destino") or "").strip()
    presupuesto = datos.get("presupuesto") or 0

    if not origen or not destino:
        return jsonify({"error": "Origen y destino son obligatorios."}), 400

    try:
        presupuesto = float(presupuesto)
    except (TypeError, ValueError):
        presupuesto = 0

    resumen = route_service.calcular_ruta(origen, destino, presupuesto)
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

    ruta = route_service.calcular_ruta(origen, destino) if origen and destino else None

    sugerencias = ai_service.sugerir_paradas(
        lista_intereses, limite=limite, ruta=ruta, horas_max=horas_max, excluir_ids=ids_excluidos
    )
    return jsonify({"sugerencias": sugerencias})


@main_bp.route("/api/rutas", methods=["GET"])
def api_listar_rutas():
    return jsonify({"rutas": listar_rutas()})


@main_bp.route("/api/rutas", methods=["POST"])
def api_guardar_ruta():
    datos = request.get_json(silent=True) or {}

    nombre = (datos.get("nombre") or "Ruta sin nombre").strip()
    origen = (datos.get("origen") or "").strip()
    destino = (datos.get("destino") or "").strip()
    presupuesto = datos.get("presupuesto") or 0
    intereses = datos.get("intereses") or []
    resumen = datos.get("resumen") or {}
    paradas = datos.get("paradas") or []

    if not origen or not destino:
        return jsonify({"error": "Origen y destino son obligatorios."}), 400

    try:
        presupuesto = float(presupuesto)
    except (TypeError, ValueError):
        presupuesto = 0

    ruta = RutaGuardada(
        nombre=nombre,
        origen=origen,
        destino=destino,
        presupuesto=presupuesto,
        intereses=intereses,
        resumen=resumen,
        paradas=paradas,
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
