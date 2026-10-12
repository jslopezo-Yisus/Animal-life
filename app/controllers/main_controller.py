from app.services.analytics_service import (
    obtener_indicadores_generales,
    obtener_reportes_por_estado,
    obtener_reportes_por_tipo,
    obtener_reportes_por_mes,
)
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.reporte import Reporte
from app.models.estado_reporte import EstadoReporte

main = Blueprint("main", __name__)


# ==========================================================
# CONTROL DE ACCESO
# ==========================================================

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            flash(
                "Debes iniciar sesión para acceder a esta sección.",
                "warning",
            )
            return redirect(url_for("auth.login"))

        return view_func(*args, **kwargs)

    return wrapper


def roles_required(*roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not session.get("user_id"):
                flash(
                    "Debes iniciar sesión para continuar.",
                    "warning",
                )
                return redirect(url_for("auth.login"))

            if session.get("user_rol") not in roles_permitidos:
                flash(
                    "No tienes permisos para acceder a esta sección.",
                    "danger",
                )
                return redirect(url_for("main.panel"))

            return view_func(*args, **kwargs)

        return wrapper

    return decorator


# ==========================================================
# PÁGINA PRINCIPAL
# ==========================================================

@main.route("/")
def index():
    return render_template("index.html")


# ==========================================================
# REGISTRO DE CIUDADANOS
# ==========================================================

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

        if not nombre or not apellido or not correo or not password:
            error = "Completa todos los campos obligatorios."

        elif len(password) < 8:
            error = "La contraseña debe tener mínimo 8 caracteres."

        elif password != confirm_password:
            error = "Las contraseñas no coinciden."

        elif Usuario.query.filter_by(correo=correo).first():
            error = "Ya existe un usuario registrado con ese correo."

        else:
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
                    estado=True,
                )

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
        success=success,
    )


# ==========================================================
# REDIRECCIÓN SEGÚN EL ROL
# ==========================================================

@main.route("/panel")
@login_required
def panel():
    paneles_por_rol = {
        "Administrador": "main.panel_administrador",
        "Ciudadano": "main.panel_ciudadano",
        "Veterinario": "main.panel_veterinario",
        "Tecnico": "main.panel_tecnico",
        "Fundacion": "main.panel_fundacion",
    }

    endpoint = paneles_por_rol.get(session.get("user_rol"))

    if endpoint:
        return redirect(url_for(endpoint))

    session.clear()
    flash(
        "No se pudo identificar tu rol. Inicia sesión nuevamente.",
        "warning",
    )
    return redirect(url_for("auth.login"))


# ==========================================================
# PANELES DIFERENCIADOS
# ==========================================================

@main.route("/panel/administrador")
@roles_required("Administrador")
def panel_administrador():
    return render_template("paneles/administrador.html")


@main.route("/panel/ciudadano")
@roles_required("Ciudadano")
def panel_ciudadano():
    return render_template("paneles/ciudadano.html")


@main.route("/panel/veterinario")
@roles_required("Veterinario")
def panel_veterinario():
    return render_template("paneles/veterinario.html")


@main.route("/panel/tecnico")
@roles_required("Tecnico")
def panel_tecnico():
    return render_template("paneles/tecnico.html")


@main.route("/panel/fundacion")
@roles_required("Fundacion")
def panel_fundacion():
    return render_template("paneles/fundacion.html")


# ==========================================================
# GESTIÓN DE USUARIOS: SOLO ADMINISTRADORES
# ==========================================================

@main.route("/panel/administrador/usuarios")
@roles_required("Administrador")
def administrar_usuarios():
    busqueda = request.args.get("buscar", "").strip()
    filtro_rol = request.args.get("rol", "").strip()
    filtro_estado = request.args.get("estado", "").strip()

    consulta = Usuario.query.join(Rol)

    if busqueda:
        patron = f"%{busqueda}%"
        consulta = consulta.filter(
            or_(
                Usuario.nombre.ilike(patron),
                Usuario.apellido.ilike(patron),
                Usuario.correo.ilike(patron),
            )
        )

    if filtro_rol.isdigit():
        consulta = consulta.filter(Usuario.rol_id == int(filtro_rol))

    if filtro_estado == "activo":
        consulta = consulta.filter(Usuario.estado.is_(True))
    elif filtro_estado == "inactivo":
        consulta = consulta.filter(Usuario.estado.is_(False))

    usuarios = consulta.order_by(Usuario.id.desc()).all()
    roles = Rol.query.order_by(Rol.nombre).all()

    return render_template(
        "paneles/usuarios.html",
        usuarios=usuarios,
        roles=roles,
        buscar=busqueda,
        filtro_rol=filtro_rol,
        filtro_estado=filtro_estado,
    )


# ==========================================================
# CAMBIAR ESTADO DE UNA CUENTA
# ==========================================================

@main.route(
    "/panel/administrador/usuarios/<int:usuario_id>/estado",
    methods=["POST"],
)
@roles_required("Administrador")
def cambiar_estado_usuario(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)

    if usuario is None:
        flash("El usuario solicitado no existe.", "danger")
        return redirect(url_for("main.administrar_usuarios"))

    # No permitir que el administrador desactive su propia cuenta.
    if usuario.id == session.get("user_id"):
        flash("No puedes cambiar el estado de tu propia cuenta.", "warning")
        return redirect(url_for("main.administrar_usuarios"))

    nuevo_estado = not bool(usuario.estado)

    # No dejar el sistema sin ningún administrador activo.
    if not nuevo_estado and usuario.rol.nombre == "Administrador":
        administradores_activos = (
            Usuario.query
            .join(Rol)
            .filter(
                Rol.nombre == "Administrador",
                Usuario.estado.is_(True),
            )
            .count()
        )

        if administradores_activos <= 1:
            flash(
                "No puedes desactivar al último administrador activo.",
                "warning",
            )
            return redirect(url_for("main.administrar_usuarios"))

    usuario.estado = nuevo_estado

    try:
        db.session.commit()
        mensaje = "activada" if nuevo_estado else "desactivada"
        flash(f"La cuenta fue {mensaje} correctamente.", "success")
    except Exception:
        db.session.rollback()
        flash("No fue posible actualizar el estado de la cuenta.", "danger")

    return redirect(url_for("main.administrar_usuarios"))


# ==========================================================
# CAMBIAR ROL DE UN USUARIO
# ==========================================================

@main.route(
    "/panel/administrador/usuarios/<int:usuario_id>/rol",
    methods=["POST"],
)
@roles_required("Administrador")
def cambiar_rol_usuario(usuario_id):
    usuario = db.session.get(Usuario, usuario_id)

    if usuario is None:
        flash("El usuario solicitado no existe.", "danger")
        return redirect(url_for("main.administrar_usuarios"))

    # No permitir cambiar el propio rol desde esta pantalla.
    if usuario.id == session.get("user_id"):
        flash("No puedes cambiar tu propio rol.", "warning")
        return redirect(url_for("main.administrar_usuarios"))

    rol_id = request.form.get("rol_id", type=int)
    nuevo_rol = db.session.get(Rol, rol_id) if rol_id else None

    if nuevo_rol is None or not nuevo_rol.estado:
        flash("Selecciona un rol válido y activo.", "danger")
        return redirect(url_for("main.administrar_usuarios"))

    # No quitar el rol al último administrador activo.
    if (
        usuario.estado
        and usuario.rol.nombre == "Administrador"
        and nuevo_rol.nombre != "Administrador"
    ):
        administradores_activos = (
            Usuario.query
            .join(Rol)
            .filter(
                Rol.nombre == "Administrador",
                Usuario.estado.is_(True),
            )
            .count()
        )

        if administradores_activos <= 1:
            flash(
                "No puedes quitar el rol al último administrador activo.",
                "warning",
            )
            return redirect(url_for("main.administrar_usuarios"))

    usuario.rol_id = nuevo_rol.id

    try:
        db.session.commit()
        flash("El rol del usuario fue actualizado correctamente.", "success")
    except Exception:
        db.session.rollback()
        flash("No fue posible actualizar el rol.", "danger")

    return redirect(url_for("main.administrar_usuarios"))

# ==========================================================
# REPORTES DEL CIUDADANO
# ==========================================================

@main.route("/panel/ciudadano/reportes")
@roles_required("Ciudadano")
def mis_reportes():
    reportes = (
        Reporte.query
        .filter_by(usuario_id=session["user_id"])
        .order_by(Reporte.fecha_creacion.desc())
        .all()
    )

    return render_template(
        "paneles/mis_reportes.html",
        reportes=reportes
    )


# ==========================================================
# DETALLE DE UN REPORTE
# ==========================================================

@main.route("/panel/ciudadano/reportes/<int:reporte_id>")
@roles_required("Ciudadano", "Administrador", "Fundacion")
def detalle_reporte(reporte_id):
    consulta = Reporte.query.filter_by(id=reporte_id)

    # Los ciudadanos solo pueden consultar sus propios reportes.
    if session.get("user_rol") == "Ciudadano":
        consulta = consulta.filter_by(
            usuario_id=session["user_id"]
        )

    reporte = consulta.first_or_404()

    return render_template(
        "paneles/detalle_reporte.html",
        reporte=reporte
    )



# ==========================================================
# GESTIÓN INTERNA DE REPORTES
# ==========================================================

@main.route("/panel/gestion-reportes")
@roles_required("Administrador", "Fundacion")
def gestionar_reportes():
    busqueda = request.args.get("buscar", "").strip()
    filtro_estado = request.args.get("estado", "").strip()

    consulta = (
    Reporte.query
    .join(Usuario, Reporte.usuario_id == Usuario.id)
    .options(joinedload(Reporte.estado))
    )

    if busqueda:
        patron = f"%{busqueda}%"
        consulta = consulta.filter(
            or_(
                Reporte.titulo.ilike(patron),
                Reporte.tipo.ilike(patron),
                Usuario.nombre.ilike(patron),
                Usuario.apellido.ilike(patron),
                Usuario.correo.ilike(patron)
            )
        )

    if filtro_estado.isdigit():
        consulta = consulta.filter(
            Reporte.estado_id == int(filtro_estado)
        )

    reportes = consulta.order_by(
        Reporte.fecha_creacion.desc()
    ).all()

    estados = EstadoReporte.query.order_by(
        EstadoReporte.id
    ).all()

    return render_template(
        "paneles/gestion_reportes.html",
        reportes=reportes,
        estados=estados,
        buscar=busqueda,
        filtro_estado=filtro_estado
    )


@main.route(
    "/panel/gestion-reportes/<int:reporte_id>/estado",
    methods=["POST"]
)
@roles_required("Administrador", "Fundacion")
def actualizar_estado_reporte(reporte_id):
    reporte = db.session.get(Reporte, reporte_id)

    if reporte is None:
        flash("El reporte solicitado no existe.", "danger")
        return redirect(url_for("main.gestionar_reportes"))

    estado_id = request.form.get("estado_id", type=int)
    nuevo_estado = (
        db.session.get(EstadoReporte, estado_id)
        if estado_id else None
    )

    if nuevo_estado is None:
        flash("Selecciona un estado válido.", "warning")
        return redirect(url_for("main.gestionar_reportes"))

    reporte.estado_id = nuevo_estado.id

    try:
        db.session.commit()
        flash(
            f"El estado del reporte #{reporte.id} "
            f"se actualizó a «{nuevo_estado.nombre}».",
            "success"
        )
    except Exception:
        db.session.rollback()
        flash(
            "No fue posible actualizar el estado del reporte.",
            "danger"
        )

    return redirect(url_for("main.gestionar_reportes"))

@main.route(
    "/panel/ciudadano/reportes/crear",
    methods=["GET", "POST"]
)
@roles_required("Ciudadano")
def crear_reporte():
    estados = EstadoReporte.query.order_by(
        EstadoReporte.id
    ).all()

    estado_pendiente = EstadoReporte.query.filter_by(
        nombre="Pendiente"
    ).first()

    if estado_pendiente is None:
        flash(
            "No se encontró el estado Pendiente en la base de datos.",
            "danger"
        )
        return redirect(url_for("main.mis_reportes"))

    if request.method == "POST":
        tipo = request.form.get("tipo", "").strip()
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        direccion = request.form.get("direccion", "").strip()

        tipos_permitidos = {
            "Abandono",
            "Maltrato",
            "Salud",
            "Bienestar",
            "Otro"
        }

        if (
            tipo not in tipos_permitidos
            or not titulo
            or not descripcion
        ):
            flash(
                "Selecciona un tipo válido y completa el título "
                "y la descripción.",
                "warning"
            )
            return render_template(
                "paneles/crear_reporte.html",
                estados=estados
            )

        if len(titulo) > 150 or len(tipo) > 100:
            flash(
                "El título o el tipo del reporte exceden "
                "la longitud permitida.",
                "warning"
            )
            return render_template(
                "paneles/crear_reporte.html",
                estados=estados
            )

        nuevo_reporte = Reporte(
            usuario_id=session["user_id"],
            estado_id=estado_pendiente.id,
            tipo=tipo,
            titulo=titulo,
            descripcion=descripcion,
            direccion=direccion or None
        )

        try:
            db.session.add(nuevo_reporte)
            db.session.commit()

            flash(
                "Reporte registrado correctamente.",
                "success"
            )
            return redirect(url_for("main.mis_reportes"))

        except Exception:
            db.session.rollback()
            flash(
                "No fue posible guardar el reporte. "
                "Inténtalo nuevamente.",
                "danger"
            )

    return render_template(
        "paneles/crear_reporte.html",
        estados=estados
    )


@main.route("/dashboard")
@roles_required("Administrador")
def dashboard():
    indicadores = obtener_indicadores_generales()
    reportes_estado = obtener_reportes_por_estado()
    reportes_tipo = obtener_reportes_por_tipo()
    reportes_mes = obtener_reportes_por_mes()

    return render_template(
        "dashboard.html",
        indicadores=indicadores,
        reportes_estado=reportes_estado,
        reportes_tipo=reportes_tipo,
        reportes_mes=reportes_mes,
    )