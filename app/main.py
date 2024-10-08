from fastapi import FastAPI
from app.api import email_routes
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

app = FastAPI()

# Incluir las rutas definidas en email_routes
app.include_router(email_routes.router)

# Definir un health check
@app.get("/")
def health_check() -> dict:
    return {"status": "ok"}
