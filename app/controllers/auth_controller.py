from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from app.models.usuario import Usuario


auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():

    # Mostrar el formulario de inicio de sesión
    if request.method == "GET":
        return render_template("login.html")

    # Obtener los datos enviados por el formulario
    correo = request.form.get("correo", "").strip().lower()
    password = request.form.get("password", "")

    # Validar campos vacíos
    if not correo or not password:
        flash(
            "Debes ingresar el correo y la contraseña.",
            "danger"
        )
        return redirect(url_for("auth.login"))

    # Buscar el usuario por su correo electrónico
    usuario = Usuario.query.filter_by(correo=correo).first()

    # Validar existencia del usuario y contraseña
    if usuario is None or not usuario.check_password(password):
        flash(
            "Correo o contraseña incorrectos.",
            "danger"
        )
        return redirect(url_for("auth.login"))

    # Validar si la cuenta está activa
    if not usuario.estado:
        flash(
            "Tu cuenta se encuentra desactivada. Contacta al administrador.",
            "warning"
        )
        return redirect(url_for("auth.login"))

    # Eliminar cualquier sesión anterior
    session.clear()

    # Guardar los datos necesarios del usuario en la sesión
    session["user_id"] = usuario.id
    session["user_nombre"] = usuario.nombre
    session["user_apellido"] = usuario.apellido
    session["user_correo"] = usuario.correo
    session["user_rol_id"] = usuario.rol_id
    session["user_rol"] = usuario.rol.nombre

    # Redirigir a la página principal
    return redirect(url_for("main.panel"))


@auth.route("/logout", methods=["GET"])
def logout():

    # Limpiar la sesión del usuario
    session.clear()

    # Informar que se cerró la sesión
    flash(
        "Has cerrado sesión correctamente.",
        "success"
    )

    # Regresar al formulario de inicio de sesión
    return redirect(url_for("auth.login"))