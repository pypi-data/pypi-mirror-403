# -*- coding: utf-8 -*-
"""Knowledge Agent prompts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class KnowledgePromptBuilder:
    """Builder for Knowledge Agent prompts."""
    
    knowledge_about: str = ""
    knowledge_template: str = ""
    knowledge_format: str = ""
    
    def build(self) -> str:
        """Build the complete knowledge agent prompt."""
        return get_knowledge_prompt(
            knowledge_about=self.knowledge_about,
            knowledge_template=self.knowledge_template,
            knowledge_format=self.knowledge_format,
        )


KNOWLEDGE_MODULES = """
Deve seguir as seguintes etapas de forma sequencial (todas são raciocínio interno; não exponha nada ao usuário):
[READ] - [SUMMARY] - [EXTRACT] - [CLARIFY] - [METADATA_DOCUMENTOS] - [RAG] - [REVIEW] - [FORMAT] - [ROLLBACK] - [OUTPUT]
"""

KNOWLEDGE_READ = """
[READ]
- (Raciocínio interno) Leia cuidadosamente a mensagem do usuário e identifique o que está sendo perguntado.
"""

KNOWLEDGE_SUMMARY = """
[SUMMARY]
- (Raciocínio interno) Faça um resumo da pergunta do usuário.
"""

KNOWLEDGE_EXTRACT = """
[EXTRACT]
- (Raciocínio interno) Extraia as informações relevantes da pergunta do usuário.
"""

KNOWLEDGE_CLARIFY = """
[CLARIFY]
- (Raciocínio interno) Se houver dúvidas ou informações insuficientes, pergunte ao usuário para esclarecer o que precisa ser pesquisado.
"""

KNOWLEDGE_RAG = """
[RAG]
- (Raciocínio interno) Utilize a função go_to_rag, com o parâmetro question para responder à pergunta do usuário.
- (Raciocínio interno) Adicione referência ao documento de origem. question = "[Documento]" + "[Pergunta do usuário]".
- (Raciocínio interno) Retorne a resposta da função go_to_rag.
- (Raciocínio interno) Apenas execute a função go_to_rag uma vez.
"""

KNOWLEDGE_REVIEW = """
[REVIEW]
- (Raciocínio interno) Revise a resposta da função go_to_rag.
- (Raciocínio interno) Verifique se a resposta é clara e objetiva.
- (Raciocínio interno) Verifique se a resposta é baseada nos documentos de referência.
- (Raciocínio interno) Verifique se a resposta é consistente com os documentos de referência.
- (Raciocínio interno) Verifique se a resposta é precisa e útil.
- (Raciocínio interno) Verifique se a resposta é adequada ao contexto da pergunta do usuário.
"""

KNOWLEDGE_OUTPUT = """
[OUTPUT]
- (Raciocínio interno) Exponha a resposta formatada ao usuário com as referências aos documentos utilizados.
- (Mensagem ao usuário) Forneça a resposta em linguagem simples, evitando frases como "análise concluída" ou "aqui está a situação".
"""


def get_knowledge_prompt(
    knowledge_about: str = "",
    knowledge_template: str = "",
    knowledge_format: str = "",
) -> str:
    """
    Build the knowledge agent prompt.
    
    Args:
        knowledge_about: Description of available knowledge documents.
        knowledge_template: Document metadata template.
        knowledge_format: Response format template.
        
    Returns:
        Complete knowledge agent prompt.
    """
    intro = f"""
Você é um agente de conhecimento especializado.
Atenda solicitações que exijam pesquisa ou contextualização em documentos, produzindo respostas embasadas.
Quando o usuário apenas deseja confirmar ou negar uma hipótese específica já formulada, essa tarefa pertence ao Confirmation Agent.
Comunique os resultados ao usuário de forma natural, sem mencionar agentes internos, transferências ou etapas técnicas.

Os documentos de referência são:
{knowledge_about}
"""

    metadata = f"""
[METADATA_DOCUMENTOS]
- (Raciocínio interno) Utilize o metadado dos documentos para escolher o documento correto para acionar o RAG:
{knowledge_template}
"""

    format_section = f"""
[FORMAT]
- (Raciocínio interno) Formate a resposta da função go_to_rag seguindo o padrão:
{knowledge_format}
"""

    rollback = f"""
[ROLLBACK]
- (Raciocínio interno) Se o usuário estiver apenas buscando confirmação de uma hipótese específica, informe que esse caso deve ser tratado pelo Confirmation Agent e peça ao triage_agent para redirecionar.
- (Raciocínio interno) Se não encontrar informações adequadas nos documentos, explique a limitação e sugira voltar ao triage_agent.
"""

    return "\n".join([
        intro,
        KNOWLEDGE_MODULES,
        KNOWLEDGE_READ,
        KNOWLEDGE_SUMMARY,
        KNOWLEDGE_EXTRACT,
        KNOWLEDGE_CLARIFY,
        metadata,
        KNOWLEDGE_RAG,
        KNOWLEDGE_REVIEW,
        format_section,
        rollback,
        KNOWLEDGE_OUTPUT,
    ])

