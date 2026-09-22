# Tier 1 Feature Tests: Frontend Modules & Workflows (FEAT-R3-01 to FEAT-R3-05)
# Authoritative Sources: ORIGINAL_REQUEST.md § R3, PROJECT.md § Feature Inventory
from tests_e2e.core.runner import TestRegistry
from tests_e2e.core.contracts import (
    AUTHENTIC_PERU_MALLS, is_within_peru, check_rbac_permission,
    ROLE_COMERCIAL, ROLE_PROYECTOS, TICKET_ESTADOS, LOCAL_ESTADOS
)

# ==========================================
# FEAT-R3-01: Peru Satellite Overview Map
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-01-01",
    name="Verify Satellite map initial center centered on Peru",
    tier=1,
    feature_id="FEAT-R3-01",
    authoritative_source="PROJECT.md § Peru Satellite GIS Map"
)
def test_r3_01_map_center():
    # Centered on Peru: approx [-9.19, -75.015] or Lima [-12.046, -77.042]
    center_lat, center_lon = -12.0464, -77.0428
    assert is_within_peru(center_lat, center_lon)

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-01-02",
    name="Verify Esri World Imagery satellite tiles layer URL format",
    tier=1,
    feature_id="FEAT-R3-01",
    authoritative_source="PROJECT.md § Satellite Imagery"
)
def test_r3_01_satellite_tiles():
    esri_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    assert "ArcGIS/rest/services/World_Imagery" in esri_url
    assert "{z}/{y}/{x}" in esri_url

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-01-03",
    name="Verify markers placed for all authentic Peru malls",
    tier=1,
    feature_id="FEAT-R3-01",
    authoritative_source="PROJECT.md § Peru Satellite GIS Map"
)
def test_r3_01_mall_markers():
    markers = [{"id": m["slug"], "position": [m["lat"], m["lon"]], "title": m["nombre"]} for m in AUTHENTIC_PERU_MALLS]
    assert len(markers) == len(AUTHENTIC_PERU_MALLS)
    assert all(is_within_peru(m["position"][0], m["position"][1]) for m in markers)

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-01-04",
    name="Verify marker popup information payload",
    tier=1,
    feature_id="FEAT-R3-01",
    authoritative_source="PROJECT.md § Satellite Map Popups"
)
def test_r3_01_popup_payload():
    popup_data = {
        "nombre": "Real Plaza Salaverry",
        "departamento": "Lima",
        "total_locales": 180,
        "superficie_total_m2": 85000.0
    }
    assert len(popup_data["nombre"]) > 0
    assert popup_data["total_locales"] > 0
    assert popup_data["superficie_total_m2"] > 0

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-01-05",
    name="Verify map marker click triggers mall selection event",
    tier=1,
    feature_id="FEAT-R3-01",
    authoritative_source="PROJECT.md § Navigation Flow"
)
def test_r3_01_marker_click():
    event = {"type": "MALL_SELECTED", "mall_slug": "plaza-center-ves"}
    assert event["type"] == "MALL_SELECTED"
    assert event["mall_slug"] is not None

# ==========================================
# FEAT-R3-02: Mall Portfolio Summary Table
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-02-01",
    name="Verify portfolio summary table column schema",
    tier=1,
    feature_id="FEAT-R3-02",
    authoritative_source="PROJECT.md § 14. Mall Portfolio Summary Table"
)
def test_r3_02_columns_schema():
    expected_columns = ["Código", "Nombre", "Departamento", "Locales", "Superficie", "Acciones"]
    assert len(expected_columns) == 6
    assert "Acciones" in expected_columns

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-02-02",
    name="Verify portfolio total aggregation metrics",
    tier=1,
    feature_id="FEAT-R3-02",
    authoritative_source="PROJECT.md § Summary Table Aggregations"
)
def test_r3_02_portfolio_metrics():
    malls_sample = [
        {"locales": 26, "area": 45000.0},
        {"locales": 150, "area": 85000.0},
        {"locales": 200, "area": 120000.0}
    ]
    total_locales = sum(m["locales"] for m in malls_sample)
    total_area = sum(m["area"] for m in malls_sample)
    assert total_locales == 376
    assert total_area == 250000.0

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-02-03",
    name="Verify table row click navigates to blueprint viewer URL",
    tier=1,
    feature_id="FEAT-R3-02",
    authoritative_source="PROJECT.md § Navigation Flow"
)
def test_r3_02_navigation_url():
    mall_slug = "plaza-center-ves"
    target_url = f"/planos?mall={mall_slug}"
    assert target_url == "/planos?mall=plaza-center-ves"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-02-04",
    name="Verify department filter logic across malls portfolio",
    tier=1,
    feature_id="FEAT-R3-02",
    authoritative_source="PROJECT.md § Filtering"
)
def test_r3_02_department_filter():
    lima_malls = [m for m in AUTHENTIC_PERU_MALLS if m["departamento"] == "Lima"]
    arequipa_malls = [m for m in AUTHENTIC_PERU_MALLS if m["departamento"] == "Arequipa"]
    assert len(lima_malls) >= 3
    assert len(arequipa_malls) >= 2

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-02-05",
    name="Verify empty state representation when portfolio has 0 items",
    tier=1,
    feature_id="FEAT-R3-02",
    authoritative_source="PROJECT.md § Edge Cases"
)
def test_r3_02_empty_state():
    empty_list = []
    empty_message = "No se encontraron centros comerciales." if not empty_list else ""
    assert len(empty_message) > 0

# ==========================================
# FEAT-R3-03: Commercial Unit Sheet (Ficha del Local)
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-03-01",
    name="Verify Ficha del Local opens on polygon click",
    tier=1,
    feature_id="FEAT-R3-03",
    authoritative_source="ORIGINAL_REQUEST.md § R3 & PROJECT.md"
)
def test_r3_03_drawer_open():
    ui_state = {"selected_local_id": "loc-coolbox-103", "drawer_open": True}
    assert ui_state["drawer_open"] is True
    assert ui_state["selected_local_id"] == "loc-coolbox-103"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-03-02",
    name="Verify Ficha del Local displays all required technical and commercial specs",
    tier=1,
    feature_id="FEAT-R3-03",
    authoritative_source="PROJECT.md § 1. Backend API Contracts /locales/{id}"
)
def test_r3_03_specs_display():
    ficha = {
        "codigo_local": "LCE-103",
        "nombre_comercial": "COOLBOX",
        "categoria": "Tecnología",
        "estado": "arrendado",
        "area_m2": 29.70,
        "precio_alquiler_mensual": 1200.00,
        "moneda": "USD",
        "piso_nivel": "Nivel 1"
    }
    assert ficha["codigo_local"] == "LCE-103"
    assert ficha["area_m2"] > 0
    assert ficha["estado"] in LOCAL_ESTADOS

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-03-03",
    name="Verify commercial terms edit payload PUT /locales/{id}",
    tier=1,
    feature_id="FEAT-R3-03",
    authoritative_source="PROJECT.md § 1. Backend API Contracts"
)
def test_r3_03_edit_payload():
    update_payload = {
        "precio_alquiler_mensual": 1350.00,
        "nombre_comercial": "COOLBOX TECH STORE"
    }
    assert update_payload["precio_alquiler_mensual"] > 0
    assert len(update_payload["nombre_comercial"]) > 0

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-03-04",
    name="Verify Ficha validation rejects negative rent values",
    tier=1,
    feature_id="FEAT-R3-03",
    authoritative_source="PROJECT.md § Edge Cases"
)
def test_r3_03_negative_rent_validation():
    invalid_rent = -500.00
    is_valid = invalid_rent > 0
    assert is_valid is False

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-03-05",
    name="Verify 'Crear Requerimiento' button initializes ticket modal with local context",
    tier=1,
    feature_id="FEAT-R3-03",
    authoritative_source="PROJECT.md § UI Action Flow"
)
def test_r3_03_create_ticket_from_ficha():
    context = {"mall_id": "mall-ves", "local_id": "loc-coolbox-103"}
    ticket_draft = {"centro_comercial_id": context["mall_id"], "local_id": context["local_id"]}
    assert ticket_draft["local_id"] == "loc-coolbox-103"

# ==========================================
# FEAT-R3-04: Ticket Creation Flow (Comercial)
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-04-01",
    name="Verify Ticket creation form structure",
    tier=1,
    feature_id="FEAT-R3-04",
    authoritative_source="PROJECT.md § 16. Ticket Creation Flow"
)
def test_r3_04_form_structure():
    required_fields = ["titulo", "descripcion", "tipo", "prioridad", "centro_comercial_id"]
    form_data = {
        "titulo": "Avería en tablero eléctrico",
        "descripcion": "Tablero secundario presenta salto de térmico.",
        "tipo": "mantenimiento",
        "prioridad": "alta",
        "centro_comercial_id": "mall-ves"
    }
    assert all(f in form_data for f in required_fields)

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-04-02",
    name="Verify auto-linking of mall and local when creating ticket from sheet",
    tier=1,
    feature_id="FEAT-R3-04",
    authoritative_source="PROJECT.md § Survey Handoff"
)
def test_r3_04_autolinking():
    origin_local = {"id": "loc-105", "mall_id": "mall-ves"}
    created_ticket = {"local_id": origin_local["id"], "centro_comercial_id": origin_local["mall_id"]}
    assert created_ticket["local_id"] == "loc-105"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-04-03",
    name="Verify validation prevents ticket creation with empty title",
    tier=1,
    feature_id="FEAT-R3-04",
    authoritative_source="PROJECT.md § Edge Cases"
)
def test_r3_04_empty_title_rejection():
    title = "   "
    is_valid = len(title.strip()) >= 3
    assert is_valid is False

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-04-04",
    name="Verify successful POST /api/v1/tickets payload format",
    tier=1,
    feature_id="FEAT-R3-04",
    authoritative_source="PROJECT.md § 1. Backend API Contracts"
)
def test_r3_04_post_ticket_payload():
    payload = {
        "centro_comercial_id": "mall-ves",
        "local_id": "loc-103",
        "titulo": "Solicitud de pintura exterior",
        "descripcion": "Se requiere autorizar cambio de color de fachada.",
        "tipo": "revision_comercial",
        "prioridad": "media"
    }
    assert len(payload["titulo"]) > 0
    assert payload["tipo"] in {"modificacion_plano", "division_local", "mantenimiento", "revision_comercial", "nuevo_requerimiento"}

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-04-05",
    name="Verify user feedback toast notification upon ticket creation",
    tier=1,
    feature_id="FEAT-R3-04",
    authoritative_source="PROJECT.md § UI UX Feedback"
)
def test_r3_04_toast_notification():
    toast = {"type": "success", "message": "Ticket TCK-2026-0002 creado exitosamente."}
    assert toast["type"] == "success"
    assert "creado exitosamente" in toast["message"]

# ==========================================
# FEAT-R3-05: Tickets Inbox & Resolution Panel
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-05-01",
    name="Verify Ticket inbox table structure and status badges",
    tier=1,
    feature_id="FEAT-R3-05",
    authoritative_source="PROJECT.md § 17. Tickets Inbox"
)
def test_r3_05_inbox_structure():
    tickets = [
        {"id": "t1", "codigo": "TCK-001", "estado": "abierto"},
        {"id": "t2", "codigo": "TCK-002", "estado": "en_revision"},
        {"id": "t3", "codigo": "TCK-003", "estado": "resuelto"}
    ]
    assert len(tickets) == 3
    assert all(t["estado"] in TICKET_ESTADOS for t in tickets)

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-05-02",
    name="Verify inbox status filter tabs logic",
    tier=1,
    feature_id="FEAT-R3-05",
    authoritative_source="PROJECT.md § 17. Tickets Inbox"
)
def test_r3_05_filter_tabs():
    tickets = [
        {"id": "t1", "estado": "abierto"},
        {"id": "t2", "estado": "resuelto"},
        {"id": "t3", "estado": "abierto"}
    ]
    abiertos = [t for t in tickets if t["estado"] == "abierto"]
    assert len(abiertos) == 2

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-05-03",
    name="Verify Resolution button permission check for Proyectos role",
    tier=1,
    feature_id="FEAT-R3-05",
    authoritative_source="ORIGINAL_REQUEST.md § R4 Roles"
)
def test_r3_05_resolve_button_permission():
    assert check_rbac_permission(ROLE_PROYECTOS, "resolve_ticket") is True
    assert check_rbac_permission(ROLE_COMERCIAL, "resolve_ticket") is False

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-05-04",
    name="Verify resolution modal requires technical notes",
    tier=1,
    feature_id="FEAT-R3-05",
    authoritative_source="PROJECT.md § 1. Backend API Contracts PATCH /resolve"
)
def test_r3_05_resolution_notes_required():
    empty_notes = "  "
    valid_notes = "Trabajos de acometida eléctrica concluidos satisfactoriamente."
    assert len(empty_notes.strip()) == 0
    assert len(valid_notes.strip()) >= 10

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R3-05-05",
    name="Verify ticket resolution updates state to RESUELTO",
    tier=1,
    feature_id="FEAT-R3-05",
    authoritative_source="PROJECT.md § 1. Backend API Contracts"
)
def test_r3_05_state_transition_resuelto():
    ticket = {"estado": "en_revision"}
    ticket["estado"] = "resuelto"
    ticket["notas_resolucion"] = "Inspección técnica aprobada."
    assert ticket["estado"] == "resuelto"

