from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TicketEstado(str, Enum):
    ABIERTO = "abierto"
    EN_REVISION = "en_revision"
    RESUELTO = "resuelto"
    RECHAZADO = "rechazado"


class TicketBase(BaseModel):
    centro_comercial_id: str
    local_id: Optional[str] = None
    titulo: str
    descripcion: str
    tipo: str = Field(
        default="nuevo_requerimiento",
        pattern="^(modificacion_plano|division_local|mantenimiento|revision_comercial|nuevo_requerimiento)$"
    )
    prioridad: str = Field(
        default="media",
        pattern="^(baja|media|alta|urgente)$"
    )
    creado_por: str = "comercial"
    asignado_a: Optional[str] = None


class TicketCreate(TicketBase):
    pass


class TicketResolve(BaseModel):
    notas_resolucion: str = Field(
        ..., min_length=1, description="Notas técnicas obligatorias para resolver el ticket"
    )


class TicketResponse(TicketBase):
    id: str
    codigo_ticket: str
    estado: str
    notas_resolucion: Optional[str] = None
    resuelto_en: Optional[datetime] = None
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)
