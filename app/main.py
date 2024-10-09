from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.api import email_routes
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

app = FastAPI()

# Incluir las rutas definidas en email_routes
app.include_router(email_routes.router)

# Sirve los archivos estáticos como CSS y JS desde la carpeta "static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta principal que devuelve el archivo HTML
@app.get("/", response_class=HTMLResponse)
def serve_frontend() -> HTMLResponse:
    with open("index.html") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Definir un health check
@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
