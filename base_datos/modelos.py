"""Modelos de datos de RutaMX.

Estado, Destino, Usuario y RutaGuardada viven en Postgres (Supabase) vía
SQLAlchemy. Estado/Destino son el catálogo/"plantilla" que alimenta las
sugerencias; Usuario es la cuenta (nombre + apellido + PIN, sin correo —
decisión explícita para este proyecto escolar); RutaGuardada guarda las
rutas que arma cada usuario, ligadas a su cuenta.
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
    # Gastronomía reconocida públicamente (UNESCO Ciudad Creativa de la
    # Gastronomía o Guía Michelin). Solo se marca con una fuente verificable;
    # `reconocimiento_gastronomico` dice cuál. Ver scripts/marcar_gastronomia_destacada.py.
    gastronomia_destacada = db.Column(db.Boolean, nullable=False, default=False, server_default="false")
    reconocimiento_gastronomico = db.Column(db.Text)
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
            "gastronomia_destacada": bool(self.gastronomia_destacada),
            "reconocimiento_gastronomico": self.reconocimiento_gastronomico,
            "fuente": self.fuente,
        }


class Usuario(db.Model):
    """Cuenta de usuario: nombre + apellido + PIN de 4 dígitos, sin
    correo — suficiente para un proyecto escolar. Si más adelante se
    lanza la app al público, ahí sí valdría la pena agregar correo.
    """

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.Text, nullable=False)
    apellido = db.Column(db.Text, nullable=False)
    # nombre+apellido normalizado (sin acentos/mayúsculas), para detectar
    # duplicados sin importar cómo los haya escrito cada quien.
    clave_normalizada = db.Column(db.Text, nullable=False, unique=True)
    pin_hash = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre, "apellido": self.apellido}


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
    # Nullable a propósito: no rompe filas guardadas antes de que
    # existiera el login.
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
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


def listar_rutas(usuario_id: int):
    rutas = (
        RutaGuardada.query.filter_by(usuario_id=usuario_id)
        .order_by(RutaGuardada.creado_en.desc())
        .all()
    )
    return [ruta.to_dict() for ruta in rutas]
