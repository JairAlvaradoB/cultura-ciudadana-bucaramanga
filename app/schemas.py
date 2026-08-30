from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResumenComuna(BaseModel):
    comuna: str
    numero_comuna: int
    total_casos: int


class ResumenTipologia(BaseModel):
    tipologia: str
    total_casos: int


class ResumenTemporal(BaseModel):
    anio: int
    mes: int
    total_casos: int


class ResumenBarrio(BaseModel):
    barrio: str
    comuna: str
    total_casos: Optional[int]
    dato_protegido: bool




class EncuestaCrear(BaseModel):
    comuna_id: int
    curso_vida_id: int
    sexo: str
    percepcion_seguridad_dia: int
    percepcion_seguridad_noche: int
    frecuencia_mal_uso_espacio: int
    participacion_comunitaria: bool
    comentario: Optional[str] = None


class EncuestaRespuestaOut(BaseModel):
    id: int
    fecha_respuesta: datetime

    class Config:
        from_attributes = True


class ResumenPercepcionComuna(BaseModel):
    comuna: str
    total_respuestas: int
    promedio_seguridad_dia: float
    promedio_seguridad_noche: float
    promedio_mal_uso_espacio: float