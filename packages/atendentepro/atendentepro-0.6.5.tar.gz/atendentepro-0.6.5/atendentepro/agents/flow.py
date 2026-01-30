# -*- coding: utf-8 -*-
"""Flow Agent for AtendentePro."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from agents import Agent

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote
from atendentepro.prompts import get_flow_prompt

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Flow Agent
FlowAgent = Agent[ContextNote]


def create_flow_agent(
    flow_template: str = "",
    flow_keywords: str = "",
    handoffs: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Flow Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> FlowAgent:
    """
    Create a Flow Agent instance.
    
    The flow agent identifies topics and routes users to the interview agent.
    
    Args:
        flow_template: Template with available topics.
        flow_keywords: Keywords for topic identification.
        handoffs: List of agents to hand off to.
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Flow Agent instance.
    """
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        prompt = get_flow_prompt(flow_template=flow_template, flow_keywords=flow_keywords)
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {prompt}"
    
    # Append style instructions if provided
    if style_instructions:
        instructions += style_instructions
    
    # Single reply mode: respond once then return to triage
    if single_reply:
        instructions += "\n\nIMPORTANTE: Após fornecer sua resposta, transfira IMEDIATAMENTE para o triage_agent. Você só pode dar UMA resposta antes de transferir."
    
    return Agent[ContextNote](
        name=name,
        handoff_description="""
        Um agente de fluxo inteligente que:
        1. Se o usuário já especificou um tópico específico, vai direto para o interview_agent
        2. Se não especificou, apresenta a lista de tópicos para o usuário escolher
        3. Só transfere para triage se a resposta não for clara o suficiente
        """,
        instructions=instructions,
        handoffs=handoffs or [],
        input_guardrails=guardrails or [],
    )

