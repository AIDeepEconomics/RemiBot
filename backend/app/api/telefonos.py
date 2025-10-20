from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.settings import get_settings

router = APIRouter()


class TelefonoCreate(BaseModel):
    numero_telefono: str
    id_empresa: str
    notas: str | None = None


class TelefonoResponse(BaseModel):
    id: str
    numero_telefono: str
    numero_normalizado: str
    id_empresa: str
    activo: bool
    notas: str | None
    created_at: str


@router.get("/empresa/{empresa_id}", response_model=List[TelefonoResponse])
async def list_telefonos_by_empresa(
    empresa_id: str,
    settings=Depends(get_settings),  # type: ignore[no-untyped-def]
) -> List[dict]:
    """Lista todos los teléfonos autorizados de una empresa."""
    return await settings.phone_service.list_phones_by_empresa(empresa_id)


@router.post("/", response_model=TelefonoResponse, status_code=status.HTTP_201_CREATED)
async def add_telefono(
    payload: TelefonoCreate,
    settings=Depends(get_settings),  # type: ignore[no-untyped-def]
) -> dict:
    """Agrega un número de teléfono a una empresa."""
    try:
        return await settings.phone_service.add_phone_to_empresa(
            phone=payload.numero_telefono,
            empresa_id=payload.id_empresa,
            notas=payload.notas,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al agregar teléfono: {str(exc)}",
        ) from exc


@router.delete("/{telefono_id}")
async def remove_telefono(
    telefono_id: str,
    settings=Depends(get_settings),  # type: ignore[no-untyped-def]
) -> dict:
    """Desactiva un número de teléfono."""
    success = await settings.phone_service.remove_phone_from_empresa(telefono_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teléfono no encontrado",
        )
    return {"message": "Teléfono desactivado exitosamente"}


@router.get("/check/{numero}", response_model=List[str])
async def check_telefono(
    numero: str,
    settings=Depends(get_settings),  # type: ignore[no-untyped-def]
) -> List[str]:
    """Verifica qué empresas están asociadas a un número de teléfono."""
    return await settings.phone_service.find_empresas_by_phone(numero)
