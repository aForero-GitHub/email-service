import pytest
import json
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api.email_routes import router  # Importa correctamente el router
from app.models import EmailRequest

client = TestClient(router)

# Aquí es donde hacemos el mock directamente del cliente de boto3
@patch('app.api.email_routes.sqs_client')  # Importa la referencia correcta de 'sqs_client'
def test_send_email_sqs(mock_sqs_client):
    # Crea un email de prueba
    email_data = EmailRequest(
        to="example@example.com",
        subject="Test Email",
        body="This is a test.",
        from_email="from@example.com"
    )

    # Simulamos una respuesta vacía del método send_message
    mock_sqs_client.send_message.return_value = {}

    # Envía la solicitud POST al endpoint
    response = client.post(
        "/send-email/",
        json=email_data.dict()  # Convierte el modelo en un diccionario JSON
    )

    # Verifica que la respuesta del servidor sea exitosa
    assert response.status_code == 200
    assert response.json() == {"message": "Email queued successfully"}

    # Asegúrate de que el método send_message haya sido llamado una vez
    mock_sqs_client.send_message.assert_called_once()
