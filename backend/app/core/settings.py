from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from app.core.catalog_service import CatalogService
from app.core.config_store import ConfigStore
from app.core.conversation_store import ConversationStore
from app.core.empresa_context_service import EmpresaContextService
from app.core.llm_service import LLMService
from app.core.log_service import LogService
from app.core.phone_service import PhoneService
from app.core.qrcode_service import QRCodeService
from app.core.remito_flow_v2 import RemitoFlowManagerV2
from app.core.remito_flow_v2_refactored import RemitoFlowManagerV2Refactored
from app.core.remito_service import RemitoService
from app.core.supabase_client import build_supabase_client
from app.core.whatsapp_service import WhatsAppService


class Settings(BaseSettings):
    environment: str = Field("development", alias="ENVIRONMENT")
    frontend_url: str = Field("http://localhost:5173", alias="FRONTEND_URL")

    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str | None = Field(None, alias="SUPABASE_ANON_KEY")

    claude_api_key: str | None = Field(None, alias="CLAUDE_API_KEY")
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    llm_prompt: str | None = Field(None, alias="LLM_PROMPT")

    whatsapp_token: str | None = Field(None, alias="WHATSAPP_TOKEN")
    whatsapp_phone_id: str | None = Field(None, alias="WHATSAPP_PHONE_ID")
    whatsapp_api_version: str = Field("v18.0", alias="WHATSAPP_API_VERSION")
    whatsapp_verify_token: str = Field("remibot_verify_2025", alias="WHATSAPP_VERIFY_TOKEN")

    # Servicios inicializados en __init__
    supabase_service_client: Any = None
    supabase_anon_client: Any = None
    qrcode_service: Any = None
    llm_service: Any = None
    conversation_store: Any = None
    log_service: Any = None
    config_store: Any = None
    remito_service: Any = None
    catalog_service: Any = None
    whatsapp_service: Any = None
    phone_service: Any = None
    empresa_context_service: Any = None
    remito_flow_v2: Any = None
    remito_flow_v2_refactored: Any = None

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    def __init__(self, **values):
        super().__init__(**values)
        supabase_manager = build_supabase_client(
            url=self.supabase_url,
            service_role_key=self.supabase_service_role_key,
            anon_key=self.supabase_anon_key,
        )
        self.supabase_service_client = supabase_manager.service_client
        self.supabase_anon_client = supabase_manager.anon_client

        self.qrcode_service = QRCodeService(self.supabase_service_client)
        self.llm_service = LLMService(
            claude_api_key=self.claude_api_key,
            openai_api_key=self.openai_api_key,
            default_system_prompt=self.llm_prompt,
        )
        self.conversation_store = ConversationStore()

        self.log_service = LogService(self.supabase_service_client)

        self.config_store = ConfigStore(
            supabase=self.supabase_service_client,
            log_service=self.log_service,
        )
        self.remito_service = RemitoService(
            supabase_client=self.supabase_service_client,
            qrcode_service=self.qrcode_service,
            log_service=self.log_service,
        )
        self.catalog_service = CatalogService(self.supabase_service_client)
        
        # Phone service (gestión de teléfonos por empresa)
        self.phone_service = PhoneService(self.supabase_service_client)
        
        # Empresa context service (catálogos personalizados)
        self.empresa_context_service = EmpresaContextService(self.supabase_service_client)
        
        # WhatsApp service (opcional)
        self.whatsapp_service = None
        if self.whatsapp_token and self.whatsapp_phone_id:
            self.whatsapp_service = WhatsAppService(
                phone_id=self.whatsapp_phone_id,
                access_token=self.whatsapp_token,
                api_version=self.whatsapp_api_version,
            )
        
        # Importar servicios del nuevo sistema
        from app.services.conversation_service import ConversationService
        from app.usecases.create_remito_usecase import CreateRemitoUseCase
        
        # Flujo conversacional V2 (antiguo - mantenido para compatibilidad)
        self.remito_flow_v2 = RemitoFlowManagerV2(
            llm_service=self.llm_service,
            catalog_service=self.catalog_service,
            remito_service=self.remito_service,
            conversation_store=self.conversation_store,
            log_service=self.log_service,
            whatsapp_service=self.whatsapp_service,
            config_store=self.config_store,
            phone_service=self.phone_service,
            empresa_context_service=self.empresa_context_service,
        )
        
        # Nuevo sistema refacturado
        conversation_service = ConversationService(
            llm_service=self.llm_service,
            conversation_store=self.conversation_store,
            log_service=self.log_service,
        )
        
        create_remito_usecase = CreateRemitoUseCase(
            remito_service=self.remito_service,
            catalog_service=self.catalog_service,
            qrcode_service=self.qrcode_service,
            log_service=self.log_service,
        )
        
        self.remito_flow_v2_refactored = RemitoFlowManagerV2Refactored(
            conversation_service=conversation_service,
            create_remito_usecase=create_remito_usecase,
            llm_service=self.llm_service,
            log_service=self.log_service,
            empresa_context_service=self.empresa_context_service,
            whatsapp_service=self.whatsapp_service,
            config_store=self.config_store,
            phone_service=self.phone_service,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
