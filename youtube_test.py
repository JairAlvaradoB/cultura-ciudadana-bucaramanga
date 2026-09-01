import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
PLAYLIST_ID = "PL0z3JydD83hZGbAA1SQsPEjjurPhR26pK"  # "Noticias de Bucaramanga" - Vanguardia

# Palabras clave relacionadas con las dimensiones de cultura ciudadana
# que definimos en el Marco Referencial (convivencia, espacio público, seguridad)
PALABRAS_CLAVE = [
    "seguridad", "inseguridad", "hurto", "robo", "convivencia",
    "espacio público", "andén", "policía", "delito", "violencia",
    "atraco", "homicidio", "ciudadano"
]

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

print("Buscando videos relevantes en la playlist...\n")

videos_relevantes = []
siguiente_pagina = None

# Recorremos varias páginas de la playlist buscando coincidencias
for _ in range(6):  # 6 páginas x 50 = hasta 300 videos revisados
    respuesta = youtube.playlistItems().list(
        part="snippet",
        playlistId=PLAYLIST_ID,
        maxResults=50,
        pageToken=siguiente_pagina
    ).execute()

    for item in respuesta["items"]:
        titulo = item["snippet"]["title"].lower()
        if any(palabra in titulo for palabra in PALABRAS_CLAVE):
            videos_relevantes.append({
                "video_id": item["snippet"]["resourceId"]["videoId"],
                "titulo": item["snippet"]["title"],
                "fecha": item["snippet"]["publishedAt"][:10]
            })

    siguiente_pagina = respuesta.get("nextPageToken")
    if not siguiente_pagina:
        break

print(f"Videos relevantes encontrados: {len(videos_relevantes)}\n")
for v in videos_relevantes[:15]:
    print(f"- [{v['fecha']}] {v['titulo']}")