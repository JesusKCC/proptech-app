from typing import Any, Dict, List
from pydantic import BaseModel


class WebhookDispatchResult(BaseModel):
    event_id: str
    tipo_evento: str
    entidad_id: str
    payload: Dict[str, Any]
    signature: str
    status: str


class WebhookDispatchResponse(BaseModel):
    total_procesados: int
    eventos: List[WebhookDispatchResult]
