from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.repositories.base import BaseRepository


class EmpresaRepository(BaseRepository[Dict[str, Any]]):
    """Repositorio para gestionar empresas."""

    def __init__(self, supabase_client) -> None:
        super().__init__(supabase_client, "empresas", dict)

    async def get_by_name(self, nombre: str) -> Optional[Dict[str, Any]]:
        """Obtiene una empresa por su nombre."""
        return await self.get_by_field("nombre", nombre)

    async def get_or_create_by_name(self, nombre: str) -> Dict[str, Any]:
        """Obtiene o crea una empresa por su nombre."""
        empresa = await self.get_by_name(nombre)
        if empresa:
            return empresa
        
        return await self.create({"nombre": nombre})

    async def list_active(self) -> List[Dict[str, Any]]:
        """Lista todas las empresas activas."""
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
