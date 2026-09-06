from datetime import datetime

from app.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(100), nullable=False)

    apellido = db.Column(db.String(100), nullable=False)

    correo = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    rol = db.Column(
        db.String(30),
        nullable=False,
        default="ciudadano"
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    fecha_registro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Usuario {self.correo}>"