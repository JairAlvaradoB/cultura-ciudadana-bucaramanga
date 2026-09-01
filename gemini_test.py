import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Probando conexión con Gemini...\n")

respuesta = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Responde en una sola frase: ¿qué es la cultura ciudadana?"
)

print("Respuesta de Gemini:")
print(respuesta.text)