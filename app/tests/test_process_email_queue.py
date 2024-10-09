import pytest
from unittest.mock import patch
from app.workers import process_email_queue  # Asegúrate de que esta ruta sea correcta

# Ajusta el patch al lugar correcto donde se usa `EmailService`
@patch('app.services.email_service.EmailService.send_email')
def test_process_email_queue(mock_send_email):
    # Simulamos un evento de SQS con un mensaje
    event = {
        "Records": [
            {
                "body": '{"to": "example@example.com", "subject": "Test", "body": "This is a test.", "from_email": "from@example.com"}'
            }
        ]
    }

    # Llamamos a la función que procesa el correo
    process_email_queue(event, None)

    # Validamos que el servicio de correo fue llamado
    mock_send_email.assert_called_once()
