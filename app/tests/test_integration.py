from moto import mock_aws
import pytest
import json
from unittest.mock import patch
import boto3
from fastapi.testclient import TestClient
from app.main import app
from app.models import EmailRequest
from app.core.config import SQS_QUEUE_URL

client = TestClient(app)

@mock_aws
def test_integration_sqs_to_email_provider():
    # Mock SQS creation
    sqs = boto3.client("sqs", region_name="us-east-2")
    sqs.create_queue(QueueName=SQS_QUEUE_URL.split("/")[-1])  # Create queue using the correct name

    email_data = EmailRequest(
        to="example@example.com",
        subject="Test Email Integration",
        body="This is an integration test.",
        from_email="foreromartinez.andres@gmail.com"
    )

    # Mock Redis and SendGrid/SES services
    with patch('app.services.email_service.RedisHandler.get_usage_count', return_value=0), \
         patch('app.services.email_service.RedisHandler.get_predicted_latency', return_value=0.2), \
         patch('app.services.email_service.SendGridService.send_email') as mock_sendgrid, \
         patch('app.services.email_service.SESService.send_email') as mock_ses:

        # Step 1: Send a POST request to enqueue the email
        response = client.post("/send-email/", json=email_data.model_dump())

        # Assert successful queuing
        assert response.status_code == 200
        assert response.json() == {"message": "Email queued successfully"}

        # Step 2: Simulate SQS event and process the queue
        from app.workers.sqs_worker import process_email_queue

        sqs_event = {
            "Records": [
                {
                    "body": json.dumps(email_data.model_dump())
                }
            ]
        }

        # Process the queue and assert that SendGrid was used
        process_email_queue(sqs_event, None)
        mock_sendgrid.assert_called_once()
        mock_ses.assert_not_called()
