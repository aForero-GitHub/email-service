from pydantic import BaseModel, EmailStr
from typing import Optional

class EmailRequest(BaseModel):
    to: EmailStr  # Validación automática para direcciones de correo válidas
    subject: str  # Asunto del correo
    body: str     # Cuerpo del correo en formato HTML o texto plano
    from_email: Optional[EmailStr] = None  # Opción de usar un correo 'from' específico
    
    class Config:
        schema_extra = {
            "example": {
                "to": "destinatario@example.com",
                "subject": "Asunto del correo",
                "body": "<h1>Este es un mensaje de prueba</h1>",
                "from_email": "foreromartinez.andres@gmail.com"  # Este campo es opcional
            }
        }
