# Tier 1 Feature Tests: Backend Verification & Acceptance Criteria (FEAT-AC-01 & FEAT-AC-02)
# Authoritative Sources: ORIGINAL_REQUEST.md § Acceptance Criteria, PROJECT.md § Feature Inventory
import os
import sys
from pydantic import ValidationError
from fastapi import HTTPException

# Ensure backend root is in sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", ".."))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from tests_e2e.core.runner import TestRegistry
from tests_e2e.core.contracts import (
    AUTHENTIC_PERU_MALLS, is_within_peru, validate_polygon_geometry,
    check_rbac_permission, ROLE_COMERCIAL, ROLE_PROYECTOS
)
from seed import AUTHENTIC_MALLS_DATA, AUTHENTIC_LOCALES_DATA, AUTHENTIC_POLYGONS_DATA
from app.schemas.centro_comercial import CentroComercialCreate, CentroComercialResponse
from app.schemas.local import LocalCreate, LocalResponse
from app.schemas.poligono import PoligonoCreate, RelativeCoordinate
from app.schemas.ticket import TicketCreate, TicketResolve, TicketResponse, TicketEstado
from app.core.security import require_proyectos, UserRole

# ==========================================
# FEAT-AC-01: Database Seed Script (seed.py)
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-01-01",
    name="Verify seed script structure and specification requirements",
    tier=1,
    feature_id="FEAT-AC-01",
    authoritative_source="ORIGINAL_REQUEST.md § AC Backend y BD"
)
def test_ac_01_seed_specification():
    # Specification contract: seed must define >= 1 shopping center, >= 3 commercial units, and >= 1 polygon in Peru
    assert len(AUTHENTIC_MALLS_DATA) >= 1, f"Seed must provide >= 1 mall, found {len(AUTHENTIC_MALLS_DATA)}"
    assert len(AUTHENTIC_LOCALES_DATA) >= 3, f"Seed must provide >= 3 commercial units, found {len(AUTHENTIC_LOCALES_DATA)}"
    assert len(AUTHENTIC_POLYGONS_DATA) >= 1, f"Seed must provide >= 1 polygon, found {len(AUTHENTIC_POLYGONS_DATA)}"

    # Validate each seeded mall with CentroComercialCreate schema ensuring Peru envelope compliance
    for mall_dict in AUTHENTIC_MALLS_DATA:
        schema_mall = CentroComercialCreate(**mall_dict)
        assert -18.5 <= schema_mall.lat <= 0.0, f"Mall {schema_mall.nombre} lat outside Peru"
        assert -81.5 <= schema_mall.lon <= -68.5, f"Mall {schema_mall.nombre} lon outside Peru"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-01-02",
    name="Verify seed data includes authentic Peru mall in Lima",
    tier=1,
    feature_id="FEAT-AC-01",
    authoritative_source="ORIGINAL_REQUEST.md § AC Backend y BD & PROJECT.md"
)
def test_ac_01_seed_mall_peru():
    ves_mall = next((m for m in AUTHENTIC_MALLS_DATA if "Villa El Salvador" in m["nombre"]), None)
    assert ves_mall is not None, "Authentic Villa El Salvador mall must be present in seed"
    
    # Validate via application schema
    validated = CentroComercialCreate(**ves_mall)
    assert is_within_peru(validated.lat, validated.lon)
    assert validated.departamento == "Lima"

    # Adversarial check: overseas coordinate must be rejected by Pydantic schema
    invalid_mall = dict(ves_mall)
    invalid_mall["lat"] = 40.4168  # Madrid
    invalid_mall["lon"] = -3.7038
    try:
        CentroComercialCreate(**invalid_mall)
        assert False, "Overseas coordinates must be rejected by CentroComercialCreate"
    except ValidationError:
        pass

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-01-03",
    name="Verify seed data includes at least 3 distinct commercial units",
    tier=1,
    feature_id="FEAT-AC-01",
    authoritative_source="ORIGINAL_REQUEST.md § AC Backend y BD"
)
def test_ac_01_seed_locales():
    assert len(AUTHENTIC_LOCALES_DATA) >= 3
    unique_codes = {l[0] for l in AUTHENTIC_LOCALES_DATA}
    assert len(unique_codes) == len(AUTHENTIC_LOCALES_DATA)

    # Validate first 3 locales using application schema LocalCreate
    dummy_cc_id = "test-cc-id-123"
    for code, name, area, cat, estado, precio in AUTHENTIC_LOCALES_DATA[:3]:
        local_in = LocalCreate(
            centro_comercial_id=dummy_cc_id,
            codigo_local=code,
            nombre_comercial=name,
            area_m2=area,
            categoria=cat,
            estado=estado,
            precio_alquiler_mensual=precio
        )
        assert local_in.codigo_local == code
        assert local_in.area_m2 > 0

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-01-04",
    name="Verify seed data includes at least 1 normalized polygon",
    tier=1,
    feature_id="FEAT-AC-01",
    authoritative_source="ORIGINAL_REQUEST.md § AC Backend y BD"
)
def test_ac_01_seed_polygon():
    assert len(AUTHENTIC_POLYGONS_DATA) >= 1
    # Check that authentic polygon coordinates parse into valid normalized coordinates in [0..1]
    poly_spec = AUTHENTIC_POLYGONS_DATA[0]
    raw_coords = poly_spec["coords"].split()
    pts = []
    # Seed normalizes by 4967 x 3509
    for pair in raw_coords:
        px, py = pair.split(",")
        pts.append(RelativeCoordinate(x=round(float(px) / 4967.0, 4), y=round(float(py) / 3509.0, 4)))

    assert len(pts) >= 3
    for pt in pts:
        assert 0.0 <= pt.x <= 1.0
        assert 0.0 <= pt.y <= 1.0

    poly_create = PoligonoCreate(
        local_id="loc-test-1",
        plano_id="plano-test-1",
        coordenadas_relativas=pts,
        color_relleno=poly_spec.get("color", "#3b82f6")
    )
    assert len(poly_create.coordenadas_relativas) >= 3

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-01-05",
    name="Verify seed idempotency contract (UPSERT / conflict handling)",
    tier=1,
    feature_id="FEAT-AC-01",
    authoritative_source="PROJECT.md § Survey Handoff Seed Idempotency"
)
def test_ac_01_seed_idempotency_contract():
    # Model contract: unique slug lookup prevents duplicate insertion
    slugs = [m["slug"] for m in AUTHENTIC_MALLS_DATA]
    assert len(slugs) == len(set(slugs)), "Seed malls must define mutually unique slugs"
    
    # Check seed.py file logic contains lookup queries for idempotency
    seed_py_path = os.path.join(BACKEND_ROOT, "seed.py")
    assert os.path.exists(seed_py_path)
    with open(seed_py_path, "r", encoding="utf-8") as f:
        seed_content = f.read()
    assert "select(CentroComercial).where" in seed_content
    assert "select(Local).where" in seed_content
    assert "select(Poligono).where" in seed_content

# ==========================================
# FEAT-AC-02: Pytest Backend Test Suite
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-02-01",
    name="Verify pytest test suite contract and structure",
    tier=1,
    feature_id="FEAT-AC-02",
    authoritative_source="ORIGINAL_REQUEST.md § AC Backend y BD"
)
def test_ac_02_pytest_contract():
    tests_dir = os.path.join(BACKEND_ROOT, "tests")
    required_test_files = [
        "test_tickets.py",
        "test_geo.py",
        "test_polygons.py",
        "test_locales.py",
        "test_webhooks.py"
    ]
    for test_file in required_test_files:
        p = os.path.join(tests_dir, test_file)
        assert os.path.exists(p), f"Pytest suite file {test_file} must exist"
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 100, f"Pytest suite file {test_file} must contain tests"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-02-02",
    name="Verify geographic coordinates endpoint contract in FastAPI",
    tier=1,
    feature_id="FEAT-AC-02",
    authoritative_source="ORIGINAL_REQUEST.md § AC Backend y BD"
)
def test_ac_02_geo_endpoint_contract():
    # Contract: Mall schema validates lat/lon strictly in Peru bounds
    ves = AUTHENTIC_MALLS_DATA[0]
    mall = CentroComercialCreate(**ves)
    assert is_within_peru(mall.lat, mall.lon)

    # Rejection of overseas coordinates
    try:
        CentroComercialCreate(
            nombre="Plaza New York",
            slug="plaza-ny",
            departamento="NY",
            lat=40.7128,
            lon=-74.0060
        )
        assert False, "Should have rejected coordinates outside Peru"
    except ValidationError:
        pass

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-02-03",
    name="Verify ticket creation test contract in FastAPI",
    tier=1,
    feature_id="FEAT-AC-02",
    authoritative_source="ORIGINAL_REQUEST.md § AC Backend y BD"
)
def test_ac_02_ticket_creation_contract():
    # Contract: TicketCreate schema validates required fields and priority/type constraints
    ticket_in = TicketCreate(
        centro_comercial_id="mall-123",
        local_id="local-456",
        titulo="Requerimiento comercial de mantenimiento",
        descripcion="Revisión de conexiones de fibra óptica.",
        tipo="mantenimiento",
        prioridad="alta"
    )
    assert ticket_in.titulo == "Requerimiento comercial de mantenimiento"
    assert ticket_in.tipo == "mantenimiento"
    assert ticket_in.prioridad == "alta"
    assert TicketEstado.ABIERTO.value == "abierto"

    # Rejection of invalid ticket type
    try:
        TicketCreate(
            centro_comercial_id="mall-123",
            titulo="Invalido",
            descripcion="Desc",
            tipo="tipo_inexistente"
        )
        assert False, "Should have rejected invalid ticket type"
    except ValidationError:
        pass

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-02-04",
    name="Verify ticket resolution contract by Proyectos role",
    tier=1,
    feature_id="FEAT-AC-02",
    authoritative_source="ORIGINAL_REQUEST.md § AC Backend y BD & R4"
)
def test_ac_02_ticket_resolution_contract():
    # Contract: TicketResolve requires non-empty technical notes
    valid_resolve = TicketResolve(notas_resolucion="Aprobado tras inspección técnica.")
    assert len(valid_resolve.notas_resolucion) > 0
    assert TicketEstado.RESUELTO.value == "resuelto"

    # Empty notes must be rejected
    try:
        TicketResolve(notas_resolucion="")
        assert False, "Empty notas_resolucion must be rejected"
    except ValidationError:
        pass

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-02-05",
    name="Verify ticket resolution 403 Forbidden contract for Comercial role",
    tier=1,
    feature_id="FEAT-AC-02",
    authoritative_source="ORIGINAL_REQUEST.md § R4 Roles y Seguridad"
)
def test_ac_02_ticket_resolution_forbidden_contract():
    # Require proyectos dependency raises 403 when called with comercial role
    try:
        require_proyectos(role="comercial")
        assert False, "require_proyectos must raise HTTP 403 for role 'comercial'"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert "Acceso denegado" in exc.detail
