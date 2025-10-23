from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.repositories.base import BaseRepository


class EstablecimientoRepository(BaseRepository[Dict[str, Any]]):
    """Repositorio para gestionar establecimientos."""

    def __init__(self, supabase_client) -> None:
        super().__init__(supabase_client, "establecimientos", dict)

    async def get_by_name_and_empresa(self, nombre: str, empresa_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un establecimiento por nombre y empresa."""
        def _get_sync() -> Optional[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("nombre", nombre)
                .eq("id_empresa", empresa_id)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        
        record = await self._async_call(_get_sync)
        return self._record_to_model(record) if record else None

    async def get_or_create_by_name_and_empresa(
        self, 
        nombre: str, 
        empresa_id: str
    ) -> Dict[str, Any]:
        """Obtiene o crea un establecimiento por nombre y empresa."""
        establecimiento = await self.get_by_name_and_empresa(nombre, empresa_id)
        if establecimiento:
            return establecimiento
        
        return await self.create({
            "nombre": nombre,
            "id_empresa": empresa_id
        })

    async def list_by_empresa(self, empresa_id: str) -> List[Dict[str, Any]]:
        """Lista establecimientos por empresa."""
        def _list_sync() -> List[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("id_empresa", empresa_id)
                .eq("activo", True)
                .order("nombre")
                .execute()
            )
            return response.data or []
        
        records = await self._async_call(_list_sync)
        return [self._record_to_model(record) for record in records]
