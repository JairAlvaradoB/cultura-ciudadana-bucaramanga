from sqlalchemy import (
    Column, Integer, String, Date, Time, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


# ============================================================
# TABLAS DE DIMENSIÓN (catálogos)
# ============================================================

class Tipologia(Base):
    __tablename__ = "dim_tipologia"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)

    delitos = relationship("Delito", back_populates="tipologia")


class Delito(Base):
    __tablename__ = "dim_delito"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(200), unique=True, nullable=False)
    articulo = Column(String(300))
    descripcion_conducta = Column(String(300))
    tipologia_id = Column(Integer, ForeignKey("dim_tipologia.id"), nullable=False)

    tipologia = relationship("Tipologia", back_populates="delitos")


class ClaseSitio(Base):
    __tablename__ = "dim_clase_sitio"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)


class ArmaMedio(Base):
    __tablename__ = "dim_arma_medio"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)


class Movil(Base):
    __tablename__ = "dim_movil"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)


class Comuna(Base):
    __tablename__ = "dim_comuna"

    id = Column(Integer, primary_key=True)
    numero = Column(Integer, nullable=False)
    nombre = Column(String(100), nullable=False)

    __table_args__ = (UniqueConstraint("numero", "nombre", name="uq_comuna_numero_nombre"),)

    barrios = relationship("Barrio", back_populates="comuna")


class Barrio(Base):
    __tablename__ = "dim_barrio"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    comuna_id = Column(Integer, ForeignKey("dim_comuna.id"), nullable=False)

    __table_args__ = (UniqueConstraint("nombre", "comuna_id", name="uq_barrio_comuna"),)

    comuna = relationship("Comuna", back_populates="barrios")


class CursoVida(Base):
    __tablename__ = "dim_curso_vida"

    id = Column(Integer, primary_key=True)
    rango = Column(String(20), unique=True, nullable=False)
    orden = Column(Integer, nullable=False)


# ============================================================
# TABLA DE HECHOS (los incidentes en sí)
# ============================================================

class HechoDelictivo(Base):
    __tablename__ = "hecho_delictivo"

    id = Column(Integer, primary_key=True)

    fecha_hecho = Column(Date, nullable=False)
    hora_hecho = Column(Time, nullable=False)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    dia = Column(Integer, nullable=False)
    dia_nombre = Column(String(20))
    dia_nombre_orden = Column(Integer)
    rango_horario = Column(String(30))
    rango_horario_orden = Column(Integer)

    edad = Column(Integer, nullable=True)  # NULL cuando el dato original era inválido (ej. -2)
    sexo = Column(String(20))
    cantidad = Column(Integer, nullable=False, default=1)

    delito_id = Column(Integer, ForeignKey("dim_delito.id"), nullable=False)
    clase_sitio_id = Column(Integer, ForeignKey("dim_clase_sitio.id"), nullable=False)
    arma_medio_id = Column(Integer, ForeignKey("dim_arma_medio.id"), nullable=False)
    movil_victima_id = Column(Integer, ForeignKey("dim_movil.id"), nullable=True)
    movil_agresor_id = Column(Integer, ForeignKey("dim_movil.id"), nullable=True)
    barrio_id = Column(Integer, ForeignKey("dim_barrio.id"), nullable=False)
    curso_vida_id = Column(Integer, ForeignKey("dim_curso_vida.id"), nullable=True)

    delito = relationship("Delito")
    clase_sitio = relationship("ClaseSitio")
    arma_medio = relationship("ArmaMedio")
    movil_victima = relationship("Movil", foreign_keys=[movil_victima_id])
    movil_agresor = relationship("Movil", foreign_keys=[movil_agresor_id])
    barrio = relationship("Barrio")
    curso_vida = relationship("CursoVida")