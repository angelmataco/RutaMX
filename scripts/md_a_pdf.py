"""Convierte un reporte .md (subconjunto simple de Markdown) a PDF con ReportLab.

Uso (desde la raiz del proyecto; primero se escribe el .md y luego se genera el PDF):
    venv/bin/python scripts/md_a_pdf.py documentacion/Reporte_X.md documentacion/Reporte_X.pdf

Soporta titulos (#, ##, ###), parrafos, vinetas, listas numeradas, tablas, bloques
de codigo y **negritas**/`codigo` en linea. Usa fuentes estandar: sin emojis ni
caracteres fuera de Latin-1. ReportLab no esta en requirements.txt: solo se usa
para generar documentos.
"""
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

entrada, salida = sys.argv[1], sys.argv[2]
base = getSampleStyleSheet()
normal = ParagraphStyle("n", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13)
celda = ParagraphStyle("c", parent=normal, fontSize=8, leading=10)
celda_h = ParagraphStyle("ch", parent=celda, fontName="Helvetica-Bold")
h1 = ParagraphStyle("h1", parent=base["Heading1"], fontSize=16, leading=19, spaceAfter=8)
h2 = ParagraphStyle("h2", parent=base["Heading2"], fontSize=12.5, spaceBefore=12, textColor=colors.HexColor("#1f3a5f"))
h3 = ParagraphStyle("h3", parent=base["Heading3"], fontSize=10.5, spaceBefore=8)
vineta = ParagraphStyle("v", parent=normal, leftIndent=14, bulletIndent=3)
codigo = ParagraphStyle("code", fontName="Courier", fontSize=7.5, leading=9.5,
                        backColor=colors.HexColor("#f1f1f1"), leftIndent=4, rightIndent=4, borderPadding=4)


def inline(texto):
    t = escape(texto)
    t = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return t


def partir_fila(linea):
    return [c.strip() for c in linea.strip().strip("|").split("|")]


lineas = open(entrada, encoding="utf-8").read().split("\n")
hist, i = [], 0
while i < len(lineas):
    l = lineas[i]
    if l.startswith("```"):
        j = i + 1
        bloque = []
        while not lineas[j].startswith("```"):
            bloque.append(lineas[j])
            j += 1
        hist.append(Preformatted("\n".join(bloque), codigo))
        hist.append(Spacer(1, 6))
        i = j + 1
    elif l.startswith("### "):
        hist.append(Paragraph(inline(l[4:]), h3)); i += 1
    elif l.startswith("## "):
        hist.append(Paragraph(inline(l[3:]), h2)); i += 1
    elif l.startswith("# "):
        hist.append(Paragraph(inline(l[2:]), h1)); i += 1
    elif l.startswith("|"):
        filas = []
        while i < len(lineas) and lineas[i].startswith("|"):
            if not re.match(r"^\|[\s:|-]+\|$", lineas[i]):
                filas.append(partir_fila(lineas[i]))
            i += 1
        n = max(len(f) for f in filas)
        datos = [[Paragraph(inline(c), celda_h if k == 0 else celda) for c in f + [""] * (n - len(f))]
                 for k, f in enumerate(filas)]
        ancho = letter[0] - 3.6 * cm
        tabla = Table(datos, colWidths=[ancho / n] * n, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        hist.append(tabla); hist.append(Spacer(1, 6))
    elif re.match(r"^(- |\d+\. )", l):
        m = re.match(r"^(- |(\d+)\. )(.*)", l)
        hist.append(Paragraph(inline(m.group(3)), vineta, bulletText=("•" if m.group(2) is None else m.group(2) + ".")))
        i += 1
    elif l.strip() == "":
        i += 1
    else:
        hist.append(Paragraph(inline(l), normal)); hist.append(Spacer(1, 4)); i += 1


def pie(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(letter[0] / 2, 1 * cm, f"Pagina {doc.page}")


SimpleDocTemplate(salida, pagesize=letter, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                  topMargin=1.8 * cm, bottomMargin=1.8 * cm, author="Equipo RutaMX",
                  title=Path(entrada).stem.replace("_", " ")).build(hist, onFirstPage=pie, onLaterPages=pie)
