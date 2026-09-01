import os
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from transformers import pipeline
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import DATABASE_URL
from app.models.models import RedSocialComentario

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
PLAYLIST_ID = "PL0z3JydD83hZGbAA1SQsPEjjurPhR26pK"  # "Noticias de Bucaramanga" - Vanguardia

PALABRAS_CLAVE = [
    "seguridad", "inseguridad", "hurto", "robo", "convivencia",
    "espacio público", "andén", "policía", "delito", "violencia",
    "atraco", "homicidio", "ciudadano"
]

MAX_VIDEOS_A_PROCESAR = 15       # cuántos videos relevantes procesamos
MAX_COMENTARIOS_POR_VIDEO = 30   # cuántos comentarios traemos de cada uno

# ============================================================
# PASO 1: Buscar videos relevantes en la playlist
# ============================================================
print("Buscando videos relevantes en la playlist de Vanguardia...")

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

videos_relevantes = []
siguiente_pagina = None

for _ in range(6):
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
                "titulo": item["snippet"]["title"]
            })

    siguiente_pagina = respuesta.get("nextPageToken")
    if not siguiente_pagina:
        break

videos_relevantes = videos_relevantes[:MAX_VIDEOS_A_PROCESAR]
print(f"Se procesarán {len(videos_relevantes)} videos.\n")

# ============================================================
# PASO 2: Traer comentarios de cada video
# ============================================================
print("Extrayendo comentarios...")

comentarios_recolectados = []  # cada item: {video_id, video_titulo, texto}

for video in videos_relevantes:
    try:
        resp = youtube.commentThreads().list(
            part="snippet",
            videoId=video["video_id"],
            maxResults=MAX_COMENTARIOS_POR_VIDEO,
            textFormat="plainText",
            order="relevance"
        ).execute()

        for item in resp["items"]:
            texto = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comentarios_recolectados.append({
                "video_id": video["video_id"],
                "video_titulo": video["titulo"],
                "texto": texto
            })

        print(f"  '{video['titulo'][:60]}...' -> {len(resp['items'])} comentarios")

    except HttpError as e:
        # Algunos videos tienen los comentarios desactivados; no detenemos el proceso por eso
        print(f"  No se pudieron obtener comentarios de '{video['titulo'][:60]}...' ({e.status_code})")

print(f"\nTotal de comentarios recolectados: {len(comentarios_recolectados)}\n")

# ============================================================
# PASO 3: Analizar sentimiento de cada comentario
# ============================================================
print("Cargando modelo de análisis de sentimiento...")
analizador = pipeline("sentiment-analysis", model="pysentimiento/robertuito-sentiment-analysis")

print("Analizando comentarios...\n")

MAPA_ETIQUETAS = {"POS": "POSITIVO", "NEG": "NEGATIVO", "NEU": "NEUTRAL"}

registros_finales = []
for c in comentarios_recolectados:
    # Saltamos comentarios vacíos o extremadamente largos (el modelo tiene un límite de tokens)
    texto = c["texto"].strip()
    if not texto or len(texto) > 500:
        continue

    resultado = analizador(texto)[0]
    registros_finales.append(
        RedSocialComentario(
            video_id=c["video_id"],
            video_titulo=c["video_titulo"],
            comentario_texto=texto,
            sentimiento=MAPA_ETIQUETAS[resultado["label"]],
            confianza=round(resultado["score"] * 100),
            fecha_extraccion=datetime.utcnow()
        )
    )

print(f"Comentarios analizados exitosamente: {len(registros_finales)}\n")

# ============================================================
# PASO 4: Guardar en la base de datos
# ============================================================
print("Guardando en la base de datos...")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Limpiamos datos anteriores por si el script se corre más de una vez
session.query(RedSocialComentario).delete()
session.add_all(registros_finales)
session.commit()
session.close()

print("¡Listo! Comentarios de YouTube analizados y guardados correctamente.")