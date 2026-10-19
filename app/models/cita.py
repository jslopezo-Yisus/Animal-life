
from datetime import datetime

from app.extensions import db


class Cita(db.Model):
    __tablename__ = "citas"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
    )

    animal_id = db.Column(
        db.Integer,
        db.ForeignKey("animales.id"),
        nullable=False,
    )

    servicio_id = db.Column(
        db.Integer,
        db.ForeignKey("servicios.id"),
        nullable=False,
    )

    fecha = db.Column(
        db.Date,
        nullable=False,
    )

    hora = db.Column(
        db.Time,
        nullable=False,
    )

    estado = db.Column(
        db.String(50),
        nullable=False,
        default="Pendiente",
    )

    observaciones = db.Column(
        db.Text,
        nullable=True,
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    fecha_actualizacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    usuario = db.relationship("Usuario")
    animal = db.relationship("Animal")
    servicio = db.relationship("Servicio")

    def __repr__(self):
        return f"<Cita {self.id}: {self.fecha} {self.hora}>"