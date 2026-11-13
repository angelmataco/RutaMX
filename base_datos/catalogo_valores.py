"""Valores del catálogo de rutas públicas (v0.4.0).

PROPUESTA pendiente de aprobación de Angel (y de respuesta del profesor en
P-01 y P-03): las listas de categorías y regiones y la publicación
administrativa por script. Mientras no se aprueben, no se tratan como
decisión tomada. Un solo lugar las define para que el repositorio, la
migración, el script de publicar y el servicio del catálogo coincidan.
"""

CATEGORIAS = ("Playa", "Cultural", "Naturaleza", "Gastronomía", "Pueblo Mágico")
REGIONES = ("Noroeste", "Noreste", "Occidente", "Centro", "Sureste")

VISIBILIDAD_PRIVADA = "privada"
VISIBILIDAD_PUBLICA = "publica"
VISIBILIDADES = (VISIBILIDAD_PRIVADA, VISIBILIDAD_PUBLICA)

LIMITE_RESULTADOS = 50  # máximo de rutas por consulta del catálogo
LIMITE_PALABRA_CLAVE = 80  # máximo de caracteres de la búsqueda
