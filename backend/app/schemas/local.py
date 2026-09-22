from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LocalBase(BaseModel):
    centro_comercial_id: str
    plano_id: Optional[str] = None
    codigo_local: str
    nombre_comercial: str = ""
    categoria: str = "General"
    estado: str = Field(default="disponible", pattern="^(disponible|arrendado|reservado|mantenimiento)$")
    area_m2: float = 0.0
    precio_alquiler_mensual: float = 0.0
    moneda: str = "USD"
    piso_nivel: str = "Nivel 1"
    descripcion: str = ""


class LocalCreate(LocalBase):
    pass


class LocalUpdate(BaseModel):
    plano_id: Optional[str] = None
    codigo_local: Optional[str] = None
    nombre_comercial: Optional[str] = None
    categoria: Optional[str] = None
    estado: Optional[str] = Field(default=None, pattern="^(disponible|arrendado|reservado|mantenimiento)$")
    area_m2: Optional[float] = None
    precio_alquiler_mensual: Optional[float] = None
    moneda: Optional[str] = None
    piso_nivel: Optional[str] = None
    descripcion: Optional[str] = None


class LocalResponse(LocalBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
