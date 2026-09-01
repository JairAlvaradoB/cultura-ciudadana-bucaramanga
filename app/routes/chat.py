import os
import requests
from fastapi import APIRouter
from pydantic import BaseModel
from google import genai
from google.genai import types

router = APIRouter(prefix="/chat", tags=["Agente de Chat"])

API_BASE = "http://127.0.0.1:8000"
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class MensajeChat(BaseModel):
    mensaje: str


# ============================================================
# Funciones "herramienta" que el agente puede usar.
# Cada una simplemente llama a un endpoint que ya construimos.
# ============================================================

def consultar_delitos_por_comuna(anio: int = None) -> str:
    """Obtiene el total de casos de delitos agrupados por comuna en Bucaramanga.
    Usa esto cuando te pregunten sobre delitos, seguridad o criminalidad por comuna."""
    params = {"anio": anio} if anio else {}
    r = requests.get(f"{API_BASE}/delitos/resumen-por-comuna", params=params)
    return str(r.json())


def consultar_delitos_por_tipologia(anio: int = None) -> str:
    """Obtiene el total de casos agrupados por tipo de delito (tipología).
    Usa esto cuando te pregunten qué tipo de delitos son más comunes."""
    params = {"anio": anio} if anio else {}
    r = requests.get(f"{API_BASE}/delitos/resumen-por-tipologia", params=params)
    return str(r.json())


def consultar_tendencia_temporal() -> str:
    """Obtiene la cantidad de casos de delitos por año y mes.
    Usa esto cuando pregunten sobre tendencias en el tiempo."""
    r = requests.get(f"{API_BASE}/delitos/resumen-temporal")
    return str(r.json())


def consultar_percepcion_ciudadana() -> str:
    """Obtiene los promedios de percepción de seguridad reportados en encuestas, por comuna.
    Usa esto cuando pregunten qué opina la gente sobre seguridad en su comuna."""
    r = requests.get(f"{API_BASE}/encuestas/resumen-por-comuna")
    return str(r.json())


def consultar_sentimiento_redes_sociales() -> str:
    """Obtiene el total de comentarios de YouTube clasificados como positivos, negativos o neutrales.
    Usa esto cuando pregunten sobre la opinión o el sentimiento de la ciudadanía en redes sociales."""
    r = requests.get(f"{API_BASE}/redes-sociales/resumen-sentimiento")
    return str(r.json())


HERRAMIENTAS = [
    consultar_delitos_por_comuna,
    consultar_delitos_por_tipologia,
    consultar_tendencia_temporal,
    consultar_percepcion_ciudadana,
    consultar_sentimiento_redes_sociales,
]

INSTRUCCION_SISTEMA = """Eres el asistente de análisis de la Plataforma de Cultura Ciudadana
de Bucaramanga. Respondes preguntas sobre delitos, percepción ciudadana y redes sociales
usando ÚNICAMENTE los datos reales que obtienes de las herramientas disponibles.
Nunca inventes cifras. Si no tienes datos suficientes para responder algo, dilo claramente.
Responde en español, de forma clara y concisa, como si hablaras con un funcionario público
que necesita tomar decisiones basadas en evidencia."""


@router.post("/")
def chat(mensaje: MensajeChat):
    chat_session = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCCION_SISTEMA,
            tools=HERRAMIENTAS,
        ),
    )

    respuesta = chat_session.send_message(mensaje.mensaje)

    return {"respuesta": respuesta.text}