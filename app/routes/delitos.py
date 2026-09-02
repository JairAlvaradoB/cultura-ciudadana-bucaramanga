from fastapi import APIRouter, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Optional

from app.database import get_db
from app.models.models import HechoDelictivo, Comuna, Barrio, Tipologia, Delito, Movil, CursoVida
from app.schemas import ResumenComuna, ResumenTipologia, ResumenTemporal, ResumenBarrio

router = APIRouter(prefix="/delitos", tags=["Delitos"])

# Umbral mínimo de casos para mostrar un dato desagregado por barrio.
# Por debajo de este número, existe riesgo de que se pueda identificar
# a una víctima específica cruzando categoría + ubicación muy puntual.
UMBRAL_PROTECCION = 5

# Categorías que la Ley 1581 de 2012 trata como datos sensibles
# (relacionadas con menores de edad y vida sexual).
CATEGORIAS_SENSIBLES = ["MENOR", "SEXUAL", "PROSTITUCIÓN", "PROXENETISMO"]


@router.get("/resumen-por-comuna", response_model=list[ResumenComuna])
def resumen_por_comuna(
    anio: Optional[int] = Query(None, description="Filtrar por año, ej: 2025"),
    tipologia: Optional[str] = Query(None, description="Filtrar por tipología de delito"),
    db: Session = Depends(get_db),
):
    """Total de casos agrupados por comuna."""
    query = (
        db.query(
            Comuna.nombre.label("comuna"),
            Comuna.numero.label("numero_comuna"),
            func.sum(HechoDelictivo.cantidad).label("total_casos"),
        )
        .join(Barrio, Barrio.comuna_id == Comuna.id)
        .join(HechoDelictivo, HechoDelictivo.barrio_id == Barrio.id)
    )

    if anio:
        query = query.filter(HechoDelictivo.anio == anio)

    if tipologia:
        query = query.join(Delito, Delito.id == HechoDelictivo.delito_id).join(
            Tipologia, Tipologia.id == Delito.tipologia_id
        ).filter(Tipologia.nombre.ilike(f"%{tipologia}%"))

    resultados = query.group_by(Comuna.nombre, Comuna.numero).order_by(
        func.sum(HechoDelictivo.cantidad).desc()
    ).all()

    return [
        ResumenComuna(comuna=r.comuna, numero_comuna=r.numero_comuna, total_casos=r.total_casos)
        for r in resultados
    ]


@router.get("/resumen-por-tipologia", response_model=list[ResumenTipologia])
def resumen_por_tipologia(
    anio: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Total de casos agrupados por tipología (categoría general del delito)."""
    query = (
        db.query(
            Tipologia.nombre.label("tipologia"),
            func.sum(HechoDelictivo.cantidad).label("total_casos"),
        )
        .join(Delito, Delito.tipologia_id == Tipologia.id)
        .join(HechoDelictivo, HechoDelictivo.delito_id == Delito.id)
    )

    if anio:
        query = query.filter(HechoDelictivo.anio == anio)

    resultados = query.group_by(Tipologia.nombre).order_by(
        func.sum(HechoDelictivo.cantidad).desc()
    ).all()

    return [ResumenTipologia(tipologia=r.tipologia, total_casos=r.total_casos) for r in resultados]


@router.get("/resumen-temporal", response_model=list[ResumenTemporal])
def resumen_temporal(
    anio: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Total de casos agrupados por año y mes (para gráficos de tendencia)."""
    query = db.query(
        HechoDelictivo.anio.label("anio"),
        HechoDelictivo.mes.label("mes"),
        func.sum(HechoDelictivo.cantidad).label("total_casos"),
    )

    if anio:
        query = query.filter(HechoDelictivo.anio == anio)

    resultados = query.group_by(HechoDelictivo.anio, HechoDelictivo.mes).order_by(
        HechoDelictivo.anio, HechoDelictivo.mes
    ).all()

    return [
        ResumenTemporal(anio=r.anio, mes=r.mes, total_casos=r.total_casos) for r in resultados
    ]


@router.get("/resumen-por-barrio", response_model=list[ResumenBarrio])
def resumen_por_barrio(
    tipologia: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Total de casos agrupados por barrio.

    NOTA DE PROTECCIÓN DE DATOS: cuando el filtro corresponde a una
    categoría sensible (delitos sexuales, casos con menores de edad),
    los conteos por debajo del umbral definido se ocultan y se marcan
    como 'dato_protegido', para reducir el riesgo de identificar
    indirectamente a una víctima en un barrio con muy pocos casos.
    Este comportamiento aplica el principio de minimización de datos
    de la Ley 1581 de 2012.
    """
    query = (
        db.query(
            Barrio.nombre.label("barrio"),
            Comuna.nombre.label("comuna"),
            func.sum(HechoDelictivo.cantidad).label("total_casos"),
        )
        .join(Comuna, Barrio.comuna_id == Comuna.id)
        .join(HechoDelictivo, HechoDelictivo.barrio_id == Barrio.id)
    )

    es_sensible = False
    if tipologia:
        query = query.join(Delito, Delito.id == HechoDelictivo.delito_id).join(
            Tipologia, Tipologia.id == Delito.tipologia_id
        ).filter(Tipologia.nombre.ilike(f"%{tipologia}%"))
        es_sensible = any(cat in tipologia.upper() for cat in CATEGORIAS_SENSIBLES)

    resultados = query.group_by(Barrio.nombre, Comuna.nombre).all()

    respuesta = []
    for r in resultados:
        if es_sensible and r.total_casos < UMBRAL_PROTECCION:
            respuesta.append(
                ResumenBarrio(barrio=r.barrio, comuna=r.comuna, total_casos=None, dato_protegido=True)
            )
        else:
            respuesta.append(
                ResumenBarrio(barrio=r.barrio, comuna=r.comuna, total_casos=r.total_casos, dato_protegido=False)
            )

    return respuesta

@router.get("/resumen-por-rango-horario")
def resumen_por_rango_horario(
    anio: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Total de casos agrupados por rango horario del día (madrugada, mañana, tarde, noche)."""
    query = db.query(
        HechoDelictivo.rango_horario.label("rango"),
        HechoDelictivo.rango_horario_orden.label("orden"),
        func.sum(HechoDelictivo.cantidad).label("total_casos"),
    )
    if anio:
        query = query.filter(HechoDelictivo.anio == anio)

    resultados = query.group_by(
        HechoDelictivo.rango_horario, HechoDelictivo.rango_horario_orden
    ).order_by(HechoDelictivo.rango_horario_orden).all()

    return [{"rango": r.rango, "total_casos": r.total_casos} for r in resultados]

@router.get("/tendencia-mensual-por-tipologia")
def tendencia_mensual_por_tipologia(db: Session = Depends(get_db)):
    """Casos por mes y tipología, para gráficas de tendencia apiladas/superpuestas."""
    query = (
        db.query(
            HechoDelictivo.anio.label("anio"),
            HechoDelictivo.mes.label("mes"),
            Tipologia.nombre.label("tipologia"),
            func.sum(HechoDelictivo.cantidad).label("total_casos"),
        )
        .join(Delito, Delito.id == HechoDelictivo.delito_id)
        .join(Tipologia, Tipologia.id == Delito.tipologia_id)
        .group_by(HechoDelictivo.anio, HechoDelictivo.mes, Tipologia.nombre)
        .order_by(HechoDelictivo.anio, HechoDelictivo.mes)
    )
    return [
        {"anio": r.anio, "mes": r.mes, "tipologia": r.tipologia, "total_casos": r.total_casos}
        for r in query.all()
    ]


@router.get("/rango-horario-por-tipologia")
def rango_horario_por_tipologia(db: Session = Depends(get_db)):
    """Casos por rango horario, desglosados por tipología (para columnas apiladas)."""
    query = (
        db.query(
            HechoDelictivo.rango_horario.label("rango"),
            HechoDelictivo.rango_horario_orden.label("orden"),
            Tipologia.nombre.label("tipologia"),
            func.sum(HechoDelictivo.cantidad).label("total_casos"),
        )
        .join(Delito, Delito.id == HechoDelictivo.delito_id)
        .join(Tipologia, Tipologia.id == Delito.tipologia_id)
        .group_by(HechoDelictivo.rango_horario, HechoDelictivo.rango_horario_orden, Tipologia.nombre)
        .order_by(HechoDelictivo.rango_horario_orden)
    )
    return [
        {"rango": r.rango, "tipologia": r.tipologia, "total_casos": r.total_casos}
        for r in query.all()
    ]


@router.get("/resumen-por-sexo")
def resumen_por_sexo(db: Session = Depends(get_db)):
    """Total de casos agrupados por sexo de la víctima."""
    query = (
        db.query(HechoDelictivo.sexo.label("sexo"), func.sum(HechoDelictivo.cantidad).label("total_casos"))
        .group_by(HechoDelictivo.sexo)
    )
    return [{"sexo": r.sexo, "total_casos": r.total_casos} for r in query.all()]


@router.get("/resumen-por-movil-victima")
def resumen_por_movil_victima(db: Session = Depends(get_db)):
    """Total de casos agrupados por el móvil de la víctima (a pie, en moto, en bus, etc.)."""
    query = (
        db.query(Movil.nombre.label("movil"), func.sum(HechoDelictivo.cantidad).label("total_casos"))
        .join(HechoDelictivo, HechoDelictivo.movil_victima_id == Movil.id)
        .group_by(Movil.nombre)
        .order_by(func.sum(HechoDelictivo.cantidad).desc())
    )
    return [{"movil": r.movil, "total_casos": r.total_casos} for r in query.all()]


@router.get("/piramide-edad-sexo")
def piramide_edad_sexo(db: Session = Depends(get_db)):
    """Total de casos por rango de edad (curso de vida) y sexo, para gráfica de pirámide poblacional."""
    query = (
        db.query(
            CursoVida.rango.label("rango"),
            CursoVida.orden.label("orden"),
            HechoDelictivo.sexo.label("sexo"),
            func.sum(HechoDelictivo.cantidad).label("total_casos"),
        )
        .join(HechoDelictivo, HechoDelictivo.curso_vida_id == CursoVida.id)
        .group_by(CursoVida.rango, CursoVida.orden, HechoDelictivo.sexo)
        .order_by(CursoVida.orden)
    )
    return [
        {"rango": r.rango, "sexo": r.sexo, "total_casos": r.total_casos}
        for r in query.all()
    ]