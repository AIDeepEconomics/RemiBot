from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.settings import get_settings
from app.models.webhook import WhatsAppWebhookPayload, WhatsAppWebhookResponse

router = APIRouter()


@router.post("/whatsapp", response_model=WhatsAppWebhookResponse)
async def handle_whatsapp_webhook(  # type: ignore[no-untyped-def]
    payload: WhatsAppWebhookPayload,
    settings=Depends(get_settings),
) -> WhatsAppWebhookResponse:
    """
    Webhook para recibir mensajes de WhatsApp.
    Usa flujo conversacional V2 con contexto personalizado por empresa.
    """
    if not payload.body.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mensaje vacío")

    await settings.log_service.write_log(
        tipo="WEBHOOK",
        detalle="Mensaje entrante de WhatsApp",
        payload={
            "from": payload.from_number,
            "message_id": payload.message_id,
            "body": payload.body,
        },
    )

    response = await settings.remito_flow_v2.handle_message(payload)

    await settings.log_service.write_log(
        tipo="WEBHOOK",
        detalle="Respuesta enviada al contacto",
        payload={
            "from": payload.from_number,
            "message_id": payload.message_id,
            "reply": response.reply,
            "metadata": response.metadata,
        },
    )

    return response
