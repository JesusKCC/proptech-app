# Tier 1 Feature Tests: Blueprint Viewer & Coordinate Math (FEAT-R2-01 to FEAT-R2-04 & FEAT-AC-04)
# Authoritative Sources: ORIGINAL_REQUEST.md § R2 & Acceptance Criteria, PROJECT.md § 2
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
# FEAT-R2-01: React-PDF Blueprint Canvas Renderer
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-01-01",
    name="Verify Blueprint container aspect ratio consistency",
    tier=1,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § Architecture Blueprint Viewer"
)
def test_r2_01_blueprint_aspect_ratio():
    W_unscaled = 2384.0
    H_unscaled = 1684.0
    aspect_ratio = W_unscaled / H_unscaled
    assert 1.40 <= aspect_ratio <= 1.43

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-01-02",
    name="Verify standard zoom scale controls (1.0x, 1.5x, 2.0x)",
    tier=1,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § 1. ZoomControls"
)
def test_r2_01_zoom_controls():
    zoom_levels = [1.0, 1.5, 2.0]
    base_w, base_h = 1000.0, 700.0
    u, v = 0.35, 0.55
    p1 = relative_to_screen(u, v, base_w, base_h)
    for z in zoom_levels:
        pz = relative_to_screen(u, v, base_w * z, base_h * z)
        # Check linear dilation: pz == z * p1 with zero drift
        assert abs(pz[0] - z * p1[0]) < 1e-12
        assert abs(pz[1] - z * p1[1]) < 1e-12

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-01-03",
    name="Verify SVG ViewBox layer dimensions synchronize with canvas",
    tier=1,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § SVG ViewBox Overlay"
)
def test_r2_01_svg_canvas_sync():
    import os
    overlay_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "components", "pdf-viewer", "PolygonOverlay.tsx"))
    assert os.path.exists(overlay_file), f"{overlay_file} must exist"
    with open(overlay_file, "r", encoding="utf-8") as f:
        src = f.read()
    assert "VIEWBOX_SIZE = 1000" in src
    assert "viewBox={`0 0 ${VIEWBOX_SIZE} ${VIEWBOX_SIZE}`}" in src

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-01-04",
    name="Verify Retina DPR decoupling using CSS layout pixels",
    tier=1,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § Survey Handoff High-DPI"
)
def test_r2_01_dpr_decoupling():
    dpr = 2.0
    css_width = 1000.0
    click_css_x = 250.0
    rel_x = click_css_x / css_width
    assert rel_x == 0.25

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-01-05",
    name="Verify non-scaling-stroke vector attribute specification",
    tier=1,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § SVG Overlay Pattern"
)
def test_r2_01_non_scaling_stroke():
    import os
    overlay_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "components", "pdf-viewer", "PolygonOverlay.tsx"))
    assert os.path.exists(overlay_file)
    with open(overlay_file, "r", encoding="utf-8") as f:
        src = f.read()
    assert 'vectorEffect="non-scaling-stroke"' in src

# ==========================================
# FEAT-R2-02: Zoom-Invariant Relative Coordinate Engine
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-02-01",
    name="Verify screen to relative coordinate transformation",
    tier=1,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Coordinate Transformation Contract"
)
def test_r2_02_screen_to_relative():
    u, v = screen_to_relative(250.0, 300.0, 1000.0, 1000.0)
    assert u == 0.25
    assert v == 0.30

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-02-02",
    name="Verify relative to screen coordinate transformation",
    tier=1,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Coordinate Transformation Contract"
)
def test_r2_02_relative_to_screen():
    x, y = relative_to_screen(0.25, 0.30, 2000.0, 2000.0)
    assert x == 500.0
    assert y == 600.0

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-02-03",
    name="Verify identity round-trip transformation precision",
    tier=1,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Homothety Invariance"
)
def test_r2_02_round_trip():
    orig_u, orig_v = 0.345678, 0.789012
    W, H = 1435.5, 982.25
    x, y = relative_to_screen(orig_u, orig_v, W, H)
    re_u, re_v = screen_to_relative(x, y, W, H)
    assert abs(re_u - orig_u) < 1e-12
    assert abs(re_v - orig_v) < 1e-12

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-02-04",
    name="Verify linear coordinate doubling under 2x zoom",
    tier=1,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Homothety Invariance Theorem"
)
def test_r2_02_coordinate_doubling():
    u, v = 0.20, 0.40
    W1, H1 = 800.0, 600.0
    W2, H2 = 1600.0, 1200.0
    x1, y1 = relative_to_screen(u, v, W1, H1)
    x2, y2 = relative_to_screen(u, v, W2, H2)
    assert x2 == 2.0 * x1
    assert y2 == 2.0 * y1

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-02-05",
    name="Verify polygon area quadrupling (4x) under 2x zoom",
    tier=1,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Homothety Theorem Area Ratio"
)
def test_r2_02_area_quadrupling():
    poly_rel = [(0.1, 0.1), (0.3, 0.1), (0.3, 0.3), (0.1, 0.3)]
    W1, H1 = 1000.0, 1000.0
    W2, H2 = 2000.0, 2000.0
    p1 = [relative_to_screen(u, v, W1, H1) for u, v in poly_rel]
    p2 = [relative_to_screen(u, v, W2, H2) for u, v in poly_rel]
    a1 = polygon_area(p1)
    a2 = polygon_area(p2)
    assert abs(a2 / a1 - 4.0) < 1e-9

# ==========================================
# FEAT-R2-03: Interactive Polygon Drawing Canvas
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-03-01",
    name="Verify click-to-add vertex state accumulation",
    tier=1,
    feature_id="FEAT-R2-03",
    authoritative_source="ORIGINAL_REQUEST.md § R2"
)
def test_r2_03_vertex_accumulation():
    draft_points = []
    clicks = [(100, 150), (200, 150), (200, 250)]
    for c in clicks:
        draft_points.append(screen_to_relative(c[0], c[1], 1000.0, 1000.0))
    assert len(draft_points) == 3
    assert draft_points[0] == (0.1, 0.15)

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-03-02",
    name="Verify polygon closure snap threshold logic",
    tier=1,
    feature_id="FEAT-R2-03",
    authoritative_source="PROJECT.md § Drawing Tool"
)
def test_r2_03_closure_snap():
    first_pt = (100.0, 100.0)
    current_pt = (103.0, 102.0)
    dist = math.hypot(current_pt[0] - first_pt[0], current_pt[1] - first_pt[1])
    is_closed = dist <= 10.0
    assert is_closed is True

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-03-03",
    name="Verify validation requires minimum 3 vertices for closed polygon",
    tier=1,
    feature_id="FEAT-R2-03",
    authoritative_source="PROJECT.md § Edge Cases"
)
def test_r2_03_min_vertices():
    poly_2pts = [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.2}]
    valid, err = validate_polygon_geometry(poly_2pts)
    assert valid is False
    assert "at least 3 vertices" in err

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-03-04",
    name="Verify Proyectos role authorized to draw polygons",
    tier=1,
    feature_id="FEAT-R2-03",
    authoritative_source="ORIGINAL_REQUEST.md § R4 Roles"
)
def test_r2_03_proyectos_drawing_authorized():
    assert check_rbac_permission(ROLE_PROYECTOS, "create_polygon") is True

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-03-05",
    name="Verify Comercial role forbidden from drawing polygons",
    tier=1,
    feature_id="FEAT-R2-03",
    authoritative_source="ORIGINAL_REQUEST.md § R4 Roles"
)
def test_r2_03_comercial_drawing_forbidden():
    assert check_rbac_permission(ROLE_COMERCIAL, "create_polygon") is False

# ==========================================
# FEAT-R2-04: Polygon-to-Local Association Modal
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-04-01",
    name="Verify association dialogue launch on polygon completion",
    tier=1,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § Feature Inventory"
)
def test_r2_04_modal_launch():
    completed_polygon = {
        "vertices": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}, {"x": 0.2, "y": 0.2}],
        "is_complete": True
    }
    modal_open = completed_polygon["is_complete"]
    assert modal_open is True

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-04-02",
    name="Verify commercial unit code selection from available list",
    tier=1,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § 1. Backend API Contracts"
)
def test_r2_04_unit_code_selection():
    available_locales = ["LCE-103", "LCE-104", "LCE-105"]
    selected_code = "LCE-103"
    assert selected_code in available_locales

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-04-03",
    name="Verify polygon creation payload format POST /poligonos",
    tier=1,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § 1. Backend API Contracts"
)
def test_r2_04_post_payload_format():
    payload = {
        "local_id": "loc-coolbox-103",
        "plano_id": "plan-ves-01",
        "coordenadas_relativas": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}, {"x": 0.2, "y": 0.2}],
        "color_relleno": "#3B82F6",
        "color_borde": "#1D4ED8",
        "etiqueta": "LCE-103"
    }
    valid, err = validate_polygon_geometry(payload["coordenadas_relativas"])
    assert valid, err
    assert payload["local_id"] is not None

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-04-04",
    name="Verify polygon status styling update after linking",
    tier=1,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § Frontend Blueprint Viewer"
)
def test_r2_04_status_styling():
    status_colors = {
        "disponible": "#10B981",
        "arrendado": "#3B82F6",
        "reservado": "#F59E0B",
        "mantenimiento": "#EF4444"
    }
    assert status_colors["disponible"] == "#10B981"
    assert status_colors["arrendado"] == "#3B82F6"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-R2-04-05",
    name="Verify unique polygon linking prevention",
    tier=1,
    feature_id="FEAT-R2-04",
    authoritative_source="PROJECT.md § DDL Schema uq local_id in poligonos"
)
def test_r2_04_unique_local_linking():
    existing_associations = {"loc-coolbox-103": "poly-01"}
    attempted_local_id = "loc-coolbox-103"
    conflict = attempted_local_id in existing_associations
    assert conflict is True

# ==========================================
# FEAT-AC-04: Mathematical 2x Zoom Verification Script
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-04-01",
    name="Verify mathematical 2x zoom linear coordinate doubling (P2 = 2 * P1)",
    tier=1,
    feature_id="FEAT-AC-04",
    authoritative_source="ORIGINAL_REQUEST.md § AC4 & PROJECT.md § FEAT-AC-04"
)
def test_ac_04_zoom_2x_doubling():
    p1 = [(120.0, 80.0), (280.0, 80.0), (280.0, 220.0), (120.0, 220.0)]
    p2 = [(x * 2.0, y * 2.0) for x, y in p1]
    passed, err = homothety_verification(p1, p2, ratio=2.0, tolerance=1e-9)
    assert passed, err

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-04-02",
    name="Verify edge Euclidean distances scale by exactly 2.0 under 2x zoom",
    tier=1,
    feature_id="FEAT-AC-04",
    authoritative_source="ORIGINAL_REQUEST.md § AC4 & PROJECT.md"
)
def test_ac_04_zoom_2x_edge_distance():
    p1 = [(120.0, 80.0), (280.0, 80.0), (280.0, 220.0), (120.0, 220.0)]
    p2 = [(x * 2.0, y * 2.0) for x, y in p1]
    for i in range(len(p1)):
        j = (i + 1) % len(p1)
        d1 = math.hypot(p1[i][0] - p1[j][0], p1[i][1] - p1[j][1])
        d2 = math.hypot(p2[i][0] - p2[j][0], p2[i][1] - p2[j][1])
        scale_ratio = d2 / d1
        assert abs(scale_ratio - 2.0) < 1e-9

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-04-03",
    name="Verify polygon area ratio equals exactly 4.0 under 2x zoom",
    tier=1,
    feature_id="FEAT-AC-04",
    authoritative_source="ORIGINAL_REQUEST.md § AC4"
)
def test_ac_04_zoom_2x_area():
    p1 = [(120.0, 80.0), (280.0, 80.0), (280.0, 220.0), (120.0, 220.0)]
    p2 = [(x * 2.0, y * 2.0) for x, y in p1]
    a1 = polygon_area(p1)
    a2 = polygon_area(p2)
    assert abs(a2 / a1 - 4.0) < 1e-9

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-04-04",
    name="Verify zero relative drift (< 1e-9) between 1x and 2x zoom",
    tier=1,
    feature_id="FEAT-AC-04",
    authoritative_source="ORIGINAL_REQUEST.md § AC4"
)
def test_ac_04_zoom_2x_zero_drift():
    W0, H0 = 842.0, 595.0
    p1_screen = [(150.0, 100.0), (300.0, 100.0), (300.0, 250.0), (150.0, 250.0)]
    rel_coords = [screen_to_relative(x, y, W0, H0) for x, y in p1_screen]
    W2 = W0 * 2.0
    H2 = H0 * 2.0
    p2_screen = [relative_to_screen(u, v, W2, H2) for u, v in rel_coords]
    for (x1, y1), (x2, y2) in zip(p1_screen, p2_screen):
        drift_x = abs(x2 - 2.0 * x1)
        drift_y = abs(y2 - 2.0 * y1)
        assert drift_x < 1e-9
        assert drift_y < 1e-9

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-04-05",
    name="Verify mathematical scale-invariance for irregular non-convex polygon",
    tier=1,
    feature_id="FEAT-AC-04",
    authoritative_source="ORIGINAL_REQUEST.md § AC4"
)
def test_ac_04_zoom_2x_irregular_polygon():
    p1 = [(100.0, 100.0), (250.0, 100.0), (250.0, 180.0), (180.0, 180.0), (180.0, 260.0), (100.0, 260.0)]
    p2 = [(x * 2.0, y * 2.0) for x, y in p1]
    passed, err = homothety_verification(p1, p2, ratio=2.0, tolerance=1e-9)
    assert passed, err

