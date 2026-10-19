from datetime import datetime

from app.extensions import db


class Reporte(db.Model):
    __tablename__ = "reportes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False
    )
    
    responsable_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "usuarios.id",
            onupdate="CASCADE",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    animal_id = db.Column(
        db.Integer,
        db.ForeignKey("animales.id"),
        nullable=True
    )

    estado_id = db.Column(
        db.Integer,
        db.ForeignKey("estados_reporte.id"),
        nullable=False
    )

    tipo = db.Column(
        db.String(100),
        nullable=False
    )

    titulo = db.Column(
        db.String(150),
        nullable=False
    )

    descripcion = db.Column(
        db.Text,
        nullable=False
    )

    direccion = db.Column(
        db.String(255),
        nullable=True
    )

    latitud = db.Column(
        db.Numeric(10, 8),
        nullable=True
    )

    longitud = db.Column(
        db.Numeric(11, 8),
        nullable=True
    )

    fecha_creacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    fecha_actualizacion = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    estado = db.relationship(
        "EstadoReporte",
        back_populates="reportes"
    )
    
    
    usuario = db.relationship(
        "Usuario",
        foreign_keys=[usuario_id]
    )

    responsable = db.relationship(
        "Usuario",
        foreign_keys=[responsable_id]
    )

    def __repr__(self):
        return f"<Reporte {self.id}: {self.titulo}>"