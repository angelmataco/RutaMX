"""M-03 con Flask aislado, sin importar v1 ni cargar .env/base real."""
import json
from pathlib import Path
import re

from flask import Flask
import pytest

from v2 import registrar_v2
from v2.integracion.adaptador_ia import AdaptadorSimulado
from v2.utilerias import ErrorServicioExterno

RAIZ = Path(__file__).resolve().parents[2]
DATOS = {"origen": "Lugar A", "destino": "Lugar B", "duracion_dias": 3}
RUTA = {**DATOS, "paradas": [{"nombre": "Lugar C"}]}


class GeoFalsa:
    def verificar(self, nombre):
        return {"id": nombre, "latitud": 1.0, "longitud": 2.0}


def crear_app(fabrica=None, reloj=None):
    app = Flask(__name__, template_folder=str(RAIZ / 'v1/templates'), static_folder=str(RAIZ / 'v1/static'), static_url_path='/static')
    app.config.update(TESTING=True, SECRET_KEY='llave-ficticia-solo-pruebas')
    opciones = {"fabrica_adaptador": fabrica or (lambda: AdaptadorSimulado(extracciones=[DATOS], rutas=[RUTA])), "verificador": GeoFalsa(), "demostracion": True}
    if reloj is not None:
        opciones['reloj'] = reloj
    registrar_v2(app, **opciones)
    return app


@pytest.fixture
def cliente():
    return crear_app().test_client()


def abrir(cliente):
    respuesta = cliente.get('/v2/planear')
    assert respuesta.status_code == 200
    return re.search(r'name="rutamx-csrf" content="([^"]+)"', respuesta.text).group(1)


def post(cliente, token, accion='mensaje', datos=None):
    return cliente.post('/v2/planear/' + accion, json={'mensaje':'Viaje'} if datos is None else datos, headers={'X-RutaMX-CSRF':token})


def test_pagina_completa_y_estaticos_sin_main_v1(cliente):
    html = cliente.get('/v2/planear').text
    for texto in ['Planear con IA', 'Tu itinerario', 'role="tablist"', '<dialog', 'Modo demostración', 'spotlight.js', 'fondo.js', 'orbe.js']:
        assert texto in html
    assert 'js/main.js' not in html
    assert cliente.get('/v2/static/planear_ia.css').status_code == 200
    assert cliente.get('/v2/static/planear_ia.js').status_code == 200


def test_generacion_ruta_con_itinerario(cliente):
    token = abrir(cliente)
    r = post(cliente, token)
    assert r.status_code == 200
    assert r.json['estado'] == 'propuesta'
    assert r.json['ruta']['destino'] == 'Lugar B'
    assert r.json['itinerario'][0]['nombre'] == 'Lugar C'
    assert r.headers['Cache-Control'] == 'no-store'


def test_recarga_conserva_ruta(cliente):
    token = abrir(cliente)
    post(cliente, token)
    html = cliente.get('/v2/planear').text
    estado = json.loads(re.search(r'id="estado-inicial">(.*?)</script>', html, re.S).group(1))
    assert estado['ruta']['destino'] == 'Lugar B'


def test_falta_configuracion_muestra_mensaje_sin_simular():
    def fabrica():
        raise ErrorServicioExterno('Configura IA_V2_MODELO.')
    c = crear_app(fabrica).test_client()
    html = c.get('/v2/planear').text
    assert 'Planear con IA no está configurado' in html
    assert 'data-enviar disabled' in html
    token = abrir(c)
    assert post(c, token).status_code == 503


@pytest.mark.parametrize('datos', [None, [], {'mensaje': 'hola', 'ruta': RUTA}, {'acepta': True}, {'mensaje': 1}])
def test_no_acepta_estado_ni_formato_incorrecto(cliente, datos):
    token = abrir(cliente)
    r = cliente.post('/v2/planear/mensaje', json=datos, headers={'X-RutaMX-CSRF':token})
    assert r.status_code == 400


@pytest.mark.parametrize('token', ['', 'incorrecto', 'ñ'])
def test_csrf_rechaza_peticion_ajena(cliente, token):
    abrir(cliente)
    assert post(cliente, token).status_code == 403


def test_cuerpo_excesivo(cliente):
    token = abrir(cliente)
    assert post(cliente, token, datos={'mensaje':'a'*9000}).status_code == 413


def test_dos_sesiones_no_comparten_ruta():
    app = crear_app()
    a, b = app.test_client(), app.test_client()
    post(a, abrir(a))
    html = b.get('/v2/planear').text
    estado = json.loads(re.search(r'id="estado-inicial">(.*?)</script>', html, re.S).group(1))
    assert estado['ruta'] is None


def test_confirmacion_en_servidor_y_booleano_estricto():
    datos = {**DATOS, 'destino': 'Lugar A'}
    fabrica = lambda: AdaptadorSimulado(extracciones=[datos], rutas=[{**RUTA, 'destino':'Lugar A'}])
    c = crear_app(fabrica).test_client()
    token = abrir(c)
    assert post(c, token).json['estado'] == 'confirmar'
    assert post(c, token, 'confirmar', {'acepta':'sí'}).status_code == 400
    r = post(c, token, 'confirmar', {'acepta':True})
    assert r.json['estado'] == 'propuesta'
    assert post(c, token, 'confirmar', {'acepta':True}).json['estado'] == 'error'


def test_error_ia_conserva_ruta():
    c = crear_app(lambda: AdaptadorSimulado(extracciones=[DATOS, {'duracion_dias':4}], rutas=[RUTA, RuntimeError('secreto')])).test_client()
    token = abrir(c)
    antes = post(c, token).json
    r = post(c, token).json
    assert r['estado'] == 'error' and r['ruta'] == antes['ruta']
    assert 'secreto' not in r['mensaje']


def test_reiniciar_solo_con_csrf_y_borra_ruta(cliente):
    token = abrir(cliente)
    post(cliente, token)
    assert post(cliente, '', 'reiniciar', {}).status_code == 403
    r = post(cliente, token, 'reiniciar', {})
    assert r.json['ruta'] is None and r.json['datos'] == {}


def test_caducidad_no_recupera_ruta_anterior():
    tiempo = [0]
    c = crear_app(reloj=lambda:tiempo[0]).test_client()
    token = abrir(c)
    post(c, token)
    tiempo[0] = 1801
    html = c.get('/v2/planear').text
    estado = json.loads(re.search(r'id="estado-inicial">(.*?)</script>', html, re.S).group(1))
    assert estado['ruta'] is None


def test_limite_solicitudes_y_reinicio(cliente):
    token = abrir(cliente)
    for _ in range(60):
        assert post(cliente, token).status_code == 200
    assert post(cliente, token).status_code == 429
    assert post(cliente, token, 'reiniciar', {}).status_code == 200
    assert post(cliente, token).status_code == 200


def test_demo_solo_en_app_de_prueba():
    app = Flask(__name__)
    with pytest.raises(ValueError):
        registrar_v2(app, demostracion=True)


def test_error_inesperado_no_filtra_detalles():
    def fabrica():
        raise RuntimeError('llave-secreta')
    c = crear_app(fabrica).test_client()
    token = abrir(c)
    assert 'llave-secreta' not in c.get('/v2/planear').text
    assert 'llave-secreta' not in post(c, token).text


# Comprobación opcional en navegador real. Playwright no es dependencia de la app.
# Ejecutar este caso con Playwright disponible; geografía real solo con variable explícita.
import importlib.util
import os


@pytest.mark.skipif(importlib.util.find_spec('playwright') is None, reason='Playwright no instalado: comprobación de navegador opcional')
def test_navegador_escritorio_y_movil():
    from threading import Thread
    from werkzeug.serving import make_server
    from playwright.sync_api import sync_playwright, expect
    from v2.integracion.adaptador_ia import AdaptadorIA
    from v2.integracion.verificador_geografico import VerificadorNominatim

    class IADePrueba(AdaptadorIA):
        def __init__(self):
            self.fallar = False

        def _solicitar(self, operacion, datos):
            if operacion == 'extraer_datos':
                mensaje = datos['mensaje'].casefold()
                if 'fallo de prueba' in mensaje:
                    self.fallar = True
                    return {'duracion_dias': 4}
                if 'intenta otra vez' in mensaje:
                    return {}
                if 'ida y vuelta' in mensaje:
                    return {'origen': 'Ciudad de México', 'destino': 'Ciudad de México', 'duracion_dias': 3}
                if 'oaxaca' in mensaje:
                    return {'destino': 'Oaxaca', 'duracion_dias': 3}
                return {'origen': 'Ciudad de México'}
            if self.fallar:
                self.fallar = False
                raise ErrorServicioExterno('Fallo de prueba. Intenta de nuevo; tu ruta se conserva.')
            return {**datos, 'paradas': [] if datos['origen'] == datos['destino'] else [{'nombre': 'Puebla', 'descripcion': 'Parada de prueba'}]}

    app = Flask(__name__, template_folder=str(RAIZ/'v1/templates'), static_folder=str(RAIZ/'v1/static'), static_url_path='/static')
    app.config.update(TESTING=True, SECRET_KEY='llave-ficticia-navegador')
    real = os.environ.get('RUTAMX_NAVEGADOR_GEO_REAL') == '1'
    registrar_v2(app, fabrica_adaptador=IADePrueba,
                 verificador=VerificadorNominatim() if real else GeoFalsa(), demostracion=True)
    servidor = make_server('127.0.0.1', 0, app, threaded=True)
    hilo = Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch()
            try:
                pagina = navegador.new_page(viewport={'width':1280, 'height':900})
                errores = []
                pagina.on('pageerror', lambda error: errores.append(str(error)))
                pagina.goto(f'http://127.0.0.1:{servidor.server_port}/v2/planear')
                expect(pagina.get_by_text('Modo demostración: respuestas de prueba')).to_be_visible()
                expect(pagina.locator('.fondo-rutas')).to_have_count(1)
                expect(pagina.locator('.navbar')).to_have_css('position','fixed')
                expect(pagina.get_by_role('heading', name='Tu itinerario aparecerá aquí')).to_be_visible()
                campo = pagina.get_by_label('Describe tu viaje')

                def enviar(texto):
                    campo.fill(texto)
                    pagina.get_by_role('button', name='Enviar').click()
                    expect(pagina.locator('[data-formulario]')).to_have_attribute('aria-busy','false', timeout=60000)

                enviar('Salgo de Ciudad de México')
                expect(pagina.locator('[data-mensajes]')).to_contain_text('destino, duración en días')
                enviar('Voy a Oaxaca durante tres días')
                expect(pagina.locator('[data-itinerario]')).to_contain_text('Puebla', timeout=60000)
                itinerario = pagina.locator('[data-itinerario]').inner_text()
                enviar('Fallo de prueba')
                expect(pagina.locator('[data-error]')).to_contain_text('Fallo de prueba')
                assert pagina.locator('[data-itinerario]').inner_text() == itinerario
                enviar('Intenta otra vez')
                expect(pagina.locator('[data-itinerario]')).to_contain_text('4 días')
                enviar('Ida y vuelta')
                expect(pagina.locator('dialog')).to_be_visible()
                expect(pagina.locator('[data-no]')).to_be_focused()
                pagina.keyboard.press('Tab')
                expect(pagina.locator('[data-si]')).to_be_focused()
                pagina.keyboard.press('Escape')
                expect(pagina.locator('dialog')).not_to_be_visible()
                expect(pagina.locator('[data-formulario]')).to_have_attribute('aria-busy','false')
                expect(campo).to_be_focused()
                enviar('Ida y vuelta')
                pagina.get_by_role('button', name='Sí, confirmo').click()
                expect(pagina.locator('[data-formulario]')).to_have_attribute('aria-busy','false')
                expect(pagina.locator('[data-itinerario]')).to_contain_text('Sin paradas intermedias.')
                expect(pagina.locator('dialog')).not_to_be_visible()
                assert not pagina.evaluate('document.documentElement.scrollWidth > innerWidth')
                carpeta = os.environ.get('RUTAMX_CAPTURAS')
                if carpeta:
                    pagina.screenshot(path=str(Path(carpeta)/'escritorio.png'), full_page=True)
                pagina.set_viewport_size({'width':375,'height':812})
                pagina.evaluate('window.scrollTo(0,0)')
                expect(pagina.get_by_role('tab', name='Conversación')).to_be_visible()
                expect(pagina.locator('#itinerario')).not_to_be_visible()
                pagina.get_by_role('tab', name='Conversación').focus()
                pagina.keyboard.press('ArrowRight')
                expect(pagina.get_by_role('tab', name='Itinerario')).to_be_focused()
                expect(pagina.locator('#itinerario')).to_be_visible()
                expect(pagina.locator('#ruta')).not_to_be_visible()
                assert not pagina.evaluate('document.documentElement.scrollWidth > innerWidth')
                if carpeta:
                    pagina.screenshot(path=str(Path(carpeta)/'movil.png'), full_page=True)
                pagina.keyboard.press('ArrowLeft')
                expect(pagina.locator('#ruta')).to_be_visible()
                # El borrador nuevo permanece mientras una petición está en curso.
                pagina.route('**/v2/planear/mensaje', lambda ruta: ( __import__('time').sleep(.3), ruta.continue_()))
                campo.fill('Intenta otra vez')
                pagina.get_by_role('button', name='Enviar').click()
                campo.fill('Borrador que sigo escribiendo')
                expect(pagina.locator('[data-formulario]')).to_have_attribute('aria-busy','false',timeout=60000)
                expect(campo).to_have_value('Borrador que sigo escribiendo')
                pagina.emulate_media(reduced_motion='reduce')
                assert pagina.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
                assert not errores, errores
                print('Navegador: Chromium 1280x900 y 375x812; faltantes/propuesta/error/reintento/confirmar/Tab/Esc/pestañas/borrador/reducir movimiento sin errores JS. Geografía:', 'Nominatim real' if real else 'simulada')
            finally:
                navegador.close()
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=5)
        assert not hilo.is_alive()


def test_factoría_raiz_registra_v2_sin_import_en_v1():
    # Ejecuta solo la factoría de composición; evita la app global y config real.
    import ast
    codigo = ast.parse((RAIZ/'run.py').read_text())
    funcion = next(n for n in codigo.body if isinstance(n, ast.FunctionDef) and n.name == 'create_app')
    nombres = []
    def crear_v1(nombre):
        nombres.append(nombre)
        return Flask('prueba_composicion')
    espacio = {'crear_app_v1':crear_v1, 'registrar_v2':registrar_v2}
    exec(compile(ast.Module(body=[funcion], type_ignores=[]), 'factoría_prueba', 'exec'), espacio)
    app = espacio['create_app']('prueba')
    assert nombres == ['prueba']
    assert 'planear_v2' in app.blueprints
    assert not any(isinstance(n, ast.ImportFrom) and n.module and n.module.startswith('v2') for n in ast.walk(ast.parse((RAIZ/'v1/__init__.py').read_text())))
