from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import RedSocialComentario

router = APIRouter(prefix="/redes-sociales", tags=["Redes Sociales"])


@router.get("/resumen-sentimiento")
def resumen_sentimiento(db: Session = Depends(get_db)):
    """Total de comentarios agrupados por sentimiento (POSITIVO/NEGATIVO/NEUTRAL)."""
    resultados = (
        db.query(RedSocialComentario.sentimiento, func.count(RedSocialComentario.id).label("total"))
        .group_by(RedSocialComentario.sentimiento)
        .all()
    )
    return [{"sentimiento": r.sentimiento, "total": r.total} for r in resultados]


@router.get("/comentarios-recientes")
def comentarios_recientes(limite: int = 10, db: Session = Depends(get_db)):
    """Muestra de comentarios recientes con su clasificación de sentimiento."""
    comentarios = (
        db.query(RedSocialComentario)
        .order_by(RedSocialComentario.fecha_extraccion.desc())
        .limit(limite)
        .all()
    )
    return [
        {
            "video_titulo": c.video_titulo,
            "comentario": c.comentario_texto,
            "sentimiento": c.sentimiento,
            "confianza": c.confianza
        }
        for c in comentarios
    ]