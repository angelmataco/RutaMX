"""Consulta del catálogo de rutas públicas (M-09 y M-02, v0.4.0).

Solo lectura. Usa SQL propio sobre las columnas que agrega la migración
`agregar_columnas_catalogo.py`; no toca el modelo `RutaGuardada`, para que v1
no se rompa antes de migrar. Si faltan esas columnas se lanza
`ErrorMigracionPendiente`, con un mensaje claro y sin detalles de la base.

Reglas:
- Una ruta es pública solo si `visibilidad = 'publica'`; todo lo demás no sale.
- Nunca se devuelve `usuario_id`, hash ni PIN: del autor solo el nombre y la
  inicial del apellido, y `es_rutamx` cuando la fila no tiene autor.
- Todos los valores van como parámetros enlazados; la búsqueda escapa % y _.
"""

from sqlalchemy import text

from base_datos.catalogo_valores import (
    CATEGORIAS,
    LIMITE_PALABRA_CLAVE,
    LIMITE_RESULTADOS,
    REGIONES,
    VISIBILIDAD_PUBLICA,
)
from base_datos.repositorios.rutas_repositorio import ErrorRepositorio, _abrir_sesion

CODIGO_COLUMNA_INEXISTENTE = "42703"

_COLUMNAS_LISTA = """
    r.id, r.nombre, r.origen, r.destino, r.duracion_dias, r.categoria, r.region,
    jsonb_array_length(r.paradas) AS num_paradas,
    (r.autor_id IS NULL) AS es_rutamx,
    u.nombre AS autor_nombre, left(u.apellido, 1) AS autor_inicial
"""
_DESDE = """
    FROM rutas_guardadas r LEFT JOIN usuarios u ON u.id = r.autor_id
"""


class ErrorMigracionPendiente(ErrorRepositorio):
    """Faltan las columnas del catálogo: hay que correr la migración."""


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _traducir(error, mensaje):
    codigo = getattr(getattr(error, "orig", None), "pgcode", None)
    if codigo == CODIGO_COLUMNA_INEXISTENTE:
        return ErrorMigracionPendiente(
            "El catálogo necesita la migración de la base de datos (columnas nuevas) y todavía no se ha aplicado."
        )
    return ErrorRepositorio(mensaje)


def _escapar_like(texto):
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _condiciones(palabra_clave, duracion_dias, categoria, region):
    condiciones = ["r.visibilidad = :publica"]
    parametros = {"publica": VISIBILIDAD_PUBLICA}
    if palabra_clave is not None:
        if not isinstance(palabra_clave, str) or len(palabra_clave) > LIMITE_PALABRA_CLAVE:
            raise ErrorRepositorio("La palabra clave no es válida.")
        palabra = palabra_clave.strip()
        if palabra:
            condiciones.append(
                "(r.nombre ILIKE :q ESCAPE '\\' OR r.origen ILIKE :q ESCAPE '\\' "
                "OR r.destino ILIKE :q ESCAPE '\\' OR r.descripcion ILIKE :q ESCAPE '\\')"
            )
            parametros["q"] = f"%{_escapar_like(palabra)}%"
    if duracion_dias is not None:
        if not _es_entero(duracion_dias) or duracion_dias <= 0:
            raise ErrorRepositorio("La duración no es válida.")
        condiciones.append("r.duracion_dias = :duracion")
        parametros["duracion"] = duracion_dias
    if categoria is not None:
        if categoria not in CATEGORIAS:
            raise ErrorRepositorio("La categoría no es válida.")
        condiciones.append("r.categoria = :categoria")
        parametros["categoria"] = categoria
    if region is not None:
        if region not in REGIONES:
            raise ErrorRepositorio("La región no es válida.")
        condiciones.append("r.region = :region")
        parametros["region"] = region
    return condiciones, parametros


def _autor(fila):
    if fila["es_rutamx"] or not fila["autor_nombre"]:
        return None
    return {"nombre": fila["autor_nombre"], "inicial_apellido": fila["autor_inicial"] or ""}


def _vista(fila):
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "origen": fila["origen"],
        "destino": fila["destino"],
        "duracion_dias": fila["duracion_dias"],
        "categoria": fila["categoria"],
        "region": fila["region"],
        "num_paradas": fila["num_paradas"],
        "es_rutamx": bool(fila["es_rutamx"]),
        "autor": _autor(fila),
    }


def listar_publicas(palabra_clave=None, duracion_dias=None, categoria=None, region=None,
                    limite=LIMITE_RESULTADOS):
    """Rutas públicas que cumplen los filtros (la más reciente primero)."""
    if not _es_entero(limite) or not 1 <= limite <= LIMITE_RESULTADOS:
        raise ErrorRepositorio("El límite de resultados no es válido.")
    condiciones, parametros = _condiciones(palabra_clave, duracion_dias, categoria, region)
    parametros["limite"] = limite
    consulta = (
        f"SELECT {_COLUMNAS_LISTA} {_DESDE} WHERE {' AND '.join(condiciones)} "
        "ORDER BY r.creado_en DESC, r.id DESC LIMIT :limite"
    )
    try:
        with _abrir_sesion() as sesion:
            filas = sesion.execute(text(consulta), parametros).mappings().all()
            return [_vista(fila) for fila in filas]
    except Exception as error:
        raise _traducir(error, "No se pudo consultar el catálogo.") from error


def obtener_publica(ruta_id):
    """Detalle de una ruta pública, o `None` si no existe o no es pública."""
    if not _es_entero(ruta_id):
        raise ErrorRepositorio("El identificador de la ruta no es válido.")
    consulta = (
        f"SELECT {_COLUMNAS_LISTA}, r.descripcion, r.paradas {_DESDE} "
        "WHERE r.id = :id AND r.visibilidad = :publica"
    )
    try:
        with _abrir_sesion() as sesion:
            fila = sesion.execute(
                text(consulta), {"id": ruta_id, "publica": VISIBILIDAD_PUBLICA}
            ).mappings().first()
            if fila is None:
                return None
            detalle = _vista(fila)
            detalle["descripcion"] = fila["descripcion"] or ""
            detalle["paradas"] = list(fila["paradas"] or [])
            return detalle
    except Exception as error:
        raise _traducir(error, "No se pudo leer la ruta.") from error
