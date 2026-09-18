"""Genera destinos nuevos con IA cuando un lugar no está en la base.

Cuando alguien escribe un origen/destino que no está en los 369 destinos
curados, `maps_service.obtener_coordenadas()` llama a
`generar_destino_con_ia()` antes de caer a Nominatim directo. Si la IA
identifica el lugar real (corrigiendo errores de escritura si hace
falta), este módulo junta los datos que faltan y lo inserta en la tabla
`destinos` con `fuente="ia_generada"` — desde ese momento el lugar
funciona exactamente igual que cualquiera de los curados: sale en
autocompletado, en sugerencias de paradas y en cálculo de rutas.

Las coordenadas nunca se toman de lo que "sepa" la IA — siempre se
verifican con `maps_service.geocodificar()` (Nominatim), igual que los
destinos curados.
"""

from app.models import Destino, Estado, db
from app.services import llm_provider, maps_service


def generar_destino_con_ia(nombre_escrito_por_usuario: str) -> Destino | None:
    resultado = llm_provider.completar_plantilla_destino(nombre_escrito_por_usuario)
    if not resultado:
        return None

    nombre_oficial = (resultado.get("nombre") or "").strip()
    if not nombre_oficial:
        return None

    geocodificado = maps_service.geocodificar(nombre_oficial)
    if not geocodificado:
        return None
    lat, lon, _ = geocodificado

    estado = _buscar_estado(resultado.get("estado") or "")
    if not estado:
        return None

    tipo = resultado.get("tipo")
    if tipo not in Destino.TIPOS:
        return None

    intereses = [i for i in (resultado.get("intereses") or []) if isinstance(i, str)]

    destino = Destino(
        nombre=nombre_oficial,
        estado_id=estado.id,
        tipo=tipo,
        lat=lat,
        lon=lon,
        descripcion=resultado.get("descripcion") or "",
        intereses=intereses,
        poblacion=resultado.get("poblacion"),
        fuente="ia_generada",
    )
    db.session.add(destino)
    db.session.commit()
    return destino


def _buscar_estado(nombre_estado: str) -> Estado | None:
    clave = maps_service._normalizar(nombre_estado)
    if not clave:
        return None
    for estado in Estado.query.all():
        if maps_service._normalizar(estado.nombre) == clave:
            return estado
    return None
