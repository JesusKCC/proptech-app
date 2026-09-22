import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evento_outbox import EventoOutbox


async def record_outbox_event(
    db: AsyncSession,
    tipo_evento: str,
    entidad_tipo: str,
    entidad_id: str,
    payload: Dict[str, Any]
) -> EventoOutbox:
    """
    Atomically writes an event into the Transactional Outbox table.
    """
    event = EventoOutbox(
        tipo_evento=tipo_evento,
        entidad_tipo=entidad_tipo,
        entidad_id=str(entidad_id),
        payload=payload,
        estado="pendiente",
        creado_en=datetime.now(timezone.utc)
    )
    db.add(event)
    return event


def compute_hmac_signature(payload: Dict[str, Any], secret_key: str) -> str:
    """
    Computes a cryptographic HMAC-SHA256 signature for webhook verification using
    RFC 8785 canonical JSON formatting (separators=(',', ':'), sort_keys=True).
    """
    serialized = json.dumps(payload, separators=(',', ':'), sort_keys=True, default=str).encode("utf-8")
    signature = hmac.new(
        secret_key.encode("utf-8"),
        serialized,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


async def dispatch_outbox_events(
    db: AsyncSession,
    secret_key: str
) -> List[Dict[str, Any]]:
    """
    Processes all pending events from the outbox table,
    calculates their HMAC-SHA256 signatures, and transitions them to 'publicado'.
    """
    stmt = select(EventoOutbox).where(EventoOutbox.estado == "pendiente").order_by(EventoOutbox.creado_en.asc())
    result = await db.execute(stmt)
    pending_events = result.scalars().all()

    dispatched = []
    now = datetime.now(timezone.utc)

    for event in pending_events:
        sig = compute_hmac_signature(event.payload, secret_key)
        event.estado = "publicado"
        event.procesado_en = now
        
        dispatched.append({
            "event_id": event.id,
            "tipo_evento": event.tipo_evento,
            "entidad_id": event.entidad_id,
            "payload": event.payload,
            "signature": sig,
            "status": "publicado"
        })

    if pending_events:
        await db.commit()

    return dispatched
