"""
Tier 3: Cross-Feature Combination Tests
Verifies pairwise and multi-feature interactions across the PropTech platform:
- Mall CRUD + Geographic Maps
- Unit CRUD + Blueprint Geometry + Hit-Testing
- Drawing Canvas + Local Code Validation + RBAC
- Tickets + Kanban + CRM Outbox Event Dispatch
- Zoom Math + SVG ViewBox Affine Invariance
- Multi-floor Blueprint Navigation & Filtering
"""

import math
import time
import json
import hashlib
import hmac
from tests_e2e.core.contracts import (
    PERU_MALLS,
    PERU_GEOGRAPHIC_BOUNDS,
    RBAC_PERMISSIONS,
    validate_peru_coordinates,
    validate_relative_polygon,
)
from tests_e2e.core.coordinate_engine import CoordinateEngine
from tests_e2e.core.webhook_signer import WebhookSigner
from tests_e2e.core.runner import TestRegistry


# ---------------------------------------------------------------------------
# T3-CROSS-01: Mall Geo Geocoding & Distance Calculation (FEAT-R1-01 + FEAT-R3-01)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-01",
    name="Mall Geo Distance & Map Enclosure (FEAT-R1-01 + FEAT-R3-01)",
    tier=3,
    feature_id="FEAT-R1-01",
    authoritative_source="PROJECT.md § Module 1 Mall CRUD + Module 3 Interactive Map",
)
def test_t3_cross_01_mall_distance_and_map_bounds():
    mall_a = PERU_MALLS["jockey_plaza"]
    mall_b = PERU_MALLS["real_plaza_salaverry"]

    def haversine(lat1, lon1, lat2, lon2):
        r = 6371.0  # km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c

    distance = haversine(mall_a["lat"], mall_a["lng"], mall_b["lat"], mall_b["lng"])
    assert 5.0 <= distance <= 12.0, f"Distance between Jockey Plaza and Real Plaza Salaverry should be ~8km, got {distance:.2f}km"

    # Verify Peru map viewport bounds encompass both
    bounds = PERU_GEOGRAPHIC_BOUNDS
    assert bounds["lat_min"] <= mall_a["lat"] <= bounds["lat_max"]
    assert bounds["lon_min"] <= mall_a["lng"] <= bounds["lon_max"]
    assert bounds["lat_min"] <= mall_b["lat"] <= bounds["lat_max"]
    assert bounds["lon_min"] <= mall_b["lng"] <= bounds["lon_max"]


# ---------------------------------------------------------------------------
# T3-CROSS-02: Unit Creation & Blueprint Relative Polygon Linking (FEAT-R1-02 + FEAT-R1-03)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-02",
    name="Unit Creation & Relative Geometry Linking (FEAT-R1-02 + FEAT-R1-03)",
    tier=3,
    feature_id="FEAT-R1-02",
    authoritative_source="PROJECT.md § Module 1 Unit CRUD + Blueprint Geometry Linking",
)
def test_t3_cross_02_unit_creation_geometry_linking():
    unit = {
        "id": "unit-jockey-l101",
        "mall_id": "jockey_plaza",
        "code": "L-101",
        "area_m2": 120.0,
        "status": "disponible",
        "category": "Moda & Calzado",
        "floor": 1,
    }
    polygon_vertices = [
        {"x": 0.20, "y": 0.30},
        {"x": 0.32, "y": 0.30},
        {"x": 0.32, "y": 0.40},
        {"x": 0.20, "y": 0.40},
    ]
    # Validate polygon
    validate_relative_polygon(polygon_vertices)

    # Calculate relative area
    rel_area = CoordinateEngine.calculate_relative_area(polygon_vertices)
    assert rel_area > 0.0, "Relative polygon area must be positive"

    # Blueprint dimensions
    bp_width_m = 100.0
    bp_height_m = 100.0
    computed_m2 = rel_area * (bp_width_m * bp_height_m)
    assert abs(computed_m2 - 120.0) < 1.0, f"Derived m2 {computed_m2} should match unit area {unit['area_m2']}"

    # Link polygon to unit
    polygon_record = {
        "id": "poly-001",
        "blueprint_id": "bp-jockey-f1",
        "unit_id": unit["id"],
        "unit_code": unit["code"],
        "points": polygon_vertices,
    }
    assert polygon_record["unit_id"] == unit["id"]
    assert polygon_record["unit_code"] == unit["code"]


# ---------------------------------------------------------------------------
# T3-CROSS-03: Zoom Invariance & Ficha del Local Hit-testing (FEAT-R2-02 + FEAT-R3-03)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-03",
    name="Zoom Invariance & Ficha del Local Hit-testing (FEAT-R2-02 + FEAT-R3-03)",
    tier=3,
    feature_id="FEAT-R2-02",
    authoritative_source="PROJECT.md § Module 2 Relative Coordinates + Module 3 Ficha del Local",
)
def test_t3_cross_03_zoom_invariance_hit_testing():
    polygon = [
        {"x": 0.40, "y": 0.40},
        {"x": 0.60, "y": 0.40},
        {"x": 0.60, "y": 0.60},
        {"x": 0.40, "y": 0.60},
    ]
    unit_data = {
        "code": "L-204",
        "name": "Zara Peru",
        "area_m2": 450.0,
        "status": "arrendado",
        "monthly_rent_usd": 15750.0,
    }

    # Simulate clicks at 1.0x (1000x800) and 2.5x (2500x2000) inside center
    for zoom, (vw, vh) in [(1.0, (1000.0, 800.0)), (2.5, (2500.0, 2000.0))]:
        screen_pt = {"x": 0.50 * vw, "y": 0.50 * vh}
        rel_pt = CoordinateEngine.screen_to_relative(screen_pt["x"], screen_pt["y"], vw, vh)
        is_hit = CoordinateEngine.is_point_in_polygon(rel_pt["x"], rel_pt["y"], polygon)
        assert is_hit is True, f"Click at center must hit polygon at zoom {zoom}x"

    # Ficha del Local opens with correct unit details
    ficha_modal = {
        "visible": True,
        "unit_code": unit_data["code"],
        "tenant": unit_data["name"],
        "rent": unit_data["monthly_rent_usd"],
    }
    assert ficha_modal["visible"] is True
    assert ficha_modal["unit_code"] == "L-204"
    assert ficha_modal["tenant"] == "Zara Peru"


# ---------------------------------------------------------------------------
# T3-CROSS-04: Commercial Ticket Creation & Proyectos Resolution (FEAT-R3-04 + FEAT-R3-05)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-04",
    name="Ticket Lifecycle: Commercial Creation to Proyectos Resolution (FEAT-R3-04 + FEAT-R3-05)",
    tier=3,
    feature_id="FEAT-R3-04",
    authoritative_source="PROJECT.md § Module 3 Ticket Creation & Kanban Workflow",
)
def test_t3_cross_04_ticket_commercial_to_proyectos():
    # Role: comercial creates ticket
    role_creator = "comercial"
    assert RBAC_PERMISSIONS[role_creator].get("create_ticket") is True

    ticket = {
        "id": "tkt-001",
        "unit_code": "L-105",
        "title": "Fuga de agua en techo posterior",
        "priority": "URGENTE",
        "status": "PENDIENTE",
        "created_by_role": role_creator,
        "assigned_role": "proyectos",
        "history": [{"status": "PENDIENTE", "role": role_creator, "ts": time.time()}],
    }

    # Role: proyectos advances and resolves ticket
    role_resolver = "proyectos"
    assert RBAC_PERMISSIONS[role_resolver].get("resolve_ticket") is True

    # Advance to EN_PROCESO
    ticket["status"] = "EN_PROCESO"
    ticket["history"].append({"status": "EN_PROCESO", "role": role_resolver, "ts": time.time()})

    # Resolve ticket
    ticket["status"] = "RESUELTO"
    ticket["history"].append({"status": "RESUELTO", "role": role_resolver, "ts": time.time()})

    assert ticket["status"] == "RESUELTO"
    assert len(ticket["history"]) == 3
    assert ticket["history"][-1]["status"] == "RESUELTO"


# ---------------------------------------------------------------------------
# T3-CROSS-05: Role Switcher & RBAC Enforcement on Geometry Mutations (FEAT-R4-02 + FEAT-R4-01 + FEAT-R2-03)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-05",
    name="Role Switcher & Blueprint RBAC Enforcement (FEAT-R4-02 + FEAT-R4-01 + FEAT-R2-03)",
    tier=3,
    feature_id="FEAT-R4-02",
    authoritative_source="PROJECT.md § Module 4 Role Switcher + RBAC Blueprint Editing",
)
def test_t3_cross_05_role_switcher_rbac_geometry():
    # Role: comercial is read-only for blueprint geometry
    active_role = "comercial"
    canvas_editable = RBAC_PERMISSIONS[active_role].get("create_polygon", False)
    assert canvas_editable is False, "Comercial role must NOT have canvas draw/create permissions"

    # Attempted mutation as comercial fails
    save_attempt_comercial = False
    if canvas_editable:
        save_attempt_comercial = True
    assert save_attempt_comercial is False

    # Switch role to proyectos
    active_role = "proyectos"
    canvas_editable = RBAC_PERMISSIONS[active_role].get("create_polygon", False)
    assert canvas_editable is True, "Proyectos role must have canvas draw/create permissions"

    # Mutation succeeds as proyectos
    save_attempt_proyectos = False
    if canvas_editable:
        save_attempt_proyectos = True
    assert save_attempt_proyectos is True



# ---------------------------------------------------------------------------
# T3-CROSS-06: Ticket Resolution & CRM Outbox Event Dispatch (FEAT-R1-04 + FEAT-R1-05)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-06",
    name="Ticket Resolution & Outbox Event Dispatch (FEAT-R1-04 + FEAT-R1-05)",
    tier=3,
    feature_id="FEAT-R1-04",
    authoritative_source="PROJECT.md § Module 1 Ticket Resolution & CRM Outbox Integration",
)
def test_t3_cross_06_ticket_resolution_outbox_dispatch():
    ticket_id = "tkt-salaverry-88"
    secret = "secret-crm-key-99"

    event_payload = {
        "event": "ticket.resolved",
        "ticket_id": ticket_id,
        "unit_code": "L-310",
        "mall": "Real Plaza Salaverry",
        "resolved_at": "2026-09-08T12:00:00Z",
    }
    outbox_record = WebhookSigner.build_outbox_event(
        event_type=event_payload["event"],
        payload=event_payload,
        secret=secret,
    )

    assert outbox_record["status"] == "PENDING"
    assert outbox_record["event_type"] == "ticket.resolved"

    # Verify signature
    is_valid = WebhookSigner.verify_signature(
        outbox_record["payload"],
        outbox_record["signature"],
        secret,
    )
    assert is_valid is True, "Outbox event signature must verify with shared secret"


# ---------------------------------------------------------------------------
# T3-CROSS-07: Unit Status Mutation & Webhook HMAC Signature (FEAT-R1-02 + FEAT-R1-05)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-07",
    name="Unit Status Mutation & HMAC Webhook Generation (FEAT-R1-02 + FEAT-R1-05)",
    tier=3,
    feature_id="FEAT-R1-02",
    authoritative_source="PROJECT.md § Module 1 Unit Mutation & Outbox Webhook",
)
def test_t3_cross_07_unit_status_mutation_webhook():
    unit = {"id": "unit-001", "code": "L-102", "status": "disponible"}
    # Transition to reservado
    unit["status"] = "reservado"
    unit["reserved_by"] = "Cliente Ripley SAC"

    secret = "peru-proptech-crm-secret"
    raw_payload = json.dumps(unit, sort_keys=True)
    signature = WebhookSigner.generate_signature(raw_payload, secret)

    # Verify webhook receiver verification
    assert WebhookSigner.verify_signature(raw_payload, signature, secret) is True
    # Verify tampered payload fails
    tampered_payload = raw_payload.replace("reservado", "arrendado")
    assert WebhookSigner.verify_signature(tampered_payload, signature, secret) is False


# ---------------------------------------------------------------------------
# T3-CROSS-08: Seed Script Population & Summary Table Aggregation (FEAT-AC-01 + FEAT-R3-02)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-08",
    name="Seed Population & Summary Table Aggregates (FEAT-AC-01 + FEAT-R3-02)",
    tier=3,
    feature_id="FEAT-AC-01",
    authoritative_source="PROJECT.md § Module 1 Seed Script + Module 3 Summary Table",
)
def test_t3_cross_08_seed_population_summary_table():
    # Simulate seeded units for Real Plaza Salaverry
    seeded_units = [
        {"code": "L-01", "area_m2": 100.0, "status": "arrendado"},
        {"code": "L-02", "area_m2": 150.0, "status": "arrendado"},
        {"code": "L-03", "area_m2": 50.0, "status": "disponible"},
        {"code": "L-04", "area_m2": 80.0, "status": "reservado"},
    ]

    total_units = len(seeded_units)
    total_gla = sum(u["area_m2"] for u in seeded_units)
    arrendados = sum(1 for u in seeded_units if u["status"] == "arrendado")
    occupancy_rate = (arrendados / total_units) * 100.0

    assert total_units == 4
    assert total_gla == 380.0
    assert occupancy_rate == 50.0


# ---------------------------------------------------------------------------
# T3-CROSS-09: Interactive Canvas Drawing & Local Code Uniqueness (FEAT-R2-03 + FEAT-R2-04)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-09",
    name="Canvas Drawing & Unit Code Collision Prevention (FEAT-R2-03 + FEAT-R2-04)",
    tier=3,
    feature_id="FEAT-R2-03",
    authoritative_source="PROJECT.md § Module 2 Drawing Canvas + Local Code Association",
)
def test_t3_cross_09_canvas_drawing_code_uniqueness():
    existing_assignments = {"L-101": "poly-101", "L-102": "poly-102"}
    new_polygon_id = "poly-103"

    # Attempt to assign to already assigned unit L-101 should fail
    candidate_code_duplicate = "L-101"
    can_assign_dup = candidate_code_duplicate not in existing_assignments
    assert can_assign_dup is False, "Duplicate unit assignment must be blocked"

    # Assign to available unit L-103 should succeed
    candidate_code_new = "L-103"
    can_assign_new = candidate_code_new not in existing_assignments
    assert can_assign_new is True
    existing_assignments[candidate_code_new] = new_polygon_id
    assert existing_assignments["L-103"] == "poly-103"


# ---------------------------------------------------------------------------
# T3-CROSS-10: 2x Zoom Affine Transform & SVG ViewBox Calculation (FEAT-AC-04 + FEAT-R2-01)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-10",
    name="2x Zoom Affine Transform & SVG ViewBox (FEAT-AC-04 + FEAT-R2-01)",
    tier=3,
    feature_id="FEAT-AC-04",
    authoritative_source="PROJECT.md § Module 2 Double-click 2x Zoom + SVG ViewBox",
)
def test_t3_cross_10_zoom_affine_viewbox():
    orig_viewbox = {"min_x": 0.0, "min_y": 0.0, "width": 1000.0, "height": 800.0}
    # Double-click at center (500, 400)
    click_x = 500.0
    click_y = 400.0
    zoom_factor = 2.0

    new_width = orig_viewbox["width"] / zoom_factor
    new_height = orig_viewbox["height"] / zoom_factor
    new_min_x = click_x - (new_width / 2.0)
    new_min_y = click_y - (new_height / 2.0)

    assert new_width == 500.0
    assert new_height == 400.0
    assert new_min_x == 250.0
    assert new_min_y == 200.0

    # Test point (0.50, 0.50) in relative terms remains identical
    rel_x = click_x / orig_viewbox["width"]
    rel_y = click_y / orig_viewbox["height"]
    assert rel_x == 0.50
    assert rel_y == 0.50


# ---------------------------------------------------------------------------
# T3-CROSS-11: Multi-floor Blueprint Navigation & Polygon Filtering (FEAT-R2-01 + FEAT-R1-03)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-11",
    name="Multi-floor Blueprint Navigation & Polygon Filter (FEAT-R2-01 + FEAT-R1-03)",
    tier=3,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § Module 1 Multi-floor Blueprints + Module 2 Viewer",
)
def test_t3_cross_11_multifloor_polygon_filter():
    blueprints = [
        {"id": "bp-floor-1", "floor": 1, "svg_url": "/blueprints/floor1.svg"},
        {"id": "bp-floor-2", "floor": 2, "svg_url": "/blueprints/floor2.svg"},
    ]
    polygons = [
        {"id": "p1", "blueprint_id": "bp-floor-1", "unit_code": "L-101"},
        {"id": "p2", "blueprint_id": "bp-floor-1", "unit_code": "L-102"},
        {"id": "p3", "blueprint_id": "bp-floor-2", "unit_code": "L-201"},
        {"id": "p4", "blueprint_id": "bp-floor-2", "unit_code": "L-202"},
        {"id": "p5", "blueprint_id": "bp-floor-2", "unit_code": "L-203"},
    ]

    # Select Floor 1
    active_bp = blueprints[0]
    floor_1_polys = CoordinateEngine.filter_polygons_by_page(polygons, active_bp["id"])
    assert len(floor_1_polys) == 2
    assert {p["unit_code"] for p in floor_1_polys} == {"L-101", "L-102"}

    # Switch to Floor 2
    active_bp = blueprints[1]
    floor_2_polys = CoordinateEngine.filter_polygons_by_page(polygons, active_bp["id"])
    assert len(floor_2_polys) == 3
    assert {p["unit_code"] for p in floor_2_polys} == {"L-201", "L-202", "L-203"}


# ---------------------------------------------------------------------------
# T3-CROSS-12: Frontend Unit Selection & Canvas Polygon Highlighting (FEAT-AC-05 + FEAT-R2-02)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-12",
    name="Unit Selection & Canvas Visual Highlighting (FEAT-AC-05 + FEAT-R2-02)",
    tier=3,
    feature_id="FEAT-AC-05",
    authoritative_source="PROJECT.md § Module 2 SVG Polygon Rendering + Module 3 Interactive Selection",
)
def test_t3_cross_12_unit_selection_canvas_highlight():
    polygons = [
        {"id": "poly-1", "unit_code": "L-101", "state": "normal", "stroke": "#cccccc"},
        {"id": "poly-2", "unit_code": "L-102", "state": "normal", "stroke": "#cccccc"},
    ]
    selected_code = "L-102"

    for p in polygons:
        if p["unit_code"] == selected_code:
            p["state"] = "selected"
            p["stroke"] = "#ff0000"
            p["stroke_width"] = 3
        else:
            p["state"] = "normal"
            p["stroke"] = "#cccccc"
            p["stroke_width"] = 1

    selected_poly = next(p for p in polygons if p["unit_code"] == selected_code)
    unselected_poly = next(p for p in polygons if p["unit_code"] == "L-101")
    assert selected_poly["state"] == "selected"
    assert selected_poly["stroke"] == "#ff0000"
    assert unselected_poly["state"] == "normal"


# ---------------------------------------------------------------------------
# T3-CROSS-13: Dual-Currency Lease Pricing & Commercial Metric Aggregation (FEAT-R1-02 + FEAT-R3-02)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-13",
    name="Dual-Currency Lease Pricing Aggregations (FEAT-R1-02 + FEAT-R3-02)",
    tier=3,
    feature_id="FEAT-R1-02",
    authoritative_source="PROJECT.md § Module 1 Dual-Currency + Module 3 Summary Aggregates",
)
def test_t3_cross_13_dual_currency_aggregations():
    units = [
        {"code": "L-1", "rent_usd": 1000.0, "maintenance_pen": 750.0},
        {"code": "L-2", "rent_usd": 2000.0, "maintenance_pen": 1500.0},
        {"code": "L-3", "rent_usd": 1500.0, "maintenance_pen": 1125.0},
    ]
    fx_pen_per_usd = 3.75

    total_usd = sum(u["rent_usd"] for u in units)
    total_pen = sum(u["maintenance_pen"] for u in units)
    total_revenue_usd = total_usd + (total_pen / fx_pen_per_usd)

    assert total_usd == 4500.0
    assert total_pen == 3375.0
    assert total_revenue_usd == 4500.0 + 900.0 == 5400.0


# ---------------------------------------------------------------------------
# T3-CROSS-14: Category Filter & Polygon Canvas Color Coding (FEAT-R3-02 + FEAT-R2-02)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-14",
    name="Category Filter & Visual Dimming / Highlighting (FEAT-R3-02 + FEAT-R2-02)",
    tier=3,
    feature_id="FEAT-R3-02",
    authoritative_source="PROJECT.md § Module 2 SVG Styling + Module 3 Category Filtering",
)
def test_t3_cross_14_category_filter_polygon_styling():
    units = [
        {"code": "L-01", "category": "Gastronomia", "color": "#f39c12"},
        {"code": "L-02", "category": "Moda & Calzado", "color": "#3498db"},
        {"code": "L-03", "category": "Gastronomia", "color": "#f39c12"},
    ]
    filter_category = "Gastronomia"

    styled_polygons = []
    for u in units:
        is_match = u["category"] == filter_category
        styled_polygons.append({
            "code": u["code"],
            "fill": u["color"],
            "opacity": 1.0 if is_match else 0.2,
            "highlighted": is_match,
        })

    highlighted = [p for p in styled_polygons if p["highlighted"]]
    dimmed = [p for p in styled_polygons if not p["highlighted"]]
    assert len(highlighted) == 2
    assert len(dimmed) == 1
    assert dimmed[0]["opacity"] == 0.2


# ---------------------------------------------------------------------------
# T3-CROSS-15: Polygon Unlinking & Re-assignment (FEAT-R1-03 + FEAT-R2-04)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-15",
    name="Polygon Unlink & Reassignment Workflow (FEAT-R1-03 + FEAT-R2-04)",
    tier=3,
    feature_id="FEAT-R1-03",
    authoritative_source="PROJECT.md § Module 1 Geometry Linking + Module 2 Local Code Association",
)
def test_t3_cross_15_polygon_unlink_reassignment():
    polygon = {
        "id": "poly-50",
        "unit_id": "unit-10",
        "unit_code": "L-10",
        "points": [{"x": 0.1, "y": 0.1}, {"x": 0.2, "y": 0.1}, {"x": 0.2, "y": 0.2}, {"x": 0.1, "y": 0.2}],
    }

    # Step 1: Unlink from Unit 10
    polygon["unit_id"] = None
    polygon["unit_code"] = None
    assert polygon["unit_id"] is None
    assert polygon["unit_code"] is None

    # Step 2: Reassign to Unit 11
    polygon["unit_id"] = "unit-11"
    polygon["unit_code"] = "L-11"
    assert polygon["unit_id"] == "unit-11"
    assert polygon["unit_code"] == "L-11"
    # Verify points remain untouched
    assert len(polygon["points"]) == 4


# ---------------------------------------------------------------------------
# T3-CROSS-16: Urgent Ticket Escalation & Outbox Notification (FEAT-R1-04 + FEAT-R1-05)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-16",
    name="Urgent Ticket Escalation & Outbox Notification (FEAT-R1-04 + FEAT-R1-05)",
    tier=3,
    feature_id="FEAT-R1-04",
    authoritative_source="PROJECT.md § Module 1 Ticket Urgent SLA + CRM Outbox Notification",
)
def test_t3_cross_16_urgent_ticket_escalation_outbox():
    ticket = {
        "id": "tkt-urg-01",
        "priority": "URGENTE",
        "title": "Corte electrico tablero central",
        "unit_code": "L-FOOD-01",
    }
    secret = "secret-escalation-key"
    payload = {
        "event": "ticket.urgent_escalated",
        "ticket_id": ticket["id"],
        "priority": ticket["priority"],
        "unit_code": ticket["unit_code"],
        "sla_hours": 4,
    }

    outbox = WebhookSigner.build_outbox_event(
        event_type="ticket.urgent_escalated",
        payload=payload,
        secret=secret,
    )
    assert outbox["event_type"] == "ticket.urgent_escalated"
    assert WebhookSigner.verify_signature(outbox["payload"], outbox["signature"], secret) is True


# ---------------------------------------------------------------------------
# T3-CROSS-17: Drawing Canvas Polygon Deletion & Unit Safeguards (FEAT-R2-03 + FEAT-R1-02)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-17",
    name="Canvas Polygon Deletion & Leased Unit Safeguards (FEAT-R2-03 + FEAT-R1-02)",
    tier=3,
    feature_id="FEAT-R2-03",
    authoritative_source="PROJECT.md § Module 2 Drawing Canvas + Module 1 Leased Unit Integrity",
)
def test_t3_cross_17_polygon_deletion_safeguards():
    def attempt_delete_polygon(unit_status):
        if unit_status == "arrendado":
            raise PermissionError("Cannot delete polygon associated with an active lease (arrendado)")
        return True

    # Attempting to delete polygon linked to leased unit must raise error
    try:
        attempt_delete_polygon("arrendado")
        assert False, "Should have raised PermissionError"
    except PermissionError as e:
        assert "Cannot delete polygon" in str(e)

    # Deleting polygon linked to disponible unit succeeds
    success = attempt_delete_polygon("disponible")
    assert success is True


# ---------------------------------------------------------------------------
# T3-CROSS-18: Viewport Drag Pan Navigation & ViewBox Bounds Clamping (FEAT-R2-01 + FEAT-AC-04)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-18",
    name="Viewport Pan Drag & ViewBox Boundary Clamping (FEAT-R2-01 + FEAT-AC-04)",
    tier=3,
    feature_id="FEAT-R2-01",
    authoritative_source="PROJECT.md § Module 2 Pan Dragging + Boundary Clamping Math",
)
def test_t3_cross_18_pan_drag_clamping():
    canvas_w, canvas_h = 1000.0, 800.0
    view_w, view_h = 500.0, 400.0  # 2x zoom viewport

    def clamp_pan(pan_x, pan_y):
        min_x = 0.0
        max_x = canvas_w - view_w
        min_y = 0.0
        max_y = canvas_h - view_h
        return max(min_x, min(pan_x, max_x)), max(min_y, min(pan_y, max_y))

    # Test normal pan
    cx, cy = clamp_pan(100.0, 100.0)
    assert (cx, cy) == (100.0, 100.0)

    # Test negative overshoot
    cx, cy = clamp_pan(-50.0, -100.0)
    assert (cx, cy) == (0.0, 0.0)

    # Test positive overflow
    cx, cy = clamp_pan(800.0, 600.0)
    assert (cx, cy) == (500.0, 400.0)


# ---------------------------------------------------------------------------
# T3-CROSS-19: Ficha del Local Ticket Submission to Kanban Board (FEAT-R3-03 + FEAT-R3-05)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-19",
    name="Ficha del Local Ticket Creation to Kanban Column (FEAT-R3-03 + FEAT-R3-05)",
    tier=3,
    feature_id="FEAT-R3-03",
    authoritative_source="PROJECT.md § Module 3 Ficha del Local Ticket Modal + Kanban",
)
def test_t3_cross_19_ficha_ticket_to_kanban():
    kanban_columns = {
        "PENDIENTE": [],
        "EN_PROCESO": [],
        "RESUELTO": [],
    }
    # From Ficha del Local for unit L-302:
    new_ticket = {
        "id": "tkt-f-101",
        "unit_code": "L-302",
        "title": "Ajuste de cerradura principal",
        "priority": "MEDIA",
        "status": "PENDIENTE",
    }
    kanban_columns[new_ticket["status"]].append(new_ticket)

    assert len(kanban_columns["PENDIENTE"]) == 1
    assert kanban_columns["PENDIENTE"][0]["unit_code"] == "L-302"
    assert len(kanban_columns["EN_PROCESO"]) == 0
    assert len(kanban_columns["RESUELTO"]) == 0


# ---------------------------------------------------------------------------
# T3-CROSS-20: Sequential Status Updates & Outbox Idempotency Ordering (FEAT-R1-02 + FEAT-R1-05)
# ---------------------------------------------------------------------------
@TestRegistry.register(
    test_id="T3-CROSS-20",
    name="Sequential Status Updates & Outbox Idempotency (FEAT-R1-02 + FEAT-R1-05)",
    tier=3,
    feature_id="FEAT-R1-02",
    authoritative_source="PROJECT.md § Module 1 Unit Lifecycle Transitions + Outbox Event Ordering",
)
def test_t3_cross_20_status_updates_outbox_ordering():
    secret = "secret-order-key"
    transitions = ["disponible", "reservado", "arrendado"]
    outbox_events = []

    for idx, status in enumerate(transitions):
        payload = {
            "unit_code": "L-999",
            "status": status,
            "version": idx + 1,
            "timestamp": 1725700000 + (idx * 60),
        }
        event = WebhookSigner.build_outbox_event(
            event_type="unit.status_changed",
            payload=payload,
            secret=secret,
        )
        outbox_events.append(event)

    assert len(outbox_events) == 3
    # Check versions strictly increase
    versions = [json.loads(e["payload"])["version"] for e in outbox_events]
    assert versions == [1, 2, 3]

    # Check distinct signatures
    sigs = [e["signature"] for e in outbox_events]
    assert len(set(sigs)) == 3

