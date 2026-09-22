import uuid
from typing import List, Optional
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Local(Base):
    __tablename__ = "locales"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    centro_comercial_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("centros_comerciales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plano_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("planos_centro.id", ondelete="SET NULL"), nullable=True, index=True
    )
    codigo_local: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    nombre_comercial: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    categoria: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    estado: Mapped[str] = mapped_column(
        String(50), nullable=False, default="disponible", index=True
    )  # disponible, arrendado, reservado, mantenimiento
    area_m2: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    precio_alquiler_mensual: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    moneda: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    piso_nivel: Mapped[str] = mapped_column(String(50), nullable=False, default="Nivel 1")
    descripcion: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Relationships
    centro_comercial: Mapped["CentroComercial"] = relationship(
        "CentroComercial", back_populates="locales"
    )
    plano: Mapped[Optional["PlanoCentro"]] = relationship(
        "PlanoCentro", back_populates="locales"
    )
    poligonos: Mapped[List["Poligono"]] = relationship(
        "Poligono", back_populates="local", cascade="all, delete-orphan"
    )
    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket", back_populates="local", cascade="all, delete-orphan"
    )
