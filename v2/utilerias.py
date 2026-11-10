"""M-11 Utilerías de v2: errores seguros, validación de entradas y constantes.

Es el módulo más bajo de v2: no importa de ningún otro módulo de v2 y lo
usan todos. Solo contiene lo mínimo que comparten (RNF-12, RNF-14, RNF-19).

- Errores con mensaje seguro (RNF-14): un `ErrorRutaMX` lleva un mensaje
  pensado para mostrarse al usuario, sin SQL, rutas de archivos ni llaves.
  Cualquier otra excepción se muestra con un mensaje genérico
  (`mensaje_seguro`); el detalle técnico no sale de aquí.
- Validación de entradas (RNF-12): texto, enteros y listas se validan antes
  de que otro módulo los use.
- Constantes de configuración (RNF-19): los límites viven aquí, no dentro de
  la lógica de los demás módulos. Son límites técnicos de la implementación,
  no valores que diga la especificación v2.0.
"""

import re

# --- Constantes de configuración (RNF-19) ---
LONGITUD_MAXIMA_TEXTO = 200  # nombres de lugares y de ruta
LONGITUD_MAXIMA_MENSAJE = 1000  # un mensaje del usuario en el chat
DURACION_MAXIMA_DIAS = 60  # tope técnico de duración de una ruta
MENSAJE_ERROR_GENERICO = "Ocurrió un error inesperado. Intenta de nuevo."

_CARACTERES_DE_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_ESPACIOS = re.compile(r"\s+")


class ErrorRutaMX(Exception):
    """Error de v2 cuyo mensaje es seguro de mostrar al usuario."""


class ErrorValidacion(ErrorRutaMX):
    """Un dato de entrada no es válido (RNF-12)."""


class ErrorServicioExterno(ErrorRutaMX):
    """Un servicio externo (por ejemplo la IA) falló (RF-36)."""


def mensaje_seguro(error, por_defecto=MENSAJE_ERROR_GENERICO):
    """Devuelve el texto que se puede mostrar al usuario para un error.

    Solo los `ErrorRutaMX` muestran su propio mensaje; cualquier otra
    excepción (base de datos, red, bug) se oculta tras `por_defecto`.
    """
    if isinstance(error, ErrorRutaMX) and str(error).strip():
        return str(error)
    return por_defecto


def limpiar_texto(valor, campo, maximo=LONGITUD_MAXIMA_TEXTO, obligatorio=True):
    """Valida y normaliza un texto: sin controles, espacios colapsados.

    Devuelve el texto limpio. Si `obligatorio` es False y llega vacío o
    `None`, devuelve `None`. Lanza `ErrorValidacion` si no es texto, si queda
    vacío siendo obligatorio o si excede `maximo`.
    """
    if valor is None:
        if obligatorio:
            raise ErrorValidacion(f"Falta el dato «{campo}».")
        return None
    if not isinstance(valor, str):
        raise ErrorValidacion(f"El dato «{campo}» debe ser texto.")
    limpio = _ESPACIOS.sub(" ", _CARACTERES_DE_CONTROL.sub("", valor)).strip()
    if not limpio:
        if obligatorio:
            raise ErrorValidacion(f"Falta el dato «{campo}».")
        return None
    if len(limpio) > maximo:
        raise ErrorValidacion(f"El dato «{campo}» excede {maximo} caracteres.")
    return limpio


def validar_entero_positivo(valor, campo, maximo=DURACION_MAXIMA_DIAS):
    """Valida un entero mayor que cero y no mayor que `maximo`.

    No acepta `bool` ni texto ni decimales: la conversión es decisión de
    quien llama, no de la validación.
    """
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ErrorValidacion(f"El dato «{campo}» debe ser un número entero.")
    if valor < 1:
        raise ErrorValidacion(f"El dato «{campo}» debe ser mayor que cero.")
    if valor > maximo:
        raise ErrorValidacion(f"El dato «{campo}» no puede ser mayor que {maximo}.")
    return valor


def validar_lista_de_textos(valor, campo, maximo_elementos, maximo_texto=LONGITUD_MAXIMA_TEXTO):
    """Valida una lista de textos (puede ir vacía) y devuelve la lista limpia."""
    if not isinstance(valor, (list, tuple)):
        raise ErrorValidacion(f"El dato «{campo}» debe ser una lista.")
    if len(valor) > maximo_elementos:
        raise ErrorValidacion(f"El dato «{campo}» admite como máximo {maximo_elementos} elementos.")
    return [limpiar_texto(elemento, campo, maximo=maximo_texto) for elemento in valor]
