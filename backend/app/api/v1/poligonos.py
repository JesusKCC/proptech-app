from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import require_comercial_or_proyectos, require_proyectos
from app.db.session import get_db
from app.models.local import Local
from app.models.plano_centro import PlanoCentro
from app.models.poligono import Poligono
from app.schemas.poligono import PoligonoCreate, PoligonoResponse, PoligonoUpdate
from app.services.outbox_service import record_outbox_event

router = APIRouter()


@router.get(
    "/",
    response_model=List[PoligonoResponse],
    summary="Listar Polígonos de Planos"
)
async def list_poligonos(
    plano_id: Optional[str] = Query(None, description="Filtrar por Plano ID"),
    local_id: Optional[str] = Query(None, description="Filtrar por Local ID"),
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    stmt = select(Poligono)
    if plano_id:
        stmt = stmt.where(Poligono.plano_id == plano_id)
    if local_id:
        stmt = stmt.where(Poligono.local_id == local_id)

    result = await db.execute(stmt)
    poligonos = result.scalars().all()
    return [PoligonoResponse.model_validate(p) for p in poligonos]


@router.post(
    "/",
    response_model=PoligonoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear/Asociar Polígono a Local (Requiere rol proyectos - 403 para comercial)"
)
async def create_poligono(
    poly_in: PoligonoCreate,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_proyectos)
):
    # Verify local exists
    local = (await db.execute(select(Local).where(Local.id == poly_in.local_id))).scalar_one_or_none()
    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con id '{poly_in.local_id}' no encontrado"
        )

    # Verify plano exists
    plano = (await db.execute(select(PlanoCentro).where(PlanoCentro.id == poly_in.plano_id))).scalar_one_or_none()
    if not plano:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plano con id '{poly_in.plano_id}' no encontrado"
        )

    # Validate relative coordinate bounds: [0.0, 1.0]
    coords_dict = [coord.model_dump() for coord in poly_in.coordenadas_relativas]
    for idx, pt in enumerate(coords_dict):
        if not (0.0 <= pt["x"] <= 1.0 and 0.0 <= pt["y"] <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Vértice {idx} ({pt['x']}, {pt['y']}) fuera del rango normalizado permitido [0.0, 1.0]"
            )

    poligono = Poligono(
        local_id=poly_in.local_id,
        plano_id=poly_in.plano_id,
        coordenadas_relativas=coords_dict,
        color_relleno=poly_in.color_relleno,
        color_borde=poly_in.color_borde,
        opacidad=poly_in.opacidad,
        etiqueta=poly_in.etiqueta or local.codigo_local
    )
    db.add(poligono)

    # Update local's plano_id if unset
    if not local.plano_id:
        local.plano_id = poly_in.plano_id

    # Emit outbox event
    await record_outbox_event(
        db=db,
        tipo_evento="poligono.creado",
        entidad_tipo="poligono",
        entidad_id=poligono.id,
        payload={
            "poligono_id": poligono.id,
            "local_id": local.id,
            "codigo_local": local.codigo_local,
            "plano_id": poly_in.plano_id,
            "num_vertices": len(coords_dict)
        }
    )

    await db.commit()
    await db.refresh(poligono)
    return PoligonoResponse.model_validate(poligono)


@router.put(
    "/{id}",
    response_model=PoligonoResponse,
    summary="Actualizar geometría o estilo de polígono (Requiere rol proyectos - 403 para comercial)"
)
async def update_poligono(
    id: str,
    poly_in: PoligonoUpdate,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_proyectos)
):
    stmt = select(Poligono).where(Poligono.id == id)
    result = await db.execute(stmt)
    poligono = result.scalar_one_or_none()

    if not poligono:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polígono con id '{id}' no encontrado"
        )

    update_dict = poly_in.model_dump(exclude_unset=True)
    if "coordenadas_relativas" in update_dict and update_dict["coordenadas_relativas"]:
        coords = [coord.model_dump() for coord in poly_in.coordenadas_relativas]
        for idx, pt in enumerate(coords):
            if not (0.0 <= pt["x"] <= 1.0 and 0.0 <= pt["y"] <= 1.0):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Vértice {idx} ({pt['x']}, {pt['y']}) fuera del rango normalizado [0.0, 1.0]"
                )
        poligono.coordenadas_relativas = coords
        del update_dict["coordenadas_relativas"]

    for field, value in update_dict.items():
        setattr(poligono, field, value)

    await record_outbox_event(
        db=db,
        tipo_evento="poligono.actualizado",
        entidad_tipo="poligono",
        entidad_id=poligono.id,
        payload={
            "poligono_id": poligono.id,
            "local_id": poligono.local_id,
            "plano_id": poligono.plano_id
        }
    )

    await db.commit()
    await db.refresh(poligono)
    return PoligonoResponse.model_validate(poligono)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar polígono (Requiere rol proyectos)"
)
async def delete_poligono(
    id: str,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_proyectos)
):
    stmt = select(Poligono).where(Poligono.id == id)
    result = await db.execute(stmt)
    poligono = result.scalar_one_or_none()

    if not poligono:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polígono con id '{id}' no encontrado"
        )

    await db.delete(poligono)
    await db.commit()
    return None
