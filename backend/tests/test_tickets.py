import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evento_outbox import EventoOutbox
from app.models.ticket import Ticket


@pytest.mark.asyncio
async def test_create_ticket_comercial_role_success(client: AsyncClient, seeded_entities: dict, db_session: AsyncSession):
    """Verifies that Area Comercial can successfully create requirement tickets and emits outbox event."""
    mall = seeded_entities["mall"]
    local = seeded_entities["locales"][0]

    payload = {
        "centro_comercial_id": mall.id,
        "local_id": local.id,
        "titulo": "Revisión urgente de falso techo",
        "descripcion": "Filtración detectada en falso techo sobre el mostrador principal.",
        "tipo": "mantenimiento",
        "prioridad": "alta",
        "creado_por": "comercial"
    }

    response = await client.post(
        "/api/v1/tickets/",
        json=payload,
        headers={"X-User-Role": "comercial"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["codigo_ticket"].startswith("TCK-2026-")
    assert data["titulo"] == payload["titulo"]
    assert data["estado"] == "abierto"
    assert data["creado_por"] == "comercial"

    # Verify outbox event was atomically recorded
    stmt = select(EventoOutbox).where(EventoOutbox.tipo_evento == "ticket.creado")
    events = (await db_session.execute(stmt)).scalars().all()
    assert len(events) >= 1
    last_event = events[-1]
    assert last_event.entidad_tipo == "ticket"
    assert last_event.payload["titulo"] == payload["titulo"]
    assert last_event.estado == "pendiente"


@pytest.mark.asyncio
async def test_create_ticket_proyectos_role_success(client: AsyncClient, seeded_entities: dict):
    """Verifies that Area Proyectos can also create tickets."""
    mall = seeded_entities["mall"]

    payload = {
        "centro_comercial_id": mall.id,
        "titulo": "Inspección estructural pasillo este",
        "descripcion": "Revisión programada de ductos de ventilación.",
        "tipo": "modificacion_plano",
        "prioridad": "media"
    }

    response = await client.post(
        "/api/v1/tickets/",
        json=payload,
        headers={"X-User-Role": "proyectos"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "abierto"


@pytest.mark.asyncio
async def test_resolve_ticket_proyectos_role_success(client: AsyncClient, seeded_entities: dict, db_session: AsyncSession):
    """Verifies that Area Proyectos can resolve open tickets with technical notes and emits outbox event."""
    mall = seeded_entities["mall"]
    local = seeded_entities["locales"][0]

    # First create ticket
    create_res = await client.post(
        "/api/v1/tickets/",
        json={
            "centro_comercial_id": mall.id,
            "local_id": local.id,
            "titulo": "Ampliación de acometida eléctrica",
            "descripcion": "Cliente solicita pasar de 15kW a 25kW.",
            "tipo": "nuevo_requerimiento",
            "prioridad": "urgente"
        },
        headers={"X-User-Role": "comercial"}
    )
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]

    # Resolve with Proyectos role
    resolve_payload = {
        "notas_resolucion": "Inspección técnica favorable. Tablero eléctrico secundario reforzado con interruptor 50A."
    }
    resolve_res = await client.patch(
        f"/api/v1/tickets/{ticket_id}/resolve",
        json=resolve_payload,
        headers={"X-User-Role": "proyectos"}
    )

    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["estado"] == "resuelto"
    assert res_data["notas_resolucion"] == resolve_payload["notas_resolucion"]
    assert res_data["resuelto_en"] is not None

    # Check outbox event for ticket.resuelto
    stmt = select(EventoOutbox).where(EventoOutbox.tipo_evento == "ticket.resuelto")
    event = (await db_session.execute(stmt)).scalars().first()
    assert event is not None
    assert event.payload["estado"] == "resuelto"
    assert "reforzado con interruptor" in event.payload["notas_resolucion"]


@pytest.mark.asyncio
async def test_resolve_ticket_comercial_role_forbidden_403(client: AsyncClient, seeded_entities: dict):
    """Verifies that RBAC strictly rejects (403 Forbidden) Area Comercial from resolving tickets."""
    mall = seeded_entities["mall"]

    # Create ticket
    create_res = await client.post(
        "/api/v1/tickets/",
        json={
            "centro_comercial_id": mall.id,
            "titulo": "Validación de carga",
            "descripcion": "Verificación de capacidad de piso.",
            "tipo": "revision_comercial",
            "prioridad": "media"
        },
        headers={"X-User-Role": "comercial"}
    )
    ticket_id = create_res.json()["id"]

    # Attempt to resolve using COMERCIAL role
    resolve_res = await client.patch(
        f"/api/v1/tickets/{ticket_id}/resolve",
        json={"notas_resolucion": "Intento no autorizado de resolución comercial"},
        headers={"X-User-Role": "comercial"}
    )

    assert resolve_res.status_code == 403
    assert "Acceso denegado" in resolve_res.json()["detail"]


@pytest.mark.asyncio
async def test_resolve_ticket_empty_notes_validation_error(client: AsyncClient, seeded_entities: dict):
    """Verifies that resolving a ticket without resolution notes fails validation (422)."""
    mall = seeded_entities["mall"]
    create_res = await client.post(
        "/api/v1/tickets/",
        json={
            "centro_comercial_id": mall.id,
            "titulo": "Ticket para prueba de validación",
            "descripcion": "Prueba de validación.",
            "tipo": "nuevo_requerimiento"
        },
        headers={"X-User-Role": "proyectos"}
    )
    ticket_id = create_res.json()["id"]

    # Missing/empty notes
    res = await client.patch(
        f"/api/v1/tickets/{ticket_id}/resolve",
        json={"notas_resolucion": ""},
        headers={"X-User-Role": "proyectos"}
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_resolve_already_resolved_ticket_fails_400(client: AsyncClient, seeded_entities: dict, db_session: AsyncSession):
    """Verifies that attempting to resolve an already resolved ticket returns 400 Bad Request without duplicate outbox event."""
    mall = seeded_entities["mall"]
    create_res = await client.post(
        "/api/v1/tickets/",
        json={
            "centro_comercial_id": mall.id,
            "titulo": "Ticket doble resolución",
            "descripcion": "Prueba doble resolución.",
            "tipo": "nuevo_requerimiento"
        },
        headers={"X-User-Role": "proyectos"}
    )
    ticket_id = create_res.json()["id"]

    # First resolve
    res1 = await client.patch(
        f"/api/v1/tickets/{ticket_id}/resolve",
        json={"notas_resolucion": "Primera resolución válida"},
        headers={"X-User-Role": "proyectos"}
    )
    assert res1.status_code == 200

    # Second resolve
    res2 = await client.patch(
        f"/api/v1/tickets/{ticket_id}/resolve",
        json={"notas_resolucion": "Segunda resolución inválida"},
        headers={"X-User-Role": "proyectos"}
    )
    assert res2.status_code == 400
    assert "ya se encuentra en estado resuelto" in res2.json()["detail"]

    # Verify no duplicate outbox event was generated
    stmt = select(EventoOutbox).where(
        EventoOutbox.tipo_evento == "ticket.resuelto",
        EventoOutbox.entidad_id == ticket_id
    )
    events = (await db_session.execute(stmt)).scalars().all()
    assert len(events) == 1, f"Expected exactly 1 outbox event, found {len(events)}"


@pytest.mark.asyncio
async def test_list_tickets_with_filters(client: AsyncClient, seeded_entities: dict):
    """Verifies ticket querying and filtering by mall and status."""
    mall = seeded_entities["mall"]
    # List tickets
    res = await client.get(
        f"/api/v1/tickets/?centro_comercial_id={mall.id}&estado=abierto",
        headers={"X-User-Role": "proyectos"}
    )
    assert res.status_code == 200
    tickets = res.json()
    assert isinstance(tickets, list)
