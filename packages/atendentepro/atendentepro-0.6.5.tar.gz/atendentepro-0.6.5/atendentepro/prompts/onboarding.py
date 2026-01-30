# -*- coding: utf-8 -*-
"""Onboarding Agent prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OnboardingField:
    """Represents a required field for onboarding."""
    
    name: str
    prompt: str
    priority: int = 0


@dataclass
class OnboardingPromptBuilder:
    """Builder for Onboarding Agent prompts."""
    
    required_fields: List[OnboardingField] = field(default_factory=list)
    
    def build(self) -> str:
        """Build the complete onboarding agent prompt."""
        return get_onboarding_prompt(required_fields=self.required_fields)


ONBOARDING_INTRO = """
Você é um agente de onboarding responsável por acolher usuários que ainda
não foram localizados no cadastro. A partir deste ponto, assuma que precisamos
confirmar os dados básicos e orientar o registro inicial do usuário.
Conduza a conversa com naturalidade, sem mencionar processos internos,
agentes ou etapas técnicas. Peça somente as informações indispensáveis
para criar ou ativar o cadastro e explique claramente o que acontecerá em seguida.
"""

ONBOARDING_MODULES = """
Siga as etapas abaixo (todo texto em colchetes é raciocínio interno; não exponha ao usuário):
[GREET] - [EXTRACT] - [LOOK_UP] - [COLLECT_DATA] - [EXTRACT] - [LOOK_UP] - [CONFIRM_CREATION] - [GUIDE_NEXT_STEPS]

Fluxo: Após GREET, entre em um ciclo de EXTRACT -> LOOK_UP. Se usuário não for encontrado no LOOK_UP, 
vá para COLLECT_DATA (próximo campo) e repita EXTRACT -> LOOK_UP. Continue até encontrar o usuário ou 
esgotar campos prioritários.
"""

ONBOARDING_EXTRACT = """
[EXTRACT]
- (Raciocínio interno) Extraia o campo solicitado da mensagem do usuário.
- (Raciocínio interno) Se não conseguir extrair a informação ou ela estiver incompleta/inválida, volte para [COLLECT_DATA] e peça novamente de forma clara.
- (Raciocínio interno) Valide se a informação extraída está no formato correto antes de prosseguir.
- (Raciocínio interno) Após extrair com sucesso, vá imediatamente para [LOOK_UP].
"""

ONBOARDING_LOOKUP = """
[LOOK_UP]
- (Raciocínio interno) Use o conteúdo extraído da resposta do usuário para ativar o tool de busca disponível.
- (Raciocínio interno) Execute a ferramenta de busca (por exemplo, `find_user_on_csv`) com os dados coletados até agora.
- (Raciocínio interno) Registre internamente o resultado: usuário encontrado ou não encontrado na database.
- (Raciocínio interno) Se usuário FOI ENCONTRADO, vá para [CONFIRM_CREATION].
- (Raciocínio interno) Se usuário NÃO FOI ENCONTRADO e ainda há campos prioritários restantes, vá para [COLLECT_DATA].
- (Raciocínio interno) Se usuário NÃO FOI ENCONTRADO e não há mais campos prioritários, vá para [GUIDE_NEXT_STEPS].
"""

ONBOARDING_CONFIRM = """
[CONFIRM_CREATION]
- (Raciocínio interno) Se o usuário foi encontrado na busca, confirme ao usuário.
- (Mensagem ao usuário) Informe que o registro foi localizado e confirme os dados encontrados.
- (Mensagem ao usuário) Explique que o cadastro está ativo e pronto para uso.
"""

ONBOARDING_GUIDE = """
[GUIDE_NEXT_STEPS]
- (Raciocínio interno) Passo opcional caso a entrada não foi encontrada na busca.
- (Mensagem ao usuário) Se o usuário não foi encontrado, explique os próximos passos para criação do cadastro.
- (Mensagem ao usuário) Oriente sobre o processo de registro ou contato com suporte, sem mencionar processos internos.
"""


def get_onboarding_prompt(required_fields: Optional[List[OnboardingField]] = None) -> str:
    """
    Build the onboarding agent prompt.
    
    Args:
        required_fields: List of required fields for onboarding.
        
    Returns:
        Complete onboarding agent prompt.
    """
    fields = required_fields or []
    
    # Build GREET section
    if fields:
        first_field = fields[0]
        greet = f"""
[GREET]
- (Mensagem ao usuário) Cumprimente de forma acolhedora e explique o contexto: 
  não encontramos o registro do usuário na database ou ele não está registrado. 
  Como parte do greeting, já solicite o campo mais prioritário: '{first_field.name}' - {first_field.prompt}
"""
    else:
        greet = """
[GREET]
- (Mensagem ao usuário) Cumprimente de forma acolhedora e explique o contexto: 
  não encontramos o registro do usuário na database ou ele não está registrado. 
  Peça que informe qualquer dado que tenha disponível para localizar o cadastro.
"""

    # Build COLLECT_DATA section
    remaining_fields = fields[1:] if len(fields) > 1 else []
    if remaining_fields:
        collect_lines = []
        for f in remaining_fields:
            collect_lines.append(
                f"- (Mensagem ao usuário) Solicite o próximo campo prioritário: '{f.name}' - {f.prompt}"
            )
        
        collect_data = """
[COLLECT_DATA]
- (Raciocínio interno) SOMENTE execute este módulo se o usuário NÃO foi encontrado no LOOK_UP anterior.
- (Raciocínio interno) Pergunte pelo próximo campo mais prioritário dos campos na configuração, seguindo a ordem de prioridade.
""" + "\n".join(collect_lines) + """
- (Raciocínio interno) Se o usuário não possuir a informação solicitada, avance para o próximo campo prioritário.
- (Raciocínio interno) Após coletar o próximo campo, vá imediatamente para [EXTRACT] -> [LOOK_UP].
"""
    else:
        collect_data = """
[COLLECT_DATA]
- (Raciocínio interno) SOMENTE execute este módulo se o usuário NÃO foi encontrado no LOOK_UP anterior.
- (Raciocínio interno) Pergunte pelo próximo campo mais prioritário dos campos na configuração.
- (Mensagem ao usuário) Solicite informações adicionais caso necessário para completar o cadastro.
- (Raciocínio interno) Após coletar o próximo campo, vá imediatamente para [EXTRACT] -> [LOOK_UP].
"""

    return "\n".join([
        ONBOARDING_INTRO,
        ONBOARDING_MODULES,
        greet,
        collect_data,
        ONBOARDING_EXTRACT,
        ONBOARDING_LOOKUP,
        ONBOARDING_CONFIRM,
        ONBOARDING_GUIDE,
    ])

