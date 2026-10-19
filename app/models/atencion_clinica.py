from datetime import datetime

from app.extensions import db


class AtencionClinica(db.Model):
    """Registro clínico asociado a una cita veterinaria."""

    __tablename__ = "atenciones_clinicas"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cita_id = db.Column(
        db.Integer,
        db.ForeignKey("citas.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    veterinario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    diagnostico = db.Column(db.Text, nullable=False)
    tratamiento = db.Column(db.Text, nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    fecha_atencion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_actualizacion = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    cita = db.relationship("Cita")
    veterinario = db.relationship("Usuario")

    def __repr__(self):
        return f"<AtencionClinica {self.id}: cita {self.cita_id}>"
