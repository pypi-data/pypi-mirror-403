# -*- coding: utf-8 -*-
"""Configuration module for AtendentePro library."""

from .settings import (
    AtendentProConfig,
    get_config,
    configure,
    RECOMMENDED_PROMPT_PREFIX,
    DEFAULT_MODEL,
)

__all__ = [
    "AtendentProConfig",
    "get_config",
    "configure",
    "RECOMMENDED_PROMPT_PREFIX",
    "DEFAULT_MODEL",
]

