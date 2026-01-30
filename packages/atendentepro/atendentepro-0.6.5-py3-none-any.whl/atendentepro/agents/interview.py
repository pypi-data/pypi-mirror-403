# -*- coding: utf-8 -*-
"""Interview Agent for AtendentePro."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from agents import Agent

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote
from atendentepro.prompts import get_interview_prompt

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Interview Agent
InterviewAgent = Agent[ContextNote]


def create_interview_agent(
    interview_template: str = "",
    interview_questions: str = "",
    handoffs: Optional[List] = None,
    tools: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Interview Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> InterviewAgent:
    """
    Create an Interview Agent instance.
    
    The interview agent collects information from users through structured
    questions based on the identified topic.
    
    Args:
        interview_template: Template with topic routing info.
        interview_questions: Configured interview questions.
        handoffs: List of agents to hand off to.
        tools: List of tools available to the agent.
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Interview Agent instance.
    """
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        prompt = get_interview_prompt(
            interview_template=interview_template,
            interview_questions=interview_questions,
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
        handoff_description="""
        Um agente de entrevista que pode entrevistar o usuário para obter informações relevantes.
        """,
        instructions=instructions,
        handoffs=handoffs or [],
        tools=tools or [],
        input_guardrails=guardrails or [],
    )

