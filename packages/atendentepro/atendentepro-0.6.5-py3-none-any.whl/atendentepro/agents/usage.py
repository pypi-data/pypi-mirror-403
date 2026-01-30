# -*- coding: utf-8 -*-
"""Usage Agent for AtendentePro."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from agents import Agent

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Usage Agent
UsageAgent = Agent[ContextNote]


DEFAULT_USAGE_INSTRUCTIONS = """
You are a helpful usage agent. You will answer questions about the usage of the system.
Respond in natural language and never mention internal agents, transfers, or reasoning steps.
"""


def create_usage_agent(
    handoffs: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Usage Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> UsageAgent:
    """
    Create a Usage Agent instance.
    
    The usage agent answers questions about system usage.
    
    Args:
        handoffs: List of agents to hand off to.
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Usage Agent instance.
    """
    instructions = custom_instructions or DEFAULT_USAGE_INSTRUCTIONS
    
    # Append style instructions if provided
    if style_instructions:
        instructions += style_instructions
    
    # Single reply mode: respond once then return to triage
    if single_reply:
        instructions += "\n\nIMPORTANTE: Após fornecer sua resposta, transfira IMEDIATAMENTE para o triage_agent. Você só pode dar UMA resposta antes de transferir."
    
    return Agent[ContextNote](
        name=name,
        handoff_description="A usage agent that can answer questions about the usage of the system.",
        instructions=instructions,
        handoffs=handoffs or [],
        input_guardrails=guardrails or [],
    )

