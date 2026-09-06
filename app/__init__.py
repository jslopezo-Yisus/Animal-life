from flask import Flask

from config import Config
from app.extensions import db


def create_app():

    app = Flask(__name__)

    # Configuración
    app.config.from_object(Config)

    # Inicializar base de datos
    db.init_app(app)

    # Registrar controladores
    from app.controllers.main_controller import main

    app.register_blueprint(main)

    # Importar modelos
    from app.models.usuario import Usuario

    # Crear tablas
    with app.app_context():
        db.create_all()

    return app