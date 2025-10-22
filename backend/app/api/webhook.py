from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.core.settings import get_settings
from app.models.webhook import WhatsAppWebhookPayload, WhatsAppWebhookResponse

router = APIRouter()


@router.get("/whatsapp")
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
    settings=Depends(get_settings),
) -> PlainTextResponse:
    """
    Endpoint de verificación del webhook de WhatsApp.
    Meta/Facebook llama a este endpoint con parámetros de verificación.
    """
    # El verify token debe estar en las variables de entorno
    expected_token = settings.whatsapp_verify_token
    
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        try:
            await settings.log_service.write_log(
                tipo="WEBHOOK",
                detalle="Webhook verificado exitosamente",
                payload={"mode": hub_mode},
            )
        except Exception:
            pass  # No fallar si el log falla
        return PlainTextResponse(content=hub_challenge)
    
    try:
        await settings.log_service.write_log(
            tipo="WEBHOOK",
            detalle="Intento de verificación fallido",
            payload={"mode": hub_mode, "token_match": hub_verify_token == expected_token},
        )
    except Exception:
        pass  # No fallar si el log falla
    
    raise HTTPException(status_code=403, detail="Verificación fallida")


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
