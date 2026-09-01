from transformers import pipeline

print("Descargando y cargando el modelo de análisis de sentimiento en español...")
print("(la primera vez puede tardar unos minutos, descarga ~500 MB)\n")

analizador = pipeline(
    "sentiment-analysis",
    model="pysentimiento/robertuito-sentiment-analysis"
)

comentarios_prueba = [
    "Qué bueno que la policía por fin capturó a esos delincuentes, se sentía la inseguridad en el barrio",
    "Otra vez roban en el mismo sector y nadie hace nada, esto está cada vez peor",
    "Bucaramanga tiene un clima muy agradable en esta época del año"
]

for texto in comentarios_prueba:
    resultado = analizador(texto)[0]
    print(f"Texto: {texto}")
    print(f"  -> Sentimiento: {resultado['label']}, confianza: {round(resultado['score']*100, 1)}%\n")