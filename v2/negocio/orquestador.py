"""M-04: conversación de creación de rutas, sin Flask ni persistencia.

Una instancia por conversación. M-03 debe conservarla del lado del servidor;
no aceptar ruta, confirmaciones previas ni estado del cliente como autoridad.
Las operaciones se serializan por conversación; los fallos conservan la ruta.
"""
from copy import deepcopy
from threading import RLock

from v2.negocio.gestor_rutas import GestorRutas, ErrorRutaRequiereConfirmacion
from v2.utilerias import (
    ErrorValidacion, LONGITUD_MAXIMA_MENSAJE, limpiar_texto,
    validar_entero_positivo, validar_lista_de_textos, mensaje_seguro,
)

_OBLIGATORIOS = ("origen", "destino", "duracion_dias")
_ETIQUETAS = {"origen": "origen", "destino": "destino", "duracion_dias": "duración en días"}


def _validar_datos(datos):
    if not isinstance(datos, dict):
        raise ErrorValidacion("No se pudieron interpretar los datos del viaje. Intenta de nuevo.")
    salida = {}
    for campo in ("origen", "destino"):
        if campo in datos:
            salida[campo] = limpiar_texto(datos[campo], campo)
    if "duracion_dias" in datos:
        salida["duracion_dias"] = validar_entero_positivo(datos["duracion_dias"], "duración")
    if "intereses" in datos:
        salida["intereses"] = validar_lista_de_textos(datos["intereses"], "intereses", 10)
    return salida


class OrquestadorPlaneacion:
    """Coordina AdaptadorIA y GestorRutas; solo crea propuestas en v0.2.0."""

    def __init__(self, adaptador, verificador=None):
        self._ia = adaptador
        self._gestor = GestorRutas(verificador)
        self._datos = {}
        self._por_generar = False
        self._pendiente = None
        self._mensajes = []
        self._candado = RLock()
        self._aclaracion = None

    def iniciar(self):
        """Saludo idempotente, sin consultar la IA."""
        with self._candado:
            if not self._mensajes:
                self._agregar("asistente", "Cuéntame tu viaje: ¿de dónde sales, a dónde vas y cuántos días tienes? Los intereses son opcionales.")
            return self._vista("inicio")

    def _agregar(self, rol, texto):
        self._mensajes.append({"rol": rol, "texto": texto})

    def _vista(self, estado, mensaje=None):
        ruta = self._gestor.ruta
        return {
            "estado": estado,
            "mensaje": mensaje if mensaje is not None else (self._mensajes[-1]["texto"] if self._mensajes else ""),
            "mensajes": deepcopy(self._mensajes),
            "datos": deepcopy(self._datos),
            "faltantes": [c for c in _OBLIGATORIOS if c not in self._datos],
            "confirmacion": self._pendiente["confirmacion"] if self._pendiente else None,
            "ruta": ruta,
            "itinerario": self._gestor.itinerario() if ruta else [],
        }

    def _responder(self, estado, mensaje):
        self._agregar("asistente", mensaje)
        return self._vista(estado, mensaje)

    def procesar(self, mensaje):
        with self._candado:
            self.iniciar()
            try:
                texto = limpiar_texto(mensaje, "mensaje", maximo=LONGITUD_MAXIMA_MENSAJE)
            except ErrorValidacion as error:
                return self._responder("error", mensaje_seguro(error))
            self._agregar("usuario", texto)
            if self._pendiente and texto.casefold() in {"sí", "si", "confirmo", "no", "cancelar"}:
                return self._confirmar(texto.casefold() in {"sí", "si", "confirmo"})
            if self._aclaracion:
                return self._modificar(texto)
            # Otra descripción invalida las confirmaciones de la propuesta anterior.
            contexto = deepcopy(self._pendiente["datos"] if self._pendiente else self._datos)
            self._pendiente = None
            try:
                extraidos = _validar_datos(self._ia.extraer_datos(texto, deepcopy(contexto)))
                if (self._gestor.ruta is not None and not self._por_generar
                        and extraidos and set(extraidos) <= {"duracion_dias", "intereses"}):
                    return self._cambiar_preferencias(extraidos)
                if self._gestor.ruta is not None and not extraidos and not self._por_generar:
                    return self._modificar(texto)
                candidatos = {**contexto, **extraidos}
                # Los datos pertenecen al usuario, aunque el proveedor falle.
                # La ruta aceptada sigue siendo responsabilidad de M-05.
                self._datos = deepcopy(candidatos)
                faltantes = [c for c in _OBLIGATORIOS if c not in candidatos]
                if faltantes:
                    self._datos = candidatos
                    etiquetas = ", ".join(_ETIQUETAS[c] for c in faltantes)
                    return self._responder("faltan_datos", f"Para proponer la ruta necesito: {etiquetas}.")
                if not extraidos and not self._por_generar:
                    return self._responder("sin_datos", "Describe el origen, destino o duración del viaje que quieres crear.")
                self._por_generar = True
                propuesta = self._ia.generar_ruta(deepcopy(candidatos))
                # No aceptar una ruta distinta de lo que el usuario pidió.
                if not isinstance(propuesta, dict) or any(propuesta.get(c) != candidatos[c] for c in _OBLIGATORIOS):
                    raise ErrorValidacion("No se pudo generar la ruta solicitada. Cambia alguno de los datos e intenta de nuevo.")
                if propuesta.get("intereses", []) != candidatos.get("intereses", []):
                    raise ErrorValidacion("La propuesta no respeta los intereses del viaje. Intenta de nuevo.")
                return self._aceptar(propuesta, candidatos, set())
            except Exception as error:
                return self._responder("error", mensaje_seguro(error))

    def _modificar(self, texto):
        try:
            instruccion = texto
            if self._aclaracion:
                instruccion = (
                    f"Instrucción pendiente: {self._aclaracion['instruccion']}\n"
                    f"Pregunta: {self._aclaracion['pregunta']}\nRespuesta: {texto}"
                )
            accion = self._ia.interpretar_modificacion(instruccion, self._gestor.ruta)
            if accion["accion"] == "aclarar":
                self._aclaracion = {"instruccion": instruccion, "pregunta": accion["pregunta"]}
                return self._responder("aclarar", accion["pregunta"])
            self._aclaracion = None
            if accion["accion"] == "no_soportada":
                return self._responder("no_soportada", "Esa acción no está disponible. Sí puedes crear una ruta, agregar o eliminar paradas, reordenarlas y cambiar la duración o el tipo de lugares.")
            if accion["accion"] in {"eliminar_parada", "reordenar_paradas"}:
                return self._aplicar_operacion(accion, set())
            if accion["accion"] == "cambiar_preferencias":
                return self._cambiar_preferencias({k: v for k, v in accion.items() if k != "accion"})
            if accion["accion"] != "agregar_parada":
                raise ErrorValidacion("No se pudo interpretar el cambio.")
            # M-07 usa índice desde cero; M-05 recibe posición desde uno.
            posicion = accion.get("posicion")
            propuesta = self._gestor.ruta
            indice = len(propuesta["paradas"]) if posicion is None else posicion
            if (not isinstance(indice, int) or isinstance(indice, bool)
                    or not 0 <= indice <= len(propuesta["paradas"])):
                raise ErrorValidacion("La posición de la parada no es válida.")
            propuesta["paradas"].insert(indice, {
                "nombre": accion["nombre"], "descripcion": accion.get("descripcion", ""),
            })
            return self._aceptar(propuesta, self._datos, set(), origen="modificar")
        except Exception as error:
            return self._responder("error", mensaje_seguro(error))

    def _cambiar_preferencias(self, cambios):
        if not cambios or set(cambios) - {"duracion_dias", "intereses"}:
            raise ErrorValidacion("Solo puedes cambiar la duración o el tipo de lugares.")
        cambios = _validar_datos(cambios)
        vigente = self._gestor.ruta
        if vigente is None:
            raise ErrorValidacion("Todavía no hay una ruta propuesta.")
        datos = {c: deepcopy(vigente[c]) for c in (*_OBLIGATORIOS, "intereses")}
        candidatos = {**datos, **cambios}
        if candidatos == datos:
            return self._responder("propuesta", "Las preferencias ya tienen esos valores; el itinerario se conserva.")
        propuesta = self._ia.generar_ruta(deepcopy(candidatos))
        if (not isinstance(propuesta, dict)
                or any(propuesta.get(c) != candidatos[c] for c in _OBLIGATORIOS)):
            raise ErrorValidacion("No se pudo generar la ruta solicitada. Cambia alguno de los datos e intenta de nuevo.")
        if propuesta.get("intereses", []) != candidatos["intereses"]:
            raise ErrorValidacion("La propuesta no respeta los intereses del viaje. Intenta de nuevo.")
        # _aceptar confirma los datos solo después de aceptar la ruta por D-03.
        return self._aceptar(propuesta, candidatos, set(), origen="modificar")

    def _aplicar_operacion(self, accion, confirmaciones):
        anterior = self._gestor.ruta
        try:
            if accion["accion"] == "eliminar_parada":
                posicion = accion.get("posicion")
                if "posicion" in accion:
                    if not isinstance(posicion, int) or isinstance(posicion, bool) or posicion < 0:
                        raise ErrorValidacion("La posición de la parada no es válida.")
                    posicion += 1  # M-07 desde 0; M-05 desde 1.
                self._gestor.eliminar_parada(
                    nombre=accion.get("nombre"), posicion=posicion,
                    confirmaciones=confirmaciones)
            else:
                self._gestor.reordenar_paradas(accion.get("orden"), confirmaciones=confirmaciones)
        except ErrorRutaRequiereConfirmacion as error:
            self._por_generar = False
            self._pendiente = {
                "operacion": deepcopy(accion), "datos": deepcopy(self._datos),
                "confirmaciones": set(confirmaciones), "confirmacion": error.pendiente,
                "origen": "modificar",
            }
            return self._responder("confirmar", mensaje_seguro(error))
        self._pendiente = None
        self._por_generar = False
        if self._gestor.ruta == anterior:
            return self._responder("propuesta", "Las paradas ya tienen ese orden; no hay cambios que aplicar.")
        return self._responder("propuesta", self._gestor.resumen_chat())

    def _aceptar(self, propuesta, datos, confirmaciones, origen="crear"):
        try:
            self._gestor.proponer(propuesta, confirmaciones=confirmaciones)
        except ErrorRutaRequiereConfirmacion as error:
            self._por_generar = False
            self._pendiente = {
                "propuesta": deepcopy(propuesta), "datos": deepcopy(datos),
                "confirmaciones": set(confirmaciones), "confirmacion": error.pendiente,
                "origen": origen,
            }
            return self._responder("confirmar", mensaje_seguro(error))
        self._datos = deepcopy(datos)
        self._por_generar = False
        self._pendiente = None
        return self._responder("propuesta", self._gestor.resumen_chat())

    def confirmar(self, acepta):
        """Confirmación explícita de la última propuesta; solo admite bool."""
        with self._candado:
            if not isinstance(acepta, bool):
                return self._responder("error", "La confirmación debe indicar sí o no.")
            self._agregar("usuario", "Sí" if acepta else "No")
            return self._confirmar(acepta)

    def _confirmar(self, acepta):
        if self._pendiente is None:
            return self._responder("error", "No hay una propuesta pendiente de confirmación.")
        pendiente = self._pendiente
        self._pendiente = None
        if not acepta:
            return self._responder("cancelado", "Propuesta descartada. Cambia los datos para intentar de nuevo; la ruta anterior se conserva.")
        confirmaciones = pendiente["confirmaciones"] | {pendiente["confirmacion"]}
        try:
            if "operacion" in pendiente:
                return self._aplicar_operacion(pendiente["operacion"], confirmaciones)
            return self._aceptar(pendiente["propuesta"], pendiente["datos"], confirmaciones,
                                 origen=pendiente["origen"])
        except Exception as error:
            self._por_generar = pendiente["origen"] == "crear"
            return self._responder("error", mensaje_seguro(error))
