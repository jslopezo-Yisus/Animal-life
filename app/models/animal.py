from datetime import datetime

from app.extensions import db


class Animal(db.Model):
    __tablename__ = "animales"

    id = db.Column(
        "id",
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    nombre = db.Column(db.String(100), nullable=False)
    especie = db.Column(db.String(50), nullable=False)
    raza = db.Column(db.String(100), nullable=True)
    sexo = db.Column(db.String(20), nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    tamano = db.Column(db.String(30), nullable=True)
    color = db.Column(db.String(100), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)

    estado = db.Column(
        db.String(50),
        nullable=False,
        default="Disponible",
    )

    imagen = db.Column(db.String(255), nullable=True)

    fecha_registro = db.Column(
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

    def __repr__(self):
        return f"<Animal {self.id}: {self.nombre}>"
