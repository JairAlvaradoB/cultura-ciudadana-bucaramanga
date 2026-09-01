from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.models import models
from app.routes import delitos, encuestas, redes_sociales, chat

app = FastAPI(title="Plataforma de Cultura Ciudadana - Bucaramanga")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción esto se restringiría a un dominio específico
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(delitos.router)
app.include_router(encuestas.router)
app.include_router(redes_sociales.router)
app.include_router(chat.router)

app.mount("/dashboard", StaticFiles(directory="static", html=True), name="dashboard")


@app.get("/")
def home():
    return {"mensaje": "La plataforma está funcionando correctamente"}