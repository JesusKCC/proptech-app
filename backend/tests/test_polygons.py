import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evento_outbox import EventoOutbox


@pytest.mark.asyncio
async def test_create_polygon_proyectos_role_success(client: AsyncClient, seeded_entities: dict, db_session: AsyncSession):
    """Verifies that Area Proyectos can create and associate polygons on architectural blueprints."""
    plano = seeded_entities["plano"]
    local_tinka = seeded_entities["locales"][1]  # LCE-104

    payload = {
        "local_id": local_tinka.id,
        "plano_id": plano.id,
        "coordenadas_relativas": [
            {"x": 0.7167, "y": 0.5523},
            {"x": 0.7167, "y": 0.4967},
            {"x": 0.7360, "y": 0.4967},
            {"x": 0.7360, "y": 0.5523}
        ],
        "color_relleno": "#f59e0b",
        "color_borde": "#b45309",
        "opacidad": 0.45,
        "etiqueta": "LCE-104"
    }

    res = await client.post(
        "/api/v1/poligonos/",
        json=payload,
        headers={"X-User-Role": "proyectos"}
    )

    assert res.status_code == 201
    data = res.json()
    assert data["local_id"] == local_tinka.id
    assert data["plano_id"] == plano.id
    assert len(data["coordenadas_relativas"]) == 4
    assert data["coordenadas_relativas"][0]["x"] == 0.7167

    # Verify outbox event for poligono.creado
    stmt = select(EventoOutbox).where(EventoOutbox.tipo_evento == "poligono.creado")
    event = (await db_session.execute(stmt)).scalars().first()
    assert event is not None
    assert event.payload["codigo_local"] == "LCE-104"


@pytest.mark.asyncio
async def test_create_polygon_comercial_role_forbidden_403(client: AsyncClient, seeded_entities: dict):
    """Verifies that Area Comercial is strictly forbidden (403) from drawing or creating polygons."""
    plano = seeded_entities["plano"]
    local_tinka = seeded_entities["locales"][1]

    payload = {
        "local_id": local_tinka.id,
        "plano_id": plano.id,
        "coordenadas_relativas": [
            {"x": 0.1, "y": 0.1},
            {"x": 0.2, "y": 0.1},
            {"x": 0.2, "y": 0.2}
        ]
    }

    res = await client.post(
        "/api/v1/poligonos/",
        json=payload,
        headers={"X-User-Role": "comercial"}
    )

    assert res.status_code == 403
    assert "Acceso denegado" in res.json()["detail"]


@pytest.mark.asyncio
async def test_update_polygon_comercial_role_forbidden_403(client: AsyncClient, seeded_entities: dict):
    """Verifies that Area Comercial is forbidden (403) from modifying polygon vertices or styles."""
    polygon = seeded_entities["polygon"]

    res = await client.put(
        f"/api/v1/poligonos/{polygon.id}",
        json={"color_relleno": "#ff0000"},
        headers={"X-User-Role": "comercial"}
    )

    assert res.status_code == 403


@pytest.mark.asyncio
async def test_polygon_relative_coordinate_boundary_rejection_422(client: AsyncClient, seeded_entities: dict):
    """
    Verifies that polygon coordinates strictly adhere to [0.0, 1.0].
    Any vertex > 1.0 or < 0.0 must be rejected with 422 Unprocessable Entity.
    """
    plano = seeded_entities["plano"]
    local_bitel = seeded_entities["locales"][2]

    # Coordinate X = 1.35 (exceeds normalized unit space)
    invalid_upper = {
        "local_id": local_bitel.id,
        "plano_id": plano.id,
        "coordenadas_relativas": [
            {"x": 1.35, "y": 0.2},
            {"x": 0.5, "y": 0.2},
            {"x": 0.5, "y": 0.5}
        ]
    }
    res_upper = await client.post(
        "/api/v1/poligonos/",
        json=invalid_upper,
        headers={"X-User-Role": "proyectos"}
    )
    assert res_upper.status_code == 422

    # Coordinate Y = -0.15 (below normalized unit space)
    invalid_lower = {
        "local_id": local_bitel.id,
        "plano_id": plano.id,
        "coordenadas_relativas": [
            {"x": 0.2, "y": -0.15},
            {"x": 0.4, "y": 0.2},
            {"x": 0.4, "y": 0.4}
        ]
    }
    res_lower = await client.post(
        "/api/v1/poligonos/",
        json=invalid_lower,
        headers={"X-User-Role": "proyectos"}
    )
    assert res_lower.status_code == 422


@pytest.mark.asyncio
async def test_polygon_insufficient_vertices_rejection_422(client: AsyncClient, seeded_entities: dict):
    """Verifies that a polygon with fewer than 3 vertices is rejected with 422."""
    plano = seeded_entities["plano"]
    local_bitel = seeded_entities["locales"][2]

    res = await client.post(
        "/api/v1/poligonos/",
        json={
            "local_id": local_bitel.id,
            "plano_id": plano.id,
            "coordenadas_relativas": [
                {"x": 0.2, "y": 0.2},
                {"x": 0.5, "y": 0.5}  # Only 2 points, cannot form polygon
            ]
        },
        headers={"X-User-Role": "proyectos"}
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_list_polygons_by_plano(client: AsyncClient, seeded_entities: dict):
    """Verifies retrieval of all polygons associated with a blueprint."""
    plano = seeded_entities["plano"]
    res = await client.get(
        f"/api/v1/poligonos/?plano_id={plano.id}",
        headers={"X-User-Role": "comercial"}
    )
    assert res.status_code == 200
    polys = res.json()
    assert len(polys) >= 1
    assert polys[0]["plano_id"] == plano.id


@pytest.mark.asyncio
async def test_delete_polygon_proyectos_role_success(client: AsyncClient, seeded_entities: dict):
    """Verifies that Proyectos role can delete a polygon."""
    polygon = seeded_entities["polygon"]
    res = await client.delete(
        f"/api/v1/poligonos/{polygon.id}",
        headers={"X-User-Role": "proyectos"}
    )
    assert res.status_code == 204
