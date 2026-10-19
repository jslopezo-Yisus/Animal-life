from app.services.analytics_service import (
    obtener_indicadores_generales,
    obtener_reportes_por_estado,
    obtener_reportes_por_tipo,
    obtener_reportes_por_mes,
)
from functools import wraps
import os
import uuid
from datetime import date

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app,
)
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.reporte import Reporte
from app.models.estado_reporte import EstadoReporte
from app.models.animal import Animal
from app.models.adopcion import Adopcion
from datetime import datetime, date, time
from app.models.servicio import Servicio
from app.models.cita import Cita
from app.models.evidencia import Evidencia

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


# ==========================================================
# ASIGNACIONES DEL TECNICO
# ==========================================================

@main.route("/panel/tecnico/asignaciones")
@roles_required("Tecnico")
def asignaciones_tecnico():
    tecnico_id = session.get("user_id")
    reportes = (
        Reporte.query
        .filter_by(responsable_id=tecnico_id)
        .order_by(Reporte.fecha_actualizacion.desc())
        .all()
    )
    estados = EstadoReporte.query.order_by(EstadoReporte.id).all()
    return render_template(
        "paneles/asignaciones_tecnico.html",
        reportes=reportes,
        estados=estados,
    )


@main.route("/panel/tecnico/asignaciones/<int:reporte_id>/estado", methods=["POST"])
@roles_required("Tecnico")
def actualizar_estado_reporte_tecnico(reporte_id):
    tecnico_id = session.get("user_id")
    reporte = Reporte.query.filter_by(
        id=reporte_id, responsable_id=tecnico_id
    ).first()

    if reporte is None:
        flash("El caso no existe o no está asignado a tu usuario.", "danger")
        return redirect(url_for("main.asignaciones_tecnico"))

    estado_nuevo_id = request.form.get("estado_id", type=int)
    estado_nuevo = db.session.get(EstadoReporte, estado_nuevo_id) if estado_nuevo_id else None
    if estado_nuevo is None:
        flash("Selecciona un estado válido.", "warning")
        return redirect(url_for("main.asignaciones_tecnico"))

    transiciones = {
        "Asignado": ["En proceso"],
        "En proceso": ["Resuelto"],
    }
    permitidos = transiciones.get(reporte.estado.nombre, [])
    if estado_nuevo.nombre not in permitidos:
        flash("Ese cambio de estado no está permitido para este caso.", "warning")
        return redirect(url_for("main.asignaciones_tecnico"))

    reporte.estado_id = estado_nuevo.id
    try:
        db.session.commit()
        flash(f"El caso #{reporte.id} se actualizó a «{estado_nuevo.nombre}».", "success")
    except Exception:
        db.session.rollback()
        flash("No fue posible actualizar el caso.", "danger")
    return redirect(url_for("main.asignaciones_tecnico"))


@main.route("/panel/fundacion")
@roles_required("Fundacion")
def panel_fundacion():
    return render_template("paneles/fundacion.html")


# ==========================================================
# GESTIÓN DE ANIMALES
# ==========================================================

ESTADOS_ANIMAL = [
    "Disponible",
    "En tratamiento",
    "En adopción",
    "Adoptado",
    "No disponible",
]


@main.route("/panel/fundacion/animales")
@roles_required("Fundacion", "Administrador")
def gestionar_animales():
    busqueda = request.args.get("buscar", "").strip()
    filtro_especie = request.args.get("especie", "").strip()
    filtro_estado = request.args.get("estado", "").strip()

    consulta = Animal.query

    if busqueda:
        patron = f"%{busqueda}%"
        consulta = consulta.filter(
            or_(
                Animal.nombre.ilike(patron),
                Animal.raza.ilike(patron),
                Animal.color.ilike(patron),
            )
        )

    if filtro_especie:
        consulta = consulta.filter(
            Animal.especie == filtro_especie
        )

    if filtro_estado in ESTADOS_ANIMAL:
        consulta = consulta.filter(
            Animal.estado == filtro_estado
        )

    animales = consulta.order_by(
        Animal.fecha_registro.desc()
    ).all()

    especies = [
        especie[0]
        for especie in db.session.query(
            Animal.especie
        ).distinct().order_by(Animal.especie).all()
        if especie[0]
    ]

    return render_template(
        "paneles/animales.html",
        animales=animales,
        especies=especies,
        estados=ESTADOS_ANIMAL,
        buscar=busqueda,
        filtro_especie=filtro_especie,
        filtro_estado=filtro_estado,
    )


@main.route(
    "/panel/fundacion/animales/crear",
    methods=["GET", "POST"],
)
@roles_required("Fundacion", "Administrador")
def crear_animal():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        especie = request.form.get("especie", "").strip()
        raza = request.form.get("raza", "").strip()
        sexo = request.form.get("sexo", "").strip()
        fecha_texto = request.form.get(
            "fecha_nacimiento", ""
        ).strip()
        tamano = request.form.get("tamano", "").strip()
        color = request.form.get("color", "").strip()
        descripcion = request.form.get(
            "descripcion", ""
        ).strip()
        estado = request.form.get(
            "estado", "Disponible"
        ).strip()

        fecha_nacimiento = None

        if fecha_texto:
            try:
                fecha_nacimiento = date.fromisoformat(
                    fecha_texto
                )
            except ValueError:
                flash(
                    "La fecha de nacimiento no es válida.",
                    "warning",
                )
                return render_template(
                    "paneles/formulario_animal.html",
                    animal=None,
                    estados=ESTADOS_ANIMAL,
                )

        if (
            not nombre
            or not especie
            or len(nombre) > 100
            or len(especie) > 50
            or len(raza) > 100
            or len(sexo) > 20
            or len(tamano) > 30
            or len(color) > 100
            or estado not in ESTADOS_ANIMAL
        ):
            flash(
                "Verifica los campos obligatorios y sus "
                "longitudes antes de continuar.",
                "warning",
            )
            return render_template(
                "paneles/formulario_animal.html",
                animal=None,
                estados=ESTADOS_ANIMAL,
            )

        if fecha_nacimiento and fecha_nacimiento > date.today():
            flash(
                "La fecha de nacimiento no puede ser futura.",
                "warning",
            )
            return render_template(
                "paneles/formulario_animal.html",
                animal=None,
                estados=ESTADOS_ANIMAL,
            )

        nuevo_animal = Animal(
            nombre=nombre,
            especie=especie,
            raza=raza or None,
            sexo=sexo or None,
            fecha_nacimiento=fecha_nacimiento,
            tamano=tamano or None,
            color=color or None,
            descripcion=descripcion or None,
            estado=estado,
        )

        try:
            db.session.add(nuevo_animal)
            db.session.commit()
            flash(
                f"El animal {nuevo_animal.nombre} fue registrado.",
                "success",
            )
            return redirect(
                url_for("main.gestionar_animales")
            )
        except Exception:
            db.session.rollback()
            flash(
                "No fue posible registrar el animal.",
                "danger",
            )

    return render_template(
    "paneles/formulario_animal.html",
    animal=None,
    estados=ESTADOS_ANIMAL,
    today=date.today().isoformat(),
    )


@main.route(
    "/panel/fundacion/animales/<int:animal_id>/editar",
    methods=["GET", "POST"],
)
@roles_required("Fundacion", "Administrador")
def editar_animal(animal_id):
    animal = db.session.get(Animal, animal_id)

    if animal is None:
        flash("El animal solicitado no existe.", "danger")
        return redirect(
            url_for("main.gestionar_animales")
        )

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        especie = request.form.get("especie", "").strip()
        raza = request.form.get("raza", "").strip()
        sexo = request.form.get("sexo", "").strip()
        fecha_texto = request.form.get(
            "fecha_nacimiento", ""
        ).strip()
        tamano = request.form.get("tamano", "").strip()
        color = request.form.get("color", "").strip()
        descripcion = request.form.get(
            "descripcion", ""
        ).strip()
        estado = request.form.get("estado", "").strip()

        fecha_nacimiento = None

        if fecha_texto:
            try:
                fecha_nacimiento = date.fromisoformat(
                    fecha_texto
                )
            except ValueError:
                flash(
                    "La fecha de nacimiento no es válida.",
                    "warning",
                )
                return render_template(
                    "paneles/formulario_animal.html",
                    animal=animal,
                    estados=ESTADOS_ANIMAL,
                )

        if (
            not nombre
            or not especie
            or len(nombre) > 100
            or len(especie) > 50
            or len(raza) > 100
            or len(sexo) > 20
            or len(tamano) > 30
            or len(color) > 100
            or estado not in ESTADOS_ANIMAL
        ):
            flash(
                "Verifica los campos obligatorios y sus "
                "longitudes antes de continuar.",
                "warning",
            )
            return render_template(
                "paneles/formulario_animal.html",
                animal=animal,
                estados=ESTADOS_ANIMAL,
            )

        if fecha_nacimiento and fecha_nacimiento > date.today():
            flash(
                "La fecha de nacimiento no puede ser futura.",
                "warning",
            )
            return render_template(
                "paneles/formulario_animal.html",
                animal=animal,
                estados=ESTADOS_ANIMAL,
            )

        animal.nombre = nombre
        animal.especie = especie
        animal.raza = raza or None
        animal.sexo = sexo or None
        animal.fecha_nacimiento = fecha_nacimiento
        animal.tamano = tamano or None
        animal.color = color or None
        animal.descripcion = descripcion or None
        animal.estado = estado

        try:
            db.session.commit()
            flash(
                "La información del animal fue actualizada.",
                "success",
            )
            return redirect(
                url_for("main.gestionar_animales")
            )
        except Exception:
            db.session.rollback()
            flash(
                "No fue posible actualizar el animal.",
                "danger",
            )

    return render_template(
    "paneles/formulario_animal.html",
    animal=animal,
    estados=ESTADOS_ANIMAL,
    today=date.today().isoformat(),
    )


@main.route(
    "/panel/fundacion/animales/<int:animal_id>/estado",
    methods=["POST"],
)
@roles_required("Fundacion", "Administrador")
def cambiar_estado_animal(animal_id):
    animal = db.session.get(Animal, animal_id)

    if animal is None:
        flash("El animal solicitado no existe.", "danger")
        return redirect(
            url_for("main.gestionar_animales")
        )

    nuevo_estado = request.form.get("estado", "").strip()

    if nuevo_estado not in ESTADOS_ANIMAL:
        flash("Selecciona un estado válido.", "warning")
        return redirect(
            url_for("main.gestionar_animales")
        )

    animal.estado = nuevo_estado

    try:
        db.session.commit()
        flash(
            f"El estado de {animal.nombre} cambió a "
            f"{nuevo_estado}.",
            "success",
        )
    except Exception:
        db.session.rollback()
        flash(
            "No fue posible cambiar el estado del animal.",
            "danger",
        )

    return redirect(
        url_for("main.gestionar_animales")
    )

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
# SOLICITUDES DE ADOPCIÓN
# ==========================================================

ESTADOS_ADOPCION = ["Pendiente", "Aprobada", "Rechazada"]


@main.route("/panel/ciudadano/adopciones")
@roles_required("Ciudadano")
def animales_para_adopcion():
    animales = (
        Animal.query
        .filter_by(estado="Disponible")
        .order_by(Animal.fecha_registro.desc())
        .all()
    )

    solicitudes = (
        Adopcion.query
        .filter_by(usuario_id=session["user_id"])
        .order_by(Adopcion.fecha_solicitud.desc())
        .all()
    )

    return render_template(
        "paneles/adopciones_ciudadano.html",
        animales=animales,
        solicitudes=solicitudes,
    )


@main.route(
    "/panel/ciudadano/adopciones/solicitar/<int:animal_id>",
    methods=["POST"],
)
@roles_required("Ciudadano")
def solicitar_adopcion(animal_id):
    animal = db.session.get(Animal, animal_id)

    if animal is None:
        flash("El animal solicitado no existe.", "danger")
        return redirect(url_for("main.animales_para_adopcion"))

    if animal.estado != "Disponible":
        flash(
            "Este animal ya no está disponible para adopción.",
            "warning",
        )
        return redirect(url_for("main.animales_para_adopcion"))

    usuario_id = session["user_id"]

    solicitud_existente = Adopcion.query.filter(
        Adopcion.animal_id == animal.id,
        Adopcion.usuario_id == usuario_id,
        Adopcion.estado == "Pendiente",
    ).first()

    if solicitud_existente:
        flash(
            "Ya tienes una solicitud pendiente para este animal.",
            "warning",
        )
        return redirect(url_for("main.animales_para_adopcion"))

    nueva_solicitud = Adopcion(
        animal_id=animal.id,
        usuario_id=usuario_id,
        estado="Pendiente",
        observaciones=None,
    )

    try:
        db.session.add(nueva_solicitud)
        db.session.commit()

        flash(
            f"Tu solicitud para adoptar a {animal.nombre} "
            "fue registrada correctamente.",
            "success",
        )
    except Exception:
        db.session.rollback()
        flash(
            "No fue posible registrar la solicitud. "
            "Inténtalo nuevamente.",
            "danger",
        )

    return redirect(url_for("main.animales_para_adopcion"))


# ==========================================================
# GESTIÓN DE SOLICITUDES DE ADOPCIÓN
# ==========================================================

@main.route("/panel/fundacion/adopciones")
@roles_required("Fundacion", "Administrador")
def gestionar_adopciones():
    filtro_estado = request.args.get("estado", "").strip()

    consulta = Adopcion.query

    if filtro_estado in ESTADOS_ADOPCION:
        consulta = consulta.filter(
            Adopcion.estado == filtro_estado
        )

    solicitudes = consulta.order_by(
        Adopcion.fecha_solicitud.desc()
    ).all()

    return render_template(
        "paneles/gestion_adopciones.html",
        solicitudes=solicitudes,
        estados=ESTADOS_ADOPCION,
        filtro_estado=filtro_estado,
    )


@main.route(
    "/panel/fundacion/adopciones/<int:solicitud_id>/resolver",
    methods=["POST"],
)
@roles_required("Fundacion", "Administrador")
def resolver_adopcion(solicitud_id):
    solicitud = db.session.get(Adopcion, solicitud_id)

    if solicitud is None:
        flash("La solicitud de adopción no existe.", "danger")
        return redirect(url_for("main.gestionar_adopciones"))

    if solicitud.estado != "Pendiente":
        flash(
            "Esta solicitud ya fue resuelta y no puede modificarse.",
            "warning",
        )
        return redirect(url_for("main.gestionar_adopciones"))

    decision = request.form.get("estado", "").strip()
    observaciones = request.form.get("observaciones", "").strip()

    if decision not in ["Aprobada", "Rechazada"]:
        flash("Selecciona una decisión válida.", "warning")
        return redirect(url_for("main.gestionar_adopciones"))

    if len(observaciones) > 65535:
        flash("Las observaciones son demasiado extensas.", "warning")
        return redirect(url_for("main.gestionar_adopciones"))

    animal = db.session.get(Animal, solicitud.animal_id)

    if animal is None:
        flash(
            "No se encontró el animal asociado a la solicitud.",
            "danger",
        )
        return redirect(url_for("main.gestionar_adopciones"))

    if decision == "Aprobada" and animal.estado != "Disponible":
        flash(
            "No se puede aprobar: el animal ya no está disponible.",
            "warning",
        )
        return redirect(url_for("main.gestionar_adopciones"))

    try:
        solicitud.estado = decision
        solicitud.fecha_respuesta = datetime.now()
        solicitud.observaciones = observaciones or None

        if decision == "Aprobada":
            animal.estado = "Adoptado"

            # Cerrar otras solicitudes pendientes del mismo animal.
            otras_solicitudes = Adopcion.query.filter(
                Adopcion.animal_id == animal.id,
                Adopcion.id != solicitud.id,
                Adopcion.estado == "Pendiente",
            ).all()

            for otra in otras_solicitudes:
                otra.estado = "Rechazada"
                otra.fecha_respuesta = datetime.now()
                otra.observaciones = (
                    "Solicitud cerrada porque el animal "
                    "fue asignado a otra adopción."
                )

        db.session.commit()

        flash(
            "La solicitud fue "
            f"{'aprobada' if decision == 'Aprobada' else 'rechazada'} "
            "correctamente.",
            "success",
        )

    except Exception:
        db.session.rollback()
        flash(
            "No fue posible resolver la solicitud. "
            "Inténtalo nuevamente.",
            "danger",
        )

    return redirect(url_for("main.gestionar_adopciones"))

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
@roles_required(
    "Ciudadano",
    "Administrador",
    "Fundacion",
    "Tecnico",
)
def detalle_reporte(reporte_id):
    consulta = Reporte.query.filter_by(id=reporte_id)
    rol = session.get("user_rol")

    if rol == "Ciudadano":
        consulta = consulta.filter_by(
            usuario_id=session["user_id"]
        )
    elif rol == "Tecnico":
        consulta = consulta.filter_by(
            responsable_id=session["user_id"]
        )

    reporte = consulta.first_or_404()
    evidencias = (
        Evidencia.query
        .filter_by(reporte_id=reporte.id)
        .order_by(Evidencia.fecha_subida.desc())
        .all()
    )
    puede_subir_evidencia = (
        rol in ("Administrador", "Fundacion")
        or (rol == "Tecnico" and reporte.responsable_id == session.get("user_id"))
    )

    return render_template(
        "paneles/detalle_reporte.html",
        reporte=reporte,
        evidencias=evidencias,
        puede_subir_evidencia=puede_subir_evidencia,
    )


@main.route(
    "/panel/reportes/<int:reporte_id>/evidencias/subir",
    methods=["POST"],
)
@roles_required("Administrador", "Fundacion", "Tecnico")
def subir_evidencia_reporte(reporte_id):
    rol = session.get("user_rol")
    consulta = Reporte.query.filter_by(id=reporte_id)

    if rol == "Tecnico":
        consulta = consulta.filter_by(responsable_id=session.get("user_id"))

    reporte = consulta.first()
    if reporte is None:
        flash("El reporte no existe o no tienes permiso para adjuntar evidencias.", "danger")
        return redirect(url_for("main.asignaciones_tecnico") if rol == "Tecnico" else url_for("main.gestionar_reportes"))

    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        flash("Selecciona un archivo para adjuntar.", "warning")
        return redirect(url_for("main.detalle_reporte", reporte_id=reporte.id))

    if request.content_length and request.content_length > 5 * 1024 * 1024:
        flash("El archivo supera el límite de 5 MB.", "warning")
        return redirect(url_for("main.detalle_reporte", reporte_id=reporte.id))

    nombre_seguro = secure_filename(archivo.filename)
    extension = nombre_seguro.rsplit(".", 1)[-1].lower() if "." in nombre_seguro else ""
    extensiones_permitidas = {"jpg", "jpeg", "png", "webp", "pdf"}
    if not nombre_seguro or extension not in extensiones_permitidas:
        flash("Formato no permitido. Usa JPG, JPEG, PNG, WEBP o PDF.", "warning")
        return redirect(url_for("main.detalle_reporte", reporte_id=reporte.id))

    nombre_guardado = f"reporte_{reporte.id}_{uuid.uuid4().hex}.{extension}"
    carpeta = os.path.join(current_app.root_path, "static", "uploads", "evidencias")
    os.makedirs(carpeta, exist_ok=True)
    ruta_fisica = os.path.join(carpeta, nombre_guardado)
    ruta_relativa = f"uploads/evidencias/{nombre_guardado}"

    try:
        archivo.save(ruta_fisica)
        evidencia = Evidencia(
            reporte_id=reporte.id,
            nombre_archivo=nombre_seguro,
            ruta_archivo=ruta_relativa,
            tipo_archivo=archivo.mimetype or ("application/pdf" if extension == "pdf" else f"image/{extension}"),
        )
        db.session.add(evidencia)
        db.session.commit()
        flash("La evidencia se adjuntó correctamente.", "success")
    except Exception:
        db.session.rollback()
        if os.path.exists(ruta_fisica):
            os.remove(ruta_fisica)
        flash("No fue posible guardar la evidencia. Inténtalo nuevamente.", "danger")

    return redirect(url_for("main.detalle_reporte", reporte_id=reporte.id))




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
        .options(
            joinedload(Reporte.estado),
            joinedload(Reporte.usuario),
            joinedload(Reporte.responsable)
        )
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

    responsables = (
        Usuario.query
        .join(Rol)
        .filter(
            Usuario.estado.is_(True),
            Rol.nombre.in_([
                "Tecnico",
                "Veterinario",
                "Fundacion"
            ])
        )
        .order_by(Usuario.nombre.asc())
        .all()
    )

    return render_template(
        "paneles/gestion_reportes.html",
        reportes=reportes,
        estados=estados,
        responsables=responsables,
        buscar=busqueda,
        filtro_estado=filtro_estado
    )


# ==========================================================
# ACTUALIZAR ESTADO DE UN REPORTE
# ==========================================================

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


# ==========================================================
# ASIGNAR RESPONSABLE A UN REPORTE
# ==========================================================

@main.route(
    "/panel/gestion-reportes/<int:reporte_id>/responsable",
    methods=["POST"]
)
@roles_required("Administrador", "Fundacion")
def asignar_responsable_reporte(reporte_id):
    reporte = db.session.get(Reporte, reporte_id)

    if reporte is None:
        flash("El reporte solicitado no existe.", "danger")
        return redirect(url_for("main.gestionar_reportes"))

    responsable_id = request.form.get(
        "responsable_id",
        type=int
    )

    if responsable_id is None:
        flash("Selecciona un responsable válido.", "warning")
        return redirect(url_for("main.gestionar_reportes"))

    responsable = (
        Usuario.query
        .join(Rol)
        .filter(
            Usuario.id == responsable_id,
            Usuario.estado.is_(True),
            Rol.nombre.in_([
                "Tecnico",
                "Veterinario",
                "Fundacion"
            ])
        )
        .first()
    )

    if responsable is None:
        flash(
            "El responsable seleccionado no existe, "
            "está inactivo o no tiene un rol permitido.",
            "warning"
        )
        return redirect(url_for("main.gestionar_reportes"))

    reporte.responsable_id = responsable.id

    estado_asignado = EstadoReporte.query.filter_by(
        nombre="Asignado"
    ).first()

    if estado_asignado:
        reporte.estado_id = estado_asignado.id

    try:
        db.session.commit()
        flash(
            f"El reporte #{reporte.id} fue asignado a "
            f"{responsable.nombre} {responsable.apellido}.",
            "success"
        )
    except Exception:
        db.session.rollback()
        flash(
            "No fue posible asignar el responsable.",
            "danger"
        )

    return redirect(url_for("main.gestionar_reportes"))


# ==========================================================
# CREAR REPORTE
# ==========================================================

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


# ==========================================================
# SERVICIOS DISPONIBLES PARA EL CIUDADANO
# ==========================================================

@main.route("/panel/ciudadano/servicios")
@roles_required("Ciudadano")
def consultar_servicios():
    servicios = (
        Servicio.query
        .filter_by(estado=True)
        .order_by(Servicio.nombre.asc())
        .all()
    )

    animales = (
        Animal.query
        .filter_by(estado="Disponible")
        .order_by(Animal.nombre.asc())
        .all()
    )

    return render_template(
        "paneles/servicios_ciudadano.html",
        servicios=servicios,
        animales=animales,
        hoy=date.today().isoformat(),
    )


# ==========================================================
# SOLICITAR UNA CITA
# ==========================================================

@main.route(
    "/panel/ciudadano/citas/crear",
    methods=["POST"],
)
@roles_required("Ciudadano")
def crear_cita():
    servicio_id = request.form.get("servicio_id", type=int)
    animal_id = request.form.get("animal_id", type=int)
    fecha_texto = request.form.get("fecha", "").strip()
    hora_texto = request.form.get("hora", "").strip()
    observaciones = request.form.get("observaciones", "").strip()

    if not servicio_id or not animal_id or not fecha_texto or not hora_texto:
        flash("Completa todos los campos obligatorios.", "warning")
        return redirect(url_for("main.consultar_servicios"))

    servicio = db.session.get(Servicio, servicio_id)
    animal = db.session.get(Animal, animal_id)

    if not servicio or not servicio.estado:
        flash("El servicio seleccionado no está disponible.", "warning")
        return redirect(url_for("main.consultar_servicios"))

    if not animal or animal.estado in ["Adoptado", "No disponible"]:
        flash("El animal seleccionado no está disponible.", "warning")
        return redirect(url_for("main.consultar_servicios"))

    try:
        fecha_cita = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
        hora_cita = datetime.strptime(hora_texto, "%H:%M").time()
    except ValueError:
        flash("La fecha o la hora no tienen un formato válido.", "warning")
        return redirect(url_for("main.consultar_servicios"))

    if fecha_cita < date.today():
        flash("No puedes solicitar una cita en una fecha pasada.", "warning")
        return redirect(url_for("main.consultar_servicios"))

    if fecha_cita == date.today() and hora_cita <= datetime.now().time():
        flash("Selecciona una hora futura para la cita.", "warning")
        return redirect(url_for("main.consultar_servicios"))

    if len(observaciones) > 5000:
        flash("Las observaciones son demasiado extensas.", "warning")
        return redirect(url_for("main.consultar_servicios"))

    # Evitar solicitudes duplicadas para el mismo animal,
    # fecha y hora, mientras la cita no esté cancelada o rechazada.
    cita_existente = Cita.query.filter(
        Cita.animal_id == animal_id,
        Cita.fecha == fecha_cita,
        Cita.hora == hora_cita,
        Cita.estado.notin_(["Cancelada", "Rechazada"]),
    ).first()

    if cita_existente:
        flash(
            "Ese animal ya tiene una cita registrada para esa fecha y hora.",
            "warning",
        )
        return redirect(url_for("main.consultar_servicios"))

    nueva_cita = Cita(
        usuario_id=session["user_id"],
        animal_id=animal_id,
        servicio_id=servicio_id,
        fecha=fecha_cita,
        hora=hora_cita,
        estado="Pendiente",
        observaciones=observaciones or None,
    )

    try:
        db.session.add(nueva_cita)
        db.session.commit()
        flash("Tu solicitud de cita fue registrada correctamente.", "success")
    except Exception:
        db.session.rollback()
        flash("No fue posible registrar la cita. Inténtalo nuevamente.", "danger")

    return redirect(url_for("main.mis_citas"))


# ==========================================================
# CONSULTAR LAS CITAS DEL CIUDADANO
# ==========================================================

@main.route("/panel/ciudadano/citas")
@roles_required("Ciudadano")
def mis_citas():
    citas = (
        Cita.query
        .filter_by(usuario_id=session["user_id"])
        .order_by(Cita.fecha.desc(), Cita.hora.desc())
        .all()
    )

    return render_template(
        "paneles/mis_citas.html",
        citas=citas,
    )


# ==========================================================
# CANCELAR UNA CITA PROPIA
# ==========================================================

@main.route(
    "/panel/ciudadano/citas/<int:cita_id>/cancelar",
    methods=["POST"],
)
@roles_required("Ciudadano")
def cancelar_cita(cita_id):
    cita = Cita.query.filter_by(
        id=cita_id,
        usuario_id=session["user_id"],
    ).first()

    if not cita:
        flash("No se encontró la cita solicitada.", "danger")
        return redirect(url_for("main.mis_citas"))

    if cita.estado != "Pendiente":
        flash("Solo puedes cancelar citas que estén pendientes.", "warning")
        return redirect(url_for("main.mis_citas"))

    cita.estado = "Cancelada"

    try:
        db.session.commit()
        flash("La cita fue cancelada correctamente.", "success")
    except Exception:
        db.session.rollback()
        flash("No fue posible cancelar la cita.", "danger")

    return redirect(url_for("main.mis_citas"))


# ==========================================================
# GESTIÓN DE CITAS PARA PERSONAL AUTORIZADO
# ==========================================================

@main.route("/panel/gestion-citas")
@roles_required("Fundacion", "Administrador", "Veterinario")
def gestionar_citas():
    filtro_estado = request.args.get("estado", "").strip()

    estados_permitidos = [
        "Pendiente",
        "Confirmada",
        "En proceso",
        "Completada",
        "Cancelada",
        "Rechazada",
    ]

    consulta = Cita.query

    if filtro_estado in estados_permitidos:
        consulta = consulta.filter(Cita.estado == filtro_estado)

    citas = consulta.order_by(
        Cita.fecha.asc(),
        Cita.hora.asc(),
    ).all()

    transiciones_cita = {
        "Pendiente": ["Confirmada", "Cancelada", "Rechazada"],
        "Confirmada": ["En proceso", "Cancelada", "Rechazada"],
        "En proceso": ["Completada"],
        "Completada": [],
        "Cancelada": [],
        "Rechazada": [],
    }

    return render_template(
        "paneles/gestion_citas.html",
        citas=citas,
        estados=estados_permitidos,
        filtro_estado=filtro_estado,
        transiciones_cita=transiciones_cita,
    )


@main.route(
    "/panel/gestion-citas/<int:cita_id>/estado",
    methods=["POST"],
)
@roles_required("Fundacion", "Administrador", "Veterinario")
def actualizar_estado_cita(cita_id):
    cita = db.session.get(Cita, cita_id)

    if not cita:
        flash("No se encontró la cita.", "danger")
        return redirect(url_for("main.gestionar_citas"))

    estado_nuevo = request.form.get("estado", "").strip()

    transiciones_permitidas = {
        "Pendiente": ["Confirmada", "Cancelada", "Rechazada"],
        "Confirmada": ["En proceso", "Cancelada", "Rechazada"],
        "En proceso": ["Completada"],
        "Completada": [],
        "Cancelada": [],
        "Rechazada": [],
    }

    estados_disponibles = transiciones_permitidas.get(cita.estado, [])

    if estado_nuevo not in estados_disponibles:
        flash(
            "La transición seleccionada no está permitida "
            "para el estado actual de la cita.",
            "warning",
        )
        return redirect(url_for("main.gestionar_citas"))

    cita.estado = estado_nuevo

    try:
        db.session.commit()
        flash("El estado de la cita se actualizó correctamente.", "success")
    except Exception:
        db.session.rollback()
        flash("No fue posible actualizar el estado de la cita.", "danger")

    return redirect(url_for("main.gestionar_citas"))