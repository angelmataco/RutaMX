"""RutaMX v2: Descubrir y Planear con Ayuda IA.

Aquí va todo lo nuevo. Puede importar de `base_datos` y de `v1` (solo la
autenticación); v1 nunca importa de aquí. Se registra en la misma app de Flask
que v1 desde `run.py`.
"""


def registrar_v2(app, **opciones):
    """Registra v2 en la app compartida; la composición vive en run.py."""
    from v2.interfaz.rutas_descubrir import registrar_descubrir
    from v2.interfaz.rutas_guardadas import registrar_guardadas
    from v2.interfaz.rutas_planear import registrar_planear
    from v2.negocio.catalogo import Catalogo
    from v2.negocio.guardado_rutas import GuardadoRutas

    # Un solo servicio de guardado compartido; las pruebas inyectan uno falso.
    guardado = opciones.pop("guardado", None) or GuardadoRutas()
    catalogo = opciones.pop("catalogo", None) or Catalogo()
    copia = opciones.pop("copia", None)
    registrar_planear(app, guardado=guardado, **opciones)
    registrar_guardadas(app, guardado=guardado)
    registrar_descubrir(app, catalogo=catalogo, copia=copia)
