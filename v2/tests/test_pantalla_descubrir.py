"""M-01 Descubrir: render de la plantilla REAL de /v2/descubrir.

A diferencia de test_interfaz_descubrir.py (que sustituye la plantilla por una
cadena), aquí se usan las plantillas de verdad con las de v1 (navbar, iconos,
estilos) y los recursos estáticos reales. Sin base, sin red y con datos
ficticios: el catálogo es el servicio real con un repositorio falso.
"""
import re
from pathlib import Path

from flask import Flask
import pytest

from base_datos.catalogo_valores import CATEGORIAS, REGIONES
from v2 import registrar_v2
from v2.negocio.catalogo import Catalogo
from v2.negocio.guardado_rutas import GuardadoRutas

RAIZ = Path(__file__).resolve().parents[2]


class RepoVacio:
    def listar_publicas(self, **filtros):
        return []

    def obtener_publica(self, ruta_id):
        return None


class GuardadoFalso(GuardadoRutas):
    def __init__(self):
        pass


@pytest.fixture(scope="module")
def html():
    app = Flask(
        __name__,
        template_folder=str(RAIZ / "v1" / "templates"),
        static_folder=str(RAIZ / "v1" / "static"),
    )
    app.config.update(TESTING=True, SECRET_KEY="llave-ficticia-solo-pruebas")
    registrar_v2(app, demostracion=True, guardado=GuardadoFalso(), catalogo=Catalogo(RepoVacio()))
    respuesta = app.test_client().get("/v2/descubrir")
    assert respuesta.status_code == 200
    return respuesta.get_data(as_text=True)


def test_plantilla_real_responde_200_con_titulo_y_catalogo(html):
    assert "<title>Descubrir" in html
    assert 'data-catalogo-lista' in html and 'data-catalogo-estado' in html


def test_anclas_internas_tienen_destino_en_la_pagina(html):
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    for ancla in re.findall(r'href="#([^"]+)"', html):
        assert ancla in ids, f"el ancla #{ancla} no tiene destino"


def test_recursos_locales_se_sirven_y_no_son_externos_salvo_fuentes(html):
    for ruta in re.findall(r'(?:src|href)="(/[^"#]+\.(?:css|js|svg))"', html):
        assert ruta.startswith(("/static/", "/v2/")), ruta
    externos = re.findall(r'<(?:script|link)[^>]+(?:src|href)="(https?://[^"]+)"', html)
    assert all(url.startswith("https://fonts.googleapis.com/") for url in externos), externos


def test_recursos_locales_responden_200():
    app = Flask(
        __name__,
        template_folder=str(RAIZ / "v1" / "templates"),
        static_folder=str(RAIZ / "v1" / "static"),
    )
    app.config.update(TESTING=True, SECRET_KEY="llave-ficticia-solo-pruebas")
    registrar_v2(app, demostracion=True, guardado=GuardadoFalso(), catalogo=Catalogo(RepoVacio()))
    cliente = app.test_client()
    texto = cliente.get("/v2/descubrir").get_data(as_text=True)
    rutas = re.findall(r'(?:src|href)="(/[^"#]+\.(?:css|js|svg))"', texto)
    assert any(r.endswith("descubrir.js") for r in rutas) and any(r.endswith("descubrir.css") for r in rutas)
    for ruta in rutas:
        assert cliente.get(ruta).status_code == 200, ruta


def test_opciones_de_categoria_y_region_vienen_del_catalogo(html):
    def opciones(nombre):
        bloque = re.search(rf'<select name="{nombre}">(.*?)</select>', html, re.S).group(1)
        return re.findall(r'<option value="([^"]*)"', bloque)
    assert opciones("categoria") == [""] + list(CATEGORIAS)
    assert opciones("region") == [""] + list(REGIONES)


def test_elementos_data_que_usa_el_js_existen(html):
    js = (RAIZ / "v2" / "static" / "descubrir.js").read_text(encoding="utf-8")
    usados = set(re.findall(r"\[(data-[a-z-]+)\]", js))
    assert usados, "el JS ya no busca elementos data-*"
    for atributo in usados:
        assert atributo in html, f"el JS busca [{atributo}] y la plantilla no lo tiene"


def test_js_no_usa_innerhtml():
    js = (RAIZ / "v2" / "static" / "descubrir.js").read_text(encoding="utf-8")
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js


def test_detalle_incluye_copia_sesion_y_csrf(html):
    assert re.search(r'<meta name="rutamx-csrf" content="[^"]+">', html)
    dialogo = re.search(r'<dialog\b.*?</dialog>', html, re.S).group(0)
    assert 'data-copiar-ruta' in dialogo and 'Copiar a mis rutas' in dialogo
    assert 'data-copia-estado' in dialogo and 'aria-live="polite"' in dialogo
    assert 'data-copia-sesion' in dialogo and 'href="/" target="_blank" rel="noopener"' in dialogo
    assert 'href="/v2/rutas" data-copia-lista hidden' in dialogo


def test_detalle_incluye_bloque_del_mapa_con_avisos_accesibles(html):
    dialogo = re.search(r'<dialog\b.*?</dialog>', html, re.S).group(0)
    assert 'data-mapa-bloque' in dialogo and '>Recorrido<' in dialogo
    assert re.search(r'role="status"[^>]*data-mapa-estado', dialogo)
    assert 'data-mapa' in dialogo and 'role="img"' in dialogo
    assert 'la línea no representa el trayecto por carretera' in dialogo
    # El bloque va entre el estado del detalle y el contenido, y el botón de copiar queda fuera del mapa.
    assert dialogo.index('data-detalle-estado') < dialogo.index('data-mapa-bloque') < dialogo.index('data-detalle-contenido')
    mapa = re.search(r'<section[^>]*data-mapa-bloque.*?</section>', dialogo, re.S).group(0)
    assert 'data-copiar-ruta' not in mapa


def test_js_carga_leaflet_del_mismo_cdn_que_v1_y_solo_bajo_demanda(html):
    js = (RAIZ / "v2" / "static" / "descubrir.js").read_text(encoding="utf-8")
    base = (RAIZ / "v1" / "templates" / "base.html").read_text(encoding="utf-8")
    for url in ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css", "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"):
        assert url in js and url in base
    assert "leaflet" not in html.lower().replace("data-", "")  # diferido: la página no lo carga de inicio


def test_js_del_mapa_trae_los_textos_acordados():
    js = (RAIZ / "v2" / "static" / "descubrir.js").read_text(encoding="utf-8")
    for texto in ("Cargando mapa…", "El mapa no pudo cargarse. El resto de la ruta sigue disponible.",
                  "Esta ruta no tiene ubicaciones para mostrar en el mapa.", "sin coordenadas válidas"):
        assert texto in js
    for contrato in ("invalidateSize", "mapa.remove()", "fitBounds", "padding: [24, 24]", "--color-terracota"):
        assert contrato in js


def test_css_del_mapa_tiene_alto_fijo_de_escritorio_y_movil():
    css = (RAIZ / "v2" / "static" / "descubrir.css").read_text(encoding="utf-8")
    assert re.search(r"\.descubrir-mapa \{[^}]*height: 260px", css)
    assert re.search(r"@media \(max-width: 600px\) \{ \.descubrir-mapa \{ height: 200px; \} \}", css)


def test_js_del_mapa_protege_contra_mapas_viejos_y_espera_css_y_js():
    js = (RAIZ / "v2" / "static" / "descubrir.js").read_text(encoding="utf-8")
    # Cada mapa actúa solo sobre su propia instancia y solo mientras sea el vigente.
    assert "const propio = window.L.map" in js and "if (mapa !== propio) return;" in js
    assert "falloDelMapa(propio)" in js and "instancia !== mapa" in js
    # La carga espera estilos y script; el fallo de cualquiera es RF-12.
    assert "estilos.onload" in js and "estilos.onerror" in js and "listos === necesarios" in js
    # window.L solo prueba que el script existe: el éxito depende de una bandera con ambas cargas.
    assert "leafletCompleto && window.L" in js and "leafletCompleto = true" in js
