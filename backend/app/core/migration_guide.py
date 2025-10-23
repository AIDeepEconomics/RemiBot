"""
Guía de Migración: De RemitoFlowManagerV2 a RemitoFlowManagerV2Refactored

Este archivo documenta cómo migrar del código antiguo al nuevo usando la arquitectura refacturada.
"""

# ANTES (código antiguo):
# from app.core.remito_flow_v2 import RemitoFlowManagerV2
# 
# manager = RemitoFlowManagerV2(
#     llm_service=llm_service,
#     catalog_service=catalog_service,
#     remito_service=remito_service,
#     conversation_store=conversation_store,
#     log_service=log_service,
#     whatsapp_service=whatsapp_service,
#     config_store=config_store,
#     phone_service=phone_service,
#     empresa_context_service=empresa_context_service,
# )

# DESPUÉS (código nuevo):
# from app.core.remito_flow_v2_refactored import RemitoFlowManagerV2Refactored
# from app.services.conversation_service import ConversationService
# from app.usecases.create_remito_usecase import CreateRemitoUseCase
# 
# # Crear servicios especializados
# conversation_service = ConversationService(
#     llm_service=llm_service,
#     conversation_store=conversation_store,
#     log_service=log_service,
# )
# 
# create_remito_usecase = CreateRemitoUseCase(
#     remito_service=remito_service,
#     catalog_service=catalog_service,
#     qrcode_service=qrcode_service,
#     log_service=log_service,
# )
# 
# # Crear el nuevo manager
# manager = RemitoFlowManagerV2Refactored(
#     conversation_service=conversation_service,
#     create_remito_usecase=create_remito_usecase,
#     llm_service=llm_service,
#     log_service=log_service,
#     empresa_context_service=empresa_context_service,
#     phone_service=phone_service,
#     config_store=config_store,
#     whatsapp_service=whatsapp_service,
# )

# Ventajas de la nueva arquitectura:
# 1. Separación de responsabilidades claras
# 2. Código más testeable
# 3. Menos dependencias por componente
# 4. Validación centralizada
# 5. Prompts externos para fácil modificación
# 6. Repositorios reutilizables

# Pasos para migrar:
# 1. Reemplazar importaciones
# 2. Crear instancias de los nuevos servicios
# 3. Actualizar la configuración de dependencias
# 4. Los métodos públicos (handle_message) mantienen la misma firma
