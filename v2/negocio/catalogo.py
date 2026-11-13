"""M-02: filtros y vistas públicas del catálogo, sin Flask ni datos privados."""
from base_datos.catalogo_valores import CATEGORIAS, REGIONES, LIMITE_PALABRA_CLAVE
from base_datos.repositorios import catalogo_repositorio
from base_datos.repositorios.catalogo_repositorio import ErrorMigracionPendiente
from v2.utilerias import ErrorRutaMX, ErrorValidacion, limpiar_texto, validar_entero_positivo


class ErrorCatalogo(ErrorRutaMX):
    """Fallo seguro del catálogo."""


class RutaNoEncontrada(ErrorCatalogo):
    """Igual para rutas privadas e inexistentes."""


def _opcion(valor, campo, opciones):
    texto = limpiar_texto(valor, campo, obligatorio=False)
    if texto is not None and texto not in opciones:
        raise ErrorValidacion(f'El dato «{campo}» no es una opción válida.')
    return texto


def _vista(fila):
    # Proyección cerrada: aunque un repositorio devuelva campos privados,
    # la interfaz nunca los recibe. El autor ya viene reducido por M-09.
    salida = {c: fila[c] for c in ('id', 'nombre', 'origen', 'destino',
              'duracion_dias', 'num_paradas', 'categoria', 'region')}
    salida['es_rutamx'] = bool(fila['es_rutamx'])
    autor = fila.get('autor')
    if salida['es_rutamx']:
        salida['autor'] = 'RutaMx'
    elif isinstance(autor, dict) and isinstance(autor.get('nombre'), str):
        inicial = autor.get('inicial_apellido') or ''
        salida['autor'] = autor['nombre'] + (f' {inicial[:1]}.' if inicial else '')
    else:
        salida['autor'] = 'Autor no disponible'
    return salida


class Catalogo:
    """Repositorio inyectable con listar_publicas y obtener_publica."""

    def __init__(self, repositorio=None):
        self._repo = catalogo_repositorio if repositorio is None else repositorio

    def listar(self, palabra_clave=None, duracion_dias=None, categoria=None, region=None):
        palabra = limpiar_texto(palabra_clave, 'búsqueda', maximo=LIMITE_PALABRA_CLAVE, obligatorio=False)
        if duracion_dias is not None:
            duracion_dias = validar_entero_positivo(duracion_dias, 'duración')
        categoria = _opcion(categoria, 'categoría', CATEGORIAS)
        region = _opcion(region, 'región', REGIONES)
        try:
            return [_vista(f) for f in self._repo.listar_publicas(
                palabra_clave=palabra, duracion_dias=duracion_dias,
                categoria=categoria, region=region)]
        except ErrorMigracionPendiente:
            raise ErrorCatalogo('El catálogo necesita la migración de la base de datos; todavía no se ha aplicado.') from None
        except Exception:
            raise ErrorCatalogo('No se pudo consultar el catálogo. Intenta de nuevo.') from None

    def detalle(self, ruta_id):
        if not isinstance(ruta_id, int) or isinstance(ruta_id, bool) or ruta_id <= 0:
            raise ErrorValidacion('El identificador de la ruta no es válido.')
        try:
            fila = self._repo.obtener_publica(ruta_id)
            if fila is None:
                raise RutaNoEncontrada('No se encontró la ruta.')
            salida = _vista(fila)
            salida['descripcion'] = fila.get('descripcion') or ''
            salida['paradas'] = [
                {'orden': n, 'nombre': p['nombre'], 'descripcion': p.get('descripcion') or ''}
                for n, p in enumerate(fila.get('paradas') or [], start=1)]
            return salida
        except RutaNoEncontrada:
            raise
        except ErrorMigracionPendiente:
            raise ErrorCatalogo('El catálogo necesita la migración de la base de datos; todavía no se ha aplicado.') from None
        except Exception:
            raise ErrorCatalogo('No se pudo leer la ruta. Intenta de nuevo.') from None
