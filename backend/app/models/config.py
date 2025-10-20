from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, SecretStr


class AppConfig(BaseModel):
    whatsapp_api_key: Optional[SecretStr] = Field(None, description="Meta WhatsApp Cloud API token")
    gpt_api_key: Optional[SecretStr] = Field(None, description="OpenAI API key")
    claude_api_key: Optional[SecretStr] = Field(None, description="Anthropic Claude API key")
    llm_prompt: Optional[str] = Field(None, description="Prompt plantilla para el bot")
    auth_password_hash: Optional[str] = Field(
        None, description="Hash de la contraseña para acceder al panel"
    )


class AppConfigUpdate(AppConfig):
    pass
