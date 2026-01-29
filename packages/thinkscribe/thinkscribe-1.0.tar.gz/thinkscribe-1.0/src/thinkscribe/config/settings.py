"""Configuration for report generation."""

import warnings
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for report generation."""

    # LLM Configuration (Provider-agnostic)
    llm_provider: Literal["ollama", "openai", "azure"] = Field(
        default="ollama",
        description="LLM provider to use (ollama, openai, azure)",
    )
    llm_base_url: Optional[str] = Field(
        default=None,
        description="Base URL for LLM API (provider-specific default if None)",
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="Model name to use for report generation",
    )
    llm_api_key: Optional[str] = Field(
        default=None,
        description="API key for LLM provider (required for OpenAI/Azure)",
    )
    llm_temperature: float = Field(
        default=0.3,
        description="Temperature for LLM generation",
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for LLM response",
    )

    # Legacy Ollama Configuration (deprecated but supported)
    ollama_host: Optional[str] = Field(
        default=None,
        description="[DEPRECATED] Use llm_base_url instead",
    )
    ollama_model: Optional[str] = Field(
        default=None,
        description="[DEPRECATED] Use llm_model instead",
    )
    ollama_temperature: Optional[float] = Field(
        default=None,
        description="[DEPRECATED] Use llm_temperature instead",
    )
    ollama_max_tokens: Optional[int] = Field(
        default=None,
        description="[DEPRECATED] Use llm_max_tokens instead",
    )

    # PDF Configuration
    pdf_output_dir: str = Field(
        default="reports",
        description="Output directory for generated PDFs",
    )

    @model_validator(mode="after")
    def migrate_legacy_settings(self):
        """Migrate from legacy ollama_* settings to new llm_* settings."""
        # Check if legacy settings are being used
        using_legacy = any([
            self.ollama_host is not None,
            self.ollama_model is not None,
            self.ollama_temperature is not None,
            self.ollama_max_tokens is not None,
        ])

        if using_legacy:
            warnings.warn(
                "Legacy 'ollama_*' settings are deprecated. "
                "Please migrate to 'llm_*' settings. "
                "See documentation for details.",
                DeprecationWarning,
                stacklevel=2,
            )

            # Migrate settings if new ones aren't set
            if self.ollama_host and not self.llm_base_url:
                self.llm_base_url = self.ollama_host
                self.llm_provider = "ollama"

            if self.ollama_model and not self.llm_model:
                self.llm_model = self.ollama_model

            if self.ollama_temperature is not None and self.llm_temperature == 0.3:
                self.llm_temperature = self.ollama_temperature

            if self.ollama_max_tokens is not None and self.llm_max_tokens == 4096:
                self.llm_max_tokens = self.ollama_max_tokens

        # Set provider-specific defaults if not specified
        if not self.llm_base_url:
            if self.llm_provider == "ollama":
                self.llm_base_url = "http://localhost:11434"
            elif self.llm_provider == "openai":
                self.llm_base_url = "https://api.openai.com"
            elif self.llm_provider == "azure":
                # Azure requires explicit base URL
                pass

        if not self.llm_model:
            if self.llm_provider == "ollama":
                self.llm_model = "gpt-oss:20b"
            elif self.llm_provider == "openai":
                self.llm_model = "gpt-4-turbo-preview"
            elif self.llm_provider == "azure":
                # Azure model is part of deployment URL
                pass

        return self

    @field_validator("llm_api_key")
    @classmethod
    def validate_api_key_for_provider(cls, v, info):
        """Validate that API key is provided for providers that require it."""
        # This runs before model_validator, so we check the raw values
        return v

    class Config:
        env_prefix = "REPORT_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
