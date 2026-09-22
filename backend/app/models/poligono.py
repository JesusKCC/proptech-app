import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Poligono(Base):
    __tablename__ = "poligonos"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    local_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plano_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("planos_centro.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # JSON array of relative coordinates: [{"x": float, "y": float}, ...] with x, y in [0..1]
    coordenadas_relativas: Mapped[List[Dict[str, float]]] = mapped_column(JSON, nullable=False)
    color_relleno: Mapped[str] = mapped_column(String(30), default="#3b82f6")
    color_borde: Mapped[str] = mapped_column(String(30), default="#1d4ed8")
    opacidad: Mapped[float] = mapped_column(Float, default=0.40)
    etiqueta: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    local: Mapped["Local"] = relationship("Local", back_populates="poligonos")
    plano: Mapped["PlanoCentro"] = relationship("PlanoCentro", back_populates="poligonos")
