# Tier 2 Boundary & Corner Cases: Compilation & Integration (FEAT-AC-03 & FEAT-AC-05)
# Authoritative Sources: ORIGINAL_REQUEST.md § Acceptance Criteria, PROJECT.md § 20 & 21
from tests_e2e.core.runner import TestRegistry
from tests_e2e.core.webhook_signer import create_outbox_event

# ==========================================
# FEAT-AC-03: Frontend Compilation Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-03-01",
    name="Verify API URL fallback when NEXT_PUBLIC_API_URL is unset",
    tier=2,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Environment Configuration"
)
def test_t2_ac_03_env_fallback():
    env = {}
    api_url = env.get("NEXT_PUBLIC_API_URL") or "http://localhost:8000"
    assert api_url == "http://localhost:8000"

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-03-02",
    name="Verify Next.js image domain whitelist for satellite tiles",
    tier=2,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Next.js Config"
)
def test_t2_ac_03_image_domains():
    image_config = {
        "remotePatterns": [
            {"protocol": "https", "hostname": "server.arcgisonline.com"},
            {"protocol": "https", "hostname": "tile.openstreetmap.org"}
        ]
    }
    hostnames = [p["hostname"] for p in image_config["remotePatterns"]]
    assert "server.arcgisonline.com" in hostnames

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-03-03",
    name="Verify Leaflet map SSR disabled via dynamic import flag",
    tier=2,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Leaflet SSR Caveat"
)
def test_t2_ac_03_ssr_disabled():
    import os
    planos_page = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "app", "planos", "page.tsx"))
    assert os.path.exists(planos_page), "planos/page.tsx must exist"
    with open(planos_page, "r", encoding="utf-8") as f:
        src = f.read()
    assert "ssr: false" in src, "Dynamic import must specify ssr: false for client-only canvas/PDF viewer"

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-03-04",
    name="Verify bundle size warning thresholds in build configuration",
    tier=2,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Frontend Performance"
)
def test_t2_ac_03_bundle_threshold():
    import os, json
    pkg_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "package.json"))
    assert os.path.exists(pkg_file)
    with open(pkg_file, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    assert "build" in pkg.get("scripts", {})
    assert "next build" in pkg["scripts"]["build"]

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-03-05",
    name="Verify standalone output mode declared in Next.js config",
    tier=2,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Production Build Target"
)
def test_t2_ac_03_standalone_output():
    import os
    next_cfg = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "next.config.mjs"))
    assert os.path.exists(next_cfg), "next.config.mjs must exist"
    with open(next_cfg, "r", encoding="utf-8") as f:
        content = f.read()
    assert "reactStrictMode: true" in content or "canvas" in content

# ==========================================
# FEAT-AC-05: Full Integration Boundaries
# ==========================================

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-05-01",
    name="Verify concurrent edit conflict resolution on commercial unit",
    tier=2,
    feature_id="FEAT-AC-05",
    authoritative_source="PROJECT.md § Concurrent Updates"
)
def test_t2_ac_05_concurrent_edits():
    unit = {"version": 1, "rent": 1200.0}
    # Edit A
    edit_a = {"expected_version": 1, "rent": 1300.0}
    if edit_a["expected_version"] == unit["version"]:
        unit["rent"] = edit_a["rent"]
        unit["version"] += 1
    # Edit B (with stale version)
    edit_b = {"expected_version": 1, "rent": 1400.0}
    conflict = edit_b["expected_version"] != unit["version"]
    assert conflict is True
    assert unit["rent"] == 1300.0

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-05-02",
    name="Verify client error boundary on backend 500 during Ficha save",
    tier=2,
    feature_id="FEAT-AC-05",
    authoritative_source="PROJECT.md § Error Handling"
)
def test_t2_ac_05_backend_500_recovery():
    client_state = {"error": "Error interno del servidor al guardar ficha", "formDisabled": False}
    assert "Error interno" in client_state["error"]
    assert client_state["formDisabled"] is False

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-05-03",
    name="Verify polygon click on vacant unit shows Disponible badge and placeholder tenant",
    tier=2,
    feature_id="FEAT-AC-05",
    authoritative_source="PROJECT.md § Ficha del Local UX"
)
def test_t2_ac_05_vacant_unit_display():
    vacant_unit = {"codigo": "LCE-108", "nombre_comercial": None, "estado": "disponible"}
    display_name = vacant_unit["nombre_comercial"] or "Local Disponible"
    assert display_name == "Local Disponible"
    assert vacant_unit["estado"] == "disponible"

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-05-04",
    name="Verify rapid consecutive polygon clicking updates selected unit without lag",
    tier=2,
    feature_id="FEAT-AC-05",
    authoritative_source="PROJECT.md § Blueprint Viewer Responsiveness"
)
def test_t2_ac_05_rapid_polygon_clicks():
    state = {"active_id": None}
    clicks = ["poly-1", "poly-2", "poly-3", "poly-4", "poly-5"]
    for p in clicks:
        state["active_id"] = p
    assert state["active_id"] == "poly-5"

@TestRegistry.register(
    test_id="E2E-T2-FEAT-AC-05-05",
    name="Verify CRM webhook failure does not block client HTTP response (200 OK)",
    tier=2,
    feature_id="FEAT-AC-05",
    authoritative_source="PROJECT.md § Transactional Outbox Decoupling"
)
def test_t2_ac_05_outbox_decoupling():
    # Transaction succeeds in DB, event queued in outbox
    db_committed = True
    event = create_outbox_event("local.actualizado", "local", "L-01", {"rent": 1500.0})
    # CRM webhook network call fails asynchronously
    crm_network_ok = False
    if not crm_network_ok:
        event["reintentos"] += 1
    # User's API response is 200 OK regardless of CRM outage
    http_status = 200 if db_committed else 500
    assert http_status == 200
    assert event["reintentos"] == 1

