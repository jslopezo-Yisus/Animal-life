import smtplib
from email.message import EmailMessage

from config import Config


def enviar_correo(destinatario, asunto, mensaje):
    correo = Config.MAIL_USERNAME
    password = Config.MAIL_PASSWORD

    if not correo or not password:
        raise ValueError(
            "No se han configurado las credenciales SMTP."
        )

    email = EmailMessage()

    email["From"] = correo
    email["To"] = destinatario
    email["Subject"] = asunto

    email.set_content(mensaje)

    with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as servidor:
        servidor.starttls()
        servidor.login(correo, password)
        servidor.send_message(email)