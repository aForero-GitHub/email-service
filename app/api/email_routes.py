import boto3
import json
from ..models import EmailRequest
from ..core.config import SQS_QUEUE_URL
from fastapi import APIRouter, HTTPException

# Inicializa el cliente de SQS
sqs_client = boto3.client('sqs', region_name='us-east-2')

router = APIRouter()

@router.post("/send-email/")
async def send_email(request: EmailRequest) -> dict:
    """
    Endpoint para encolar un correo electrónico en SQS.
    """
    try:
        # Serializa el contenido del email para encolarlo en SQS
        message_body = json.dumps(request.dict())

        # Enviar mensaje a la cola SQS
        sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message_body
        )
        return {"message": "Email queued successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al encolar el correo: {str(e)}")


# Aquí está el lambda_handler para AWS Lambda
def lambda_handler(event, context) -> dict:
    """
    Lambda handler que procesa las solicitudes HTTP de API Gateway.
    """
    try:
        # Extraer los datos del evento de API Gateway
        body = json.loads(event['body'])
        
        # Convertir el cuerpo de la solicitud en el modelo de EmailRequest
        email_data = EmailRequest(**body)
        
        # Serializa el contenido del email para encolarlo en SQS
        message_body = json.dumps(email_data.dict())

        # Enviar mensaje a la cola SQS
        sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=message_body
        )

        # Respuesta exitosa para API Gateway
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Email queued successfully"})
        }

    except Exception as e:
        # Respuesta en caso de error
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error al encolar el correo: {str(e)}"})
        }
