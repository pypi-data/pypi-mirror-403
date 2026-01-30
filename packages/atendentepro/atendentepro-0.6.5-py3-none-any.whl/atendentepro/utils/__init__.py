# -*- coding: utf-8 -*-
"""Utility modules for AtendentePro library."""

from .openai_client import (
    get_async_client,
    get_provider,
    AsyncClient,
    Provider,
)
from .tracing import (
    # MonkAI Trace (recommended)
    configure_monkai_trace,
    get_monkai_hooks,
    set_monkai_user,
    set_monkai_input,
    run_with_monkai_tracking,
    # Application Insights (Azure)
    configure_application_insights,
    # Legacy
    configure_tracing,
)

__all__ = [
    # OpenAI Client
    "get_async_client",
    "get_provider",
    "AsyncClient",
    "Provider",
    # MonkAI Trace
    "configure_monkai_trace",
    "get_monkai_hooks",
    "set_monkai_user",
    "set_monkai_input",
    "run_with_monkai_tracking",
    # Application Insights
    "configure_application_insights",
    # Legacy
    "configure_tracing",
]

