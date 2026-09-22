import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_centros_comerciales_standard_json(client: AsyncClient, seeded_entities: dict):
    """Verifies retrieval of standard JSON list of shopping centers with geographic coordinates."""
    res = await client.get("/api/v1/centros-comerciales/", headers={"X-User-Role": "comercial"})
    assert res.status_code == 200
    malls = res.json()
    assert isinstance(malls, list)
    assert len(malls) >= 2

    # Check first mall
    ves = next((m for m in malls if m["slug"] == "plaza-center-villa-el-salvador"), None)
    assert ves is not None
    assert ves["nombre"] == "Plaza Center Villa El Salvador"
    assert ves["departamento"] == "Lima"
    assert ves["lat"] == -12.215
    assert ves["lon"] == -76.938
    assert ves["total_locales"] == 26


@pytest.mark.asyncio
async def test_get_centros_comerciales_geojson_feature_collection(client: AsyncClient, seeded_entities: dict):
    """
    Verifies that requesting format=geojson returns a valid GeoJSON FeatureCollection
    conforming to RFC 7946 for Leaflet/Mapbox integration.
    """
    res = await client.get(
        "/api/v1/centros-comerciales/?format=geojson",
        headers={"X-User-Role": "comercial"}
    )
    assert res.status_code == 200
    data = res.json()

    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) >= 2

    first_feature = data["features"][0]
    assert first_feature["type"] == "Feature"
    assert "geometry" in first_feature
    assert first_feature["geometry"]["type"] == "Point"
    # GeoJSON standard specifies [longitude, latitude]
    coords = first_feature["geometry"]["coordinates"]
    assert len(coords) == 2
    lon, lat = coords[0], coords[1]
    assert -82.0 <= lon <= -68.0
    assert -19.0 <= lat <= 0.0

    # Check properties payload
    props = first_feature["properties"]
    assert "nombre" in props
    assert "departamento" in props
    assert "total_locales" in props


@pytest.mark.asyncio
async def test_peru_geographic_coordinate_bounds(client: AsyncClient, seeded_entities: dict):
    """Verifies that all shopping center coordinates lie strictly within the geographic bounds of Peru."""
    res = await client.get("/api/v1/centros-comerciales/", headers={"X-User-Role": "comercial"})
    assert res.status_code == 200
    malls = res.json()

    for m in malls:
        lat = m["lat"]
        lon = m["lon"]
        # Peru bounding box: Lat [-18.5, 0.0], Lon [-81.5, -68.0]
        assert -18.5 <= lat <= 0.0, f"Mall {m['nombre']} lat {lat} out of Peru bounds"
        assert -81.5 <= lon <= -68.0, f"Mall {m['nombre']} lon {lon} out of Peru bounds"


@pytest.mark.asyncio
async def test_get_centro_comercial_detail_with_planos(client: AsyncClient, seeded_entities: dict):
    """Verifies retrieval of mall details including nested architectural blueprints."""
    mall = seeded_entities["mall"]
    res = await client.get(
        f"/api/v1/centros-comerciales/{mall.slug}",
        headers={"X-User-Role": "comercial"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["slug"] == mall.slug
    assert "planos" in data
    assert len(data["planos"]) >= 1

    plano = data["planos"][0]
    assert plano["nombre_piso"] == "Nivel 1 - Galería Principal"
    assert plano["ancho_unscaled_pt"] == 2384.0
    assert plano["alto_unscaled_pt"] == 1684.0
    assert "pacita_ves_nivel1.pdf" in plano["archivo_pdf_url"]


@pytest.mark.asyncio
async def test_create_centro_comercial_outside_peru_bounds_rejected_422(client: AsyncClient):
    """Verifies that attempting to create a shopping center with coordinates outside Peru envelope is rejected with 422."""
    # Coordinates in Madrid, Spain (outside Peru [-18.5, 0.0], [-81.5, -68.5])
    overseas_payload = {
        "nombre": "Centro Comercial Madrid Norte",
        "slug": "cc-madrid-norte",
        "direccion": "Gran Vía 1",
        "departamento": "Madrid",
        "provincia": "Madrid",
        "distrito": "Centro",
        "lat": 40.4168,
        "lon": -3.7038,
        "total_locales": 50,
        "superficie_total_m2": 25000.0
    }
    res = await client.post(
        "/api/v1/centros-comerciales/",
        json=overseas_payload,
        headers={"X-User-Role": "proyectos"}
    )
    assert res.status_code == 422
    assert "outside official Peru territorial envelope" in str(res.json())


@pytest.mark.asyncio
async def test_create_centro_comercial_valid_peru_coordinates_success(client: AsyncClient):
    """Verifies that a shopping center with valid Peru coordinates is successfully created."""
    valid_payload = {
        "nombre": "Plaza San Martín Cusco",
        "slug": "plaza-san-martin-cusco",
        "direccion": "Av. El Sol 100",
        "departamento": "Cusco",
        "provincia": "Cusco",
        "distrito": "Wanchaq",
        "lat": -13.5226,
        "lon": -71.9427,
        "total_locales": 30,
        "superficie_total_m2": 15000.0
    }
    res = await client.post(
        "/api/v1/centros-comerciales/",
        json=valid_payload,
        headers={"X-User-Role": "proyectos"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["slug"] == valid_payload["slug"]
    assert data["lat"] == -13.5226
    assert data["lon"] == -71.9427
