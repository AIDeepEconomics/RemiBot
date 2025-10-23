from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.core.settings import get_settings
from app.models.webhook import WhatsAppWebhookPayload, WhatsAppWebhookResponse

router = APIRouter()


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> PlainTextResponse:
    """
    Endpoint de verificación del webhook de WhatsApp.
    Meta/Facebook llama a este endpoint con parámetros de verificación.
    """
    # Token de verificación hardcodeado para simplificar
    expected_token = "remibot_verify_2025"
    
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return PlainTextResponse(content=hub_challenge)
    
    raise HTTPException(status_code=403, detail="Verificación fallida")


@router.post("/whatsapp")
async def handle_whatsapp_webhook(
    request: Request,
    settings=Depends(get_settings),
):
    """
    Webhook para recibir mensajes de WhatsApp.
    Usa flujo conversacional V2 con contexto personalizado por empresa.
    """
    try:
        # Obtener el payload raw de WhatsApp
        raw_payload = await request.json()
        
        # Log del payload completo para debugging
        try:
            await settings.log_service.write_log(
                tipo="WEBHOOK",
                detalle="Payload raw de WhatsApp",
                payload=raw_payload,
            )
        except Exception:
            pass  # No fallar si el log falla
        
        # Extraer información del formato de WhatsApp
        # Formato: {"object": "whatsapp_business_account", "entry": [...]}
        if raw_payload.get("object") != "whatsapp_business_account":
            return {"status": "ok"}
        
        entries = raw_payload.get("entry", [])
        if not entries:
            return {"status": "ok"}
        
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for message in messages:
                    message_id = message.get("id")
                    from_number = message.get("from")
                    message_type = message.get("type")
                    
                    # Solo procesar mensajes de texto
                    if message_type != "text":
                        continue
                    
                    body = message.get("text", {}).get("body", "")
                    
                    if not body.strip():
                        continue
                    
                    # Crear payload en el formato esperado
                    webhook_payload = WhatsAppWebhookPayload(
                        message_id=message_id,
                        from_number=from_number,
                        body=body,
                        raw_event=raw_payload,
                    )
                    
                    # Procesar el mensaje con el nuevo sistema refacturado
                    response = await settings.remito_flow_v2_refactored.handle_message(webhook_payload)
                    
                    try:
                        await settings.log_service.write_log(
                            tipo="WEBHOOK",
                            detalle="Respuesta enviada al contacto",
                            payload={
                                "from": from_number,
                                "message_id": message_id,
                                "reply": response.reply,
                                "metadata": response.metadata,
                            },
                        )
                    except Exception:
                        pass  # No fallar si el log falla
        
        return {"status": "ok"}
        
    except Exception as e:
        import traceback
        try:
            await settings.log_service.write_log(
                tipo="WEBHOOK",
                detalle=f"Error procesando webhook: {str(e)}",
                payload={"error": str(e), "traceback": traceback.format_exc()},
            )
        except Exception:
            pass
        # Devolver 200 para que WhatsApp no reintente
        return {"status": "error", "message": str(e)}
