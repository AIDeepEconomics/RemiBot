from __future__ import annotations

import asyncio
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from supabase import Client

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Repositorio base para eliminar duplicación en acceso a datos."""

    def __init__(self, supabase_client: Client, table_name: str, model_class: Type[T]):
        self.supabase = supabase_client
        self.table_name = table_name
        self.model_class = model_class

    async def get_by_id(self, id_value: str, id_field: str = "id") -> Optional[T]:
        """Obtiene un registro por ID."""
        def _get_sync() -> Optional[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq(id_field, id_value)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None

        record = await asyncio.to_thread(_get_sync)
        return self._record_to_model(record) if record else None

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[T]:
        """Obtiene un registro por cualquier campo."""
        def _get_sync() -> Optional[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .select("*")
                .eq(field_name, field_value)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None

        record = await asyncio.to_thread(_get_sync)
        return self._record_to_model(record) if record else None

    async def get_all(self, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[T]:
        """Obtiene todos los registros."""
        def _get_all_sync() -> List[Dict[str, Any]]:
            query = self.supabase.table(self.table_name).select("*")
            
            if order_by:
                query = query.order(order_by)
            if limit:
                query = query.limit(limit)
                
            response = query.execute()
            return response.data or []

        records = await asyncio.to_thread(_get_all_sync)
        return [self._record_to_model(record) for record in records]

    async def create(self, data: Dict[str, Any]) -> T:
        """Crea un nuevo registro."""
        def _create_sync() -> Dict[str, Any]:
            response = self.supabase.table(self.table_name).insert(data).execute()
            return response.data[0] if response.data else data

        record = await asyncio.to_thread(_create_sync)
        return self._record_to_model(record)

    async def update(self, id_value: str, data: Dict[str, Any], id_field: str = "id") -> Optional[T]:
        """Actualiza un registro existente."""
        def _update_sync() -> Optional[Dict[str, Any]]:
            response = (
                self.supabase.table(self.table_name)
                .update(data)
                .eq(id_field, id_value)
                .execute()
            )
            return response.data[0] if response.data else None

        record = await asyncio.to_thread(_update_sync)
        return self._record_to_model(record) if record else None

    async def delete(self, id_value: str, id_field: str = "id") -> bool:
        """Elimina un registro (soft delete si tiene campo activo)."""
        def _delete_sync() -> bool:
            response = (
                self.supabase.table(self.table_name)
                .update({"activo": False})
                .eq(id_field, id_value)
                .execute()
            )
            return bool(response.data)

        result = await asyncio.to_thread(_delete_sync)
        return result

    async def get_or_create(self, data: Dict[str, Any], unique_fields: List[str]) -> T:
        """Obtiene o crea un registro basado en campos únicos."""
        # Buscar por campos únicos
        query = self.supabase.table(self.table_name).select("*")
        
        for field in unique_fields:
            if field in data:
                query = query.eq(field, data[field])
        
        def _get_or_create_sync() -> Dict[str, Any]:
            response = query.limit(1).execute()
            if response.data:
                return response.data[0]
            
            created = self.supabase.table(self.table_name).insert(data).execute()
            return created.data[0] if created.data else data

        record = await asyncio.to_thread(_get_or_create_sync)
        return self._record_to_model(record)

    def _record_to_model(self, record: Dict[str, Any]) -> T:
        """Convierte un registro de Supabase al modelo correspondiente."""
        return self.model_class(**record)
