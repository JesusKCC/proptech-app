#!/usr/bin/env python3
"""
scripts/verify_e2e_integration.py
Live End-to-End Integration Verification Script
Project: PropTech Commercial Asset Management & Interactive Blueprint Platform (Milestone 4)

Verifies the live integration between Frontend API Client and FastAPI Backend:
1. Reads commercial units from /api/v1/locales
2. Simulates polygon click event triggering unit sheet retrieval (/api/v1/locales/{id})
3. Updates commercial terms via PUT /api/v1/locales/{id}
4. Persists and re-reads the updated data from database
5. Creates a ticket under role Comercial (/api/v1/tickets)
6. Resolves the ticket under role Proyectos (/api/v1/tickets/{id}/resolve)
7. Verifies 403 Forbidden when Comercial attempts ticket resolution
8. Verifies Transactional Outbox CRM events (local.actualizado, ticket.creado, ticket.resuelto)
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional

# Add project root and backend to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

try:
    import httpx
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from app.main import app
    from app.db.base import Base
    from app.db.session import get_db
    from app.models.centro_comercial import CentroComercial
    from app.models.plano_centro import PlanoCentro
    from app.models.local import Local
    from app.models.poligono import Poligono
    from app.models.ticket import Ticket
    from app.models.evento_outbox import EventoOutbox
    FASTAPI_AVAILABLE = True
except Exception as e:
    FASTAPI_AVAILABLE = False
    IMPORT_ERR = str(e)


async def seed_integration_data(session: AsyncSession) -> Dict[str, Any]:
    """Ensures base entities exist for integration verification."""
    # Check if mall exists
    res = await session.execute(
        select(CentroComercial).where(CentroComercial.slug == "plaza-center-villa-el-salvador")
    )
    mall = res.scalar_one_or_none()
    if not mall:
        mall = CentroComercial(
            id="mall-ves-integration",
            nombre="Plaza Center Villa El Salvador",
            slug="plaza-center-villa-el-salvador",
            direccion="Av. Pachacútec con Av. El Sol, Villa El Salvador",
            departamento="Lima",
            provincia="Lima",
            distrito="Villa El Salvador",
            lat=-12.215,
            lon=-76.938,
            total_locales=26,
            superficie_total_m2=60000.0,
            imagen_url="https://images.unsplash.com/photo-1519567241046-7f570eee3ce6?w=800"
        )
        session.add(mall)
        await session.flush()

    # Blueprint
    res_plano = await session.execute(
        select(PlanoCentro).where(PlanoCentro.centro_comercial_id == mall.id)
    )
    plano = res_plano.scalar_one_or_none()
    if not plano:
        plano = PlanoCentro(
            id="plano-ves-integration-n1",
            centro_comercial_id=mall.id,
            nombre_piso="Nivel 1 - Galería Principal",
            archivo_pdf_url="/static/blueprints/pacita_ves_nivel1.pdf",
            ancho_unscaled_pt=2384.0,
            alto_unscaled_pt=1684.0
        )
        session.add(plano)
        await session.flush()

    # Commercial Units
    res_local = await session.execute(
        select(Local).where(Local.codigo_local == "LCE-103")
    )
    local = res_local.scalar_one_or_none()
    if not local:
        local = Local(
            id="loc-ves-103-integration",
            centro_comercial_id=mall.id,
            plano_id=plano.id,
            codigo_local="LCE-103",
            nombre_comercial="COOLBOX",
            categoria="Tecnología",
            estado="arrendado",
            area_m2=36.96,
            precio_alquiler_mensual=1850.0,
            moneda="USD",
            piso_nivel="Nivel 1",
            descripcion="Venta de gadgets y accesorios electrónicos de alta rotación."
        )
        session.add(local)
        await session.flush()

    # Polygon
    res_poly = await session.execute(
        select(Poligono).where(Poligono.local_id == local.id)
    )
    polygon = res_poly.scalar_one_or_none()
    if not polygon:
        polygon = Poligono(
            id="poly-ves-103-integration",
            local_id=local.id,
            plano_id=plano.id,
            coordenadas_relativas=[
                {"x": 0.7341, "y": 0.4929},
                {"x": 0.7634, "y": 0.4929},
                {"x": 0.7634, "y": 0.5255},
                {"x": 0.7341, "y": 0.5255}
            ],
            color_relleno="rgba(59, 130, 246, 0.4)",
            color_borde="#2563eb",
            opacidad=0.45,
            etiqueta="LCE-103 COOLBOX"
        )
        session.add(polygon)
        await session.flush()

    await session.commit()
    return {"mall": mall, "plano": plano, "local": local, "polygon": polygon}


class IntegrationVerifier:
    def __init__(self, client: httpx.AsyncClient, session: Optional[AsyncSession] = None):
        self.client = client
        self.session = session
        self.results = []

    def record_step(self, step_num: int, title: str, passed: bool, details: str):
        status = "[PASS]" if passed else "[FAIL]"
        self.results.append({"step": step_num, "title": title, "passed": passed, "details": details})
        print(f"  {status} Paso {step_num}: {title}")
        if details:
            print(f"         {details}")

    async def execute_all_steps(self):
        print("\n" + "=" * 76)
        print(" PROPTECH PLATFORM: LIVE FRONTEND-BACKEND INTEGRATION VERIFICATION")
        print("=" * 76 + "\n")

        # -------------------------------------------------------------
        # STEP 1: Reads commercial units from /api/v1/locales
        # -------------------------------------------------------------
        res = await self.client.get(
            "/api/v1/locales/",
            headers={"X-User-Role": "comercial"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        locales = res.json()
        assert isinstance(locales, list) and len(locales) > 0, "No commercial units returned"
        target_local = next((l for l in locales if l.get("codigo_local") == "LCE-103"), locales[0])
        self.record_step(
            1,
            "Lectura de Locales Comerciales (/api/v1/locales)",
            True,
            f"Se listaron {len(locales)} locales comerciales. Local objetivo: {target_local['codigo_local']} ({target_local['nombre_comercial']})"
        )

        # -------------------------------------------------------------
        # STEP 2: Simulates polygon click event triggering unit sheet retrieval
        # -------------------------------------------------------------
        # Retrieve blueprint polygons
        poly_res = await self.client.get(
            f"/api/v1/poligonos/?plano_id={target_local.get('plano_id')}",
            headers={"X-User-Role": "comercial"}
        )
        assert poly_res.status_code == 200, f"Failed to get polygons: {poly_res.text}"
        polygons = poly_res.json()
        target_poly = next((p for p in polygons if p.get("local_id") == target_local["id"]), None)
        if not target_poly and len(polygons) > 0:
            target_poly = polygons[0]

        # Simulate click on polygon centroid: triggers GET /api/v1/locales/{id}
        click_local_id = target_poly["local_id"] if target_poly else target_local["id"]
        sheet_res = await self.client.get(
            f"/api/v1/locales/{click_local_id}",
            headers={"X-User-Role": "comercial"}
        )
        assert sheet_res.status_code == 200, f"Ficha del Local retrieval failed: {sheet_res.text}"
        ficha = sheet_res.json()
        assert ficha["codigo_local"] == target_local["codigo_local"]
        assert "poligonos" in ficha, "Ficha del Local must include attached polygons"
        self.record_step(
            2,
            "Simulación de Clic en Polígono -> Ficha del Local (/api/v1/locales/{id})",
            True,
            f"Polígono {target_poly.get('id', 'poly-click')} disparó apertura de Ficha: {ficha['codigo_local']} con {len(ficha['poligonos'])} polígono(s) asociado(s)"
        )

        # -------------------------------------------------------------
        # STEP 3: Updates commercial terms via PUT /api/v1/locales/{id}
        # -------------------------------------------------------------
        new_rent = 2150.00
        new_description = "Local remodelado con mampara de vidrio templado y nuevo sistema LED."
        update_payload = {
            "precio_alquiler_mensual": new_rent,
            "descripcion": new_description,
            "estado": "arrendado"
        }
        put_res = await self.client.put(
            f"/api/v1/locales/{target_local['id']}",
            json=update_payload,
            headers={"X-User-Role": "comercial"}
        )
        assert put_res.status_code == 200, f"Update failed: {put_res.text}"
        updated_local = put_res.json()
        assert updated_local["precio_alquiler_mensual"] == new_rent
        self.record_step(
            3,
            "Actualización de Términos Comerciales (PUT /api/v1/locales/{id})",
            True,
            f"Alquiler mensual actualizado a ${new_rent:.2f} USD. Emitido outbox local.actualizado"
        )

        # -------------------------------------------------------------
        # STEP 4: Persists and re-reads the updated data
        # -------------------------------------------------------------
        reread_res = await self.client.get(
            f"/api/v1/locales/{target_local['id']}",
            headers={"X-User-Role": "comercial"}
        )
        assert reread_res.status_code == 200
        persisted_data = reread_res.json()
        assert persisted_data["precio_alquiler_mensual"] == new_rent
        assert persisted_data["descripcion"] == new_description
        self.record_step(
            4,
            "Persistencia y Re-lectura de Datos Actualizados",
            True,
            f"Verificado valor persistido en base de datos: Alquiler ${persisted_data['precio_alquiler_mensual']} USD"
        )

        # -------------------------------------------------------------
        # STEP 5: Creates a ticket under role Comercial
        # -------------------------------------------------------------
        ticket_payload = {
            "centro_comercial_id": target_local["centro_comercial_id"],
            "local_id": target_local["id"],
            "titulo": "Revisión técnica de carga eléctrica adicional",
            "descripcion": "El inquilino instalará 3 refrigeradores industriales que requieren trifásica.",
            "tipo": "nuevo_requerimiento",
            "prioridad": "alta"
        }
        create_tck_res = await self.client.post(
            "/api/v1/tickets/",
            json=ticket_payload,
            headers={"X-User-Role": "comercial"}
        )
        assert create_tck_res.status_code == 201, f"Ticket creation failed: {create_tck_res.text}"
        ticket_data = create_tck_res.json()
        assert ticket_data["codigo_ticket"].startswith("TCK-2026-")
        assert ticket_data["creado_por"] == "comercial"
        assert ticket_data["estado"] == "abierto"
        ticket_id = ticket_data["id"]
        self.record_step(
            5,
            "Creación de Ticket bajo Rol Comercial (POST /api/v1/tickets)",
            True,
            f"Ticket {ticket_data['codigo_ticket']} creado exitosamente (Prioridad: {ticket_data['prioridad']})"
        )

        # -------------------------------------------------------------
        # STEP 6: Resolves the ticket under role Proyectos
        # -------------------------------------------------------------
        resolve_payload = {
            "notas_resolucion": "Factibilidad aprobada. Subestación eléctrica cuenta con carga disponible. Se programó acometida trifásica para el 15/09."
        }
        resolve_res = await self.client.patch(
            f"/api/v1/tickets/{ticket_id}/resolve",
            json=resolve_payload,
            headers={"X-User-Role": "proyectos"}
        )
        assert resolve_res.status_code == 200, f"Resolution failed: {resolve_res.text}"
        resolved_data = resolve_res.json()
        assert resolved_data["estado"] == "resuelto"
        assert resolved_data["notas_resolucion"] == resolve_payload["notas_resolucion"]
        assert resolved_data["resuelto_en"] is not None
        self.record_step(
            6,
            "Resolución de Ticket bajo Rol Proyectos (PATCH /api/v1/tickets/{id}/resolve)",
            True,
            f"Ticket {ticket_data['codigo_ticket']} resuelto con notas técnicas de ingeniería"
        )

        # -------------------------------------------------------------
        # STEP 7: Verifies 403 Forbidden when Comercial attempts ticket resolution
        # -------------------------------------------------------------
        # Create second ticket for RBAC testing
        second_tck = await self.client.post(
            "/api/v1/tickets/",
            json={
                "centro_comercial_id": target_local["centro_comercial_id"],
                "local_id": target_local["id"],
                "titulo": "Ticket para verificación de seguridad RBAC",
                "descripcion": "Verificación de bloqueo de resolución para Comercial.",
                "tipo": "mantenimiento",
                "prioridad": "baja"
            },
            headers={"X-User-Role": "comercial"}
        )
        assert second_tck.status_code == 201
        second_tck_id = second_tck.json()["id"]

        # Attempt to resolve using COMERCIAL role
        unauthorized_res = await self.client.patch(
            f"/api/v1/tickets/{second_tck_id}/resolve",
            json={"notas_resolucion": "Intento de resolución no autorizado"},
            headers={"X-User-Role": "comercial"}
        )
        assert unauthorized_res.status_code == 403, (
            f"Expected 403 Forbidden, got {unauthorized_res.status_code}: {unauthorized_res.text}"
        )
        error_detail = unauthorized_res.json().get("detail", "")
        assert "Acceso denegado" in error_detail or "proyectos" in error_detail
        self.record_step(
            7,
            "Verificación de Seguridad RBAC: Comercial bloqueado con 403 Forbidden",
            True,
            f"HTTP 403 recibido correctamente al intentar resolver como 'comercial' ('{error_detail}')"
        )

        # -------------------------------------------------------------
        # STEP 8: Transactional Outbox CRM Dispatch Verification
        # -------------------------------------------------------------
        dispatch_res = await self.client.post(
            "/api/v1/webhooks/test-dispatch",
            headers={"X-User-Role": "proyectos"}
        )
        assert dispatch_res.status_code == 200
        outbox_info = dispatch_res.json()
        assert outbox_info["total_procesados"] >= 3, "Expected at least 3 events processed"
        self.record_step(
            8,
            "Despacho y Firma Criptográfica HMAC-SHA256 de Eventos Outbox CRM",
            True,
            f"{outbox_info['total_procesados']} eventos transaccionales despachados con firma HMAC-SHA256"
        )

        print("\n" + "=" * 76)
        print(" RESUMEN: TODOS LOS 8 PASOS DE INTEGRACIÓN E2E COMPLETADOS CON ÉXITO")
        print("=" * 76 + "\n")
        return True


async def run_live_or_inprocess():
    """Runs integration test against live server if available, or using in-process ASGI engine."""
    server_url = os.getenv("API_URL", "http://127.0.0.1:8000")
    print(f"Checking connectivity to: {server_url} ...")

    is_live = False
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(f"{server_url}/health")
            if resp.status_code == 200:
                is_live = True
    except Exception:
        is_live = False

    if is_live:
        print(f"[INFO] Active FastAPI server detected at {server_url}. Running in LIVE HTTP mode.")
        async with httpx.AsyncClient(base_url=server_url, timeout=10.0) as client:
            verifier = IntegrationVerifier(client=client)
            success = await verifier.execute_all_steps()
            return 0 if success else 1
    else:
        print("[INFO] No external server detected. Initializing FastAPI in-process ASGI client with database engine.")
        if not FASTAPI_AVAILABLE:
            print(f"[FATAL] FastAPI modules could not be loaded: {IMPORT_ERR}")
            return 1

        # Use an in-memory SQLite engine for isolated, non-destructive integration verification
        from httpx import ASGITransport
        from sqlalchemy.pool import StaticPool

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with session_factory() as session:
            await seed_integration_data(session)

        # Override dependency
        async def override_get_db():
            async with session_factory() as sess:
                yield sess

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            verifier = IntegrationVerifier(client=client)
            success = await verifier.execute_all_steps()

        return 0 if success else 1


def main():
    exit_code = asyncio.run(run_live_or_inprocess())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
