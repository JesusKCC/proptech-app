from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import require_proyectos, UserRole
from app.db.session import get_db
from app.schemas.webhook import WebhookDispatchResponse, WebhookDispatchResult
from app.services.outbox_service import dispatch_outbox_events

router = APIRouter()


@router.post(
    "/test-dispatch",
    response_model=WebhookDispatchResponse,
    summary="Procesar y despachar cola outbox de eventos con firma criptográfica HMAC-SHA256"
)
async def test_dispatch_webhooks(
    db: AsyncSession = Depends(get_db),
    current_role: UserRole = Depends(require_proyectos)
):
    dispatched = await dispatch_outbox_events(
        db=db,
        secret_key=settings.WEBHOOK_HMAC_SECRET
    )

    results = [
        WebhookDispatchResult(
            event_id=item["event_id"],
            tipo_evento=item["tipo_evento"],
            entidad_id=item["entidad_id"],
            payload=item["payload"],
            signature=item["signature"],
            status=item["status"]
        )
        for item in dispatched
    ]

    return WebhookDispatchResponse(
        total_procesados=len(results),
        eventos=results
    )


# Backward compatibility alias
trigger_webhook_dispatch = test_dispatch_webhooks
