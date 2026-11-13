"""M-01 Descubrir: página y endpoints públicos del catálogo.

Flask aislado, M-02 real con un repositorio falso en memoria; sin base ni red.
Comprueban que es abierto a visitantes, los filtros (normal, límite y error),
el mensaje sin resultados, el 404 igual para privada e inexistente, los
errores seguros y que un fallo del catálogo no rompe el resto de v2.
Todos los datos son ficticios.
"""
from copy import deepcopy

from flask import Flask
from jinja2 import DictLoader
import pytest

from base_datos.catalogo_valores import CATEGORIAS, REGIONES
from base_datos.repositorios.catalogo_repositorio import ErrorMigracionPendiente
from v2 import registrar_v2
from v2.negocio.catalogo import Catalogo, ErrorCatalogo
from v2.negocio.guardado_rutas import GuardadoRutas


def fila(id, **cambios):
    datos = {
        "id": id, "nombre": f"Ruta {id}", "origen": "Lugar A", "destino": "Lugar B",
        "duracion_dias": 3, "categoria": "Playa", "region": "Centro", "num_paradas": 2,
        "es_rutamx": False, "autor": {"nombre": "Ana", "inicial_apellido": "F"},
        "descripcion": "Texto ficticio", "paradas": [{"nombre": "Parada 1"}, {"nombre": "Parada 2"}],
        "publica": True,
    }
    datos.update(cambios)
    return datos


class RepoFalso:
    def __init__(self, filas=()):
        self.filas = list(filas)
        self.llamadas = []
        self.falla = None

    def listar_publicas(self, palabra_clave=None, duracion_dias=None, categoria=None, region=None):
        self.llamadas.append((palabra_clave, duracion_dias, categoria, region))
        if self.falla:
            raise self.falla
        salida = []
        for f in self.filas:
            if not f["publica"]:
                continue
            if palabra_clave and palabra_clave.lower() not in f["nombre"].lower():
                continue
            if duracion_dias and f["duracion_dias"] != duracion_dias:
                continue
            if categoria and f["categoria"] != categoria:
                continue
            if region and f["region"] != region:
                continue
            salida.append(deepcopy(f))
        return salida

    def obtener_publica(self, ruta_id):
        if self.falla:
            raise self.falla
        for f in self.filas:
            if f["id"] == ruta_id and f["publica"]:
                return deepcopy(f)
        return None


class GuardadoFalso(GuardadoRutas):
    def __init__(self):
        pass


def crear_app(catalogo):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="llave-ficticia-solo-pruebas")
    app.jinja_loader = DictLoader({
        "planear_ia.html": '<meta name="rutamx-csrf" content="{{ csrf }}">',
        "rutas_guardadas.html": "guardadas",
        "descubrir.html": "cats={{ categorias|join(',') }};regs={{ regiones|join(',') }}",
    })
    registrar_v2(app, demostracion=True, guardado=GuardadoFalso(), catalogo=catalogo)
    return app


@pytest.fixture
def repo():
    return RepoFalso([
        fila(1), fila(2, nombre="Cultural larga", categoria="Cultural", duracion_dias=7, region="Sureste"),
        fila(3, nombre="Oficial", es_rutamx=True, autor=None), fila(4, nombre="Privada", publica=False),
    ])


@pytest.fixture
def cliente(repo):
    return crear_app(Catalogo(repo)).test_client()


# ------------------------------------------------------------------ página

def test_pagina_abierta_a_visitantes_sin_sesion(cliente):
    respuesta = cliente.get("/v2/descubrir")
    assert respuesta.status_code == 200
    assert ",".join(CATEGORIAS) in respuesta.text and ",".join(REGIONES) in respuesta.text
    assert respuesta.headers["Cache-Control"] == "no-store"


# ------------------------------------------------------------------- lista

def test_lista_solo_publicas_con_total_y_sin_mensaje(cliente):
    cuerpo = cliente.get("/v2/descubrir/rutas").json
    assert [r["id"] for r in cuerpo["rutas"]] == [1, 2, 3] and cuerpo["total"] == 3
    assert "mensaje" not in cuerpo


def test_lista_entrega_autor_legible_y_rutamx(cliente):
    rutas = {r["id"]: r for r in cliente.get("/v2/descubrir/rutas").json["rutas"]}
    assert rutas[1]["autor"] == "Ana F." and rutas[3]["autor"] == "RutaMx" and rutas[3]["es_rutamx"] is True


def test_lista_no_expone_campos_privados(cliente):
    for ruta in cliente.get("/v2/descubrir/rutas").json["rutas"]:
        assert not {"publica", "usuario_id", "autor_id", "descripcion", "paradas"} & set(ruta)


def test_filtros_por_texto_duracion_categoria_y_region(cliente):
    def ids(consulta):
        return [r["id"] for r in cliente.get("/v2/descubrir/rutas" + consulta).json["rutas"]]
    assert ids("?q=cultural") == [2]
    assert ids("?duracion=7") == [2]
    assert ids("?categoria=Cultural") == [2]
    assert ids("?region=Sureste") == [2]
    assert ids("?q=ruta&duracion=3&categoria=Playa&region=Centro") == [1]


def test_filtros_vacios_equivalen_a_sin_filtro(cliente, repo):
    assert cliente.get("/v2/descubrir/rutas?q=&duracion=&categoria=&region=").json["total"] == 3
    assert repo.llamadas[-1] == (None, None, None, None)


def test_sin_resultados_da_lista_vacia_y_mensaje(cliente):
    respuesta = cliente.get("/v2/descubrir/rutas?q=nada-coincide")
    assert respuesta.status_code == 200
    assert respuesta.json["rutas"] == [] and respuesta.json["total"] == 0
    assert "No hay rutas" in respuesta.json["mensaje"]


def test_ruta_privada_nunca_aparece_ni_con_su_nombre(cliente):
    assert cliente.get("/v2/descubrir/rutas?q=privada").json["rutas"] == []


@pytest.mark.parametrize("consulta", [
    "?duracion=abc", "?duracion=-1", "?duracion=3.5", "?duracion=0", "?duracion=61", "?duracion=1000",
    "?duracion=" + "9" * 5000, "?categoria=Inventada", "?categoria=playa", "?region=Marte",
    "?q=" + "x" * 81,
])
def test_filtros_invalidos_dan_400_sin_consultar(cliente, repo, consulta):
    respuesta = cliente.get("/v2/descubrir/rutas" + consulta)
    assert respuesta.status_code == 400 and respuesta.json["error"]
    assert repo.llamadas == []


def test_limites_validos_se_aceptan(cliente):
    assert cliente.get("/v2/descubrir/rutas?duracion=60&q=" + "x" * 80).status_code == 200
    assert cliente.get("/v2/descubrir/rutas?duracion=1").status_code == 200


def test_texto_hostil_en_la_busqueda_no_rompe_ni_se_refleja(cliente):
    respuesta = cliente.get("/v2/descubrir/rutas?q=<script>alert(1)</script>")
    assert respuesta.status_code == 200 and "<script>" not in respuesta.text


# ----------------------------------------------------------------- detalle

def test_detalle_de_ruta_publica(cliente):
    ruta = cliente.get("/v2/descubrir/rutas/1").json["ruta"]
    assert ruta["nombre"] == "Ruta 1" and ruta["descripcion"] == "Texto ficticio"
    assert [p["orden"] for p in ruta["paradas"]] == [1, 2]
    assert not {"publica", "usuario_id", "autor_id"} & set(ruta)


def test_privada_e_inexistente_dan_el_mismo_404(cliente):
    privada, inexistente = cliente.get("/v2/descubrir/rutas/4"), cliente.get("/v2/descubrir/rutas/999")
    assert privada.status_code == inexistente.status_code == 404
    assert privada.json == inexistente.json


@pytest.mark.parametrize("identificador", ["abc", "0x1", "-1", "1.5", "1e3", "1" * 10, "%3Cscript%3E"])
def test_identificador_invalido_da_400(cliente, identificador):
    respuesta = cliente.get("/v2/descubrir/rutas/" + identificador)
    assert respuesta.status_code in (400, 404) and respuesta.json["error"]


def test_identificador_cero_no_existe(cliente):
    assert cliente.get("/v2/descubrir/rutas/0").status_code == 400


# ----------------------------------------------------------------- errores

def test_migracion_pendiente_da_503_claro_en_lista_y_detalle(cliente, repo):
    repo.falla = ErrorMigracionPendiente("detalle interno con SQL")
    for url in ("/v2/descubrir/rutas", "/v2/descubrir/rutas/1"):
        respuesta = cliente.get(url)
        assert respuesta.status_code == 503
        assert "migración" in respuesta.json["error"] and "SQL" not in respuesta.json["error"]


def test_otro_fallo_da_503_sin_detalles(cliente, repo):
    repo.falla = RuntimeError("postgresql://usuario:clave@host/db")
    for url in ("/v2/descubrir/rutas", "/v2/descubrir/rutas/1"):
        respuesta = cliente.get(url)
        assert respuesta.status_code == 503
        assert "clave" not in respuesta.text and "postgresql" not in respuesta.text


class CatalogoRoto:
    def listar(self, **_):
        raise ZeroDivisionError("bug interno")

    def detalle(self, _):
        raise ErrorCatalogo("Falla controlada del catálogo.")


def test_errores_inesperados_del_servicio_se_ocultan():
    cliente = crear_app(CatalogoRoto()).test_client()
    lista = cliente.get("/v2/descubrir/rutas")
    assert lista.status_code == 503 and "bug interno" not in lista.text
    detalle = cliente.get("/v2/descubrir/rutas/1")
    assert detalle.status_code == 503 and detalle.json["error"] == "Falla controlada del catálogo."


def test_un_catalogo_caido_no_rompe_el_resto_de_v2(repo):
    repo.falla = RuntimeError("caído")
    cliente = crear_app(Catalogo(repo)).test_client()
    assert cliente.get("/v2/descubrir/rutas").status_code == 503
    assert cliente.get("/v2/planear").status_code == 200
    assert cliente.get("/v2/rutas").status_code == 200


# ----------------------------------------------------------- solo lectura

@pytest.mark.parametrize("metodo", ["post", "put", "delete", "patch"])
@pytest.mark.parametrize("url", ["/v2/descubrir/rutas", "/v2/descubrir/rutas/1", "/v2/descubrir"])
def test_los_endpoints_son_de_solo_lectura(cliente, metodo, url):
    assert getattr(cliente, metodo)(url).status_code == 405


def test_no_pide_sesion_aunque_exista_otra(cliente):
    with cliente.session_transaction() as sesion:
        sesion["usuario_id"] = 5
    assert cliente.get("/v2/descubrir/rutas").json["total"] == 3
