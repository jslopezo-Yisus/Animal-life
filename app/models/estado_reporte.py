from app.extensions import db


class EstadoReporte(db.Model):
    __tablename__ = "estados_reporte"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    descripcion = db.Column(
        db.String(255),
        nullable=True
    )

    reportes = db.relationship(
        "Reporte",
        back_populates="estado"
    )

    def __repr__(self):
        return f"<EstadoReporte {self.nombre}>"