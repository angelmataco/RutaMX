"""RutaMX v2: Descubrir y Planear con Ayuda IA.

Aquí va todo lo nuevo. Puede importar de `base_datos` y de `v1` (solo la
autenticación); v1 nunca importa de aquí. Se registra en la misma app de Flask
que v1 desde `run.py`.
"""


def registrar_v2(app, **opciones):
    """Registra v2 en la app compartida; la composición vive en run.py."""
    from v2.interfaz.rutas_planear import registrar_planear

    registrar_planear(app, **opciones)
