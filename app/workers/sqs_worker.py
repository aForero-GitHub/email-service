import json
from ..services.email_service import EmailService

email_service = EmailService()

def process_email_queue(event, context) -> None:
    """
    Procesa los correos encolados y los envía.
    """
    for record in event['Records']:
        email_data = json.loads(record['body'])
        try:
            email_service.send_email(email_data)
            print(f"Correo enviado con éxito: {email_data}")
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
