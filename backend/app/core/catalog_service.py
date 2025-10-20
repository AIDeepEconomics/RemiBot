from __future__ import annotations

import asyncio
from typing import Any, Dict

from supabase import Client


class CatalogService:
    """Acceso simplificado a catálogos (empresas, establecimientos, chacras, destinos)."""

    def __init__(self, supabase_client: Client) -> None:
        self.supabase = supabase_client

    async def get_or_create_empresa(self, nombre: str) -> Dict[str, Any]:
        nombre = self._normalize(nombre)
        if not nombre:
            raise ValueError("El nombre de la empresa no puede estar vacío")

        def _sync() -> Dict[str, Any]:
            response = (
                self.supabase.table("empresas")
                .select("*")
                .eq("nombre", nombre)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]
            created = self.supabase.table("empresas").insert({"nombre": nombre}).execute()
            return created.data[0]

        return await asyncio.to_thread(_sync)

    async def get_or_create_establecimiento(self, nombre: str, empresa_id: str) -> Dict[str, Any]:
        nombre = self._normalize(nombre)
        if not nombre:
            raise ValueError("El nombre del establecimiento no puede estar vacío")

        def _sync() -> Dict[str, Any]:
            response = (
                self.supabase.table("establecimientos")
                .select("*")
                .eq("nombre", nombre)
                .eq("id_empresa", empresa_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]
            created = (
                self.supabase.table("establecimientos")
                .insert({"nombre": nombre, "id_empresa": empresa_id})
                .execute()
            )
            return created.data[0]

        return await asyncio.to_thread(_sync)

    async def get_or_create_chacra(
        self,
        nombre_chacra: str,
        establecimiento_id: str,
        empresa_id: str,
    ) -> Dict[str, Any]:
        nombre_chacra = self._normalize(nombre_chacra)
        if not nombre_chacra:
            raise ValueError("El nombre de la chacra no puede estar vacío")

        def _sync() -> Dict[str, Any]:
            response = (
                self.supabase.table("chacras")
                .select("*")
                .eq("nombre_chacra", nombre_chacra)
                .eq("id_establecimiento", establecimiento_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]
            created = (
                self.supabase.table("chacras")
                .insert(
                    {
                        "nombre_chacra": nombre_chacra,
                        "id_establecimiento": establecimiento_id,
                        "id_empresa": empresa_id,
                    }
                )
                .execute()
            )
            return created.data[0]

        return await asyncio.to_thread(_sync)

    async def get_or_create_destino(self, nombre: str) -> Dict[str, Any]:
        nombre = self._normalize(nombre)
        if not nombre:
            raise ValueError("El nombre del destino no puede estar vacío")

        def _sync() -> Dict[str, Any]:
            response = (
                self.supabase.table("destinos")
                .select("*")
                .eq("nombre", nombre)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]
            created = self.supabase.table("destinos").insert({"nombre": nombre}).execute()
            return created.data[0]

        return await asyncio.to_thread(_sync)

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip()
