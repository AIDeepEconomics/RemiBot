from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.repositories.base import BaseRepository


class DestinoRepository(BaseRepository[Dict[str, Any]]):
    """Repositorio para gestionar destinos."""

    def __init__(self, supabase_client) -> None:
        super().__init__(supabase_client, "destinos", dict)

    async def get_by_name(self, nombre: str) -> Optional[Dict[str, Any]]:
        """Obtiene un destino por su nombre."""
        return await self.get_by_field("nombre", nombre)

    async def get_or_create_by_name(self, nombre: str) -> Dict[str, Any]:
        """Obtiene o crea un destino por su nombre."""
        destino = await self.get_by_name(nombre)
        if destino:
            return destino
        
        return await self.create({"nombre": nombre})

    async def list_active(self) -> List[Dict[str, Any]]:
        """Lista todos los destinos activos."""
        def _list_sync() -> List[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("activo", True)
                .order("nombre")
                .execute()
            )
            return response.data or []
        
        records = await self._async_call(_list_sync)
        return [self._record_to_model(record) for record in records]
