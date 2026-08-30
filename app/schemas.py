from pydantic import BaseModel
from typing import Optional


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