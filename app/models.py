"""Modelos de datos de RutaMX.

Estado y Destino viven en Postgres (Supabase) vía SQLAlchemy: son el
catálogo/"plantilla" de estados, ciudades principales y pueblos mágicos
que alimenta las sugerencias de la app.

Ruta (rutas guardadas por el usuario) todavía vive en memoria mientras no
se decide cómo se van a guardar las rutas de cada usuario.
# TODO: reemplazar RUTAS_GUARDADAS por una tabla real cuando se agregue
# autenticación de usuarios.
"""

import itertools

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY

db = SQLAlchemy()


class Estado(db.Model):
    __tablename__ = "estados"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False, unique=True)
    clave = db.Column(db.Text, nullable=False, unique=True)

    destinos = db.relationship("Destino", back_populates="estado")

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre, "clave": self.clave}


class Destino(db.Model):
    __tablename__ = "destinos"

    TIPOS = ("ciudad_principal", "pueblo_magico", "sitio_turistico")

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    estado_id = db.Column(db.Integer, db.ForeignKey("estados.id"), nullable=False)
    tipo = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    intereses = db.Column(ARRAY(db.Text), nullable=False, default=list)
    poblacion = db.Column(db.Integer)
    fuente = db.Column(db.Text, nullable=False, default="curada")
    creado_en = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    estado = db.relationship("Estado", back_populates="destinos")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "estado": self.estado.nombre if self.estado else None,
            "tipo": self.tipo,
            "lat": self.lat,
            "lon": self.lon,
            "descripcion": self.descripcion,
            "intereses": self.intereses or [],
            "poblacion": self.poblacion,
            "fuente": self.fuente,
        }


_id_counter = itertools.count(1)

# Almacenamiento en memoria de rutas guardadas por el usuario.
RUTAS_GUARDADAS = []


class Ruta:
    """Representa una ruta de road trip armada por el usuario."""

    def __init__(self, nombre, origen, destino, presupuesto, intereses, resumen, paradas):
        self.id = next(_id_counter)
        self.nombre = nombre
        self.origen = origen
        self.destino = destino
        self.presupuesto = presupuesto
        self.intereses = intereses
        self.resumen = resumen
        self.paradas = paradas

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "origen": self.origen,
            "destino": self.destino,
            "presupuesto": self.presupuesto,
            "intereses": self.intereses,
            "resumen": self.resumen,
            "paradas": self.paradas,
        }


def guardar_ruta(ruta: Ruta) -> Ruta:
    RUTAS_GUARDADAS.append(ruta)
    return ruta


def listar_rutas():
    return [ruta.to_dict() for ruta in RUTAS_GUARDADAS]
