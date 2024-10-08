import boto3
import os
from botocore.exceptions import BotoCoreError, ClientError
from typing import Optional
from ..core.config import AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, SES_EMAIL_FROM

class SESService:
    def __init__(self) -> None:
        # Inicializar el cliente de SES con las credenciales de AWS
        self.client = boto3.client(
            'ses',
            region_name=os.getenv("AWS_REGION", AWS_REGION),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", AWS_ACCESS_KEY_ID),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", AWS_SECRET_ACCESS_KEY)
        )

    def send_email(self, to: str, subject: str, body: str, from_email: Optional[str] = None) -> dict:
        """
        Envía un correo electrónico utilizando Amazon SES.
        """
        if not from_email:
            from_email = os.getenv("SES_EMAIL_FROM", SES_EMAIL_FROM)

        try:
            # Enviar el correo utilizando SES
            response = self.client.send_email(
                Source=from_email,
                Destination={
                    'ToAddresses': [to]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                    },
                    'Body': {
                        'Html': {
                            'Data': body,
                        }
                    }
                }
            )

            # Validar el código de respuesta de SES
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                raise RuntimeError(f"Amazon SES falló con el estado: {response['ResponseMetadata']['HTTPStatusCode']}")

            return response

        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Error al enviar correo con SES: {e}")
