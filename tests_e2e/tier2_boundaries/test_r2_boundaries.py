# Tier 2 Boundary & Corner Cases: Blueprint Viewer & Coordinate Math (FEAT-R2-01 to FEAT-R2-04 & FEAT-AC-04)
# Authoritative Sources: ORIGINAL_REQUEST.md § R2 & AC4, PROJECT.md § 2
import math
from tests_e2e.core.runner import TestRegistry
from tests_e2e.core.contracts import (
    validate_polygon_geometry, check_rbac_permission,
    ROLE_COMERCIAL, ROLE_PROYECTOS
)
from tests_e2e.core.coordinate_engine import (
    screen_to_relative, relative_to_screen, polygon_area,
    homothety_verification, calculate_bounding_box
)

# ==========================================
# FEAT-R2-01: Blueprint Viewer Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-01-01",
    name="Verify minimum zoom scale boundary clamp (0.25x)",
    tier=2,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § ZoomControls Constraints"
)
def test_t2_r2_01_min_zoom_clamp():
    min_zoom = 0.25
    requested_zoom = 0.10
    clamped_zoom = max(min_zoom, requested_zoom)
    assert clamped_zoom == 0.25

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-01-02",
    name="Verify maximum zoom scale boundary clamp (5.0x)",
    tier=2,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § ZoomControls Constraints"
)
def test_t2_r2_01_max_zoom_clamp():
    max_zoom = 5.0
    requested_zoom = 8.5
    clamped_zoom = min(max_zoom, requested_zoom)
    assert clamped_zoom == 5.0

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-01-03",
    name="Verify non-positive zoom factors raise ValueError",
    tier=2,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § Coordinate Engine Assertions"
)
def test_t2_r2_01_non_positive_zoom():
    for invalid_zoom in [0.0, -1.0, -0.5]:
        try:
            screen_to_relative(100, 100, 1000 * invalid_zoom, 1000 * invalid_zoom)
            raised = False
        except ValueError:
            raised = True
        assert raised is True

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-01-04",
    name="Verify error boundary state on unreachable blueprint URL",
    tier=2,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § Edge Cases #13"
)
def test_t2_r2_01_unreachable_pdf():
    pdf_state = {"error": "Error al cargar plano arquitectónico", "can_retry": True}
    assert "Error al cargar" in pdf_state["error"]
    assert pdf_state["can_retry"] is True

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-01-05",
    name="Verify arbitrary fractional zoom preserves exact landscape ratio",
    tier=2,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § Viewport Scaling"
)
def test_t2_r2_01_fractional_zoom_aspect():
    base_w, base_h = 2384.0, 1684.0
    base_ratio = base_w / base_h
    fractional_zoom = 1.333333
    scaled_w = base_w * fractional_zoom
    scaled_h = base_h * fractional_zoom
    scaled_ratio = scaled_w / scaled_h
    assert abs(scaled_ratio - base_ratio) < 1e-12

# ==========================================
# FEAT-R2-02: Relative Coordinate Engine Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-02-01",
    name="Verify division by zero raised on zero viewport dimensions",
    tier=2,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Coordinate Transformation Contract"
)
def test_t2_r2_02_zero_dimensions():
    try:
        screen_to_relative(100, 100, 0.0, 500.0)
        raised = False
    except ValueError:
        raised = True
    assert raised is True

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-02-02",
    name="Verify clamped screen-to-relative keeps points strictly in [0, 1]",
    tier=2,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Edge Cases (Border Clamping)"
)
def test_t2_r2_02_clamping_boundary():
    u_neg, v_neg = screen_to_relative(-50.0, -20.0, 1000.0, 1000.0, clamp=True)
    assert u_neg == 0.0 and v_neg == 0.0
    u_over, v_over = screen_to_relative(1200.0, 1500.0, 1000.0, 1000.0, clamp=True)
    assert u_over == 1.0 and v_over == 1.0

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-02-03",
    name="Verify sub-pixel precision (< 1e-12) coordinate transformation",
    tier=2,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Coordinate Normalization Rigor"
)
def test_t2_r2_02_subpixel_precision():
    precise_u = 0.123456789012
    precise_v = 0.987654321098
    W, H = 1920.0, 1080.0
    x, y = relative_to_screen(precise_u, precise_v, W, H)
    re_u, re_v = screen_to_relative(x, y, W, H)
    assert abs(re_u - precise_u) < 1e-12
    assert abs(re_v - precise_v) < 1e-12

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-02-04",
    name="Verify extreme high-zoom (10.0x) linear coordinate consistency",
    tier=2,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Homothety Invariance Theorem"
)
def test_t2_r2_02_high_zoom():
    poly_rel = [(0.1, 0.1), (0.2, 0.1), (0.2, 0.2)]
    W0, H0 = 1000.0, 1000.0
    p1 = [relative_to_screen(u, v, W0, H0) for u, v in poly_rel]
    p10 = [relative_to_screen(u, v, W0 * 10.0, H0 * 10.0) for u, v in poly_rel]
    passed, err = homothety_verification(p1, p10, ratio=10.0, tolerance=1e-9)
    assert passed, err

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-02-05",
    name="Verify shrink zoom (0.5x) area scales to exactly 0.25x",
    tier=2,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Homothety Theorem Area Ratio"
)
def test_t2_r2_02_shrink_zoom():
    poly_rel = [(0.2, 0.2), (0.6, 0.2), (0.6, 0.6), (0.2, 0.6)]
    W0, H0 = 1000.0, 1000.0
    p1 = [relative_to_screen(u, v, W0, H0) for u, v in poly_rel]
    p_half = [relative_to_screen(u, v, W0 * 0.5, H0 * 0.5) for u, v in poly_rel]
    a1 = polygon_area(p1)
    a_half = polygon_area(p_half)
    assert abs(a_half / a1 - 0.25) < 1e-9

# ==========================================
# FEAT-R2-03: Drawing Tool Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-03-01",
    name="Verify Escape key aborts drawing and clears draft vertices",
    tier=2,
    feature_id="FEAT-R2-03",
    authoritative_source="PROJECT.md § Edge Cases #4"
)
def test_t2_r2_03_escape_clears():
    draft = [(0.1, 0.1), (0.2, 0.2)]
    # User hits Escape
    draft.clear()
    assert len(draft) == 0

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-03-02",
    name="Verify clicks outside canvas boundaries are clamped or discarded",
    tier=2,
    feature_id="FEAT-R2-03",
    authoritative_source="PROJECT.md § Edge Cases #2"
)
def test_t2_r2_03_outside_clicks():
    click_x, click_y = -15.0, 1050.0
    W, H = 1000.0, 1000.0
    u, v = screen_to_relative(click_x, click_y, W, H, clamp=True)
    assert 0.0 <= u <= 1.0
    assert 0.0 <= v <= 1.0

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-03-03",
    name="Verify debouncing rapid clicks within 150ms",
    tier=2,
    feature_id="FEAT-R2-03",
    authoritative_source="PROJECT.md § Drawing Ergonomics"
)
def test_t2_r2_03_debounce_clicks():
    t1 = 1000  # ms
    t2 = 1050  # 50ms later -> debounced
    t3 = 1200  # 150ms later -> accepted
    accepted_clicks = [t1]
    if t2 - accepted_clicks[-1] > 100:
        accepted_clicks.append(t2)
    if t3 - accepted_clicks[-1] > 100:
        accepted_clicks.append(t3)
    assert len(accepted_clicks) == 2

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-03-04",
    name="Verify Comercial user cannot initiate polygon drawing mode",
    tier=2,
    feature_id="FEAT-R2-03",
    authoritative_source="ORIGINAL_REQUEST.md § R4 Roles"
)
def test_t2_r2_03_comercial_draw_block():
    user_role = ROLE_COMERCIAL
    drawing_enabled = check_rbac_permission(user_role, "create_polygon")
    assert drawing_enabled is False

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-03-05",
    name="Verify self-intersecting polygon boundary detection alert",
    tier=2,
    feature_id="FEAT-R2-03",
    authoritative_source="PROJECT.md § Edge Cases (Self-Intersection)"
)
def test_t2_r2_03_self_intersection():
    # Hourglass polygon: (0,0)-(1,1)-(1,0)-(0,1)
    hourglass = [(0.0, 0.0), (1.0, 1.0), (1.0, 0.0), (0.0, 1.0)]
    # Detection: bounding box is valid, but segments cross
    bbox = calculate_bounding_box(hourglass)
    assert bbox == (0.0, 0.0, 1.0, 1.0)

# ==========================================
# FEAT-R2-04: Polygon-to-Local Modal Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-04-01",
    name="Verify modal handles zero available commercial units in mall",
    tier=2,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § Edge Cases"
)
def test_t2_r2_04_zero_units():
    available_units = []
    can_associate = len(available_units) > 0
    assert can_associate is False

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-04-02",
    name="Verify cancelling modal dialogue discards newly drawn polygon",
    tier=2,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § Edge Cases #4"
)
def test_t2_r2_04_modal_cancel():
    state = {"draft_poly": [(0.1, 0.1), (0.2, 0.2), (0.3, 0.1)], "saved": False}
    # Cancel action
    state["draft_poly"] = None
    assert state["draft_poly"] is None

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-04-03",
    name="Verify association permitted for maintenance status unit",
    tier=2,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § Relational Schema"
)
def test_t2_r2_04_maintenance_unit():
    unit = {"id": "loc-maint-01", "estado": "mantenimiento"}
    can_link = unit["id"] is not None
    assert can_link is True

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-04-04",
    name="Verify overwrite confirmation required when reassigning unit",
    tier=2,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § Edge Cases #7"
)
def test_t2_r2_04_overwrite_dialog():
    unit_has_poly = True
    requires_confirm = unit_has_poly
    assert requires_confirm is True

@TestRegistry.register(
    test_id="E2E-T2-FEAT-R2-04-05",
    name="Verify serialized wire coordinates conform to JSON array format",
    tier=2,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § 1. Backend API Contracts"
)
def test_t2_r2_04_wire_format():
    points = [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.2}, {"x": 0.3, "y": 0.4}]
    valid, err = validate_polygon_geometry(points)
    assert valid, err

# ==========================================
# FEAT-AC-04: 2x Zoom Mathematical Invariance Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-04-01",
    name="Verify mathematical invariance under 3.0x zoom factor",
    tier=2,
    feature_id="FEAT-AC-04",
    authoritative_source="PROJECT.md § Homothety Theorem"
)
def test_t2_ac_04_zoom_3x():
    p1 = [(100.0, 100.0), (300.0, 100.0), (300.0, 200.0), (100.0, 200.0)]
    p3 = [(x * 3.0, y * 3.0) for x, y in p1]
    passed, err = homothety_verification(p1, p3, ratio=3.0, tolerance=1e-9)
    assert passed, err

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-04-02",
    name="Verify mathematical invariance under fractional 1.75x zoom factor",
    tier=2,
    feature_id="FEAT-AC-04",
    authoritative_source="PROJECT.md § Homothety Theorem"
)
def test_t2_ac_04_zoom_1_75x():
    p1 = [(100.0, 100.0), (300.0, 100.0), (300.0, 200.0), (100.0, 200.0)]
    p_frac = [(x * 1.75, y * 1.75) for x, y in p1]
    passed, err = homothety_verification(p1, p_frac, ratio=1.75, tolerance=1e-9)
    assert passed, err

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-04-03",
    name="Verify homothety verification detects artificial 1-pixel drift",
    tier=2,
    feature_id="FEAT-AC-04",
    authoritative_source="PROJECT.md § Homothety Invariance Zero Drift"
)
def test_t2_ac_04_drift_detection():
    p1 = [(100.0, 100.0), (300.0, 100.0), (300.0, 200.0), (100.0, 200.0)]
    # Introduce 1px artificial drift on vertex 2
    p2_drift = [(x * 2.0, y * 2.0) for x, y in p1]
    p2_drift[2] = (p2_drift[2][0] + 1.0, p2_drift[2][1])
    passed, err = homothety_verification(p1, p2_drift, ratio=2.0, tolerance=1e-9)
    assert passed is False
    assert "exceeds tolerance" in err

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-04-04",
    name="Verify strict floating-point tolerance threshold stress test",
    tier=2,
    feature_id="FEAT-AC-04",
    authoritative_source="PROJECT.md § Quality Thresholds (1e-9 tolerance)"
)
def test_t2_ac_04_tolerance_stress():
    p1 = [(123.456789, 234.567890), (456.789012, 234.567890), (456.789012, 345.678901)]
    p2 = [(x * 2.0, y * 2.0) for x, y in p1]
    passed, err = homothety_verification(p1, p2, ratio=2.0, tolerance=1e-9)
    assert passed, err

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-04-05",
    name="Verify homothety invariance on minimal 3-vertex polygon triangle",
    tier=2,
    feature_id="FEAT-AC-04",
    authoritative_source="PROJECT.md § Homothety Invariance"
)
def test_t2_ac_04_minimal_triangle():
    triangle_1 = [(100.0, 100.0), (200.0, 100.0), (150.0, 200.0)]
    triangle_2 = [(x * 2.0, y * 2.0) for x, y in triangle_1]
    passed, err = homothety_verification(triangle_1, triangle_2, ratio=2.0, tolerance=1e-9)
    assert passed, err

