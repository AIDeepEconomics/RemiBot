from __future__ import annotations

import json
from typing import Any, Dict, Optional

import httpx


class LLMService:
    """Wrapper para interactuar con los proveedores LLM soportados (Anthropic / OpenAI)."""

    def __init__(
        self,
        *,
        claude_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_model: str = "claude-3-haiku-20240307",
        openai_model: str = "gpt-4o-mini",
        default_system_prompt: Optional[str] = None,
        timeout_seconds: int = 30,
        max_tokens: int = 600,
    ) -> None:
        self.claude_api_key = claude_api_key
        self.openai_api_key = openai_api_key
        self.anthropic_model = anthropic_model
        self.openai_model = openai_model
        self.default_system_prompt = default_system_prompt or "Eres un asistente útil."
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens

    def derive(
        self,
        *,
        claude_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
        anthropic_model: Optional[str] = None,
        openai_model: Optional[str] = None,
    ) -> "LLMService":
        return LLMService(
            claude_api_key=claude_api_key or self.claude_api_key,
            openai_api_key=openai_api_key or self.openai_api_key,
            anthropic_model=anthropic_model or self.anthropic_model,
            openai_model=openai_model or self.openai_model,
            default_system_prompt=system_prompt or self.default_system_prompt,
            timeout_seconds=self.timeout_seconds,
            max_tokens=self.max_tokens,
        )

    async def run_dialogue(
        self,
        prompt: str = None,
        *,
        context: Dict[str, Any] | None = None,
        system_prompt: Optional[str] = None,
        user_message: Optional[str] = None,
        conversation_history: Optional[list] = None,
    ) -> str:
        # Soportar ambos estilos: prompt tradicional o conversación con historial
        if user_message is None and prompt:
            user_message = prompt
        
        if not user_message or not user_message.strip():
            raise ValueError("El mensaje del usuario no puede estar vacío.")

        system_prompt = system_prompt or self.default_system_prompt
        context = context or {}
        conversation_history = conversation_history or []

        if self.claude_api_key:
            return await self._invoke_claude(
                user_message, 
                system_prompt=system_prompt, 
                context=context,
                conversation_history=conversation_history,
            )
        if self.openai_api_key:
            return await self._invoke_openai(
                user_message, 
                system_prompt=system_prompt, 
                context=context,
                conversation_history=conversation_history,
            )

        return (
            "No se encontró ninguna API key configurada para el LLM. Configura CLAUDE_API_KEY o"
            " OPENAI_API_KEY para habilitar las respuestas inteligentes."
        )

    async def _invoke_claude(
        self,
        prompt: str,
        *,
        system_prompt: str,
        context: Dict[str, Any],
        conversation_history: list = None,
    ) -> str:
        conversation_history = conversation_history or []
        
        # Construir mensajes con historial
        messages = []
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })
        
        # Agregar mensaje actual
        composed_prompt = self._compose_prompt(prompt, context) if context else prompt
        messages.append({
            "role": "user",
            "content": composed_prompt,
        })
        
        payload = {
            "model": self.anthropic_model,
            "system": system_prompt,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        contents = data.get("content", [])
        if not contents:
            raise RuntimeError("Respuesta vacía del modelo Claude")

        return contents[0].get("text", "").strip()

    async def _invoke_openai(
        self,
        prompt: str,
        *,
        system_prompt: str,
        context: Dict[str, Any],
        conversation_history: list = None,
    ) -> str:
        conversation_history = conversation_history or []
        
        # Construir mensajes con historial
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })
        
        # Agregar mensaje actual
        composed_prompt = self._compose_prompt(prompt, context) if context else prompt
        messages.append({
            "role": "user",
            "content": composed_prompt,
        })
        
        payload = {
            "model": self.openai_model,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Respuesta vacía del modelo OpenAI")

        return choices[0]["message"]["content"].strip()

    @staticmethod
    def _compose_prompt(prompt: str, context: Dict[str, Any]) -> str:
        if not context:
            return prompt
        context_json = json.dumps(context, ensure_ascii=False, indent=2)
        return f"{prompt}\n\n[Contexto adicional]\n{context_json}"
