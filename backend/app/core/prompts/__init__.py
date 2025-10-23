"""Módulo para gestionar prompts del sistema."""

import os
from typing import Optional


def load_system_prompt(prompt_name: str) -> Optional[str]:
    """Carga un prompt del sistema desde archivo."""
    prompt_path = os.path.join(
        os.path.dirname(__file__), 
        "system_prompts", 
        f"{prompt_name}.md"
    )
    
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def load_catalog_template() -> str:
    """Carga la plantilla para mostrar catálogos."""
    return """
═══════════════════════════════════════════════════════════════
CONTEXTO DE EMPRESA AUTORIZADA
═══════════════════════════════════════════════════════════════

Estás trabajando para: {empresa_nombre}
ID de Empresa: {empresa_id}

{establecimientos_text}
{chacras_text}
INSTRUCCIONES IMPORTANTES PARA EL JSON:
- Cuando el usuario mencione un establecimiento, usa el ID correspondiente de la lista
- Cuando mencione una chacra, usa el ID de chacra Y el ID de establecimiento asociado
- Si el usuario menciona un nombre que NO está en las listas, pregúntale para aclarar
- SOLO puedes crear remitos para esta empresa y sus establecimientos/chacras autorizados
- Los IDs son OBLIGATORIOS en el JSON final

═══════════════════════════════════════════════════════════════
"""


def load_multiple_catalog_template() -> str:
    """Carga la plantilla para múltiples empresas."""
    return """
═══════════════════════════════════════════════════════════════
MÚLTIPLES EMPRESAS AUTORIZADAS
═══════════════════════════════════════════════════════════════

Este número está autorizado para trabajar con las siguientes empresas:

{empresas_list}

Pregunta al usuario para cuál empresa desea crear el remito.
Una vez que especifique, usa el contexto de esa empresa.

{contextos_individuales}
"""
