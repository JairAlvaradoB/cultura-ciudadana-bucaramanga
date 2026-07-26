from fastapi import FastAPI
from app.database import engine, Base

app = FastAPI(title="Plataforma de Cultura Ciudadana - Bucaramanga")

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"mensaje": "La plataforma está funcionando correctamente"}