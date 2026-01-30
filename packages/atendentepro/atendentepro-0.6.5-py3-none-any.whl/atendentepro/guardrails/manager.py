# -*- coding: utf-8 -*-
"""
Guardrails Manager for AtendentePro.

Provides scope validation and content filtering for agents.
"""

from __future__ import annotations

import logging
import textwrap
from functools import lru_cache
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

from atendentepro.models import GuardrailValidationOutput

logger = logging.getLogger(__name__)


# Type alias for guardrail callables
GuardrailCallable = Callable[
    [RunContextWrapper[None], Agent, "Union[str, List[TResponseInputItem]]"],
    Awaitable[GuardrailFunctionOutput],
]


# Cache of created guardrails by agent
_GUARDRAIL_CACHE: Dict[str, List[GuardrailCallable]] = {}

# Control of dynamically loaded template
_GUARDRAIL_TEMPLATE_ROOT: Optional[Path] = None
_GUARDRAIL_TEMPLATE_NAME: Optional[str] = None
_DEFAULT_TEMPLATE_FALLBACKS: tuple[str, ...] = ("standard",)


# Examples of out-of-scope questions
OUT_OF_SCOPE_EXAMPLES = [
    "Qual é o preço do bitcoin?",
    "Distância entre a Terra e a Lua.",
    "Resolva a equação 2x + 5 = 11.",
    "Como programar uma API em Python?",
    "Conte uma piada sobre futebol.",
]


class GuardrailManager:
    """
    Manages guardrail configuration and creation for agents.
    
    This class provides a high-level interface for loading guardrail
    configurations from YAML files and creating guardrail functions
    for agents.
    """
    
    def __init__(
        self,
        templates_root: Optional[Path] = None,
        template_name: Optional[str] = None,
    ):
        """
        Initialize the GuardrailManager.
        
        Args:
            templates_root: Root directory for template configurations.
            template_name: Name of the template to use.
        """
        self.templates_root = templates_root
        self.template_name = template_name
        self._cache: Dict[str, List[GuardrailCallable]] = {}
    
    def load_config(self) -> Dict[str, Any]:
        """Load guardrail configuration from the configured template."""
        return load_guardrail_config(
            templates_root=self.templates_root,
            template_name=self.template_name,
        )
    
    def get_guardrails(self, agent_name: str) -> List[GuardrailCallable]:
        """Get guardrails for a specific agent."""
        if agent_name in self._cache:
            return self._cache[agent_name]
        
        guardrails = get_guardrails_for_agent(
            agent_name,
            templates_root=self.templates_root,
            template_name=self.template_name,
        )
        self._cache[agent_name] = guardrails
        return guardrails
    
    def clear_cache(self) -> None:
        """Clear the guardrail cache."""
        self._cache.clear()


@lru_cache(maxsize=1)
def _load_guardrail_config_cached(
    templates_root: Optional[str] = None,
    template_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Internal cached config loader."""
    root = Path(templates_root) if templates_root else _GUARDRAIL_TEMPLATE_ROOT
    name = template_name or _GUARDRAIL_TEMPLATE_NAME
    
    candidate_paths: List[Path] = []
    
    if root and name:
        candidate_paths.append(root / name / "guardrails_config.yaml")
    
    if root:
        for folder in _DEFAULT_TEMPLATE_FALLBACKS:
            candidate_paths.append(root / folder / "guardrails_config.yaml")
    
    # Deduplicate paths
    unique_candidates: List[Path] = []
    seen: set[Path] = set()
    for path in candidate_paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_candidates.append(path)
    
    for path in unique_candidates:
        if path.exists():
            with path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
                return data if isinstance(data, dict) else {}
    
    return {}


def load_guardrail_config(
    templates_root: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load guardrail configuration from templates.
    
    Args:
        templates_root: Root directory for templates.
        template_name: Name of the template to load.
        
    Returns:
        Dictionary containing the guardrail configuration.
    """
    root_str = str(templates_root) if templates_root else None
    return _load_guardrail_config_cached(root_str, template_name)


def _normalize_agent_name(agent_name: str) -> str:
    """Normalize agent name for configuration lookup."""
    name = agent_name.strip().lower().replace("-", " ")
    return "_".join(name.split())


def _get_scope_for_agent(
    agent_name: str,
    templates_root: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> Optional[str]:
    """Retrieve the 'about' block for an agent from configuration."""
    config = load_guardrail_config(templates_root, template_name)
    scopes = config.get("agent_scopes", {})
    normalized_name = _normalize_agent_name(agent_name)
    
    if normalized_name in scopes:
        about = scopes[normalized_name].get("about", "")
        return about.strip() or None
    
    # Fallback: try fuzzy matching
    for key, value in scopes.items():
        if _normalize_agent_name(key) == normalized_name:
            about = value.get("about", "")
            return about.strip() or None
    
    return None


def get_out_of_scope_message(
    agent_name: str,
    templates_root: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> str:
    """
    Get the appropriate 'out of scope' message for an agent.
    
    Args:
        agent_name: Name of the agent.
        templates_root: Root directory for templates.
        template_name: Name of the template.
        
    Returns:
        The out of scope message for the agent.
    """
    config = load_guardrail_config(templates_root, template_name)
    out_of_scope_messages = config.get("out_of_scope_message", {})
    normalized_name = _normalize_agent_name(agent_name)
    
    # Try to find agent-specific message
    if normalized_name in out_of_scope_messages:
        message = out_of_scope_messages[normalized_name]
        if isinstance(message, str) and message.strip():
            return message.strip()
    
    # Fall back to default message
    default_message = out_of_scope_messages.get("default", "")
    if isinstance(default_message, str) and default_message.strip():
        return default_message.strip()
    
    # Final fallback
    return (
        "Desculpe, mas a pergunta que você fez está fora do escopo dos tópicos que posso abordar. "
        "Por favor, reformule sua pergunta para que ela se enquadre nos assuntos que estou autorizado a responder."
    )


def _build_guardrail_agent(agent_name: str, scope_description: str) -> Agent:
    """Create the agent responsible for scope validation."""
    negative_examples = "\n".join(
        f'- Pergunta: "{example}" -> is_in_scope: false' 
        for example in OUT_OF_SCOPE_EXAMPLES
    )
    
    instructions = f"""
    Você é um agente de validação que decide se uma solicitação está dentro do escopo do {agent_name}.

    CONTEXTO DO {agent_name.upper()}:
    {scope_description.strip()}

    REGRAS:
    1. Use apenas o contexto fornecido. Não invente ou busque informações externas.
    2. Considere mensagens neutras de saudação, agradecimento, confirmação ou pedidos para continuar a conversa como dentro do escopo (retorne is_in_scope: true).
    3. Retorne is_in_scope: false apenas quando a mensagem tratar claramente de assuntos que não têm relação com o escopo acima.
    4. Perguntas sobre assuntos gerais, entretenimento, ciências exatas, programação ou temas aleatórios devem ser marcadas como is_in_scope: false.
    5. Responda somente com JSON compatível com o formato {{"is_in_scope": bool, "reasoning": string}} e explique brevemente a decisão.

    EXEMPLOS FORA DO ESCOPO:
    {negative_examples}
    """
    
    instructions = textwrap.dedent(instructions).strip()
    
    return Agent(
        name=f"{agent_name} Guardrail",
        instructions=instructions,
        output_type=GuardrailValidationOutput,
    )


def _create_guardrail_callable(
    agent_name: str,
    guardrail_agent: Agent,
) -> GuardrailCallable:
    """Build the decorated guardrail function for a specific agent."""
    
    def _as_prompt(value: Union[str, List[TResponseInputItem]]) -> str:
        if isinstance(value, str):
            return value
        
        collected: List[str] = []
        for item in value:
            if isinstance(item, dict):
                content = item.get("content")
                if isinstance(content, str):
                    collected.append(content.strip())
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict):
                            text_val = part.get("text")
                            if isinstance(text_val, str) and text_val.strip():
                                collected.append(text_val.strip())
                            elif isinstance(text_val, dict):
                                inner_value = text_val.get("value")
                                if isinstance(inner_value, str) and inner_value.strip():
                                    collected.append(inner_value.strip())
                        elif isinstance(part, str) and part.strip():
                            collected.append(part.strip())
                continue
            
            text_attr = getattr(item, "input_text", None)
            if isinstance(text_attr, str) and text_attr.strip():
                collected.append(text_attr.strip())
            
            content_attr = getattr(item, "content", None)
            if isinstance(content_attr, str):
                collected.append(content_attr.strip())
            elif isinstance(content_attr, list):
                for part in content_attr:
                    text_part = getattr(part, "text", None)
                    if not text_part:
                        continue
                    part_value = getattr(text_part, "value", None)
                    if isinstance(part_value, str) and part_value.strip():
                        collected.append(part_value.strip())
                    elif isinstance(text_part, str) and text_part.strip():
                        collected.append(text_part.strip())
        
        if collected:
            return "\n".join(collected)
        
        return str(value)
    
    @input_guardrail
    async def guardrail(
        ctx: RunContextWrapper[None],
        agent: Agent,
        input: Union[str, List[TResponseInputItem]],
    ) -> GuardrailFunctionOutput:
        prompt = _as_prompt(input)
        
        result = await Runner.run(guardrail_agent, prompt, context=ctx.context)
        output = result.final_output
        
        if output is None:
            return GuardrailFunctionOutput(
                output_info=None,
                tripwire_triggered=True,
            )
        
        is_in_scope = bool(getattr(output, "is_in_scope", False))
        return GuardrailFunctionOutput(
            output_info=output,
            tripwire_triggered=not is_in_scope,
        )
    
    guardrail.__name__ = f"{_normalize_agent_name(agent_name)}_guardrail"
    return guardrail


def get_guardrails_for_agent(
    agent_name: str,
    templates_root: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> List[GuardrailCallable]:
    """
    Get the list of guardrails configured for an agent.
    
    Args:
        agent_name: Name of the agent (e.g., "Triage Agent", "Flow Agent").
        templates_root: Root directory for templates.
        template_name: Name of the template.
        
    Returns:
        List of guardrail callables for the agent.
    """
    cache_key = f"{agent_name}:{templates_root}:{template_name}"
    
    if cache_key in _GUARDRAIL_CACHE:
        return _GUARDRAIL_CACHE[cache_key]
    
    scope = _get_scope_for_agent(agent_name, templates_root, template_name)
    if not scope:
        _GUARDRAIL_CACHE[cache_key] = []
        return []
    
    guardrail_agent = _build_guardrail_agent(agent_name, scope)
    guardrail_callable = _create_guardrail_callable(agent_name, guardrail_agent)
    _GUARDRAIL_CACHE[cache_key] = [guardrail_callable]
    return _GUARDRAIL_CACHE[cache_key]


def set_guardrails_client(
    client_key: str,
    *,
    template_name: Optional[str] = None,
    templates_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Update the active guardrails template and clear associated caches.
    
    Args:
        client_key: Client identifier.
        template_name: Name of the template folder.
        templates_root: Root directory for templates.
        
    Returns:
        The loaded configuration dictionary.
        
    Raises:
        FileNotFoundError: If the guardrail config file doesn't exist.
    """
    root = Path(templates_root) if templates_root else None
    template_folder = template_name or client_key
    
    if root:
        config_path = root / template_folder / "guardrails_config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Guardrail config not found for client '{client_key}' at path '{config_path}'"
            )
    
    global _GUARDRAIL_TEMPLATE_ROOT, _GUARDRAIL_TEMPLATE_NAME
    _GUARDRAIL_TEMPLATE_ROOT = root
    _GUARDRAIL_TEMPLATE_NAME = template_folder
    
    clear_guardrail_cache()
    
    return load_guardrail_config(root, template_folder)


def clear_guardrail_cache() -> None:
    """Clear all guardrail caches."""
    _GUARDRAIL_CACHE.clear()
    _load_guardrail_config_cached.cache_clear()

