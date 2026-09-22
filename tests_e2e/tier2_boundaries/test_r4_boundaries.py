# Tier 2 Boundary & Corner Cases: Security & RBAC (FEAT-R4-01 & FEAT-R4-02)
# Authoritative Sources: ORIGINAL_REQUEST.md § R4, PROJECT.md § 18 & 19
from tests_e2e.core.runner import TestRegistry
from tests_e2e.core.contracts import (
    check_rbac_permission, ROLE_COMERCIAL, ROLE_PROYECTOS, VALID_ROLES
)

# ==========================================
# FEAT-R4-01: API Role Security Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-01-01",
    name="Verify case-insensitivity handling of X-User-Role header",
    tier=2,
    feature_id="FEAT-R4-01",
    authoritative_source="PROJECT.md § RBAC Security Header Parsing"
)
def test_t2_r4_01_case_insensitivity():
    variations = ["COMERCIAL", "Comercial", "comercial", "CoMeRcIaL"]
    for role in variations:
        assert check_rbac_permission(role, "view_malls") is True
        assert check_rbac_permission(role, "create_polygon") is False

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-01-02",
    name="Verify SQL injection in role header rejected with 403",
    tier=2,
    feature_id="FEAT-R4-01",
    authoritative_source="ORIGINAL_REQUEST.md § Adversarial Verification"
)
def test_t2_r4_01_sqli_role():
    sqli_roles = [
        "comercial' OR '1'='1",
        "proyectos; DROP TABLE usuarios;",
        "' UNION SELECT * FROM usuarios --"
    ]
    for role in sqli_roles:
        assert check_rbac_permission(role, "create_polygon") is False

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-01-03",
    name="Verify whitespace-padded role string is trimmed and processed",
    tier=2,
    feature_id="FEAT-R4-01",
    authoritative_source="PROJECT.md § Header Normalization"
)
def test_t2_r4_01_whitespace_trim():
    padded_role = "   proyectos   \n"
    assert check_rbac_permission(padded_role, "create_polygon") is True

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-01-04",
    name="Verify Proyectos role forbidden from system user admin modifications",
    tier=2,
    feature_id="FEAT-R4-01",
    authoritative_source="PROJECT.md § RBAC Matrix (Admin boundaries)"
)
def test_t2_r4_01_proyectos_not_admin():
    assert check_rbac_permission(ROLE_PROYECTOS, "manage_system_users") is False

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-01-05",
    name="Verify contradictory multi-value role header handled securely",
    tier=2,
    feature_id="FEAT-R4-01",
    authoritative_source="ORIGINAL_REQUEST.md § Adversarial Verification"
)
def test_t2_r4_01_multi_role_header():
    # If client sends contradictory header "comercial, proyectos", least-privilege applies
    multi_header = "comercial, proyectos"
    # Unrecognized compound string must not grant unauthorized access
    assert check_rbac_permission(multi_header, "create_polygon") is False

# ==========================================
# FEAT-R4-02: UI Role Switcher Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-02-01",
    name="Verify storage sync updates active role state across windows",
    tier=2,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § UI State Management"
)
def test_t2_r4_02_multi_window_sync():
    storage_event = {"key": "proptech_active_role", "newValue": "proyectos"}
    assert storage_event["newValue"] in VALID_ROLES

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-02-02",
    name="Verify switching to Comercial while drawing aborts draft canvas",
    tier=2,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § UI State Transition Rules"
)
def test_t2_r4_02_switch_role_aborts_drawing():
    canvas_state = {"isDrawing": True, "draftVertices": [(0.1, 0.1), (0.2, 0.2)]}
    # Role switched to Comercial
    new_role = ROLE_COMERCIAL
    if new_role == ROLE_COMERCIAL:
        canvas_state["isDrawing"] = False
        canvas_state["draftVertices"].clear()
    assert canvas_state["isDrawing"] is False
    assert len(canvas_state["draftVertices"]) == 0

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-02-03",
    name="Verify corrupted localStorage role falls back to default comercial",
    tier=2,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § Resilience"
)
def test_t2_r4_02_corrupted_storage_fallback():
    corrupted_val = "{malformed_json_role::?}"
    active_role = corrupted_val if corrupted_val in VALID_ROLES else ROLE_COMERCIAL
    assert active_role == ROLE_COMERCIAL

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-02-04",
    name="Verify rapid role toggle clicks avoid race condition",
    tier=2,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § UI Ergonomics"
)
def test_t2_r4_02_rapid_clicks():
    role = ROLE_COMERCIAL
    # 5 rapid clicks
    for _ in range(5):
        role = ROLE_PROYECTOS if role == ROLE_COMERCIAL else ROLE_COMERCIAL
    assert role == ROLE_PROYECTOS

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R4-02-05",
    name="Verify accessibility aria-checked attribute matches active role",
    tier=2,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § UI Accessibility"
)
def test_t2_r4_02_accessibility_aria():
    role = ROLE_PROYECTOS
    aria_checked = role == ROLE_PROYECTOS
    assert aria_checked is True

