import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evento_outbox import EventoOutbox


@pytest.mark.asyncio
async def test_list_locales_by_mall(client: AsyncClient, seeded_entities: dict):
    """Verifies listing commercial units for a specific shopping center."""
    mall = seeded_entities["mall"]
    res = await client.get(
        f"/api/v1/locales/?centro_comercial_id={mall.id}",
        headers={"X-User-Role": "comercial"}
    )
    assert res.status_code == 200
    locales = res.json()
    assert len(locales) == 3
    codes = [l["codigo_local"] for l in locales]
    assert "LCE-103" in codes
    assert "LCE-104" in codes
    assert "LCE-105" in codes


@pytest.mark.asyncio
async def test_get_ficha_del_local_detail(client: AsyncClient, seeded_entities: dict):
    """Verifies opening the complete Ficha del Local with attached polygons."""
    local = seeded_entities["locales"][0]  # LCE-103 COOLBOX
    res = await client.get(
        f"/api/v1/locales/{local.id}",
        headers={"X-User-Role": "comercial"}
    )
    assert res.status_code == 200
    ficha = res.json()

    assert ficha["codigo_local"] == "LCE-103"
    assert ficha["nombre_comercial"] == "COOLBOX"
    assert ficha["area_m2"] == 29.70
    assert ficha["estado"] == "arrendado"
    assert ficha["precio_alquiler_mensual"] == 1250.0
    assert "poligonos" in ficha
    assert len(ficha["poligonos"]) >= 1
    assert len(ficha["poligonos"][0]["coordenadas_relativas"]) == 4


@pytest.mark.asyncio
async def test_update_local_and_outbox_event(client: AsyncClient, seeded_entities: dict, db_session: AsyncSession):
    """
    Verifies updating commercial terms (e.g. rent increase, tenant change)
    and asserts that a transactional outbox event (local.actualizado) is emitted.
    """
    local = seeded_entities["locales"][1]  # LCE-104 TINKA

    update_payload = {
        "nombre_comercial": "TINKA LOTERIAS & APUESTAS",
        "precio_alquiler_mensual": 1750.00,
        "estado": "arrendado"
    }

    res = await client.put(
        f"/api/v1/locales/{local.id}",
        json=update_payload,
        headers={"X-User-Role": "comercial"}
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["nombre_comercial"] == "TINKA LOTERIAS & APUESTAS"
    assert updated["precio_alquiler_mensual"] == 1750.00
    assert updated["estado"] == "arrendado"

    # Verify transactional outbox event was created
    stmt = select(EventoOutbox).where(EventoOutbox.tipo_evento == "local.actualizado")
    event = (await db_session.execute(stmt)).scalars().first()
    assert event is not None
    assert event.entidad_tipo == "local"
    assert event.entidad_id == local.id
    assert event.payload["codigo_local"] == "LCE-104"
    assert event.payload["precio_alquiler_mensual"] == 1750.00
    assert event.payload["nombre_comercial"] == "TINKA LOTERIAS & APUESTAS"
    assert event.estado == "pendiente"
