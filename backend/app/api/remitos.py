from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.settings import get_settings
from app.models.remito import Remito, RemitoCreate, RemitoUpdate

router = APIRouter()


@router.get("/", response_model=List[Remito], summary="List remitos")
async def list_remitos(  # type: ignore[no-untyped-def]
    activo: bool | None = Query(None, description="Filtrar por remitos activos"),
    destino: str | None = Query(None, description="Filtrar por destino"),
    establecimiento: str | None = Query(None, description="Filtrar por establecimiento de origen"),
    chacra: str | None = Query(None, description="Filtrar por chacra de origen"),
    matricula_camion: str | None = Query(None, description="Filtrar por matrícula de camión"),
    matricula_zorra: str | None = Query(None, description="Filtrar por matrícula de zorra"),
    cedula_conductor: str | None = Query(None, description="Filtrar por cédula del conductor"),
    year: int | None = Query(None, description="Filtrar por año", ge=2020, le=2100),
    month: int | None = Query(None, description="Filtrar por mes", ge=1, le=12),
    day: int | None = Query(None, description="Filtrar por día", ge=1, le=31),
    settings=Depends(get_settings),
) -> List[Remito]:
    return await settings.remito_service.list_remitos(
        activo=activo,
        destino=destino,
        establecimiento=establecimiento,
        chacra=chacra,
        matricula_camion=matricula_camion,
        matricula_zorra=matricula_zorra,
        cedula_conductor=cedula_conductor,
        year=year,
        month=month,
        day=day,
    )


@router.get("/{remito_id}", response_model=Remito)
async def get_remito(  # type: ignore[no-untyped-def]
    remito_id: str = Path(..., description="ID del remito"),
    settings=Depends(get_settings),
) -> Remito:
    remito = await settings.remito_service.get_remito(remito_id)
    if not remito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remito no encontrado")
    return remito


@router.post("/", response_model=Remito, status_code=status.HTTP_201_CREATED)
async def create_remito(  # type: ignore[no-untyped-def]
    payload: RemitoCreate,
    settings=Depends(get_settings),
) -> Remito:
    return await settings.remito_service.create_remito(payload)


@router.patch("/{remito_id}", response_model=Remito)
async def update_remito(  # type: ignore[no-untyped-def]
    remito_id: str,
    payload: RemitoUpdate,
    settings=Depends(get_settings),
) -> Remito:
    return await settings.remito_service.update_remito(remito_id, payload)
