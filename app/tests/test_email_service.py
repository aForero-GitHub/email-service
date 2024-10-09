import pytest
from unittest.mock import patch
from app.services.email_service import EmailService
from app.models import EmailRequest

@pytest.fixture
def email_service():
    return EmailService()

# Ajuste 1: Mock de Redis, SendGrid y SES correctamente
@patch('app.services.email_service.RedisHandler')
@patch('app.services.email_service.SendGridService.send_email')  # Debemos mockear el método send_email del servicio
@patch('app.services.email_service.SESService.send_email')
def test_send_email_with_sendgrid(mock_ses_send_email, mock_sendgrid_send_email, mock_redis, email_service):
    email_data = EmailRequest(
        to="example@example.com",
        subject="Test Email",
        body="This is a test.",
        from_email="foreromartinez.andres@gmail.com"
    )

    # Simulamos que SendGrid es el proveedor seleccionado
    mock_redis.get_usage_count.return_value = 0
    mock_redis.get_predicted_latency.return_value = 0.2
    
    provider_used = email_service.send_email(email_data)

    # Validamos que SendGrid fue utilizado
    assert provider_used == "SendGrid"
    mock_sendgrid_send_email.assert_called_once()  # Aseguramos que el método send_email fue llamado en SendGrid

# Ajuste 2: Mock de Redis y lógica para cambiar a SES
@patch('app.services.email_service.RedisHandler')
@patch('app.services.email_service.SendGridService.send_email')
@patch('app.services.email_service.SESService.send_email')
def test_send_email_with_ses(mock_ses_send_email, mock_sendgrid_send_email, mock_redis, email_service):
    email_data = EmailRequest(
        to="example@example.com",
        subject="Test Email with SES",
        body="This is another test.",
        from_email="foreromartinez.andres@gmail.com"
    )

    # Simulamos que SendGrid fue utilizado 2 veces y que SES debe ser seleccionado
    mock_redis.get_usage_count.side_effect = [2, 0]  # Primer proveedor (SendGrid) se usa 2 veces
    mock_redis.get_predicted_latency.return_value = 0.2
    
    provider_used = email_service.send_email(email_data)

    # Validamos que SES fue utilizado
    assert provider_used == "Amazon SES"
    mock_ses_send_email.assert_called_once()  # Aseguramos que el método send_email fue llamado en SES
