from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    id: int = Field(..., description="Identificador incremental del log")
    timestamp: datetime = Field(..., description="Marca temporal en UTC del evento")
    tipo: str = Field(..., description="Categoría del evento")
    detalle: Optional[str] = Field(None, description="Descripción adicional")
    payload: Optional[dict[str, Any]] = Field(None, description="Información adicional serializada")
