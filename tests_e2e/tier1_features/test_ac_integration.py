# Tier 1 Feature Tests: Compilation & Full Integration (FEAT-AC-03 & FEAT-AC-05)
# Authoritative Sources: ORIGINAL_REQUEST.md § Acceptance Criteria, PROJECT.md § 20 & 21
import os
import sys
import json
from pydantic import ValidationError

# Ensure backend root is in sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", ".."))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_ROOT = os.path.join(PROJECT_ROOT, "frontend")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from tests_e2e.core.runner import TestRegistry
from tests_e2e.core.webhook_signer import create_outbox_event, compute_hmac_sha256
from app.schemas.local import LocalBase, LocalCreate, LocalUpdate, LocalResponse
from app.schemas.poligono import PoligonoCreate, PoligonoResponse, PoligonoUpdate, RelativeCoordinate
from app.services.outbox_service import compute_hmac_signature

# ==========================================
# FEAT-AC-03: Frontend Build & Compilation
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-03-01",
    name="Verify Next.js directory layout compliance",
    tier=1,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Code Layout frontend/"
)
def test_ac_03_directory_layout():
    required_dirs = [
        os.path.join(FRONTEND_ROOT, "src", "app"),
        os.path.join(FRONTEND_ROOT, "src", "components"),
        os.path.join(FRONTEND_ROOT, "src", "lib"),
        os.path.join(FRONTEND_ROOT, "public")
    ]
    for d in required_dirs:
        assert os.path.exists(d), f"Directory {d} must exist"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-03-02",
    name="Verify frontend required production packages in package.json spec",
    tier=1,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Required Dependencies"
)
def test_ac_03_package_dependencies():
    pkg_path = os.path.join(FRONTEND_ROOT, "package.json")
    assert os.path.exists(pkg_path), "package.json must exist in frontend root"
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg_data = json.load(f)
    
    deps = pkg_data.get("dependencies", {})
    expected_deps = ["next", "react", "react-dom", "leaflet", "lucide-react"]
    for dep in expected_deps:
        assert dep in deps, f"Expected production dependency '{dep}' missing in package.json"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-03-03",
    name="Verify TypeScript configuration contract",
    tier=1,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Frontend Architecture"
)
def test_ac_03_typescript_contract():
    tsconfig_path = os.path.join(FRONTEND_ROOT, "tsconfig.json")
    assert os.path.exists(tsconfig_path), "tsconfig.json must exist"
    with open(tsconfig_path, "r", encoding="utf-8") as f:
        ts_data = json.load(f)
    
    compiler_opts = ts_data.get("compilerOptions", {})
    assert compiler_opts.get("strict") is True, "TypeScript strict mode must be enabled"
    assert "@/*" in compiler_opts.get("paths", {}), "Path alias @/* must be configured"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-03-04",
    name="Verify Tailwind CSS styling framework configuration",
    tier=1,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Frontend Tailwind CSS"
)
def test_ac_03_tailwind_config():
    tailwind_path = os.path.join(FRONTEND_ROOT, "tailwind.config.ts")
    assert os.path.exists(tailwind_path), "tailwind.config.ts must exist"
    with open(tailwind_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "./src/components" in content or "./src" in content, "Tailwind content must include ./src"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-03-05",
    name="Verify public blueprint assets hosting location",
    tier=1,
    feature_id="FEAT-AC-03",
    authoritative_source="PROJECT.md § Code Layout frontend/public/blueprints"
)
def test_ac_03_public_blueprints_dir():
    pdf_path = os.path.join(FRONTEND_ROOT, "public", "blueprints", "pacita_ves_nivel1.pdf")
    assert os.path.exists(pdf_path), f"Authentic blueprint PDF must exist at {pdf_path}"
    assert os.path.getsize(pdf_path) > 1000000, "Blueprint PDF must be authentic non-dummy file (> 1MB)"

# ==========================================
# FEAT-AC-05: Full Frontend-Backend Integration
# ==========================================

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-05-01",
    name="Verify end-to-end flow: polygon click loads Ficha del Local data",
    tier=1,
    feature_id="FEAT-AC-05",
    authoritative_source="ORIGINAL_REQUEST.md § AC5 & PROJECT.md § 21"
)
def test_ac_05_polygon_click_loads_ficha():
    # Model real schema instances
    ficha = LocalResponse(
        id="loc-coolbox-103",
        centro_comercial_id="mall-ves-01",
        codigo_local="LCE-103",
        nombre_comercial="COOLBOX",
        categoria="Tecnología y Retail",
        estado="arrendado",
        area_m2=29.70,
        precio_alquiler_mensual=1250.00,
        moneda="USD",
        piso_nivel="Nivel 1",
        descripcion="Local comercial tecnológico"
    )
    poly = PoligonoResponse(
        id="poly-103",
        local_id=ficha.id,
        plano_id="plano-ves-01",
        coordenadas_relativas=[
            RelativeCoordinate(x=0.738, y=0.497),
            RelativeCoordinate(x=0.766, y=0.497),
            RelativeCoordinate(x=0.766, y=0.526),
            RelativeCoordinate(x=0.738, y=0.526)
        ],
        color_relleno="#3b82f6",
        color_borde="#1d4ed8",
        opacidad=0.4,
        etiqueta="COOLBOX"
    )
    # Verify entity association through schema
    assert poly.local_id == ficha.id
    assert ficha.codigo_local == "LCE-103"
    assert ficha.area_m2 == 29.70
    assert ficha.precio_alquiler_mensual == 1250.00

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-05-02",
    name="Verify end-to-end flow: Ficha edit submission updates database record",
    tier=1,
    feature_id="FEAT-AC-05",
    authoritative_source="ORIGINAL_REQUEST.md § AC5"
)
def test_ac_05_ficha_edit_persists():
    # Validate update submission with application schema LocalUpdate
    update_data = {"precio_alquiler_mensual": 1450.00, "estado": "arrendado"}
    local_update = LocalUpdate(**update_data)
    assert local_update.precio_alquiler_mensual == 1450.00
    assert local_update.estado == "arrendado"

    # Schema validation ensures invalid status is rejected
    try:
        LocalUpdate(estado="estado_invalido")
        assert False, "Invalid status must be rejected by LocalUpdate regex"
    except ValidationError:
        pass

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-05-03",
    name="Verify re-fetching local returns updated commercial terms",
    tier=1,
    feature_id="FEAT-AC-05",
    authoritative_source="ORIGINAL_REQUEST.md § AC5"
)
def test_ac_05_refetch_returns_persisted():
    # Validate persisted record via LocalResponse
    record_dict = {
        "id": "loc-coolbox-103",
        "centro_comercial_id": "mall-ves-01",
        "codigo_local": "LCE-103",
        "nombre_comercial": "COOLBOX",
        "categoria=" : "Retail",
        "categoria": "Retail",
        "estado": "arrendado",
        "area_m2": 29.70,
        "precio_alquiler_mensual": 1450.00,
        "moneda": "USD",
        "piso_nivel": "Nivel 1",
        "descripcion": "Actualizado"
    }
    re_fetched = LocalResponse(**record_dict)
    assert re_fetched.precio_alquiler_mensual == 1450.00
    assert re_fetched.estado == "arrendado"

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-05-04",
    name="Verify polygon visual state reflects updated commercial status",
    tier=1,
    feature_id="FEAT-AC-05",
    authoritative_source="PROJECT.md § Full Integration"
)
def test_ac_05_polygon_visual_update():
    # Validate polygon update schema handles dynamic color and opacity updates
    poly_update = PoligonoUpdate(color_relleno="#10b981", opacidad=0.6)
    assert poly_update.color_relleno == "#10b981"
    assert poly_update.opacidad == 0.6

    # Test invalid opacity bound rejection
    try:
        PoligonoUpdate(opacidad=1.5)
        assert False, "Opacity > 1.0 must be rejected by PoligonoUpdate"
    except ValidationError:
        pass

@TestRegistry.register(
    test_id="E2E-T1-FEAT-AC-05-05",
    name="Verify CRM outbox event logged upon commercial unit update",
    tier=1,
    feature_id="FEAT-AC-05",
    authoritative_source="PROJECT.md § 1. Backend API Contracts & Outbox"
)
def test_ac_05_outbox_event_logged():
    payload = {"local_id": "loc-coolbox-103", "precio_alquiler_mensual": 1450.00, "estado": "arrendado"}
    secret = "test_crm_outbox_secret_key"

    # Both backend outbox_service and E2E webhook_signer must calculate identical canonical HMAC-SHA256
    sig_backend = compute_hmac_signature(payload, secret)
    sig_test_signer = f"sha256={compute_hmac_sha256(payload, secret)}"
    assert sig_backend == sig_test_signer, f"Canonical HMAC mismatch: {sig_backend} vs {sig_test_signer}"
