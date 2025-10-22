from __future__ import annotations

import asyncio
from typing import Optional

import httpx


class WhatsAppService:
    """Servicio para enviar mensajes e imágenes por WhatsApp Cloud API."""

    def __init__(
        self,
        phone_id: str,
        access_token: str,
        api_version: str = "v18.0",
    ) -> None:
        self.phone_id = phone_id
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}/{phone_id}/messages"

    async def send_text(self, to: str, text: str) -> dict:
        """Envía un mensaje de texto por WhatsApp."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }

        return await self._send_request(payload)

    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None,
    ) -> dict:
        """Envía una imagen por WhatsApp."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url,
            },
        }

        if caption:
            payload["image"]["caption"] = caption

        return await self._send_request(payload)

    async def _send_request(self, payload: dict) -> dict:
        """Envía una petición a la API de WhatsApp."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.base_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()
