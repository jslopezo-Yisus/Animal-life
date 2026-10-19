
from datetime import datetime

from app.extensions import db


class Servicio(db.Model):
    __tablename__ = "servicios"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    nombre = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
    )

    descripcion = db.Column(db.Text, nullable=True)

    precio = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0.00,
    )

    duracion_minutos = db.Column(
        db.Integer,
        nullable=True,
    )

    estado = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def __repr__(self):
        return f"<Servicio {self.id}: {self.nombre}>"