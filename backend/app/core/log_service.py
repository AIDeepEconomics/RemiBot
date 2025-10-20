from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from supabase import Client

from app.models.log import LogEntry


class LogService:
    TABLE_NAME = "logs"

    def __init__(self, supabase_client: Client) -> None:
        self.supabase = supabase_client

    async def write_log(self, tipo: str, detalle: str, payload: Optional[Dict[str, Any]] = None) -> None:
        def _write_sync() -> None:
            self.supabase.table(self.TABLE_NAME).insert(
                {
                    "tipo": tipo,
                    "detalle": detalle,
                    "payload": payload,
                }
            ).execute()

        await asyncio.to_thread(_write_sync)

    async def list_logs(self, limit: int = 50) -> List[LogEntry]:
        def _list_sync() -> List[LogEntry]:
            response = (
                self.supabase.table(self.TABLE_NAME)
                .select("*")
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            data = response.data or []
            return [LogEntry.model_validate(item) for item in data]

        return await asyncio.to_thread(_list_sync)
