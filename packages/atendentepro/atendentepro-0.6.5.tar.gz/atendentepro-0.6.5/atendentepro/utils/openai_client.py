# -*- coding: utf-8 -*-
"""
OpenAI Client utilities for AtendentePro.

Provides unified access to both OpenAI and Azure OpenAI clients.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal, Union

from atendentepro.config import get_config


def _disable_azure_tracing() -> None:
    """Disable tracing for Azure OpenAI to avoid compatibility issues."""
    _disable_flags = {
        "OPENAI_TRACE_DISABLED": "true",
        "OPENAI_TRACING_DISABLED": "true",
        "OPENAI_TELEMETRY_DISABLED": "true",
        "OPENAI_TRACE": "false",
        "OPENAI_TELEMETRY": "false",
        "OPENAI_TRACE_ENABLED": "false",
        "OPENAI_TRACING_ENABLED": "false",
        "OPENAI_TELEMETRY_ENABLED": "false",
        "OPENAI_DISABLE_TRACING": "true",
        "OPENAI_DISABLE_TELEMETRY": "true",
        "AGENTS_TRACE_DISABLED": "true",
        "OPENAI_AGENTS_TRACE_DISABLED": "true",
    }
    for key, value in _disable_flags.items():
        os.environ.setdefault(key, value)


# Apply tracing disable for Azure if configured
config = get_config()
if config.provider == "azure":
    _disable_azure_tracing()


from openai import AsyncAzureOpenAI, AsyncOpenAI

# Try to disable tracing via SDK
try:
    from openai import traces as _openai_traces

    if hasattr(_openai_traces, "configure"):
        _openai_traces.configure(enabled=False)
    elif hasattr(_openai_traces, "set_enabled"):
        _openai_traces.set_enabled(False)
    elif hasattr(_openai_traces, "disable"):
        _openai_traces.disable()
except Exception:
    pass

# Disable tracing modules
for _trace_module in (
    "agents.tracing",
    "agents.trace",
    "openai.agents.tracing",
    "openai.agents.trace",
):
    try:
        _mod = __import__(_trace_module, fromlist=["dummy"])
    except Exception:
        continue
    for attr in ("set_tracing_client", "configure", "set_enabled", "disable"):
        func = getattr(_mod, attr, None)
        try:
            if callable(func):
                if attr == "set_tracing_client":
                    func(None)
                elif attr == "configure":
                    func(enabled=False)
                else:
                    func(False)
        except Exception:
            pass


Provider = Literal["azure", "openai"]
AsyncClient = Union[AsyncAzureOpenAI, AsyncOpenAI]


def get_provider() -> Provider:
    """Return the configured provider."""
    config = get_config()
    if config.provider not in ("azure", "openai"):
        return "openai"
    return config.provider


@lru_cache(maxsize=1)
def get_async_client() -> AsyncClient:
    """
    Instantiate and cache the async OpenAI-compatible client.
    
    Returns:
        AsyncOpenAI or AsyncAzureOpenAI client based on configuration.
        
    Raises:
        RuntimeError: If required credentials are missing.
    """
    config = get_config()
    provider = get_provider()

    if provider == "azure":
        required = {
            "AZURE_API_KEY": config.azure_api_key,
            "AZURE_API_ENDPOINT": config.azure_api_endpoint,
            "AZURE_API_VERSION": config.azure_api_version,
        }
        missing = [name for name, value in required.items() if not value]

        if missing:
            names = ", ".join(missing)
            raise RuntimeError(f"Credenciais Azure OpenAI ausentes: {names}")

        client = AsyncAzureOpenAI(
            api_key=config.azure_api_key,
            azure_endpoint=config.azure_api_endpoint,
            api_version=config.azure_api_version,
        )

        # Configure default deployment if provided
        if config.azure_deployment_name:
            client.azure_deployment = config.azure_deployment_name

        # Best effort: disable tracing hooks on the instantiated client
        try:
            traces_attr = getattr(client, "traces", None)
            if traces_attr is not None:
                if hasattr(traces_attr, "disable"):
                    traces_attr.disable()
                if hasattr(traces_attr, "set_enabled"):
                    traces_attr.set_enabled(False)
                setattr(client, "traces", None)
        except Exception:
            pass

        return client

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada. Defina-a ou selecione provider=azure.")

    return AsyncOpenAI(api_key=config.openai_api_key)


def clear_client_cache() -> None:
    """Clear the cached client to allow reconfiguration."""
    get_async_client.cache_clear()

