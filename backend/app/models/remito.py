from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RemitoBase(BaseModel):
    id_chacra: str = Field(..., description="Identificador único de la chacra")
    nombre_chacra: str
    id_establecimiento: str
    nombre_establecimiento: str
    id_empresa: str
    nombre_empresa: str
    id_destino: str
    nombre_destino: str
    nombre_conductor: str
    cedula_conductor: str
    matricula_camion: str
    matricula_zorra: Optional[str] = None
    peso_estimado_tn: float = Field(..., ge=0.0)
    estado_remito: str = Field("despachado", description="Estado del remito")
    activo: bool = True
    raw_payload: Optional[dict] = Field(default=None, description="Payload completo capturado")


class RemitoCreate(RemitoBase):
    qr_url: Optional[str] = None


class RemitoUpdate(BaseModel):
    estado_remito: Optional[str] = None
    activo: Optional[bool] = None
    qr_url: Optional[str] = None
    raw_payload: Optional[dict] = None


class Remito(RemitoBase):
    id_remito: str
    qr_url: Optional[str] = None
    timestamp_creacion: datetime
