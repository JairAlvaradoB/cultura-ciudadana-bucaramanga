from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import field_validator

from app.database import get_db
from app.models.models import EncuestaRespuesta, Comuna, CursoVida
from app.schemas import EncuestaCrear, EncuestaRespuestaOut, ResumenPercepcionComuna

router = APIRouter(prefix="/encuestas", tags=["Encuestas"])


def validar_escala(valor: int, nombre_campo: str):
    if not (1 <= valor <= 5):
        raise HTTPException(
            status_code=422,
            detail=f"'{nombre_campo}' debe estar entre 1 y 5 (recibido: {valor})"
        )


@router.get("/opciones-comuna")
def listar_comunas(db: Session = Depends(get_db)):
    """Lista de comunas para llenar el formulario de encuesta."""
    comunas = db.query(Comuna).order_by(Comuna.numero).all()
    return [{"id": c.id, "nombre": c.nombre, "numero": c.numero} for c in comunas]


@router.get("/opciones-rango-edad")
def listar_rangos_edad(db: Session = Depends(get_db)):
    """Lista de rangos de edad para llenar el formulario de encuesta."""
    rangos = db.query(CursoVida).order_by(CursoVida.orden).all()
    return [{"id": r.id, "rango": r.rango} for r in rangos]


@router.post("/", response_model=EncuestaRespuestaOut, status_code=201)
def registrar_respuesta(datos: EncuestaCrear, db: Session = Depends(get_db)):
    """Registra una nueva respuesta de encuesta de percepción ciudadana."""

    # Validamos que las escalas estén en el rango correcto
    validar_escala(datos.percepcion_seguridad_dia, "percepcion_seguridad_dia")
    validar_escala(datos.percepcion_seguridad_noche, "percepcion_seguridad_noche")
    validar_escala(datos.frecuencia_mal_uso_espacio, "frecuencia_mal_uso_espacio")

    # Validamos que la comuna y el rango de edad existan realmente
    if not db.query(Comuna).filter(Comuna.id == datos.comuna_id).first():
        raise HTTPException(status_code=422, detail="comuna_id no existe")
    if not db.query(CursoVida).filter(CursoVida.id == datos.curso_vida_id).first():
        raise HTTPException(status_code=422, detail="curso_vida_id no existe")

    nueva_respuesta = EncuestaRespuesta(**datos.model_dump())
    db.add(nueva_respuesta)
    db.commit()
    db.refresh(nueva_respuesta)

    return nueva_respuesta


@router.get("/resumen-por-comuna", response_model=list[ResumenPercepcionComuna])
def resumen_percepcion_por_comuna(db: Session = Depends(get_db)):
    """Promedios de percepción ciudadana agrupados por comuna."""
    resultados = (
        db.query(
            Comuna.nombre.label("comuna"),
            func.count(EncuestaRespuesta.id).label("total_respuestas"),
            func.avg(EncuestaRespuesta.percepcion_seguridad_dia).label("promedio_seguridad_dia"),
            func.avg(EncuestaRespuesta.percepcion_seguridad_noche).label("promedio_seguridad_noche"),
            func.avg(EncuestaRespuesta.frecuencia_mal_uso_espacio).label("promedio_mal_uso_espacio"),
        )
        .join(EncuestaRespuesta, EncuestaRespuesta.comuna_id == Comuna.id)
        .group_by(Comuna.nombre)
        .all()
    )

    return [
        ResumenPercepcionComuna(
            comuna=r.comuna,
            total_respuestas=r.total_respuestas,
            promedio_seguridad_dia=round(float(r.promedio_seguridad_dia), 2),
            promedio_seguridad_noche=round(float(r.promedio_seguridad_noche), 2),
            promedio_mal_uso_espacio=round(float(r.promedio_mal_uso_espacio), 2),
        )
        for r in resultados
    ]