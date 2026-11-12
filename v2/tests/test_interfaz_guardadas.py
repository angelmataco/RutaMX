"""M-03/M-06/M-10: guardar, listar y abrir rutas con sesión obligatoria.

Flask aislado, repositorio falso en memoria, IA y geografía simuladas; sin
base ni red. La sesión de v1 se simula escribiendo `usuario_id` en la cookie
firmada (así lo hace la autenticación existente).
"""
from copy import deepcopy
from pathlib import Path
import re

from flask import Flask
from jinja2 import DictLoader
import pytest

from v2 import registrar_v2
from v2.integracion.adaptador_ia import AdaptadorSimulado
from v2.negocio.guardado_rutas import GuardadoRutas

RAIZ = Path(__file__).resolve().parents[2]
DATOS = {"origen": "Lugar A", "destino": "Lugar B", "duracion_dias": 3}
RUTA = {**DATOS, "paradas": [{"nombre": "Lugar C"}]}
OTRA = {"origen": "Lugar X", "destino": "Lugar Y", "duracion_dias": 2}
RUTA_OTRA = {**OTRA, "paradas": []}


class GeoFalsa:
    def verificar(self, nombre):
        return {"id": nombre, "latitud": 1.0, "longitud": 2.0}


class RepoFalso:
    """Mismo contrato que M-09: solo el dueño ve y cambia su fila."""

    def __init__(self):
        self.filas = {}
        self.siguiente = 1
        self.falla = None

    def _fallar(self):
        if self.falla:
            raise RuntimeError(self.falla)

    def crear_ruta(self, datos, usuario_id):
        self._fallar()
        fila = {**deepcopy(datos), "id": self.siguiente, "usuario_id": usuario_id,
                "presupuesto": None}
        self.filas[self.siguiente] = fila
        self.siguiente += 1
        return deepcopy(fila)

    def actualizar_ruta(self, ruta_id, datos, usuario_id):
        self._fallar()
        fila = self.filas.get(ruta_id)
        if fila is None or fila["usuario_id"] != usuario_id:
            return None
        fila.update(deepcopy(datos))
        return deepcopy(fila)

    def obtener_ruta(self, ruta_id, usuario_id):
        self._fallar()
        fila = self.filas.get(ruta_id)
        return deepcopy(fila) if fila and fila["usuario_id"] == usuario_id else None

    def listar_rutas_de_usuario(self, usuario_id):
        self._fallar()
        return [deepcopy(f) for f in reversed(list(self.filas.values()))
                if f["usuario_id"] == usuario_id]


def adaptador_normal():
    return AdaptadorSimulado(
        extracciones=[DATOS, {}, {}], rutas=[RUTA],
        modificaciones=[{"accion": "agregar_parada", "nombre": "Lugar D"}])


def crear_app(repo, fabrica=adaptador_normal):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="llave-ficticia-solo-pruebas")
    app.jinja_loader = DictLoader({
        "planear_ia.html": '<meta name="rutamx-csrf" content="{{ csrf }}">',
        "rutas_guardadas.html": '<meta name="rutamx-csrf" content="{{ csrf }}">sesion={{ con_sesion }}',
    })
    registrar_v2(app, fabrica_adaptador=fabrica, verificador=GeoFalsa(), demostracion=True,
                 guardado=GuardadoRutas(repo))
    return app


@pytest.fixture
def repo():
    return RepoFalso()


@pytest.fixture
def cliente(repo):
    return crear_app(repo).test_client()


def iniciar_sesion(cliente, usuario_id):
    with cliente.session_transaction() as sesion:
        sesion["usuario_id"] = usuario_id


def cerrar_sesion(cliente):
    with cliente.session_transaction() as sesion:
        sesion.pop("usuario_id", None)


def abrir_pagina(cliente):
    respuesta = cliente.get("/v2/planear")
    assert respuesta.status_code == 200
    return re.search(r'name="rutamx-csrf" content="([^"]+)"', respuesta.text).group(1)


def accion(cliente, token, nombre, datos):
    return cliente.post("/v2/planear/" + nombre, json=datos, headers={"X-RutaMX-CSRF": token})


def mensaje(cliente, token, texto="Viaje"):
    return accion(cliente, token, "mensaje", {"mensaje": texto})


def guardar(cliente, token, nombre=None):
    return accion(cliente, token, "guardar", {"nombre": nombre})


def abrir(cliente, token, ruta_id):
    return accion(cliente, token, "abrir", {"id": ruta_id})


def con_ruta(cliente):
    token = abrir_pagina(cliente)
    assert mensaje(cliente, token).json["estado"] == "propuesta"
    return token


# --- RF-41 / HU-23: sin sesión se pide iniciar sesión ---

def test_anonimo_no_guarda_ni_lista_ni_abre_y_se_le_pide_sesion(cliente, repo):
    token = con_ruta(cliente)
    for respuesta in (guardar(cliente, token), abrir(cliente, token, 1),
                      cliente.get("/v2/rutas/lista")):
        assert respuesta.status_code == 401
        assert respuesta.json["requiere_sesion"] is True
        assert "sesión" in respuesta.json["error"]
    assert repo.filas == {}


@pytest.mark.parametrize("valor", [None, "1", 0, -3, 1.5, True, [1]])
def test_usuario_de_sesion_invalido_cuenta_como_anonimo(cliente, repo, valor):
    token = con_ruta(cliente)
    with cliente.session_transaction() as sesion:
        sesion["usuario_id"] = valor
    assert guardar(cliente, token).status_code == 401
    assert cliente.get("/v2/rutas/lista").status_code == 401
    assert repo.filas == {}


# --- RF-38, RF-39: guardar asocia la ruta al usuario de la sesión ---

def test_guardar_crea_la_ruta_del_usuario_de_la_sesion(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    r = guardar(cliente, token, "Mi viaje")
    assert r.status_code == 200
    assert r.json["estado"] == "guardada" and r.json["actualizada"] is False
    assert r.json["ruta_guardada"] == {"id": 1, "nombre": "Mi viaje"}
    assert repo.filas[1]["usuario_id"] == 7
    assert repo.filas[1]["resumen"]["rutamx_v2"]["ruta"]["destino"] == "Lugar B"


def test_nombre_por_defecto(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    assert guardar(cliente, token).json["ruta_guardada"]["nombre"] == "Lugar A a Lugar B"


def test_el_navegador_no_puede_elegir_al_dueno(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    r = accion(cliente, token, "guardar", {"nombre": None, "usuario_id": 99})
    assert r.status_code == 400
    assert repo.filas == {}


def test_guardar_sin_ruta_no_crea_nada(cliente, repo):
    token = abrir_pagina(cliente)
    iniciar_sesion(cliente, 7)
    r = guardar(cliente, token)
    assert r.status_code == 409
    assert repo.filas == {}


def test_guardar_exige_csrf_y_formato(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    assert cliente.post("/v2/planear/guardar", json={"nombre": None}).status_code == 403
    assert accion(cliente, token, "guardar", {}).status_code == 400
    assert accion(cliente, token, "guardar", {"nombre": 5}).status_code == 400
    assert accion(cliente, token, "abrir", {"id": "1"}).status_code == 400
    assert accion(cliente, token, "abrir", {"id": True}).status_code == 400
    assert repo.filas == {}


# --- CA-21.4 / D-11: guardar -> modificar -> guardar -> recuperar, misma fila ---

def test_guardar_modificar_guardar_recuperar_misma_fila(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    assert guardar(cliente, token, "Mi viaje").json["actualizada"] is False

    r = mensaje(cliente, token, "agrega Lugar D")
    assert [p["nombre"] for p in r.json["ruta"]["paradas"]] == ["Lugar C", "Lugar D"]

    segundo = guardar(cliente, token)
    assert segundo.json["actualizada"] is True
    assert segundo.json["ruta_guardada"] == {"id": 1, "nombre": "Mi viaje"}  # conserva el nombre
    assert len(repo.filas) == 1

    lista = cliente.get("/v2/rutas/lista").json["rutas"]
    assert [(f["id"], f["paradas"], f["compatible"]) for f in lista] == [(1, 2, True)]

    abierta = abrir(cliente, token, 1)
    assert abierta.status_code == 200
    assert [p["nombre"] for p in abierta.json["ruta"]["paradas"]] == ["Lugar C", "Lugar D"]


# --- Abrir INSTALA la ruta en el estado del servidor ---

def test_abrir_instala_la_ruta_en_el_servidor_y_guardar_actualiza_esa_fila(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    guardar(cliente, token)

    # Otra sesión de navegador (conversación vacía) del mismo usuario. Su IA
    # solo sabe agregar una parada: no puede "inventar" la ruta instalada.
    def ia_de_modificaciones():
        return AdaptadorSimulado(
            extracciones=[{}], modificaciones=[{"accion": "agregar_parada", "nombre": "Lugar D"}])

    otro = crear_app(repo, ia_de_modificaciones).test_client()
    iniciar_sesion(otro, 7)
    token2 = abrir_pagina(otro)
    abierta = abrir(otro, token2, 1)
    assert abierta.json["estado"] == "propuesta"
    assert abierta.json["ruta"]["destino"] == "Lugar B"

    # El estado vive en el servidor: un nuevo mensaje opera sobre la ruta
    # instalada (no sobre una conversación vacía).
    r = mensaje(otro, token2, "agrega Lugar D")
    assert r.json["estado"] == "propuesta"
    assert [p["nombre"] for p in r.json["ruta"]["paradas"]] == ["Lugar C", "Lugar D"]
    assert guardar(otro, token2).json["actualizada"] is True
    assert len(repo.filas) == 1


def test_abrir_revalida_la_ruta_guardada_con_d03(repo):
    class GeoQueNoConoceC(GeoFalsa):
        def verificar(self, nombre):
            return None if nombre == "Lugar C" else super().verificar(nombre)

    cliente = crear_app(repo).test_client()
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    guardar(cliente, token)

    # Misma base pero la fuente geográfica ya no identifica una parada.
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="llave-ficticia-solo-pruebas")
    app.jinja_loader = DictLoader({"planear_ia.html": '<meta name="rutamx-csrf" content="{{ csrf }}">'})
    registrar_v2(app, fabrica_adaptador=adaptador_normal, verificador=GeoQueNoConoceC(),
                 guardado=GuardadoRutas(repo))
    c2 = app.test_client()
    iniciar_sesion(c2, 7)
    t2 = abrir_pagina(c2)
    r = abrir(c2, t2, 1)
    assert r.status_code == 409
    assert "No se pudo abrir la ruta guardada" in r.json["error"]


def test_abrir_viaje_confirmado_con_las_dos_confirmaciones_de_d03(repo):
    # Ida y vuelta (origen = destino) con una parada igual al origen: D-03 pide
    # las DOS confirmaciones; la ruta guardada ya las tenía y debe reabrirse.
    ida_y_vuelta = {"origen": "Lugar A", "destino": "Lugar A", "duracion_dias": 2}
    ruta = {**ida_y_vuelta, "paradas": [{"nombre": "Lugar A"}]}

    def fabrica():
        return AdaptadorSimulado(extracciones=[ida_y_vuelta, {}], rutas=[ruta])

    cliente = crear_app(repo, fabrica).test_client()
    token = abrir_pagina(cliente)
    iniciar_sesion(cliente, 7)
    assert mensaje(cliente, token).json["estado"] == "confirmar"
    assert accion(cliente, token, "confirmar", {"acepta": True}).json["estado"] == "confirmar"
    assert accion(cliente, token, "confirmar", {"acepta": True}).json["estado"] == "propuesta"
    assert guardar(cliente, token).json["actualizada"] is False

    otro = crear_app(repo, fabrica).test_client()
    iniciar_sesion(otro, 7)
    token2 = abrir_pagina(otro)
    abierta = abrir(otro, token2, 1)
    assert abierta.status_code == 200 and abierta.json["estado"] == "propuesta"
    assert abierta.json["ruta"]["origen"] == abierta.json["ruta"]["destino"] == "Lugar A"
    assert guardar(otro, token2).json["actualizada"] is True
    assert len(repo.filas) == 1


def test_abrir_fallido_no_reemplaza_la_conversacion_vigente(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    assert abrir(cliente, token, 999).status_code == 400  # no existe
    r = mensaje(cliente, token, "agrega Lugar D")  # la ruta vigente sigue ahí
    assert [p["nombre"] for p in r.json["ruta"]["paradas"]] == ["Lugar C", "Lugar D"]


# --- Aislamiento entre usuarios y sesiones ---

def test_un_usuario_no_ve_ni_abre_rutas_de_otro(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    guardar(cliente, token)

    otro = crear_app(repo).test_client()
    iniciar_sesion(otro, 8)
    token2 = abrir_pagina(otro)
    assert otro.get("/v2/rutas/lista").json["rutas"] == []
    r = abrir(otro, token2, 1)
    assert r.status_code == 400
    assert "No se encontró" in r.json["error"]
    # Ni siquiera existiendo la fila se instala nada en su conversación.
    assert mensaje(otro, token2).json["estado"] == "propuesta"


def test_la_lista_no_expone_el_contenido_interno_ni_el_dueno(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    guardar(cliente, token)
    fila = cliente.get("/v2/rutas/lista").json["rutas"][0]
    assert set(fila) == {"id", "nombre", "origen", "destino", "paradas", "compatible"}


def test_cambiar_de_usuario_no_hereda_el_id_guardado(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    guardar(cliente, token)
    assert repo.filas[1]["usuario_id"] == 7

    iniciar_sesion(cliente, 8)  # otro usuario en el mismo navegador
    r = guardar(cliente, token)
    assert r.json["actualizada"] is False
    assert r.json["ruta_guardada"]["id"] == 2
    assert {i: f["usuario_id"] for i, f in repo.filas.items()} == {1: 7, 2: 8}


def test_cerrar_sesion_y_entrar_con_otra_cuenta_no_hereda_el_id(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    guardar(cliente, token)
    cerrar_sesion(cliente)
    assert guardar(cliente, token).status_code == 401
    iniciar_sesion(cliente, 8)
    assert guardar(cliente, token).json["ruta_guardada"]["id"] == 2
    assert repo.filas[1]["usuario_id"] == 7  # la de 7 no se tocó


def test_volver_a_la_misma_cuenta_si_conserva_el_id(cliente, repo):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    guardar(cliente, token)
    cerrar_sesion(cliente)
    iniciar_sesion(cliente, 7)
    assert guardar(cliente, token).json["actualizada"] is True


def test_un_viaje_nuevo_no_sobrescribe_la_ruta_guardada(repo):
    llamadas = []

    def fabrica():
        llamadas.append(1)
        if len(llamadas) == 1:
            return AdaptadorSimulado(extracciones=[DATOS], rutas=[RUTA])
        return AdaptadorSimulado(extracciones=[OTRA], rutas=[RUTA_OTRA])

    cliente = crear_app(repo, fabrica).test_client()
    token = abrir_pagina(cliente)
    iniciar_sesion(cliente, 7)
    assert mensaje(cliente, token).json["estado"] == "propuesta"
    guardar(cliente, token)
    assert accion(cliente, token, "reiniciar", {}).status_code == 200
    assert mensaje(cliente, token).json["ruta"]["destino"] == "Lugar Y"
    r = guardar(cliente, token)
    assert r.json["actualizada"] is False and r.json["ruta_guardada"]["id"] == 2
    assert repo.filas[1]["destino"] == "Lugar B"


# --- RF-42, RF-44: errores sin detalle interno y sin tocar otros datos ---

@pytest.mark.parametrize("operacion", ["guardar", "listar", "abrir"])
def test_fallo_del_repositorio_no_filtra_detalles(cliente, repo, operacion):
    token = con_ruta(cliente)
    iniciar_sesion(cliente, 7)
    guardar(cliente, token)
    antes = deepcopy(repo.filas)
    repo.falla = "postgresql://usuario:SECRETO@servidor/base"
    if operacion == "guardar":
        r = guardar(cliente, token)
    elif operacion == "listar":
        r = cliente.get("/v2/rutas/lista")
    else:
        r = abrir(cliente, token, 1)
    assert r.status_code in (400, 503)
    assert "SECRETO" not in r.get_data(as_text=True)
    assert "postgresql" not in r.get_data(as_text=True)
    repo.falla = None
    assert repo.filas == antes  # lo guardado sigue igual
    assert mensaje(cliente, token, "agrega Lugar D").json["estado"] == "propuesta"  # la ruta vigente se conserva


def test_ruta_guardada_sin_formato_v2_se_informa_sin_romper(cliente, repo):
    repo.filas[1] = {"id": 1, "nombre": "Vieja", "origen": "A", "destino": "B",
                     "intereses": [], "paradas": [], "resumen": {"distancia_km": 10},
                     "usuario_id": 7, "presupuesto": None}
    token = abrir_pagina(cliente)
    iniciar_sesion(cliente, 7)
    lista = cliente.get("/v2/rutas/lista").json["rutas"]
    assert lista[0]["compatible"] is False
    r = abrir(cliente, token, 1)
    assert r.status_code == 400
    assert "formato compatible" in r.json["error"]


# --- Pantalla de rutas guardadas (M-06) ---

def test_pantalla_de_rutas_guardadas_y_cache(cliente):
    r = cliente.get("/v2/rutas")
    assert r.status_code == 200
    assert "sesion=False" in r.text
    assert r.headers["Cache-Control"] == "no-store"
    iniciar_sesion(cliente, 7)
    assert "sesion=True" in cliente.get("/v2/rutas").text
    assert cliente.get("/v2/rutas/lista").headers["Cache-Control"] == "no-store"
