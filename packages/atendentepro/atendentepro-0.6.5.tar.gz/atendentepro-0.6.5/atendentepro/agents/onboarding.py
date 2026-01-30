# -*- coding: utf-8 -*-
"""Onboarding Agent for AtendentePro."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from agents import Agent

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote
from atendentepro.prompts import get_onboarding_prompt
from atendentepro.prompts.onboarding import OnboardingField

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Onboarding Agent
OnboardingAgent = Agent[ContextNote]


def create_onboarding_agent(
    required_fields: Optional[List[OnboardingField]] = None,
    handoffs: Optional[List] = None,
    tools: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Onboarding Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> OnboardingAgent:
    """
    Create an Onboarding Agent instance.
    
    The onboarding agent welcomes new users and guides them through
    the registration process.
    
    Args:
        required_fields: List of required fields for onboarding.
        handoffs: List of agents to hand off to.
        tools: List of tools available to the agent (e.g., find_user_on_csv).
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Onboarding Agent instance.
    """
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        prompt = get_onboarding_prompt(required_fields=required_fields)
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {prompt}"
    
    # Append style instructions if provided
    if style_instructions:
        instructions += style_instructions
    
    # Single reply mode: respond once then return to triage
    if single_reply:
        instructions += "\n\nIMPORTANTE: Após fornecer sua resposta, transfira IMEDIATAMENTE para o triage_agent. Você só pode dar UMA resposta antes de transferir."
    
    return Agent[ContextNote](
        name=name,
        handoff_description=(
            "Agente de onboarding responsável por acolher usuários não encontrados no cadastro "
            "e orientar o registro inicial."
        ),
        instructions=instructions,
        handoffs=handoffs or [],
        tools=tools or [],
        input_guardrails=guardrails or [],
    )

