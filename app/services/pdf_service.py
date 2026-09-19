"""Genera el PDF del itinerario que el usuario descarga al guardar su
ruta, con los mismos colores de marca que el resto de la app.
"""

import io

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle

from app.services import navegacion_service

TERRACOTA = colors.HexColor("#c76a4c")
VERDE_OSCURO = colors.HexColor("#1f3327")
VERDE_PALIDO = colors.HexColor("#eaf1e7")
CREMA = colors.HexColor("#f7f1e6")
MOSTAZA = colors.HexColor("#e0a63e")
BLANCO = colors.white
GRIS_TEXTO = colors.HexColor("#6b6b62")


def formato_duracion(horas):
    """9.5 -> '9 h 30 min'. Igual que formatoDuracion() en static/js/formato.js."""
    total_min = round(float(horas) * 60)
    h, m = divmod(total_min, 60)
    if h and m:
        return f"{h} h {m} min"
    return f"{h} h" if h else f"{m} min"


def _formato_moneda(valor):
    return f"${valor:,.0f} MXN"


def _qr(enlace, tamano):
    widget = QrCodeWidget(enlace)
    x0, y0, x1, y1 = widget.getBounds()
    dibujo = Drawing(tamano, tamano, transform=[tamano / (x1 - x0), 0, 0, tamano / (y1 - y0), 0, 0])
    dibujo.add(widget)
    return dibujo


def generar_pdf_itinerario(datos):
    """Genera el PDF y devuelve los bytes listos para descargar.

    `datos` es un dict con: nombre, origen, destino, resumen (dict con
    distancia_km/tiempo_h/costo_estimado/gasto), paradas (lista de
    {nombre}, en orden).
    """
    buffer = io.BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
    )

    estilo_titulo = ParagraphStyle(
        "TituloRuta", fontName="Helvetica-Bold", fontSize=22, textColor=BLANCO, leading=26
    )
    estilo_kicker = ParagraphStyle(
        "Kicker", fontName="Helvetica-Bold", fontSize=9, textColor=MOSTAZA, leading=12, spaceAfter=4
    )
    estilo_seccion = ParagraphStyle(
        "Seccion", fontName="Helvetica-Bold", fontSize=14, textColor=VERDE_OSCURO, spaceBefore=18, spaceAfter=8
    )
    estilo_texto = ParagraphStyle("Texto", fontName="Helvetica", fontSize=10.5, textColor=VERDE_OSCURO, leading=15)
    estilo_nota = ParagraphStyle("Nota", fontName="Helvetica-Oblique", fontSize=8.5, textColor=GRIS_TEXTO, leading=12)

    resumen = datos.get("resumen") or {}
    paradas = datos.get("paradas") or []

    elementos = []

    # --- Encabezado con el nombre de la ruta ---
    encabezado = Table(
        [[Paragraph("ROADTRIP · RUTAMX", estilo_kicker)], [Paragraph(datos.get("nombre") or "Tu ruta", estilo_titulo)]],
        colWidths=[17 * cm],
    )
    encabezado.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), VERDE_OSCURO),
                ("LEFTPADDING", (0, 0), (-1, -1), 18),
                ("RIGHTPADDING", (0, 0), (-1, -1), 18),
                ("TOPPADDING", (0, 0), (-1, 0), 16),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 18),
            ]
        )
    )
    elementos.append(encabezado)
    elementos.append(Spacer(1, 16))

    # --- Origen -> Destino ---
    elementos.append(
        Paragraph(f"<b>{datos.get('origen', '')}</b> &nbsp;→&nbsp; <b>{datos.get('destino', '')}</b>", estilo_texto)
    )
    elementos.append(Spacer(1, 10))
    elementos.append(HRFlowable(width="100%", color=colors.HexColor("#e7ddc9"), thickness=1))

    # --- Resumen del viaje ---
    elementos.append(Paragraph("Resumen del viaje", estilo_seccion))

    distancia_km = resumen.get("distancia_km")
    tiempo_h = resumen.get("tiempo_h")
    gasto = resumen.get("gasto") or {}
    costo_estimado = gasto.get("total", resumen.get("costo_estimado"))

    filas_resumen = [
        ["DISTANCIA", "TIEMPO ESTIMADO", "GASTO MÁX. RECOMENDADO"],
        [
            f"{distancia_km} km" if distancia_km is not None else "—",
            formato_duracion(tiempo_h) if tiempo_h is not None else "—",
            _formato_moneda(costo_estimado) if costo_estimado is not None else "—",
        ],
    ]
    tabla_resumen = Table(filas_resumen, colWidths=[5.6 * cm, 5.6 * cm, 5.6 * cm])
    tabla_resumen.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), VERDE_PALIDO),
                ("BACKGROUND", (0, 1), (-1, 1), CREMA),
                ("TEXTCOLOR", (0, 0), (-1, 0), VERDE_OSCURO),
                ("TEXTCOLOR", (0, 1), (-1, 1), TERRACOTA),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, 1), 15),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7ddc9")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7ddc9")),
            ]
        )
    )
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 6))

    if gasto:
        partes = [
            f"Gasolina {_formato_moneda(gasto['gasolina'])}",
            f"casetas ≈ {_formato_moneda(gasto['casetas'])}",
        ]
        if gasto.get("num_comidas"):
            partes.append(f"{gasto['num_comidas']} comida(s) {_formato_moneda(gasto['comidas'])}")
        if gasto.get("num_noches"):
            partes.append(f"{gasto['num_noches']} noche(s) de hospedaje {_formato_moneda(gasto['hospedaje'])}")
        partes.append(f"imprevistos {_formato_moneda(gasto['imprevistos'])}")
        elementos.append(Paragraph("Incluye: " + ", ".join(partes) + ".", estilo_nota))
        elementos.append(
            Paragraph(
                f"Gasolina calculada con {gasto.get('rendimiento_kml')} km/l a ${gasto.get('precio_litro')}/litro. "
                "Las casetas son un promedio: cada caseta cuesta distinto. Estimación para un auto particular, "
                "por el viaje completo.",
                estilo_nota,
            )
        )

    # --- Itinerario ---
    elementos.append(Paragraph("Tu itinerario", estilo_seccion))

    filas_itinerario = [["#", "PARADA", ""]]
    estilos_filas = []
    fila_actual = 1

    filas_itinerario.append(["", f"ORIGEN — {datos.get('origen', '')}", ""])
    estilos_filas.append(("BACKGROUND", (0, fila_actual), (-1, fila_actual), VERDE_PALIDO))
    fila_actual += 1

    for indice, parada in enumerate(paradas, start=1):
        filas_itinerario.append([str(indice), parada.get("nombre", ""), ""])
        estilos_filas.append(("BACKGROUND", (0, fila_actual), (-1, fila_actual), colors.white))
        fila_actual += 1

    filas_itinerario.append(["", f"DESTINO — {datos.get('destino', '')}", ""])
    estilos_filas.append(("BACKGROUND", (0, fila_actual), (-1, fila_actual), colors.HexColor("#f4e3dc")))

    tabla_itinerario = Table(filas_itinerario, colWidths=[1.2 * cm, 14 * cm, 1.6 * cm])
    tabla_itinerario.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), VERDE_OSCURO),
                ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 11),
                ("TEXTCOLOR", (0, 1), (-1, -1), VERDE_OSCURO),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 1), (0, -1), TERRACOTA),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (1, 0), (1, -1), 10),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7ddc9")),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e7ddc9")),
                *estilos_filas,
            ]
        )
    )
    elementos.append(tabla_itinerario)

    # --- Navegación: QR + enlace a Google Maps (un QR por tramo) ---
    enlaces = navegacion_service.enlaces_google_maps(datos)
    elementos.append(Paragraph("Empieza tu viaje", estilo_seccion))
    elementos.append(
        Paragraph(
            "Escanea el código con la cámara de tu teléfono para abrir la ruta completa en Google Maps "
            "y tocar «Iniciar». También puedes tocar el enlace si abres este PDF en el celular.",
            estilo_texto,
        )
    )
    elementos.append(Spacer(1, 8))
    for numero, enlace in enumerate(enlaces, start=1):
        titulo = f"Tramo {numero} de {len(enlaces)}" if len(enlaces) > 1 else "Ruta completa"
        texto = Paragraph(
            f"<b>{titulo}</b><br/><link href=\"{enlace.replace('&', '&amp;')}\" color=\"#c76a4c\">"
            "Abrir en Google Maps</link>",
            estilo_texto,
        )
        fila = Table([[_qr(enlace, 3.2 * cm), texto]], colWidths=[3.8 * cm, 13 * cm])
        fila.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        elementos.append(fila)
    if len(enlaces) > 1:
        elementos.append(
            Paragraph("Google Maps admite máximo 9 paradas por enlace, por eso el viaje se divide en tramos.", estilo_nota)
        )

    elementos.append(Spacer(1, 20))
    elementos.append(
        Paragraph(
            "Generado con RutaMX — distancias, tiempos y costos son estimaciones para ayudarte a planear tu viaje.",
            estilo_nota,
        )
    )

    documento.build(elementos)
    return buffer.getvalue()
