import hashlib
import hmac
import json
import pytest
from httpx import AsyncClient
from app.core.config import settings


@pytest.mark.asyncio
async def test_webhook_outbox_queue_dispatch_and_hmac_verification(client: AsyncClient, seeded_entities: dict):
    """
    Verifies the complete Transactional Outbox CRM workflow:
    1. Creates actions (ticket creation, local update) that generate pending events.
    2. Dispatches outbox queue via POST /api/v1/webhooks/test-dispatch.
    3. Cryptographically verifies the HMAC-SHA256 signature on the webhook payload.
    4. Asserts events transition to 'publicado' and second dispatch yields 0 pending.
    """
    mall = seeded_entities["mall"]
    local = seeded_entities["locales"][0]

    # Action 1: Create Ticket (emits ticket.creado)
    await client.post(
        "/api/v1/tickets/",
        json={
            "centro_comercial_id": mall.id,
            "local_id": local.id,
            "titulo": "Ticket para webhook test",
            "descripcion": "Probando webhook outbox",
            "tipo": "nuevo_requerimiento"
        },
        headers={"X-User-Role": "comercial"}
    )

    # Action 2: Update Local (emits local.actualizado)
    await client.put(
        f"/api/v1/locales/{local.id}",
        json={"precio_alquiler_mensual": 1399.00},
        headers={"X-User-Role": "comercial"}
    )

    # Action 3: Trigger Outbox Dispatch
    res = await client.post(
        "/api/v1/webhooks/test-dispatch",
        headers={"X-User-Role": "proyectos"}
    )
    assert res.status_code == 200
    dispatch_data = res.json()

    assert dispatch_data["total_procesados"] >= 2
    event_types = [e["tipo_evento"] for e in dispatch_data["eventos"]]
    assert "ticket.creado" in event_types
    assert "local.actualizado" in event_types

    # Cryptographic HMAC-SHA256 signature verification for each dispatched event
    for event in dispatch_data["eventos"]:
        sig = event["signature"]
        assert sig.startswith("sha256=")
        hex_sig = sig.replace("sha256=", "")

        # Re-compute HMAC-SHA256 using configured secret with RFC 8785 canonical JSON formatting
        serialized_payload = json.dumps(event["payload"], separators=(',', ':'), sort_keys=True, default=str).encode("utf-8")
        expected_hex = hmac.new(
            settings.WEBHOOK_HMAC_SECRET.encode("utf-8"),
            serialized_payload,
            hashlib.sha256
        ).hexdigest()

        assert hex_sig == expected_hex, f"HMAC signature mismatch for event {event['tipo_evento']}"
        assert event["status"] == "publicado"

    # Action 4: Second dispatch should find 0 pending events
    res_empty = await client.post(
        "/api/v1/webhooks/test-dispatch",
        headers={"X-User-Role": "proyectos"}
    )
    assert res_empty.status_code == 200
    assert res_empty.json()["total_procesados"] == 0


@pytest.mark.asyncio
async def test_webhook_dispatch_comercial_forbidden_403(client: AsyncClient):
    """Verifies that role 'comercial' receives HTTP 403 Forbidden when calling test-dispatch."""
    res = await client.post(
        "/api/v1/webhooks/test-dispatch",
        headers={"X-User-Role": "comercial"}
    )
    assert res.status_code == 403
    assert "Acceso denegado" in res.json()["detail"]
