from fastapi import APIRouter, Depends, HTTPException, status

from app.core.remito_flow_v2 import SYSTEM_PROMPT
from app.core.settings import get_settings
from app.models.config import AppConfig, AppConfigUpdate

router = APIRouter()


@router.get("/", response_model=AppConfig)
async def read_config(settings=Depends(get_settings)) -> AppConfig:  # type: ignore[no-untyped-def]
    config = await settings.config_store.read()
    # Si no hay prompt configurado, usar el default
    if not config.llm_prompt:
        config.llm_prompt = SYSTEM_PROMPT
    return config


@router.post(
    "/",
    response_model=AppConfig,
    status_code=status.HTTP_200_OK,
    summary="Persist configuration values",
)
async def write_config(
    payload: AppConfigUpdate,
    settings=Depends(get_settings),  # type: ignore[no-untyped-def]
) -> AppConfig:
    try:
        return await settings.config_store.write(payload)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
