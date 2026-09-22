import uuid
from typing import List, Optional
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PlanoCentro(Base):
    __tablename__ = "planos_centro"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    centro_comercial_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("centros_comerciales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre_piso: Mapped[str] = mapped_column(String(100), nullable=False)
    archivo_pdf_url: Mapped[str] = mapped_column(Text, nullable=False)
    ancho_unscaled_pt: Mapped[float] = mapped_column(Float, nullable=False, default=2384.0)
    alto_unscaled_pt: Mapped[float] = mapped_column(Float, nullable=False, default=1684.0)

    # Relationships
    centro_comercial: Mapped["CentroComercial"] = relationship(
        "CentroComercial", back_populates="planos"
    )
    locales: Mapped[List["Local"]] = relationship(
        "Local", back_populates="plano"
    )
    poligonos: Mapped[List["Poligono"]] = relationship(
        "Poligono", back_populates="plano", cascade="all, delete-orphan"
    )
