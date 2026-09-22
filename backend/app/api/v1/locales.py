from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.security import require_comercial_or_proyectos
from app.db.session import get_db
from app.models.local import Local
from app.models.centro_comercial import CentroComercial
from app.schemas.local import LocalCreate, LocalResponse, LocalUpdate
from app.services.outbox_service import record_outbox_event

router = APIRouter()


@router.get(
    "/",
    response_model=List[LocalResponse],
    summary="Listar Locales Comerciales"
)
async def list_locales(
    centro_comercial_id: Optional[str] = Query(None, description="Filtrar por Centro Comercial ID o Slug"),
    plano_id: Optional[str] = Query(None, description="Filtrar por Plano ID"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (disponible, arrendado, etc.)"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    stmt = select(Local)
    if centro_comercial_id:
        stmt = stmt.join(Local.centro_comercial, isouter=True).where(
            (Local.centro_comercial_id == centro_comercial_id) |
            (CentroComercial.slug == centro_comercial_id)
        )
    if plano_id:
        stmt = stmt.where(Local.plano_id == plano_id)
    if estado:
        stmt = stmt.where(Local.estado == estado.lower())
    if categoria:
        stmt = stmt.where(Local.categoria.ilike(f"%{categoria}%"))

    stmt = stmt.order_by(Local.codigo_local.asc())
    result = await db.execute(stmt)
    locales = result.scalars().all()
    return [LocalResponse.model_validate(l) for l in locales]


@router.get(
    "/{id}",
    response_model=Any,
    summary="Obtener Ficha del Local Comercial con polígonos asociados"
)
async def get_local(
    id: str,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    stmt = (
        select(Local)
        .where((Local.id == id) | (Local.codigo_local == id))
        .options(selectinload(Local.poligonos), selectinload(Local.plano))
    )
    result = await db.execute(stmt)
    local = result.scalar_one_or_none()

    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con id o código '{id}' no encontrado"
        )

    local_dict = {
        "id": local.id,
        "centro_comercial_id": local.centro_comercial_id,
        "plano_id": local.plano_id,
        "codigo_local": local.codigo_local,
        "nombre_comercial": local.nombre_comercial,
        "categoria": local.categoria,
        "estado": local.estado,
        "area_m2": local.area_m2,
        "precio_alquiler_mensual": local.precio_alquiler_mensual,
        "moneda": local.moneda,
        "piso_nivel": local.piso_nivel,
        "descripcion": local.descripcion,
        "poligonos": [
            {
                "id": p.id,
                "plano_id": p.plano_id,
                "coordenadas_relativas": p.coordenadas_relativas,
                "color_relleno": p.color_relleno,
                "color_borde": p.color_borde,
                "opacidad": p.opacidad,
                "etiqueta": p.etiqueta
            }
            for p in local.poligonos
        ]
    }
    return local_dict


@router.put(
    "/{id}",
    response_model=LocalResponse,
    summary="Actualizar términos comerciales de la Ficha del Local (Emite outbox local.actualizado)"
)
async def update_local(
    id: str,
    local_in: LocalUpdate,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    stmt = select(Local).where((Local.id == id) | (Local.codigo_local == id))
    result = await db.execute(stmt)
    local = result.scalar_one_or_none()

    if not local:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Local con id o código '{id}' no encontrado"
        )

    update_data = local_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(local, field, value)

    # Emit transactional outbox event
    payload = {
        "local_id": local.id,
        "codigo_local": local.codigo_local,
        "centro_comercial_id": local.centro_comercial_id,
        "nombre_comercial": local.nombre_comercial,
        "estado": local.estado,
        "precio_alquiler_mensual": local.precio_alquiler_mensual,
        "moneda": local.moneda,
        "area_m2": local.area_m2,
        "modificado_por_rol": _role
    }
    await record_outbox_event(
        db=db,
        tipo_evento="local.actualizado",
        entidad_tipo="local",
        entidad_id=local.id,
        payload=payload
    )

    await db.commit()
    await db.refresh(local)
    return LocalResponse.model_validate(local)


@router.post(
    "/",
    response_model=LocalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Local Comercial"
)
async def create_local(
    local_in: LocalCreate,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    local = Local(**local_in.model_dump())
    db.add(local)
    await db.commit()
    await db.refresh(local)
    return LocalResponse.model_validate(local)
