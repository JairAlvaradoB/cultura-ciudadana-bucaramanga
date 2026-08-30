from fastapi import FastAPI
from app.database import engine, Base
from app.models import models
from app.routes import delitos

app = FastAPI(title="Plataforma de Cultura Ciudadana - Bucaramanga")

Base.metadata.create_all(bind=engine)

app.include_router(delitos.router)


@app.get("/")
def home():
    return {"mensaje": "La plataforma está funcionando correctamente"}