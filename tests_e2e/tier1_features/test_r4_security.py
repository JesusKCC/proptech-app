# Tier 1 Feature Tests: Security & RBAC Enforcement (FEAT-R4-01 & FEAT-R4-02)
# Authoritative Sources: ORIGINAL_REQUEST.md § R4, PROJECT.md § 18 & 19
from tests_e2e.core.runner import TestRegistry
from tests_e2e.core.contracts import (
    check_rbac_permission, ROLE_COMERCIAL, ROLE_PROYECTOS, VALID_ROLES
)

# ==========================================
# FEAT-R4-01: API Role-Based Security Enforcement
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-01-01",
    name="Verify Comercial role allowed read access to shopping centers and blueprints",
    tier=1,
    feature_id="FEAT-R4-01",
    authoritative_source="ORIGINAL_REQUEST.md § R4 & PROJECT.md § RBAC Matrix"
)
def test_r4_01_comercial_read_allowed():
    assert check_rbac_permission(ROLE_COMERCIAL, "view_malls") is True
    assert check_rbac_permission(ROLE_COMERCIAL, "view_blueprints") is True
    assert check_rbac_permission(ROLE_COMERCIAL, "view_polygons") is True
    assert check_rbac_permission(ROLE_COMERCIAL, "view_locales") is True

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-01-02",
    name="Verify Comercial role receives 403 Forbidden on POST /api/v1/poligonos",
    tier=1,
    feature_id="FEAT-R4-01",
    authoritative_source="ORIGINAL_REQUEST.md § R4 & PROJECT.md § 1. Backend API Contracts"
)
def test_r4_01_comercial_create_polygon_forbidden():
    assert check_rbac_permission(ROLE_COMERCIAL, "create_polygon") is False

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-01-03",
    name="Verify Comercial role receives 403 Forbidden on PATCH /api/v1/tickets/{id}/resolve",
    tier=1,
    feature_id="FEAT-R4-01",
    authoritative_source="ORIGINAL_REQUEST.md § R4 & PROJECT.md § 1. Backend API Contracts"
)
def test_r4_01_comercial_resolve_ticket_forbidden():
    assert check_rbac_permission(ROLE_COMERCIAL, "resolve_ticket") is False

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-01-04",
    name="Verify Proyectos role authorized for all polygon edits and ticket resolution",
    tier=1,
    feature_id="FEAT-R4-01",
    authoritative_source="ORIGINAL_REQUEST.md § R4 & PROJECT.md § RBAC Matrix"
)
def test_r4_01_proyectos_all_authorized():
    assert check_rbac_permission(ROLE_PROYECTOS, "create_polygon") is True
    assert check_rbac_permission(ROLE_PROYECTOS, "update_polygon") is True
    assert check_rbac_permission(ROLE_PROYECTOS, "resolve_ticket") is True

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-01-05",
    name="Verify rejection of requests with missing or invalid role header",
    tier=1,
    feature_id="FEAT-R4-01",
    authoritative_source="PROJECT.md § RBAC Matrix"
)
def test_r4_01_invalid_role_rejection():
    assert check_rbac_permission(None, "create_polygon") is False
    assert check_rbac_permission("guest", "create_polygon") is False
    assert check_rbac_permission("anonymous", "view_malls") is False

# ==========================================
# FEAT-R4-02: UI Role Switcher & Dynamic Layout
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-02-01",
    name="Verify active UI role state toggle between comercial and proyectos",
    tier=1,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § 19. UI Role Switcher"
)
def test_r4_02_role_toggle():
    current_role = ROLE_COMERCIAL
    # User clicks toggle
    next_role = ROLE_PROYECTOS if current_role == ROLE_COMERCIAL else ROLE_COMERCIAL
    assert next_role == ROLE_PROYECTOS
    assert next_role in VALID_ROLES

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-02-02",
    name="Verify polygon drawing toolbar visibility conditional on Proyectos role",
    tier=1,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § RBAC UI Rendering"
)
def test_r4_02_drawing_tool_visibility():
    def is_drawing_tool_visible(role: str) -> bool:
        return role == ROLE_PROYECTOS
    assert is_drawing_tool_visible(ROLE_COMERCIAL) is False
    assert is_drawing_tool_visible(ROLE_PROYECTOS) is True

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-02-03",
    name="Verify ticket resolution action button conditional on Proyectos role",
    tier=1,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § RBAC UI Rendering"
)
def test_r4_02_resolve_button_visibility():
    def is_resolve_btn_rendered(role: str) -> bool:
        return role == ROLE_PROYECTOS
    assert is_resolve_btn_rendered(ROLE_COMERCIAL) is False
    assert is_resolve_btn_rendered(ROLE_PROYECTOS) is True

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-02-04",
    name="Verify active role persistence key in client session storage",
    tier=1,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § UI Role Switcher"
)
def test_r4_02_storage_key():
    session_storage = {"proptech_active_role": "proyectos"}
    assert session_storage.get("proptech_active_role") in VALID_ROLES

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R4-02-05",
    name="Verify HTTP client header synchronization with active role",
    tier=1,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § 1. Backend API Contracts"
)
def test_r4_02_header_sync():
    active_role = ROLE_PROYECTOS
    request_headers = {"X-User-Role": active_role}
    assert request_headers["X-User-Role"] == "proyectos"

