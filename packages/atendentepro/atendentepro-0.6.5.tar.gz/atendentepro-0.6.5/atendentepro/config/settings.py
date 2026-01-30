# -*- coding: utf-8 -*-
"""
AtendentePro Configuration Settings.

This module provides centralized configuration management for the AtendentePro library.
It supports both OpenAI and Azure OpenAI providers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AtendentProConfig:
    """Main configuration class for AtendentePro."""
    
    # Provider configuration
    provider: Literal["openai", "azure"] = "openai"
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    
    # Azure OpenAI settings
    azure_api_key: Optional[str] = None
    azure_api_endpoint: Optional[str] = None
    azure_api_version: Optional[str] = None
    azure_deployment_name: Optional[str] = None
    
    # Model settings
    default_model: str = "gpt-4.1"
    
    # OCR settings (optional)
    ocr_enabled: bool = True
    azure_ai_vision_endpoint: Optional[str] = None
    azure_ai_vision_key: Optional[str] = None
    
    # Tracing settings
    application_insights_connection_string: Optional[str] = None
    
    # Templates settings
    templates_root: Optional[Path] = None
    default_client: str = "standard"
    
    # Context output directory
    context_output_dir: str = "context"
    
    @classmethod
    def from_env(cls) -> "AtendentProConfig":
        """Create configuration from environment variables."""
        # Determine provider
        provider_env = (os.getenv("OPENAI_PROVIDER") or "").strip().lower()
        azure_api_key = os.getenv("AZURE_API_KEY")
        azure_api_endpoint = os.getenv("AZURE_API_ENDPOINT") or os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if provider_env:
            provider: Literal["openai", "azure"] = "azure" if provider_env == "azure" else "openai"
        else:
            provider = "azure" if azure_api_key and azure_api_endpoint else "openai"
        
        return cls(
            provider=provider,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            azure_api_key=azure_api_key,
            azure_api_endpoint=azure_api_endpoint,
            azure_api_version=os.getenv("AZURE_API_VERSION") or os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
            default_model=os.getenv("DEFAULT_MODEL", "gpt-4.1"),
            ocr_enabled=os.getenv("OCR_ENABLED", "true").lower() == "true",
            azure_ai_vision_endpoint=os.getenv("AZURE_AI_VISION_ENDPOINT"),
            azure_ai_vision_key=os.getenv("AZURE_AI_VISION_KEY"),
            application_insights_connection_string=os.getenv("APPLICATION_INSIGHTS_CONNECTION_STRING"),
            context_output_dir=os.getenv("CONTEXT_OUTPUT_DIR", "context"),
        )


# Global configuration instance
_config: Optional[AtendentProConfig] = None


def get_config() -> AtendentProConfig:
    """Get the current configuration, initializing from environment if needed."""
    global _config
    if _config is None:
        _config = AtendentProConfig.from_env()
    return _config


def configure(config: Optional[AtendentProConfig] = None, **kwargs) -> AtendentProConfig:
    """
    Configure the AtendentePro library.
    
    Args:
        config: Optional pre-built configuration object
        **kwargs: Configuration parameters to override
        
    Returns:
        The active configuration object
    """
    global _config
    
    if config is not None:
        _config = config
    elif kwargs:
        current = get_config()
        for key, value in kwargs.items():
            if hasattr(current, key):
                setattr(current, key, value)
    
    return get_config()


# Default model
DEFAULT_MODEL = "gpt-4.1"

# Recommended prompt prefix for all agents
RECOMMENDED_PROMPT_PREFIX = """
[CONTEXT SYSTEM]
- Você faz parte de um sistema multiagente chamado Agents SDK, criado para facilitar a coordenação e execução de agentes.
- O Agents SDK utiliza duas principais abstrações: **Agentes** e **Handoffs** (transferências).
- Um agente abrange instruções e ferramentas e pode transferir uma conversa para outro agente quando apropriado.
- Transferências entre agentes são realizadas chamando uma função de transferência, geralmente nomeada como `transfer_to_<nome_do_agente>`.
- As transferências entre agentes ocorrem de forma transparente em segundo plano; não mencione nem chame atenção para essas transferências na sua conversa com o usuário.
- Produza respostas naturais, evitando termos como "transferindo para...", "análise concluída", "aqui está a situação" ou qualquer indicação de lógica interna.
"""

