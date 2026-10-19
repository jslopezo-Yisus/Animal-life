from flask import Flask

from config import Config
from app.extensions import db


def create_app():
    
    from app.models.animal import Animal
    from app.models.estado_reporte import EstadoReporte
    from app.models.reporte import Reporte
    from app.models.servicio import Servicio
    from app.models.cita import Cita
    from app.models.atencion_clinica import AtencionClinica

    app = Flask(__name__)

    # Configuración
    app.config.from_object(Config)

    # Inicializar base de datos
    db.init_app(app)

    # Importar modelos
    from app.models.rol import Rol
    from app.models.usuario import Usuario
    from app.models.estado_reporte import EstadoReporte
    from app.models.reporte import Reporte
    from app.models.adopcion import Adopcion

    # Registrar controlador principal
    from app.controllers.main_controller import main

    app.register_blueprint(main)

    # Registrar controlador de autenticación
    from app.controllers.auth_controller import auth

    app.register_blueprint(auth)

    return app