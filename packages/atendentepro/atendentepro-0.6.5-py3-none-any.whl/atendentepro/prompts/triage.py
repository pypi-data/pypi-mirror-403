# -*- coding: utf-8 -*-
"""Triage Agent prompts."""

from __future__ import annotations

from typing import Dict, Optional


TRIAGE_INTRO = """
Você é um agente de triagem prestativo. 
Você pode usar suas ferramentas para delegar perguntas para outros agentes apropriados.
"""


def get_triage_prompt(
    keywords_text: str = "",
    custom_intro: Optional[str] = None,
) -> str:
    """
    Build the triage agent prompt.
    
    Args:
        keywords_text: Formatted keywords text for agent routing.
        custom_intro: Optional custom intro text.
        
    Returns:
        Complete triage agent prompt.
    """
    intro = custom_intro or TRIAGE_INTRO
    
    base_prompt = (
        "Você é um agente de triagem prestativo. "
        "Seu papel é entender a necessidade do usuário e direcioná-lo rapidamente ao agente especializado. "
        "Faça perguntas curtas apenas quando precisar esclarecer a categoria correta, mas evite responder ao problema final. "
        "Responda com linguagem natural, sem mencionar nomes de agentes internos, processos ou etapas técnicas."
    )
    
    if keywords_text:
        base_prompt += f"\nConsidere os seguintes grupos de palavras-chave como sinais do agente ideal:\n{keywords_text}"
    
    return base_prompt

