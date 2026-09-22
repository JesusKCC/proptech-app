from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RelativeCoordinate(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0, description="Coordenada horizontal normalizada [0..1]")
    y: float = Field(..., ge=0.0, le=1.0, description="Coordenada vertical normalizada [0..1]")


class PoligonoBase(BaseModel):
    local_id: str
    plano_id: str
    coordenadas_relativas: List[RelativeCoordinate] = Field(
        ..., min_length=3, description="Lista de al menos 3 vértices normalizados en [0..1]"
    )
    color_relleno: str = "#3b82f6"
    color_borde: str = "#1d4ed8"
    opacidad: float = Field(default=0.4, ge=0.0, le=1.0)
    etiqueta: Optional[str] = None


class PoligonoCreate(PoligonoBase):
    pass


class PoligonoUpdate(BaseModel):
    coordenadas_relativas: Optional[List[RelativeCoordinate]] = Field(
        default=None, min_length=3
    )
    color_relleno: Optional[str] = None
    color_borde: Optional[str] = None
    opacidad: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    etiqueta: Optional[str] = None


class PoligonoResponse(PoligonoBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
