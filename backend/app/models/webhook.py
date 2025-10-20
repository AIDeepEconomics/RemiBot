from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WhatsAppWebhookPayload(BaseModel):
    message_id: str = Field(..., description="Identificador del mensaje entrante")
    from_number: str = Field(..., description="Número del operario de cosecha")
    body: str = Field(..., description="Contenido textual del mensaje")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_event: Optional[Dict[str, Any]] = Field(
        default=None, description="Evento completo entregado por WhatsApp"
    )


class WhatsAppWebhookResponse(BaseModel):
    reply: str = Field(..., description="Respuesta textual a ser enviada al operario")
    metadata: Dict[str, Any] = Field(default_factory=dict)
