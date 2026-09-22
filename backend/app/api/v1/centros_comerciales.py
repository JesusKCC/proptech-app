from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.security import require_comercial_or_proyectos, require_proyectos
from app.db.session import get_db
from app.models.centro_comercial import CentroComercial
from app.schemas.centro_comercial import (
    CentroComercialCreate,
    CentroComercialUpdate,
    CentroComercialResponse,
    GeoJSONFeature,
    GeoJSONFeatureCollection,
    GeoJSONGeometry,
)

router = APIRouter()


@router.get(
    "/",
    response_model=Any,
    summary="Listar Centros Comerciales (JSON o GeoJSON FeatureCollection)"
)
async def list_centros_comerciales(
    format: Optional[str] = Query(
        default="json",
        description="Formato de respuesta: 'json' para lista estándar o 'geojson' para FeatureCollection de Leaflet"
    ),
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    stmt = select(CentroComercial).order_by(CentroComercial.nombre.asc())
    result = await db.execute(stmt)
    malls = result.scalars().all()

    if format.lower() == "geojson":
        features = []
        for m in malls:
            feature = GeoJSONFeature(
                id=m.id,
                geometry=GeoJSONGeometry(
                    type="Point",
                    coordinates=[m.lon, m.lat]  # GeoJSON standard: [longitude, latitude]
                ),
                properties={
                    "id": m.id,
                    "nombre": m.nombre,
                    "slug": m.slug,
                    "direccion": m.direccion,
                    "departamento": m.departamento,
                    "provincia": m.provincia,
                    "distrito": m.distrito,
                    "lat": m.lat,
                    "lon": m.lon,
                    "total_locales": m.total_locales,
                    "superficie_total_m2": m.superficie_total_m2,
                    "imagen_url": m.imagen_url,
                }
            )
            features.append(feature)
        return GeoJSONFeatureCollection(features=features)

    return [CentroComercialResponse.model_validate(m) for m in malls]


@router.get(
    "/{id}",
    response_model=Any,
    summary="Obtener detalle de un Centro Comercial con sus planos arquitectónicos"
)
async def get_centro_comercial(
    id: str,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    stmt = (
        select(CentroComercial)
        .where((CentroComercial.id == id) | (CentroComercial.slug == id))
        .options(selectinload(CentroComercial.planos))
    )
    result = await db.execute(stmt)
    mall = result.scalar_one_or_none()

    if not mall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centro Comercial con id o slug '{id}' no encontrado"
        )

    mall_dict = {
        "id": mall.id,
        "nombre": mall.nombre,
        "slug": mall.slug,
        "direccion": mall.direccion,
        "departamento": mall.departamento,
        "provincia": mall.provincia,
        "distrito": mall.distrito,
        "lat": mall.lat,
        "lon": mall.lon,
        "total_locales": mall.total_locales,
        "superficie_total_m2": mall.superficie_total_m2,
        "imagen_url": mall.imagen_url,
        "planos": [
            {
                "id": p.id,
                "nombre_piso": p.nombre_piso,
                "archivo_pdf_url": p.archivo_pdf_url,
                "ancho_unscaled_pt": p.ancho_unscaled_pt,
                "alto_unscaled_pt": p.alto_unscaled_pt
            }
            for p in mall.planos
        ]
    }
    return mall_dict


@router.post(
    "/",
    response_model=CentroComercialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Centro Comercial (Requiere rol proyectos)"
)
async def create_centro_comercial(
    mall_in: CentroComercialCreate,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_proyectos)
):
    # Check duplicate slug
    stmt = select(CentroComercial).where(CentroComercial.slug == mall_in.slug)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un Centro Comercial con el slug '{mall_in.slug}'"
        )

    mall = CentroComercial(**mall_in.model_dump())
    db.add(mall)
    await db.commit()
    await db.refresh(mall)
    return CentroComercialResponse.model_validate(mall)


@router.put(
    "/{id}",
    response_model=CentroComercialResponse,
    summary="Actualizar Centro Comercial (Requiere rol proyectos)"
)
async def update_centro_comercial(
    id: str,
    mall_in: CentroComercialUpdate,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_proyectos)
):
    stmt = (
        select(CentroComercial)
        .where((CentroComercial.id == id) | (CentroComercial.slug == id))
    )
    result = await db.execute(stmt)
    mall = result.scalar_one_or_none()

    if not mall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centro Comercial con id o slug '{id}' no encontrado"
        )

    update_data = mall_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mall, field, value)

    await db.commit()
    await db.refresh(mall)
    return CentroComercialResponse.model_validate(mall)

