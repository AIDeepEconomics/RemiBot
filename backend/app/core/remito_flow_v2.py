from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.core.catalog_service import CatalogService
from app.core.conversation_store import ConversationStore
from app.core.llm_service import LLMService
from app.core.log_service import LogService
from app.core.remito_service import RemitoService
from app.core.whatsapp_service import WhatsAppService
from app.models.remito import RemitoCreate
from app.models.webhook import WhatsAppWebhookPayload, WhatsAppWebhookResponse


SYSTEM_PROMPT_BASE = """Eres RemiBOT, un asistente de WhatsApp que ayuda a operarios de arroceras a generar remitos de despacho.

Tu objetivo es recopilar la siguiente información del usuario de forma conversacional y natural:
1. Nombre de la empresa (molino o titular)
2. Nombre del establecimiento
3. Nombre de la chacra de origen
4. Nombre completo del conductor
5. Cédula o documento del conductor (solo números, sin puntos ni guiones, incluyendo dígito verificador)
6. Matrícula del camión
7. Matrícula de la zorra/acoplado (opcional)
8. Peso estimado en toneladas (entre 5 y 40 toneladas)
9. Destino final (molino o planta receptora)

COMPORTAMIENTO CONVERSACIONAL:
- Habla en español rioplatense, tono cordial y directo
- Sé FLEXIBLE: entiende diferentes formas de expresar la misma información
- NO dependas de palabras mágicas o frases específicas
- Si el usuario te da varios datos a la vez, extrae TODOS los que puedas identificar
- Pregunta solo por lo que falta después de analizar cada mensaje
- Cuando tengas TODOS los datos, resume y pide confirmación de forma natural

NORMALIZACIÓN DE DATOS:
- Cédula: extrae solo números, elimina puntos, guiones y espacios. Incluye el dígito verificador (el que va después del guión)
  Ejemplo: "1.234.567-8" → "12345678"
- Peso: si te dan kilos, convierte a toneladas (divide entre 1000)
  Ejemplo: "25000 kilos" → 25.0 toneladas
- Peso: debe estar entre 5 y 40 toneladas. Si está fuera de rango, pide corrección
- Matrícula zorra: si dicen "sin zorra", "no tiene", "ninguna", usa null
- Nombres: acepta cualquier variación (ej: "molino", "empresa", "titular" son lo mismo)

GENERACIÓN DEL JSON:
Cuando el usuario confirme (cualquier forma de confirmación positiva), genera SOLO el JSON sin texto adicional:

{
  "nombre_empresa": "texto",
  "nombre_establecimiento": "texto",
  "nombre_chacra": "texto",
  "nombre_conductor": "texto",
  "cedula_conductor": "solo_numeros_sin_puntos_ni_guiones",
  "matricula_camion": "texto",
  "matricula_zorra": "texto o null si no aplica",
  "peso_estimado_tn": numero_decimal,
  "nombre_destino": "texto"
}

REGLAS ESTRICTAS DEL JSON:
- peso_estimado_tn: DEBE ser un número (float o int), NO string
- cedula_conductor: string con solo números, sin puntos ni guiones
- matricula_zorra: string o null (no "ninguna", "sin zorra", etc.)
- NO incluyas campos adicionales (id_remito, qr_url, timestamp_creacion, etc.)
- El JSON debe ser válido y parseable
- Responde SOLO con el JSON, sin texto antes ni después

El usuario puede escribir "cancelar" en cualquier momento para reiniciar.
"""

# Prompt para números NO registrados
SYSTEM_PROMPT_UNREGISTERED = """Eres RemiBOT, un asistente de WhatsApp para generar remitos de arroz.

SITUACIÓN ACTUAL:
Este número de teléfono NO está registrado en el sistema. Por lo tanto, no puedes crear remitos desde este número.

TU TAREA:
Explica al usuario de forma cordial que:
1. Su número no está autorizado en el sistema RemiBOT
2. Para poder crear remitos, su empresa debe registrar este número
3. Debe contactar al administrador de su empresa para que agregue este número al sistema
4. Una vez registrado, podrá crear remitos sin problemas

TONO:
- Cordial y profesional
- Español rioplatense
- Breve y claro
- Ofrece ayuda pero explica la limitación

NO intentes recopilar información de remitos ni generes JSON.
Solo informa sobre la situación y cómo resolverla.
"""

# Mantener compatibilidad con código existente
SYSTEM_PROMPT = SYSTEM_PROMPT_BASE


class RemitoFlowManagerV2:
    """Gestor de flujo conversacional libre con LLM para creación de remitos."""

    def __init__(
        self,
        *,
        llm_service: LLMService,
        catalog_service: CatalogService,
        remito_service: RemitoService,
        conversation_store: ConversationStore,
        log_service: LogService,
        whatsapp_service: Optional[WhatsAppService] = None,
        config_store: Optional[Any] = None,
        phone_service: Optional[Any] = None,
        empresa_context_service: Optional[Any] = None,
    ) -> None:
        self.llm_service = llm_service
        self.catalog_service = catalog_service
        self.remito_service = remito_service
        self.conversation_store = conversation_store
        self.log_service = log_service
        self.whatsapp_service = whatsapp_service
        self.config_store = config_store
        self.phone_service = phone_service
        self.empresa_context_service = empresa_context_service
        self._cached_prompt: Optional[str] = None
        self._phone_empresa_cache: Dict[str, List[str]] = {}

    async def _get_empresas_for_phone(self, phone: str) -> List[str]:
        """Obtiene lista de IDs de empresa asociadas a un teléfono."""
        if phone in self._phone_empresa_cache:
            return self._phone_empresa_cache[phone]
        
        if not self.phone_service:
            return []
        
        empresa_ids = await self.phone_service.find_empresas_by_phone(phone)
        self._phone_empresa_cache[phone] = empresa_ids
        return empresa_ids

    async def _build_prompt_for_phone(self, phone: str) -> str:
        """Construye el prompt personalizado según el teléfono del usuario."""
        # Obtener prompt base desde configuración
        base_prompt = SYSTEM_PROMPT_BASE
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
            return SYSTEM_PROMPT_UNREGISTERED
        
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

    async def handle_message(self, payload: WhatsAppWebhookPayload) -> WhatsAppWebhookResponse:
        """Procesa un mensaje de WhatsApp y genera respuesta."""
        contact = payload.from_number
        incoming = payload.body.strip()

        # Guardar mensaje del usuario
        self.conversation_store.append(contact, "user", incoming)

        # Detectar cancelación
        if incoming.lower() in {"cancelar", "cancel", "salir", "stop"}:
            self.conversation_store.clear(contact)
            return WhatsAppWebhookResponse(
                reply="Proceso cancelado. Escribe 'crear remito' cuando quieras empezar de nuevo.",
                metadata={"status": "cancelled"},
            )

        # Obtener historial de conversación
        history = self.conversation_store.get_recent(contact, limit=20)

        # Construir prompt personalizado según el teléfono
        system_prompt = await self._build_prompt_for_phone(contact)

        # Generar respuesta del LLM
        llm_response = await self.llm_service.run_dialogue(
            system_prompt=system_prompt,
            user_message=incoming,
            conversation_history=history,
        )

        # Detectar si la respuesta es JSON
        json_data = self._extract_json(llm_response)

        if json_data:
            # Flujo alternativo: crear remito en Supabase y enviar QR por WhatsApp
            return await self._handle_json_response(contact, json_data, incoming)
        else:
            # Flujo normal: enviar respuesta por WhatsApp
            self.conversation_store.append(contact, "assistant", llm_response)
            
            # Enviar mensaje por WhatsApp
            if self.whatsapp_service:
                try:
                    await self.whatsapp_service.send_text(to=contact, text=llm_response)
                except Exception as e:
                    await self.log_service.write_log(
                        tipo="ERROR",
                        detalle=f"Error enviando mensaje por WhatsApp: {str(e)}",
                        payload={"contacto": contact, "error": str(e)},
                    )
            
            return WhatsAppWebhookResponse(
                reply=llm_response,
                metadata={"status": "conversation"},
            )

    async def _handle_json_response(
        self,
        contact: str,
        json_data: Dict[str, Any],
        original_message: str,
    ) -> WhatsAppWebhookResponse:
        """Procesa una respuesta JSON del LLM: crea remito y envía QR."""
        try:
            # Validar que solo tenga los campos esperados del LLM
            expected_fields = {
                "nombre_empresa",
                "nombre_establecimiento",
                "nombre_chacra",
                "nombre_conductor",
                "cedula_conductor",
                "matricula_camion",
                "matricula_zorra",
                "peso_estimado_tn",
                "nombre_destino",
            }
            
            # Validar datos requeridos (todos excepto matricula_zorra)
            required_fields = expected_fields - {"matricula_zorra"}

            for field in required_fields:
                if field not in json_data or json_data[field] is None:
                    raise ValueError(f"Campo requerido faltante: {field}")

            # Crear entidades en catálogo
            empresa = await self.catalog_service.get_or_create_empresa(json_data["nombre_empresa"])
            establecimiento = await self.catalog_service.get_or_create_establecimiento(
                json_data["nombre_establecimiento"], empresa["id_empresa"]
            )
            chacra = await self.catalog_service.get_or_create_chacra(
                json_data["nombre_chacra"],
                establecimiento["id_establecimiento"],
                empresa["id_empresa"],
            )
            destino = await self.catalog_service.get_or_create_destino(json_data["nombre_destino"])

            # Crear payload del remito
            remito_payload = RemitoCreate(
                id_chacra=chacra["id_chacra"],
                nombre_chacra=json_data["nombre_chacra"],
                id_establecimiento=establecimiento["id_establecimiento"],
                nombre_establecimiento=json_data["nombre_establecimiento"],
                id_empresa=empresa["id_empresa"],
                nombre_empresa=json_data["nombre_empresa"],
                id_destino=destino["id_destino"],
                nombre_destino=json_data["nombre_destino"],
                nombre_conductor=json_data["nombre_conductor"],
                cedula_conductor=json_data["cedula_conductor"],
                matricula_camion=json_data["matricula_camion"],
                matricula_zorra=json_data.get("matricula_zorra"),
                peso_estimado_tn=float(json_data["peso_estimado_tn"]),
                raw_payload={**json_data, "contacto": contact},
            )

            # Crear remito en Supabase (incluye generación de QR)
            remito = await self.remito_service.create_remito(remito_payload)

            # Registrar log
            await self.log_service.write_log(
                tipo="REMITO",
                detalle=f"Remito {remito.id_remito} creado desde WhatsApp (flujo LLM libre)",
                payload={"id_remito": remito.id_remito, "contacto": contact},
            )

            # Enviar QR por WhatsApp (si el servicio está disponible)
            if self.whatsapp_service and remito.qr_url:
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

            # Limpiar conversación
            self.conversation_store.clear(contact)

            # Respuesta de confirmación (no se envía por WhatsApp, solo metadata)
            return WhatsAppWebhookResponse(
                reply="",  # Vacío porque ya enviamos la imagen
                metadata={
                    "status": "created",
                    "id_remito": remito.id_remito,
                    "qr_url": remito.qr_url,
                    "image_sent": self.whatsapp_service is not None,
                },
            )

        except Exception as e:
            # Error al procesar JSON
            await self.log_service.write_log(
                tipo="ERROR",
                detalle=f"Error procesando JSON del LLM: {str(e)}",
                payload={"contacto": contact, "json_data": json_data, "error": str(e)},
            )

            error_message = (
                f"❌ Hubo un error al generar el remito: {str(e)}\n\n"
                "Por favor, intenta nuevamente o escribe 'cancelar' para reiniciar."
            )

            self.conversation_store.append(contact, "assistant", error_message)

            return WhatsAppWebhookResponse(
                reply=error_message,
                metadata={"status": "error", "error": str(e)},
            )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrae y valida JSON de una respuesta de texto."""
        # Buscar bloques JSON en el texto
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)
                # Verificar que tenga los campos esperados de un remito (mínimo empresa y peso)
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
