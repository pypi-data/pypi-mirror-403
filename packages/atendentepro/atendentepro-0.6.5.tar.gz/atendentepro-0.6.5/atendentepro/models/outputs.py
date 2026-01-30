# -*- coding: utf-8 -*-
"""Output models for AtendentePro agents."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class FlowTopic(str, Enum):
    """Enumeration of available flow topics."""
    
    GENERIC = "generic"
    CUSTOM = "custom"
    
    @classmethod
    def from_label(cls, label: str) -> "FlowTopic":
        """Create a topic from a label string."""
        normalized = label.lower().replace(" ", "_").replace("-", "_")
        for topic in cls:
            if topic.value == normalized:
                return topic
        return cls.CUSTOM


class FlowOutput(BaseModel):
    """Output model for the Flow Agent."""
    
    topic: FlowTopic = Field(
        description="O tópico identificado para o fluxo de atendimento."
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Nível de confiança na classificação do tópico (0-1)."
    )
    reasoning: str = Field(
        default="",
        description="Explicação do raciocínio para a classificação."
    )


class InterviewOutput(BaseModel):
    """Output model for the Interview Agent."""
    
    topic: str = Field(
        description="O tópico sendo entrevistado."
    )
    questions_asked: List[str] = Field(
        default_factory=list,
        description="Lista de perguntas já realizadas."
    )
    answers_collected: dict = Field(
        default_factory=dict,
        description="Respostas coletadas do usuário."
    )
    is_complete: bool = Field(
        default=False,
        description="Se a entrevista foi completada."
    )
    missing_info: List[str] = Field(
        default_factory=list,
        description="Informações ainda faltando."
    )


class KnowledgeToolResult(BaseModel):
    """Output model for Knowledge Agent RAG tool."""
    
    answer: str = Field(
        description="Resposta sintetizada usando o contexto recuperado."
    )
    context: str = Field(
        description="Trechos dos documentos utilizados para resposta."
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Documentos consultados."
    )
    confidence: float = Field(
        default=0.0,
        description="Confiança média estimada a partir da similaridade dos trechos."
    )


class GuardrailValidationOutput(BaseModel):
    """Output model for guardrail validation."""
    
    is_in_scope: bool = Field(
        description="Se a mensagem está dentro do escopo do agente."
    )
    reasoning: str = Field(
        description="Explicação do raciocínio para a decisão."
    )


class AnswerOutput(BaseModel):
    """Output model for the Answer Agent."""
    
    response: str = Field(
        description="Resposta final sintetizada para o usuário."
    )
    sources_used: List[str] = Field(
        default_factory=list,
        description="Fontes utilizadas para compor a resposta."
    )
    follow_up_needed: bool = Field(
        default=False,
        description="Se é necessário acompanhamento adicional."
    )
    follow_up_reason: Optional[str] = Field(
        default=None,
        description="Razão para o acompanhamento, se necessário."
    )

