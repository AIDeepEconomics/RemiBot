from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from supabase import Client


class EmpresaContextService:
    """Servicio para cargar contexto completo de una empresa (establecimientos y chacras)."""

    def __init__(self, supabase_client: Client) -> None:
        self.supabase = supabase_client
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def load_context(self, empresa_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Carga el contexto completo de una empresa: establecimientos y chacras.
        
        Returns:
            {
                "empresa": {...},
                "establecimientos": [...],
                "chacras": [...]
            }
        """
        if use_cache and empresa_id in self._cache:
            return self._cache[empresa_id]

        def _load_sync() -> Dict[str, Any]:
            # Cargar empresa
            empresa_resp = (
                self.supabase.table("empresas")
                .select("*")
                .eq("id_empresa", empresa_id)
                .limit(1)
                .execute()
            )
            empresa = empresa_resp.data[0] if empresa_resp.data else None

            if not empresa:
                return {"empresa": None, "establecimientos": [], "chacras": []}

            # Cargar establecimientos
            est_resp = (
                self.supabase.table("establecimientos")
                .select("*")
                .eq("id_empresa", empresa_id)
                .order("nombre")
                .execute()
            )
            establecimientos = est_resp.data or []

            # Cargar chacras con información de establecimiento
            chacras_resp = (
                self.supabase.table("chacras")
                .select("*, establecimientos(nombre)")
                .eq("id_empresa", empresa_id)
                .order("nombre_chacra")
                .execute()
            )
            chacras = chacras_resp.data or []

            return {
                "empresa": empresa,
                "establecimientos": establecimientos,
                "chacras": chacras,
            }

        context = await asyncio.to_thread(_load_sync)
        
        if use_cache and context["empresa"]:
            self._cache[empresa_id] = context
        
        return context

    async def load_multiple_contexts(self, empresa_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Carga contextos de múltiples empresas (para números en varias empresas)."""
        contexts = {}
        for empresa_id in empresa_ids:
            contexts[empresa_id] = await self.load_context(empresa_id)
        return contexts

    def clear_cache(self, empresa_id: Optional[str] = None) -> None:
        """Limpia el cache de contextos."""
        if empresa_id:
            self._cache.pop(empresa_id, None)
        else:
            self._cache.clear()

    @staticmethod
    def build_catalog_text(context: Dict[str, Any]) -> str:
        """
        Construye el texto del catálogo para agregar al prompt del LLM.
        """
        if not context.get("empresa"):
            return ""

        empresa = context["empresa"]
        establecimientos = context["establecimientos"]
        chacras = context["chacras"]

        catalog = f"""

═══════════════════════════════════════════════════════════════
CONTEXTO DE EMPRESA AUTORIZADA
═══════════════════════════════════════════════════════════════

Estás trabajando para: {empresa['nombre']}
ID de Empresa: {empresa['id_empresa']}

"""

        if establecimientos:
            catalog += "ESTABLECIMIENTOS DISPONIBLES:\n"
            for est in establecimientos:
                catalog += f"  • {est['nombre']} (ID: {est['id_establecimiento']})\n"
            catalog += "\n"
        else:
            catalog += "⚠️  No hay establecimientos registrados para esta empresa.\n\n"

        if chacras:
            catalog += "CHACRAS DISPONIBLES:\n"
            for chacra in chacras:
                est_nombre = chacra.get('establecimientos', {}).get('nombre', 'N/A')
                catalog += f"  • {chacra['nombre_chacra']} (ID: {chacra['id_chacra']})\n"
                catalog += f"    └─ Establecimiento: {est_nombre} (ID: {chacra['id_establecimiento']})\n"
            catalog += "\n"
        else:
            catalog += "⚠️  No hay chacras registradas para esta empresa.\n\n"

        catalog += """INSTRUCCIONES IMPORTANTES PARA EL JSON:
- Cuando el usuario mencione un establecimiento, usa el ID correspondiente de la lista
- Cuando mencione una chacra, usa el ID de chacra Y el ID de establecimiento asociado
- Si el usuario menciona un nombre que NO está en las listas, pregúntale para aclarar
- SOLO puedes crear remitos para esta empresa y sus establecimientos/chacras autorizados
- Los IDs son OBLIGATORIOS en el JSON final

═══════════════════════════════════════════════════════════════
"""

        return catalog

    @staticmethod
    def build_multiple_catalog_text(contexts: Dict[str, Dict[str, Any]]) -> str:
        """Construye catálogo para múltiples empresas."""
        if not contexts:
            return ""

        catalog = "\n═══════════════════════════════════════════════════════════════\n"
        catalog += "MÚLTIPLES EMPRESAS AUTORIZADAS\n"
        catalog += "═══════════════════════════════════════════════════════════════\n\n"
        catalog += "Este número está autorizado para trabajar con las siguientes empresas:\n\n"

        for empresa_id, context in contexts.items():
            if context.get("empresa"):
                empresa = context["empresa"]
                catalog += f"• {empresa['nombre']} (ID: {empresa['id_empresa']})\n"

        catalog += "\nPregunta al usuario para cuál empresa desea crear el remito.\n"
        catalog += "Una vez que especifique, usa el contexto de esa empresa.\n\n"

        # Agregar catálogos individuales
        for context in contexts.values():
            catalog += EmpresaContextService.build_catalog_text(context)

        return catalog
