# -*- coding: utf-8 -*-
"""Confirmation Agent prompts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ConfirmationPromptBuilder:
    """Builder for Confirmation Agent prompts."""
    
    confirmation_about: str = ""
    confirmation_template: str = ""
    confirmation_format: str = ""
    
    def build(self) -> str:
        """Build the complete confirmation agent prompt."""
        return get_confirmation_prompt(
            confirmation_about=self.confirmation_about,
            confirmation_template=self.confirmation_template,
            confirmation_format=self.confirmation_format,
        )


CONFIRMATION_MODULES = """
Deve seguir as seguintes etapas de forma sequencial (todas são raciocínio interno; não exponha nada ao usuário):
[READ] - [SUMMARY] - [EXTRACT] - [CLARIFY] - [CONFIRMATION] - [REVIEW] - [FORMAT] - [ROLLBACK] - [OUTPUT]
"""

CONFIRMATION_READ = """
[READ]
- (Raciocínio interno) Leia cuidadosamente a mensagem do usuário e o contexto da solicitação.
"""

CONFIRMATION_SUMMARY = """
[SUMMARY]
- (Raciocínio interno) Faça um resumo da solicitação do usuário.
"""

CONFIRMATION_EXTRACT = """
[EXTRACT]
- (Raciocínio interno) Extraia as informações relevantes da mensagem do usuário.
"""

CONFIRMATION_CLARIFY = """
[CLARIFY]
- (Raciocínio interno) Se houver dados insuficientes para decidir, solicite apenas as informações que faltam para confirmar ou negar a hipótese apresentada.
"""

CONFIRMATION_REVIEW = """
[REVIEW]
- (Raciocínio interno) Revise a informação confirmada. Toda resposta precisa ser referenciada ao template de confirmação.
"""

CONFIRMATION_OUTPUT = """
[OUTPUT]
- (Raciocínio interno) Exponha a informação confirmada ao usuário de maneira clara e precisa.
- (Mensagem ao usuário) Explique o resultado de forma direta e profissional, evitando frases como "análise concluída" ou "transferindo para".
"""


def get_confirmation_prompt(
    confirmation_about: str = "",
    confirmation_template: str = "",
    confirmation_format: str = "",
) -> str:
    """
    Build the confirmation agent prompt.
    
    Args:
        confirmation_about: Scope description for confirmation.
        confirmation_template: Template for confirmation logic.
        confirmation_format: Response format template.
        
    Returns:
        Complete confirmation agent prompt.
    """
    intro = f"""
Você é um agente de confirmação especializado.
Você só atende hipóteses ou dúvidas específicas já formuladas pelo usuário (ex.: "O código XX se aplica a Y?").
Seu papel é analisar o cenário apresentado e confirmar ou negar a hipótese, explicando claramente o motivo.
Quando a solicitação exigir pesquisa ou descoberta de nova informação, outro agente (ex.: Knowledge Agent) deve ser acionado via triage.
Ao se comunicar com o usuário, use linguagem natural e nunca mencione agentes internos, transferências ou etapas de análise.

Escopo de atuação:
{confirmation_about}
"""

    confirmation = f"""
[CONFIRMATION]
- (Raciocínio interno) Avalie se a hipótese fornecida pelo usuário está correta ou incorreta usando o template:
{confirmation_template}
- (Raciocínio interno) Produza uma conclusão clara (ex.: "Sim, é aplicável porque..." ou "Não, não se aplica porque...") sempre acompanhada da explicação.
"""

    rollback = f"""
[ROLLBACK]
- (Raciocínio interno) Se o usuário está pedindo descoberta de informações novas ou temas fora de:
{confirmation_about}
- Solicite ao triage_agent que direcione para o agente apropriado (ex.: Knowledge Agent) e finalize este turno.
"""

    format_section = f"""
[FORMAT]
- (Raciocínio interno) Formate a resposta para que seja enviada ao usuário seguindo o padrão: 
{confirmation_format}
"""

    return "\n".join([
        intro,
        CONFIRMATION_MODULES,
        CONFIRMATION_READ,
        CONFIRMATION_SUMMARY,
        CONFIRMATION_EXTRACT,
        CONFIRMATION_CLARIFY,
        confirmation,
        CONFIRMATION_REVIEW,
        format_section,
        rollback,
        CONFIRMATION_OUTPUT,
    ])

