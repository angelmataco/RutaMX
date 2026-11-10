"""M-05 Gestor de rutas: ruta estructurada como fuente única, D-03 y atomicidad.

Responsabilidades (incremento v0.2.0, solo creación de la ruta):
- Guardar en memoria la ruta estructurada de una conversación (D-08, D-09):
  `origen`, `destino`, `duracion_dias`, `intereses` y `paradas` ordenadas
  (pueden ir vacías, RF-22). Es la única fuente de verdad (RF-24).
- Validar la ruta antes de aceptarla con D-03 completo (RF-35):
  (a) origen y destino son identificables; (b) la secuencia es coherente
  (origen al inicio, destino al final, sin paradas repetidas no confirmadas);
  (c) cada lugar tiene identificador y coordenadas válidas de una fuente
  geográfica. Si origen y destino son iguales, se pide confirmación.
  Una propuesta de la IA no es una ruta válida solo por ser JSON.
- La fuente geográfica NO vive aquí: se inyecta un `verificador` (M-08 o un
  simulado en pruebas). Sin verificador, o si el servicio falla, la propuesta
  no se presenta como válida (CA-19.3): falla de forma segura.
- Aplicar cambios de forma atómica (RF-37): se trabaja sobre una copia y solo
  si todo sale bien se reemplaza la ruta. Si algo falla, la anterior sigue
  intacta (RF-36).
- Derivar las vistas (chat, itinerario, mapa) de esa única ruta (RF-23, RF-43).

Contrato del verificador: un objeto con `verificar(nombre)` que devuelve
`{"id": str, "latitud": float, "longitud": float}`, o `None` si el lugar no se
puede identificar, o lanza cualquier excepción si el servicio no está
disponible. No habla con la IA (M-07), con la base (M-09) ni con Flask.
"""

from copy import deepcopy
from math import isfinite

from v2.utilerias import (
    ErrorValidacion, limpiar_texto, validar_entero_positivo,
    validar_lista_de_textos,
)

MAX_PARADAS = 30  # tope técnico, no de la especificación
MAX_INTERESES = 10  # tope técnico, no de la especificación

CONFIRMACION_ORIGEN_IGUAL_DESTINO = "origen_igual_destino"
CONFIRMACION_PARADAS_REPETIDAS = "paradas_repetidas"
_CONFIRMACIONES_VALIDAS = {CONFIRMACION_ORIGEN_IGUAL_DESTINO, CONFIRMACION_PARADAS_REPETIDAS}


class ErrorRutaInvalida(ErrorValidacion):
    """La propuesta no es una ruta válida (D-03); el mensaje pide cambios (RF-35)."""


class ErrorRutaRequiereConfirmacion(ErrorRutaInvalida):
    """Falta una confirmación del usuario; `pendiente` dice cuál."""

    def __init__(self, mensaje, pendiente):
        super().__init__(mensaje)
        self.pendiente = pendiente


def _pedir_cambios(motivo):
    return ErrorRutaInvalida(
        f"No se puede generar una ruta válida: {motivo} "
        "Cambia el origen, el destino o la duración e intenta de nuevo."
    )


def _coordenada_valida(valor, limite):
    return (
        isinstance(valor, (int, float)) and not isinstance(valor, bool)
        and isfinite(valor) and -limite <= valor <= limite
    )


def _identificar(verificador, nombre, rol):
    """Resuelve un lugar con la fuente geográfica (D-03 a y c)."""
    try:
        lugar = verificador.verificar(nombre)
    except Exception:
        # Sin detalle del servicio: puede traer URLs o llaves (RNF-14).
        raise ErrorRutaInvalida(
            "No se pudo validar la ruta porque el servicio de lugares no está "
            "disponible. Intenta de nuevo en un momento."
        ) from None
    if lugar is None:
        raise _pedir_cambios(f"no se pudo identificar el {rol} «{nombre}».")
    identificador = lugar.get("id") if isinstance(lugar, dict) else None
    if (
        not isinstance(identificador, str) or not identificador.strip()
        or not _coordenada_valida(lugar.get("latitud"), 90)
        or not _coordenada_valida(lugar.get("longitud"), 180)
    ):
        raise _pedir_cambios(f"el {rol} «{nombre}» no tiene identificador y coordenadas válidas.")
    return {
        "id": identificador.strip(),
        "latitud": float(lugar["latitud"]),
        "longitud": float(lugar["longitud"]),
    }


def _forma(propuesta):
    """Parte de D-03 que no necesita fuente geográfica: forma de los datos."""
    if not isinstance(propuesta, dict) or not propuesta:
        raise _pedir_cambios("no hay una propuesta de ruta.")
    origen = limpiar_texto(propuesta.get("origen"), "origen")
    destino = limpiar_texto(propuesta.get("destino"), "destino")
    duracion = validar_entero_positivo(propuesta.get("duracion_dias"), "duración")
    intereses = propuesta.get("intereses")
    intereses = [] if intereses is None else validar_lista_de_textos(
        intereses, "intereses", MAX_INTERESES)
    paradas_crudas = propuesta.get("paradas")
    if not isinstance(paradas_crudas, (list, tuple)):
        raise ErrorValidacion("Las paradas deben ser una lista (puede ir vacía).")
    if len(paradas_crudas) > MAX_PARADAS:
        raise ErrorValidacion(f"La ruta admite como máximo {MAX_PARADAS} paradas.")
    paradas = []
    for parada in paradas_crudas:
        if not isinstance(parada, dict):
            raise ErrorValidacion("Cada parada debe tener nombre y descripción.")
        paradas.append({
            "nombre": limpiar_texto(parada.get("nombre"), "parada"),
            "descripcion": limpiar_texto(
                parada.get("descripcion"), "descripción de la parada",
                obligatorio=False) or "",
        })
    return origen, destino, duracion, intereses, paradas


def validar_ruta(propuesta, verificador, confirmaciones=()):
    """Aplica D-03 completo y devuelve una ruta estructurada NUEVA.

    Nunca modifica `propuesta`. `confirmaciones` es un conjunto con las
    confirmaciones que el usuario ya dio (`CONFIRMACION_*`). Lanza
    `ErrorRutaInvalida` (o `ErrorRutaRequiereConfirmacion`) si no es válida.
    """
    if not set(confirmaciones) <= _CONFIRMACIONES_VALIDAS:
        raise ErrorValidacion("Confirmación desconocida.")
    try:
        origen, destino, duracion, intereses, paradas = _forma(propuesta)
    except ErrorValidacion as error:
        if isinstance(error, ErrorRutaInvalida):
            raise
        raise _pedir_cambios(str(error)) from None
    if verificador is None or not callable(getattr(verificador, "verificar", None)):
        raise ErrorRutaInvalida(
            "No se pudo validar la ruta porque no hay servicio de lugares "
            "configurado. La ruta no se presenta como válida."
        )

    lugar_origen = _identificar(verificador, origen, "origen")
    lugar_destino = _identificar(verificador, destino, "destino")
    for parada in paradas:
        parada["lugar"] = _identificar(verificador, parada["nombre"], "parada")

    if lugar_origen["id"] == lugar_destino["id"] and \
            CONFIRMACION_ORIGEN_IGUAL_DESTINO not in confirmaciones:
        raise ErrorRutaRequiereConfirmacion(
            f"El origen y el destino son el mismo lugar ({origen}). "
            "¿Confirmas que es un viaje de ida y vuelta?",
            CONFIRMACION_ORIGEN_IGUAL_DESTINO,
        )
    vistos = {lugar_origen["id"], lugar_destino["id"]}
    repetidas = []
    for parada in paradas:
        if parada["lugar"]["id"] in vistos:
            repetidas.append(parada["nombre"])
        vistos.add(parada["lugar"]["id"])
    if repetidas and CONFIRMACION_PARADAS_REPETIDAS not in confirmaciones:
        raise ErrorRutaRequiereConfirmacion(
            "Hay paradas repetidas o iguales al origen o al destino: "
            f"{', '.join(repetidas)}. ¿Confirmas que quieres repetirlas?",
            CONFIRMACION_PARADAS_REPETIDAS,
        )
    return {
        "origen": origen,
        "origen_lugar": lugar_origen,
        "destino": destino,
        "destino_lugar": lugar_destino,
        "duracion_dias": duracion,
        "intereses": intereses,
        "paradas": paradas,
    }


class GestorRutas:
    """Ruta estructurada de UNA conversación (vive en memoria, D-09)."""

    def __init__(self, verificador=None):
        self._verificador = verificador
        self._ruta = None

    @property
    def ruta(self):
        """Copia de la ruta vigente, o `None`. Editar la copia no cambia nada."""
        return deepcopy(self._ruta)

    def aplicar(self, transformacion, confirmaciones=()):
        """Cambio atómico: `transformacion(copia)` devuelve la ruta nueva.

        Se valida el resultado completo (D-03). Si `transformacion` falla o su
        resultado no es válido, la ruta vigente queda exactamente igual
        (RF-36, RF-37) y el error se propaga.
        """
        nueva = validar_ruta(
            transformacion(deepcopy(self._ruta)), self._verificador, confirmaciones)
        self._ruta = nueva
        return deepcopy(nueva)

    def proponer(self, propuesta, confirmaciones=()):
        """Acepta la propuesta inicial de la IA si es una ruta válida."""
        return self.aplicar(lambda _anterior: propuesta, confirmaciones)

    # --- Vistas derivadas de la ruta única (RF-23, RF-43) ---

    def _exigir_ruta(self):
        if self._ruta is None:
            raise ErrorValidacion("Todavía no hay una ruta propuesta.")
        return self._ruta

    def itinerario(self):
        """Paradas en orden, con su número (vista de itinerario)."""
        ruta = self._exigir_ruta()
        return [
            {"orden": n, "nombre": p["nombre"], "descripcion": p["descripcion"]}
            for n, p in enumerate(ruta["paradas"], start=1)
        ]

    def resumen_chat(self):
        """Texto breve para el chat, escrito solo con datos de la ruta."""
        ruta = self._exigir_ruta()
        dias = "día" if ruta["duracion_dias"] == 1 else "días"
        texto = f"{ruta['origen']} a {ruta['destino']}, {ruta['duracion_dias']} {dias}"
        if ruta["paradas"]:
            nombres = ", ".join(p["nombre"] for p in ruta["paradas"])
            texto += f". Paradas: {nombres}."
        else:
            texto += ". Sin paradas intermedias."
        return texto

    def puntos_mapa(self):
        """Puntos en orden (origen, paradas, destino) con coordenadas validadas."""
        ruta = self._exigir_ruta()
        puntos = [("origen", ruta["origen"], ruta["origen_lugar"])]
        puntos += [("parada", p["nombre"], p["lugar"]) for p in ruta["paradas"]]
        puntos.append(("destino", ruta["destino"], ruta["destino_lugar"]))
        return [
            {"tipo": tipo, "nombre": nombre, "id": lugar["id"],
             "latitud": lugar["latitud"], "longitud": lugar["longitud"]}
            for tipo, nombre, lugar in puntos
        ]
