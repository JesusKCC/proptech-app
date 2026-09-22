import random
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import require_comercial_or_proyectos, require_proyectos
from app.db.session import get_db
from app.models.centro_comercial import CentroComercial
from app.models.local import Local
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketResolve, TicketResponse, TicketEstado
from app.services.outbox_service import record_outbox_event

router = APIRouter()


def generate_ticket_code() -> str:
    """Generates a human-friendly unique ticket identifier (e.g. TCK-2026-4821)."""
    rand_digits = random.randint(1000, 9999)
    return f"TCK-2026-{rand_digits}"


@router.get(
    "/",
    response_model=List[TicketResponse],
    summary="Listar Tickets con filtros de mall, local, estado y prioridad"
)
async def list_tickets(
    centro_comercial_id: Optional[str] = Query(None, description="Filtrar por Centro Comercial ID"),
    local_id: Optional[str] = Query(None, description="Filtrar por Local ID"),
    estado: Optional[str] = Query(None, description="Filtrar por estado: abierto, en_revision, resuelto, rechazado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad: baja, media, alta, urgente"),
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    stmt = select(Ticket)
    if centro_comercial_id:
        stmt = stmt.where(Ticket.centro_comercial_id == centro_comercial_id)
    if local_id:
        stmt = stmt.where(Ticket.local_id == local_id)
    if estado:
        stmt = stmt.where(Ticket.estado == estado.lower())
    if prioridad:
        stmt = stmt.where(Ticket.prioridad == prioridad.lower())

    stmt = stmt.order_by(Ticket.creado_en.desc())
    result = await db.execute(stmt)
    tickets = result.scalars().all()
    return [TicketResponse.model_validate(t) for t in tickets]


@router.get(
    "/{id}",
    response_model=TicketResponse,
    summary="Obtener detalle de ticket por ID o código"
)
async def get_ticket(
    id: str,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_comercial_or_proyectos)
):
    stmt = select(Ticket).where((Ticket.id == id) | (Ticket.codigo_ticket == id))
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket con id o código '{id}' no encontrado"
        )
    return TicketResponse.model_validate(ticket)


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Ticket de Requerimiento (Permitido para Comercial y Proyectos - Emite outbox ticket.creado)"
)
async def create_ticket(
    ticket_in: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_role: str = Depends(require_comercial_or_proyectos)
):
    # Verify mall exists
    mall = (await db.execute(select(CentroComercial).where(CentroComercial.id == ticket_in.centro_comercial_id))).scalar_one_or_none()
    if not mall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centro Comercial '{ticket_in.centro_comercial_id}' no existe"
        )

    # Verify local exists if provided
    if ticket_in.local_id:
        local = (await db.execute(select(Local).where(Local.id == ticket_in.local_id))).scalar_one_or_none()
        if not local:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Local '{ticket_in.local_id}' no existe"
            )

    # Generate unique ticket code
    code = generate_ticket_code()
    # Check collisions
    while (await db.execute(select(Ticket).where(Ticket.codigo_ticket == code))).scalar_one_or_none():
        code = generate_ticket_code()

    ticket_data = ticket_in.model_dump()
    ticket_data["codigo_ticket"] = code
    ticket_data["creado_por"] = current_role
    ticket_data["estado"] = "abierto"

    ticket = Ticket(**ticket_data)
    db.add(ticket)

    # Record transactional outbox event
    payload = {
        "ticket_id": ticket.id,
        "codigo_ticket": ticket.codigo_ticket,
        "centro_comercial_id": ticket.centro_comercial_id,
        "local_id": ticket.local_id,
        "titulo": ticket.titulo,
        "tipo": ticket.tipo,
        "prioridad": ticket.prioridad,
        "creado_por": current_role,
        "estado": "abierto"
    }
    await record_outbox_event(
        db=db,
        tipo_evento="ticket.creado",
        entidad_tipo="ticket",
        entidad_id=ticket.id,
        payload=payload
    )

    await db.commit()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


@router.patch(
    "/{id}/resolve",
    response_model=TicketResponse,
    summary="Resolver Ticket con notas técnicas (Requiere rol proyectos - 403 para comercial, emite outbox ticket.resuelto)"
)
async def resolve_ticket(
    id: str,
    resolve_in: TicketResolve,
    db: AsyncSession = Depends(get_db),
    _role: str = Depends(require_proyectos)
):
    stmt = select(Ticket).where((Ticket.id == id) | (Ticket.codigo_ticket == id))
    result = await db.execute(stmt)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket con id o código '{id}' no encontrado"
        )

    if ticket.estado == TicketEstado.RESUELTO or ticket.estado == TicketEstado.RESUELTO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ticket ya se encuentra en estado resuelto"
        )

    now = datetime.now(timezone.utc)
    ticket.estado = TicketEstado.RESUELTO.value
    ticket.notas_resolucion = resolve_in.notas_resolucion
    ticket.resuelto_en = now
    ticket.asignado_a = _role

    # Record outbox event
    payload = {
        "ticket_id": ticket.id,
        "codigo_ticket": ticket.codigo_ticket,
        "centro_comercial_id": ticket.centro_comercial_id,
        "local_id": ticket.local_id,
        "titulo": ticket.titulo,
        "estado": TicketEstado.RESUELTO.value,
        "notas_resolucion": ticket.notas_resolucion,
        "resuelto_por": _role,
        "resuelto_en": now.isoformat()
    }
    await record_outbox_event(
        db=db,
        tipo_evento="ticket.resuelto",
        entidad_tipo="ticket",
        entidad_id=ticket.id,
        payload=payload
    )

    await db.commit()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)
