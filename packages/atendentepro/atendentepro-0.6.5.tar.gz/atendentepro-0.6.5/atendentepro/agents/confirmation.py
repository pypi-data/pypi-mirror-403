# -*- coding: utf-8 -*-
"""Confirmation Agent for AtendentePro."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from agents import Agent

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote
from atendentepro.prompts import get_confirmation_prompt

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Confirmation Agent
ConfirmationAgent = Agent[ContextNote]


def create_confirmation_agent(
    confirmation_about: str = "",
    confirmation_template: str = "",
    confirmation_format: str = "",
    handoffs: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Confirmation Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> ConfirmationAgent:
    """
    Create a Confirmation Agent instance.
    
    The confirmation agent validates hypotheses and provides yes/no answers
    with explanations based on configured rules.
    
    Args:
        confirmation_about: Scope description for confirmation.
        confirmation_template: Template for confirmation logic.
        confirmation_format: Response format template.
        handoffs: List of agents to hand off to.
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Confirmation Agent instance.
    """
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        prompt = get_confirmation_prompt(
            confirmation_about=confirmation_about,
            confirmation_template=confirmation_template,
            confirmation_format=confirmation_format,
        )
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
            "Agente especializado em confirmar ou negar hipóteses específicas do usuário, "
            "explicando o motivo da decisão com base nas regras e políticas conhecidas do produto ou processo."
        ),
        instructions=instructions,
        handoffs=handoffs or [],
        input_guardrails=guardrails or [],
    )

