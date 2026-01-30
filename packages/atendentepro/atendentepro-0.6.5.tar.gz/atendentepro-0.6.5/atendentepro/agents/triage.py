# -*- coding: utf-8 -*-
"""Triage Agent for AtendentePro."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from agents import Agent

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote
from atendentepro.prompts import get_triage_prompt

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Triage Agent
TriageAgent = Agent[ContextNote]


def create_triage_agent(
    keywords_text: str = "",
    handoffs: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Triage Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
) -> TriageAgent:
    """
    Create a Triage Agent instance.
    
    The triage agent is responsible for understanding user needs and
    directing them to the appropriate specialized agent.
    
    Args:
        keywords_text: Formatted keywords for agent routing.
        handoffs: List of agents to hand off to.
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        
    Returns:
        Configured Triage Agent instance.
    """
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {get_triage_prompt(keywords_text)}"
    
    # Append style instructions if provided
    if style_instructions:
        instructions += style_instructions
    
    return Agent[ContextNote](
        name=name,
        handoff_description="A triage agent that can delegate a customer's request to the appropriate agent.",
        instructions=instructions,
        handoffs=handoffs or [],
        input_guardrails=guardrails or [],
    )

