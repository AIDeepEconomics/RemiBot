from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from pydantic import SecretStr
from supabase import Client

from app.core.log_service import LogService
from app.models.config import AppConfig, AppConfigUpdate


class ConfigStore:
    """Gestor de configuración persistida en Supabase."""

    TABLE_NAME = "configuraciones"
    CONFIG_ID = 1

    def __init__(self, supabase: Client, log_service: Optional[LogService] = None) -> None:
        self.supabase = supabase
        self.log_service = log_service

    async def read(self) -> AppConfig:
        def _read_sync() -> AppConfig:
            response = (
                self.supabase.table(self.TABLE_NAME)
                .select("*")
                .eq("id", self.CONFIG_ID)
                .limit(1)
                .execute()
            )
            record = response.data[0] if response.data else None
            return self._record_to_model(record)

        return await asyncio.to_thread(_read_sync)

    async def write(self, payload: AppConfigUpdate) -> AppConfig:
        update_data = payload.model_dump(exclude_unset=True, mode="python")
        if not update_data:
            return await self.read()

        def _write_sync() -> AppConfig:
            data = {**update_data, "id": self.CONFIG_ID, "updated_at": datetime.now(timezone.utc).isoformat()}
            response = (
                self.supabase.table(self.TABLE_NAME)
                .upsert(data, on_conflict="id")
                .execute()
            )
            record = response.data[0] if response.data else data
            return self._record_to_model(record)

        new_config = await asyncio.to_thread(_write_sync)

        if self.log_service:
            await self.log_service.write_log(
                tipo="CONFIG",
                detalle="Configuración actualizada",
                payload={"campos": list(update_data.keys())},
            )

        return new_config

    @staticmethod
    def _record_to_model(record: Optional[dict]) -> AppConfig:
        if not record:
            return AppConfig()

        def _to_secret(value: Optional[str]) -> Optional[SecretStr]:
            return SecretStr(value) if value else None

        return AppConfig(
            whatsapp_api_key=_to_secret(record.get("whatsapp_api_key")),
            gpt_api_key=_to_secret(record.get("gpt_api_key")),
            claude_api_key=_to_secret(record.get("claude_api_key")),
            llm_prompt=record.get("llm_prompt"),
            auth_password_hash=record.get("auth_password_hash"),
        )
