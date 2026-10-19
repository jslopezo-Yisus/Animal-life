from datetime import datetime

from app.extensions import db


class Evidencia(db.Model):
    __tablename__ = "evidencias"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reporte_id = db.Column(
        db.Integer,
        db.ForeignKey("reportes.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    nombre_archivo = db.Column(db.String(255), nullable=False)
    ruta_archivo = db.Column(db.String(500), nullable=False)
    tipo_archivo = db.Column(db.String(100), nullable=True)
    fecha_subida = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    reporte = db.relationship("Reporte", backref=db.backref("evidencias", lazy=True))

    def __repr__(self):
        return f"<Evidencia {self.id}: {self.nombre_archivo}>"
