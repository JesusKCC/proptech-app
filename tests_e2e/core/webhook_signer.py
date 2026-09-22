# HMAC-SHA256 Webhook Signer and Transactional Outbox Event Serializer.
# Authoritative source: PROJECT.md ? 1. Backend API Contracts & Outbox Pattern.
import hmac
import hashlib
import json
import time
import uuid
from typing import Dict, Any, Tuple, Optional

DEFAULT_SECRET = "proptech_super_secret_crm_key_2026"

def compute_hmac_sha256(payload: Any, secret: str = DEFAULT_SECRET) -> str:
    if isinstance(payload, dict):
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    elif isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    elif isinstance(payload, bytes):
        payload_bytes = payload
    else:
        payload_bytes = str(payload).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

def verify_hmac_sha256(payload: Any, signature: str, secret: str = DEFAULT_SECRET) -> bool:
    if not signature or not secret:
        return False
    if signature.startswith("sha256="):
        signature = signature[7:]
    expected = compute_hmac_sha256(payload, secret)
    return hmac.compare_digest(expected, signature)

def create_outbox_event(event_type: str, entity_type: str, entity_id: str, payload: Dict[str, Any], secret: str = DEFAULT_SECRET) -> Dict[str, Any]:
    event_id = str(uuid.uuid4())
    signature = compute_hmac_sha256(payload, secret)
    return {
        "id": event_id,
        "tipo_evento": event_type,
        "entidad_tipo": entity_type,
        "entidad_id": entity_id,
        "payload": payload,
        "estado": "pendiente",
        "signature": f"sha256={signature}",
        "reintentos": 0,
        "creado_en": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


class WebhookSigner:
    """Helper class providing HMAC-SHA256 signing and outbox event constructors."""

    @staticmethod
    def generate_signature(payload: Any, secret: str = DEFAULT_SECRET) -> str:
        return f"sha256={compute_hmac_sha256(payload, secret)}"

    @staticmethod
    def verify_signature(payload: Any, signature: str, secret: str = DEFAULT_SECRET) -> bool:
        return verify_hmac_sha256(payload, signature, secret)

    @staticmethod
    def build_outbox_event(event_type: str, payload: Dict[str, Any], secret: str = DEFAULT_SECRET) -> Dict[str, Any]:
        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":")) if isinstance(payload, dict) else str(payload)
        sig = compute_hmac_sha256(payload_str, secret)
        return {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "tipo_evento": event_type,
            "payload": payload_str,
            "signature": f"sha256={sig}",
            "status": "PENDING",
            "retry_count": 0,
            "next_retry_delay_seconds": 1,
            "created_at": time.time(),
        }

