# -*- coding: utf-8 -*-
"""Answer Agent for AtendentePro."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from agents import Agent

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote
from atendentepro.prompts import get_answer_prompt

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Answer Agent
AnswerAgent = Agent[ContextNote]


def create_answer_agent(
    answer_template: str = "",
    handoffs: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Answer Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> AnswerAgent:
    """
    Create an Answer Agent instance.
    
    The answer agent synthesizes final responses using collected data
    and the configured answer template.
    
    Args:
        answer_template: Template for answer formatting.
        handoffs: List of agents to hand off to.
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Answer Agent instance.
    """
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        prompt = get_answer_prompt(answer_template=answer_template)
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
            "Agente responsável por sintetizar a resposta técnica final usando os dados coletados. "
            "Após concluir a orientação, deve acionar o handoff para o Triage Agent a fim de encerrar o caso."
        ),
        instructions=instructions,
        handoffs=handoffs or [],
        input_guardrails=guardrails or [],
    )

