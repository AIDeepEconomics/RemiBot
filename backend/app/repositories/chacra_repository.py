from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.repositories.base import BaseRepository


class ChacraRepository(BaseRepository[Dict[str, Any]]):
    """Repositorio para gestionar chacras."""

    def __init__(self, supabase_client) -> None:
        super().__init__(supabase_client, "chacras", dict)

    async def get_by_name_and_establecimiento(
        self, 
        nombre_chacra: str, 
        establecimiento_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtiene una chacra por nombre y establecimiento."""
        def _get_sync() -> Optional[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("nombre_chacra", nombre_chacra)
                .eq("id_establecimiento", establecimiento_id)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        
        record = await self._async_call(_get_sync)
        return self._record_to_model(record) if record else None

    async def get_or_create_by_name_and_establecimiento(
        self,
        nombre_chacra: str,
        establecimiento_id: str,
        empresa_id: str,
    ) -> Dict[str, Any]:
        """Obtiene o crea una chacra por nombre y establecimiento."""
        chacra = await self.get_by_name_and_establecimiento(nombre_chacra, establecimiento_id)
        if chacra:
            return chacra
        
        return await self.create({
            "nombre_chacra": nombre_chacra,
            "id_establecimiento": establecimiento_id,
            "id_empresa": empresa_id,
        })

    async def list_by_establecimiento(self, establecimiento_id: str) -> List[Dict[str, Any]]:
        """Lista chacras por establecimiento."""
        def _list_sync() -> List[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq("id_establecimiento", establecimiento_id)
                .eq("activo", True)
                .order("nombre_chacra")
                .execute()
            )
            return response.data or []
        
        records = await self._async_call(_list_sync)
        return [self._record_to_model(record) for record in records]

    async def list_by_empresa(self, empresa_id: str) -> List[Dict[str, Any]]:
        """Lista chacras por empresa."""
        def _list_sync() -> List[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .select("*, establecimientos(nombre)")
                .eq("id_empresa", empresa_id)
                .eq("activo", True)
                .order("nombre_chacra")
                .execute()
            )
            return response.data or []
        
        records = await self._async_call(_list_sync)
        return [self._record_to_model(record) for record in records]
