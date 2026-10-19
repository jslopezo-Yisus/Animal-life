
from datetime import datetime

from app.extensions import db


class Adopcion(db.Model):
    __tablename__ = "adopciones"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    animal_id = db.Column(
        db.Integer,
        db.ForeignKey("animales.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )

    fecha_solicitud = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    fecha_respuesta = db.Column(
        db.DateTime,
        nullable=True,
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

    animal = db.relationship("Animal")
    usuario = db.relationship("Usuario")

    def __repr__(self):
        return f"<Adopcion {self.id}: {self.estado}>"