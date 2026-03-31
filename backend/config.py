from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    anthropic_api_key: str = ""

    @field_validator("anthropic_api_key", mode="before")
    @classmethod
    def strip_api_key(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v
    claude_model: str = "claude-haiku-4-5-20251001"

    # Scheduling
    calendly_api_key: str = ""
    calendly_user_uri: str = ""

    # Email
    sendgrid_api_key: str = ""
    from_email: str = ""
    from_name: str = "Agente de Ventas"

    # Widget
    widget_allowed_origins: str = "*"

    # Admin Auth
    secret_key: str = "dev-secret-key-change-in-production"
    admin_username: str = "admin"
    admin_password: str = "admin"

    # Coach access
    coach_password: str = ""  # Empty = no password required
    coach_daily_limit: int = 30  # Max messages per student per day (0 = unlimited)

    # Agent Persona
    agent_name: str = "Alex"
    agent_business_name: str = "Nuestra Empresa"
    agent_welcome_message: str = "¡Hola! Soy Alex, ¿en qué puedo ayudarte hoy?"
    collect_lead_after_messages: int = 2

    # App
    env: str = "development"
    port: int = 8000

    @property
    def allowed_origins(self) -> List[str]:
        if self.widget_allowed_origins == "*":
            return ["*"]
        return [o.strip() for o in self.widget_allowed_origins.split(",")]


settings = Settings()
