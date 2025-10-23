"""
Archivo de compatibilidad para la refactorización.
Este archivo asegura que el nuevo sistema funcione con el código existente.
"""

# Importar todos los componentes del nuevo sistema
from app.services.validation_service import RemitoValidator, ValidationResult
from app.services.conversation_service import ConversationService
from app.usecases.create_remito_usecase import CreateRemitoUseCase
from app.core.remito_flow_v2_refactored import RemitoFlowManagerV2Refactored

# Mantener compatibilidad con imports antiguos
__all__ = [
    'RemitoValidator',
    'ValidationResult', 
    'ConversationService',
    'CreateRemitoUseCase',
    'RemitoFlowManagerV2Refactored',
]
