from flask import Blueprint, render_template, request

from app.extensions import db
from app.models.usuario import Usuario
from app.models.rol import Rol


main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/registro", methods=["GET", "POST"])
def registro():

    error = None
    success = None

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validar campos obligatorios
        if not nombre or not apellido or not correo or not password:
            error = "Completa todos los campos obligatorios."

        # Validar longitud de contraseña
        elif len(password) < 8:
            error = "La contraseña debe tener mínimo 8 caracteres."

        # Confirmar contraseña
        elif password != confirm_password:
            error = "Las contraseñas no coinciden."

        # Comprobar correo existente
        elif Usuario.query.filter_by(correo=correo).first():
            error = "Ya existe un usuario registrado con ese correo."

        else:

            # Buscar el rol Ciudadano
            rol = Rol.query.filter_by(nombre="Ciudadano").first()

            if not rol:
                error = "No se encontró el rol Ciudadano en la base de datos."

            else:

                nuevo_usuario = Usuario(
                    rol_id=rol.id,
                    nombre=nombre,
                    apellido=apellido,
                    correo=correo,
                    telefono=telefono or None,
                    direccion=direccion or None,
                    estado=True
                )

                # Generar hash de contraseña
                nuevo_usuario.set_password(password)

                try:

                    db.session.add(nuevo_usuario)
                    db.session.commit()

                    success = "Usuario registrado correctamente."

                except Exception:

                    db.session.rollback()

                    error = "Ocurrió un error al registrar el usuario."

    return render_template(
        "registro.html",
        error=error,
        success=success
    )