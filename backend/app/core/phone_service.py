from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List, Optional

from supabase import Client


class PhoneService:
    """Servicio para gestionar teléfonos de empresa y normalización."""

    def __init__(self, supabase_client: Client) -> None:
        self.supabase = supabase_client

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normaliza un número de teléfono eliminando caracteres no numéricos.
        
        Ejemplos:
        - "+598 99 123 456" → "59899123456"
        - "099 123 456" → "99123456"
        - "(598) 99-123-456" → "59899123456"
        """
        return re.sub(r'[^0-9]', '', phone)

    async def find_empresas_by_phone(self, phone: str) -> List[str]:
        """
        Busca todas las empresas asociadas a un número de teléfono.
        Retorna lista de IDs de empresa.
        """
        normalized = self.normalize_phone(phone)

        def _search_sync() -> List[str]:
            # Buscar por número normalizado
            response = (
                self.supabase.table("telefonos_empresa")
                .select("id_empresa")
                .eq("numero_normalizado", normalized)
                .eq("activo", True)
                .execute()
            )
            
            if response.data:
                return [str(record["id_empresa"]) for record in response.data]
            
            # Si no encuentra, intentar con variaciones
            # Quitar código de país si existe (598 para Uruguay)
            if normalized.startswith("598") and len(normalized) > 3:
                without_country = normalized[3:]
                response = (
                    self.supabase.table("telefonos_empresa")
                    .select("id_empresa")
                    .eq("numero_normalizado", without_country)
                    .eq("activo", True)
                    .execute()
                )
                if response.data:
                    return [str(record["id_empresa"]) for record in response.data]
            
            # Intentar agregando código de país
            with_country = f"598{normalized}"
            response = (
                self.supabase.table("telefonos_empresa")
                .select("id_empresa")
                .eq("numero_normalizado", with_country)
                .eq("activo", True)
                .execute()
            )
            if response.data:
                return [str(record["id_empresa"]) for record in response.data]
            
            return []

        return await asyncio.to_thread(_search_sync)

    async def add_phone_to_empresa(
        self,
        phone: str,
        empresa_id: str,
        notas: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Agrega un número de teléfono a una empresa."""
        
        def _insert_sync() -> Dict[str, Any]:
            data = {
                "numero_telefono": phone,
                "numero_normalizado": self.normalize_phone(phone),
                "id_empresa": empresa_id,
                "activo": True,
                "notas": notas,
            }
            response = self.supabase.table("telefonos_empresa").insert(data).execute()
            return response.data[0] if response.data else data

        return await asyncio.to_thread(_insert_sync)

    async def remove_phone_from_empresa(self, phone_id: str) -> bool:
        """Elimina (desactiva) un número de teléfono."""
        
        def _update_sync() -> bool:
            response = (
                self.supabase.table("telefonos_empresa")
                .update({"activo": False})
                .eq("id", phone_id)
                .execute()
            )
            return bool(response.data)

        return await asyncio.to_thread(_update_sync)

    async def list_phones_by_empresa(self, empresa_id: str) -> List[Dict[str, Any]]:
        """Lista todos los teléfonos de una empresa."""
        
        def _list_sync() -> List[Dict[str, Any]]:
            response = (
                self.supabase.table("telefonos_empresa")
                .select("*")
                .eq("id_empresa", empresa_id)
                .eq("activo", True)
                .order("created_at", desc=True)
                .execute()
            )
            return response.data or []

        return await asyncio.to_thread(_list_sync)
