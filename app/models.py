"""Modelos de datos de RutaMX.

Estado, Destino y RutaGuardada viven en Postgres (Supabase) vía
SQLAlchemy. Estado/Destino son el catálogo/"plantilla" que alimenta las
sugerencias; RutaGuardada guarda las rutas que arma cada usuario.

# TODO: agregar una columna usuario_id a RutaGuardada cuando se decida
# implementar login, para que cada quien vea solo sus propias rutas.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

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


class RutaGuardada(db.Model):
    """Una ruta de road trip armada y guardada por el usuario."""

    __tablename__ = "rutas_guardadas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    origen = db.Column(db.Text, nullable=False)
    destino = db.Column(db.Text, nullable=False)
    presupuesto = db.Column(db.Float)
    intereses = db.Column(ARRAY(db.Text), nullable=False, default=list)
    resumen = db.Column(JSONB, nullable=False, default=dict)
    paradas = db.Column(JSONB, nullable=False, default=list)
    creado_en = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "origen": self.origen,
            "destino": self.destino,
            "presupuesto": self.presupuesto,
            "intereses": self.intereses or [],
            "resumen": self.resumen or {},
            "paradas": self.paradas or [],
        }


def guardar_ruta(ruta: RutaGuardada) -> RutaGuardada:
    db.session.add(ruta)
    db.session.commit()
    return ruta


def listar_rutas():
    rutas = RutaGuardada.query.order_by(RutaGuardada.creado_en.desc()).all()
    return [ruta.to_dict() for ruta in rutas]
