from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query

from app.core.settings import get_settings
from app.models.log import LogEntry

router = APIRouter()


@router.get(
    "/",
    response_model=List[LogEntry],
    summary="Listado paginado de logs",
)
async def list_logs(  # type: ignore[no-untyped-def]
    limit: int = Query(50, ge=1, le=500, description="Cantidad máxima de logs a devolver"),
    settings=Depends(get_settings),
) -> List[LogEntry]:
    return await settings.log_service.list_logs(limit=limit)
