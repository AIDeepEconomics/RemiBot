from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config_store import ConfigStore
from app.core.empresa_context_service import EmpresaContextService
from app.core.llm_service import LLMService
from app.core.log_service import LogService
from app.core.phone_service import PhoneService
from app.core.prompts import load_system_prompt
from app.models.webhook import WhatsAppWebhookPayload, WhatsAppWebhookResponse
from app.services.conversation_service import ConversationService
from app.usecases.create_remito_usecase import CreateRemitoUseCase


class RemitoFlowManagerV2Refactored:
    """Gestor de flujo conversacional refacturado usando nuevos servicios."""

    def __init__(
        self,
        *,
        conversation_service: ConversationService,
        create_remito_usecase: CreateRemitoUseCase,
        llm_service: LLMService,
        log_service: LogService,
        empresa_context_service: EmpresaContextService,
        phone_service: Optional[PhoneService] = None,
        config_store: Optional[ConfigStore] = None,
        whatsapp_service: Optional[Any] = None,
    ) -> None:
        self.conversation_service = conversation_service
        self.create_remito_usecase = create_remito_usecase
        self.llm_service = llm_service
        self.log_service = log_service
        self.empresa_context_service = empresa_context_service
        self.phone_service = phone_service
        self.config_store = config_store
        self.whatsapp_service = whatsapp_service
        self._phone_empresa_cache: Dict[str, List[str]] = {}

    async def handle_message(self, payload: WhatsAppWebhookPayload) -> WhatsAppWebhookResponse:
        """Procesa un mensaje de WhatsApp y genera respuesta."""
        contact = payload.from_number
        incoming = payload.body.strip()

        try:
            # Construir prompt personalizado según el teléfono
            system_prompt = await self._build_prompt_for_phone(contact)

            # Procesar mensaje con el servicio de conversación
            response_text, json_data = await self.conversation_service.process_message(
                phone=contact,
                message=incoming,
                system_prompt=system_prompt,
            )

            if json_data:
                # Crear remito usando el caso de uso
                return await self._handle_remito_creation(contact, json_data)
            else:
                # Enviar respuesta por WhatsApp si hay servicio disponible
                if self.whatsapp_service and response_text:
                    try:
                        await self.whatsapp_service.send_text(
                            to=contact, 
                            text=response_text
                        )
                    except Exception as e:
                        await self.log_service.write_log(
                            tipo="ERROR",
                            detalle=f"Error enviando mensaje por WhatsApp: {str(e)}",
                            payload={"contacto": contact, "error": str(e)},
                        )

                return WhatsAppWebhookResponse(
                    reply=response_text,
                    metadata={"status": "conversation"},
                )

        except Exception as e:
            # Manejo centralizado de errores
            await self.log_service.write_log(
                tipo="ERROR",
                detalle=f"Error procesando mensaje: {str(e)}",
                payload={"contacto": contact, "mensaje": incoming, "error": str(e)},
            )

            error_message = (
                f"❌ Hubo un error procesando tu mensaje. Por favor, intentá nuevamente.\n\n"
                f"Error: {str(e)}"
            )

            return WhatsAppWebhookResponse(
                reply=error_message,
                metadata={"status": "error", "error": str(e)},
            )

    async def _build_prompt_for_phone(self, phone: str) -> str:
        """Construye el prompt personalizado según el teléfono del usuario."""
        # Obtener prompt base desde configuración o usar el default
        base_prompt = load_system_prompt("registered_user")
        if self.config_store:
            try:
                config = await self.config_store.read()
                if config.llm_prompt:
                    base_prompt = config.llm_prompt
            except Exception:
                pass

        # Buscar empresas asociadas al teléfono
        empresa_ids = await self._get_empresas_for_phone(phone)
        
        # Si no hay empresas, usar prompt de no registrado
        if not empresa_ids:
            return load_system_prompt("unregistered_user")

        # Si no hay servicio de contexto, usar prompt base
        if not self.empresa_context_service:
            return base_prompt

        # Cargar contexto de empresa(s)
        if len(empresa_ids) == 1:
            # Una sola empresa: agregar su catálogo
            context = await self.empresa_context_service.load_context(empresa_ids[0])
            catalog_text = self.empresa_context_service.build_catalog_text(context)
            return base_prompt + catalog_text
        else:
            # Múltiples empresas: agregar todos los catálogos
            contexts = await self.empresa_context_service.load_multiple_contexts(empresa_ids)
            catalog_text = self.empresa_context_service.build_multiple_catalog_text(contexts)
            return base_prompt + catalog_text

    async def _get_empresas_for_phone(self, phone: str) -> List[str]:
        """Obtiene lista de IDs de empresa asociadas a un teléfono."""
        if phone in self._phone_empresa_cache:
            return self._phone_empresa_cache[phone]
        
        if not self.phone_service:
            return []
        
        empresa_ids = await self.phone_service.find_empresas_by_phone(phone)
        self._phone_empresa_cache[phone] = empresa_ids
        return empresa_ids

    async def _handle_remito_creation(
        self,
        contact: str,
        remito_data: Dict[str, Any],
    ) -> WhatsAppWebhookResponse:
        """Maneja la creación de un remito."""
        try:
            # Crear remito usando el caso de uso
            remito = await self.create_remito_usecase.execute(
                remito_data=remito_data,
                contact=contact,
            )

            # Limpiar conversación
            self.conversation_service.clear_conversation(contact)

            # Enviar QR por WhatsApp si está disponible
            if self.whatsapp_service and remito.qr_url:
                try:
                    await self.whatsapp_service.send_image(
                        to=contact,
                        image_url=remito.qr_url,
                        caption=f"✅ Remito generado exitosamente\n\n"
                        f"📋 ID: {remito.id_remito}\n"
                        f"🏢 {remito.nombre_establecimiento} - {remito.nombre_chacra}\n"
                        f"🚛 {remito.matricula_camion}\n"
                        f"👤 {remito.nombre_conductor}\n"
                        f"📍 Destino: {remito.nombre_destino}",
                    )
                except Exception as e:
                    await self.log_service.write_log(
                        tipo="ERROR",
                        detalle=f"Error enviando QR por WhatsApp: {str(e)}",
                        payload={"contacto": contact, "error": str(e)},
                    )

            # Respuesta de confirmación
            return WhatsAppWebhookResponse(
                reply="",  # Vacío porque ya enviamos la imagen
                metadata={
                    "status": "created",
                    "id_remito": remito.id_remito,
                    "qr_url": remito.qr_url,
                    "image_sent": str(self.whatsapp_service is not None),
                },
            )

        except Exception as e:
            # Error al crear remito
            await self.log_service.write_log(
                tipo="ERROR",
                detalle=f"Error creando remito: {str(e)}",
                payload={"contacto": contact, "data": remito_data, "error": str(e)},
            )

            error_message = (
                f"❌ Hubo un error al generar el remito: {str(e)}\n\n"
                "Por favor, intenta nuevamente o escribe 'cancelar' para reiniciar."
            )

            return WhatsAppWebhookResponse(
                reply=error_message,
                metadata={"status": "error", "error": str(e)},
            )

    def clear_cache(self, phone: Optional[str] = None) -> None:
        """Limpia el caché de empresas por teléfono."""
        if phone:
            self._phone_empresa_cache.pop(phone, None)
        else:
            self._phone_empresa_cache.clear()
