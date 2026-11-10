"""Demostración de Planear con IA (v2) SIN llave de IA: respuestas de prueba.

    venv/bin/python scripts/demo_planear_v2.py            # http://127.0.0.1:5055/v2/planear
    RUTAMX_DEMO_GEO_REAL=0 venv/bin/python scripts/demo_planear_v2.py   # sin red

La IA es un simulado con reglas fijas (no entiende lenguaje natural): reconoce
«de X a Y» o «salgo de X», «a Y» y «N días». La página muestra la franja
«Modo demostración: respuestas de prueba». Los lugares se validan con
Nominatim real salvo que RUTAMX_DEMO_GEO_REAL=0. No usa la base de datos, el
.env ni la IA real; la app normal (`run.py`) no usa nada de este archivo.
"""

import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from flask import Flask  # noqa: E402

from v2 import registrar_v2  # noqa: E402
from v2.integracion.adaptador_ia import AdaptadorIA  # noqa: E402
from v2.integracion.verificador_geografico import VerificadorNominatim  # noqa: E402

PUERTO = 5055
PARADAS_CONOCIDAS = {
    ("ciudad de méxico", "oaxaca"): [
        {"nombre": "Puebla", "descripcion": "Parada de prueba"},
        {"nombre": "Tehuacán", "descripcion": "Parada de prueba"},
    ],
}


class IAReglas(AdaptadorIA):
    """Simulado con reglas fijas; nunca consulta a un modelo."""

    def _solicitar(self, operacion, datos):
        if operacion == "generar_ruta":
            clave = (datos["origen"].casefold(), datos["destino"].casefold())
            return {**datos, "paradas": PARADAS_CONOCIDAS.get(clave, [])}
        texto = datos["mensaje"]
        salida = {}
        de_a = re.search(r"\bde\s+(.+?)\s+a\s+(.+?)(?:\s+(?:en|por|durante)\b|[,.]|$)", texto, re.I)
        if de_a:
            salida["origen"], salida["destino"] = de_a.group(1).strip(), de_a.group(2).strip()
        else:
            salgo = re.search(r"\bsalgo\s+de\s+(.+?)(?:[,.]|$)", texto, re.I)
            voy = re.search(r"\b(?:voy\s+a|a)\s+(.+?)(?:\s+(?:en|por|durante)\b|[,.]|$)", texto, re.I)
            if salgo:
                salida["origen"] = salgo.group(1).strip()
            if voy and not salgo:
                salida["destino"] = voy.group(1).strip()
            elif voy and salgo:
                salida["destino"] = voy.group(1).strip()
        dias = re.search(r"(\d{1,2})\s*d[ií]as?", texto, re.I)
        if dias:
            salida["duracion_dias"] = int(dias.group(1))
        return salida


def crear_app():
    app = Flask(
        "demo_planear_v2",
        template_folder=str(RAIZ / "v1" / "templates"),
        static_folder=str(RAIZ / "v1" / "static"),
        static_url_path="/static",
    )
    app.config.update(TESTING=True, SECRET_KEY="llave-ficticia-solo-demostracion")
    if os.environ.get("RUTAMX_DEMO_GEO_REAL", "1") == "0":
        class GeoFalsa:
            def verificar(self, nombre):
                return {"id": nombre.casefold(), "latitud": 19.0, "longitud": -99.0}
        verificador = GeoFalsa()
    else:
        verificador = VerificadorNominatim()
    registrar_v2(app, fabrica_adaptador=IAReglas, verificador=verificador, demostracion=True)
    return app


if __name__ == "__main__":
    print(f"Demostración (IA simulada): http://127.0.0.1:{PUERTO}/v2/planear")
    crear_app().run(host="127.0.0.1", port=PUERTO, debug=False)
