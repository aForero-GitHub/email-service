import os
import sendgrid
from sendgrid.helpers.mail import Mail
from typing import Optional
from ..core.config import SENDGRID_API_KEY, SES_EMAIL_FROM

class SendGridService:
    def __init__(self) -> None:
        # Cargamos la API Key de SendGrid desde las variables de entorno
        self.api_key = os.getenv("SENDGRID_API_KEY", SENDGRID_API_KEY)
        if not self.api_key:
            raise ValueError("La clave de API de SendGrid no está configurada.")
        self.client = sendgrid.SendGridAPIClient(self.api_key)

    def send_email(self, to: str, subject: str, body: str, from_email: Optional[str] = None) -> any:
        """
        Envía un correo electrónico utilizando el servicio de SendGrid.
        """
        if not from_email:
            from_email = os.getenv("SES_EMAIL_FROM", SES_EMAIL_FROM)  # Puedes configurar un valor predeterminado
        
        # Crear el mensaje de correo
        message = Mail(
            from_email=from_email,
            to_emails=to,
            subject=subject,
            html_content=body
        )
        
        # Enviar el mensaje a través de SendGrid
        response = self.client.send(message)

        # Validar que el correo se haya enviado exitosamente
        if response.status_code != 202:
            raise Exception(f"SendGrid falló con el estado: {response.status_code}")
        
        return response
