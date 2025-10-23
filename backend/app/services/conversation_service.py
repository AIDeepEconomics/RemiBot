from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.conversation_store import ConversationStore
from app.core.llm_service import LLMService
from app.core.log_service import LogService
from app.core.prompts import load_system_prompt
from app.services.validation_service import RemitoValidator


class ConversationService:
    """Servicio dedicado a manejar conversaciones de WhatsApp."""

    def __init__(
        self,
        llm_service: LLMService,
        conversation_store: ConversationStore,
        log_service: LogService,
    ) -> None:
        self.llm_service = llm_service
        self.conversation_store = conversation_store
        self.log_service = log_service

    async def process_message(
        self,
        phone: str,
        message: str,
        system_prompt: str,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Procesa un mensaje de WhatsApp.
        
        Returns:
            Tuple de (respuesta_texto, datos_json_opcional)
        """
        # Guardar mensaje del usuario
        self.conversation_store.append(phone, "user", message)

        # Detectar cancelación
        if self._is_cancel_message(message):
            self.conversation_store.clear(phone)
            return "Proceso cancelado. Escribe 'crear remito' cuando quieras empezar de nuevo.", None

        # Obtener historial de conversación
        history = self.conversation_store.get_recent(phone, limit=20)

        # Generar respuesta del LLM
        llm_response = await self.llm_service.run_dialogue(
            system_prompt=system_prompt,
            user_message=message,
            conversation_history=history,
        )

        # Guardar respuesta del asistente
        self.conversation_store.append(phone, "assistant", llm_response)

        # Detectar si la respuesta es JSON
        json_data = self._extract_json(llm_response)

        if json_data:
            # Validar el JSON antes de retornarlo
            validation_result = RemitoValidator.validate_json_remito(json_data)
            if validation_result.is_valid:
                return "", validation_result.normalized_data
            else:
                # Si hay errores de validación, informar al usuario
                error_message = self._build_validation_error_message(validation_result)
                self.conversation_store.append(phone, "assistant", error_message)
                return error_message, None

        return llm_response, None

    def clear_conversation(self, phone: str) -> None:
        """Limpia la conversación para un número específico."""
        self.conversation_store.clear(phone)

    def get_conversation_history(self, phone: str, limit: int = 20) -> List[Dict[str, str]]:
        """Obtiene el historial de conversación para un número."""
        return self.conversation_store.get_recent(phone, limit=limit)

    def _is_cancel_message(self, message: str) -> bool:
        """Detecta si el mensaje es una solicitud de cancelación."""
        cancel_keywords = {
            'cancelar', 'cancel', 'salir', 'stop', 'terminar', 'cerrar',
            'abandonar', 'reiniciar', 'empezar de nuevo', 'nuevo remito'
        }
        
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in cancel_keywords)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrae y valida JSON de una respuesta de texto."""
        # Buscar bloques JSON en el texto
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)
                # Verificar que tenga los campos esperados de un remito
                if isinstance(data, dict) and "nombre_empresa" in data and "peso_estimado_tn" in data:
                    # Limpiar campos que no deben venir del LLM
                    unwanted_fields = [
                        "id_remito", "qr_url", "timestamp_creacion", 
                        "id_chacra", "id_establecimiento", "id_empresa", "id_destino",
                        "estado_remito", "activo", "raw_payload"
                    ]
                    for field in unwanted_fields:
                        data.pop(field, None)
                    
                    return data
            except json.JSONDecodeError:
                continue

        return None

    def _build_validation_error_message(self, validation_result: RemitoValidator.ValidationResult) -> str:
        """Construye un mensaje de error amigable para el usuario."""
        if not validation_result.has_errors:
            return ""

        error_message = "❌ *Error en los datos del remito:*\n\n"
        
        for error in validation_result.errors:
            error_message += f"• {error}\n"
        
        error_message += "\nPor favor, corregí los datos y volvé a intentar."
        
        return error_message

    async def handle_error(self, phone: str, error: str) -> None:
        """Registra un error en el log y limpia la conversación si es necesario."""
        await self.log_service.write_log(
            tipo="ERROR",
            detalle=f"Error en conversación: {error}",
            payload={"contacto": phone, "error": error},
        )
