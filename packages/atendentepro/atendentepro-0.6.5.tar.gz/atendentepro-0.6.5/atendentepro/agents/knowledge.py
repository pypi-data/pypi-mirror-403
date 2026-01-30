# -*- coding: utf-8 -*-
"""Knowledge Agent for AtendentePro."""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Callable, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from agents import Agent, function_tool

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX, get_config
from atendentepro.models import ContextNote, KnowledgeToolResult
from atendentepro.prompts import get_knowledge_prompt

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable

logger = logging.getLogger(__name__)


# Type alias for the Knowledge Agent
KnowledgeAgent = Agent[ContextNote]


# Global embedding path (can be configured per client)
_EMBEDDINGS_PATH: Optional[Path] = None


def set_embeddings_path(path: Path) -> None:
    """Set the path for embeddings file."""
    global _EMBEDDINGS_PATH
    _EMBEDDINGS_PATH = path


def get_embeddings_path() -> Optional[Path]:
    """Get the current embeddings path."""
    return _EMBEDDINGS_PATH


def load_embeddings() -> List[dict]:
    """Load embeddings from disk."""
    embeddings_path = _EMBEDDINGS_PATH
    if not embeddings_path or not embeddings_path.exists():
        logger.warning("No embeddings path configured or file doesn't exist")
        return []
    
    try:
        with open(embeddings_path, "rb") as file:
            loaded_data = pickle.load(file)
            logger.info("Embeddings loaded successfully from %s", embeddings_path)
            return loaded_data
    except Exception as exc:
        logger.error("Failed to load embeddings from %s: %s", embeddings_path, exc)
        return []


def _check_rag_dependencies() -> None:
    """Check if RAG dependencies are installed."""
    try:
        import numpy  # noqa: F401
        import sklearn  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "RAG dependencies not installed. "
            "Install with: pip install atendentepro[rag]"
        ) from e


async def _find_relevant_chunks(query: str, top_k: int = 3) -> List[dict]:
    """Find most relevant chunks for a given query."""
    try:
        _check_rag_dependencies()
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        from atendentepro.utils import get_async_client
        
        client = get_async_client()
        response = await client.embeddings.create(model="text-embedding-3-large", input=query)
        query_embedding = response.data[0].embedding
        
        chunk_embeddings = load_embeddings()
        if not chunk_embeddings:
            logger.error("No embeddings loaded")
            return []
        
        similarities: List[tuple] = []
        for chunk_data in chunk_embeddings:
            chunk_embedding = chunk_data.get("embedding")
            if not chunk_embedding:
                continue
            
            query_emb = np.array(query_embedding).reshape(1, -1)
            chunk_emb = np.array(chunk_embedding).reshape(1, -1)
            similarity = cosine_similarity(query_emb, chunk_emb)[0][0]
            similarities.append((similarity, chunk_data))
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        top_results: List[dict] = []
        for score, chunk_data in similarities[:top_k]:
            enriched_chunk = dict(chunk_data)
            enriched_chunk["similarity"] = score
            top_results.append(enriched_chunk)
        
        return top_results
    
    except Exception as exc:
        logger.error("Error finding relevant chunks: %s", exc)
        return []


@function_tool
async def go_to_rag(question: str) -> KnowledgeToolResult:
    """
    Utilize RAG to answer the user's question.
    
    Args:
        question: The question to answer using RAG.
        
    Returns:
        KnowledgeToolResult with answer, context, sources, and confidence.
    """
    from atendentepro.utils import get_async_client
    from atendentepro.config import get_config
    
    logger.info("Processing question: %s", question)
    
    relevant_chunks = await _find_relevant_chunks(question, top_k=3)
    
    if not relevant_chunks:
        return KnowledgeToolResult(
            answer="Não consegui encontrar informações relevantes nos documentos para responder sua pergunta.",
            context="",
            sources=[],
            confidence=0.0,
        )
    
    context_sections: List[str] = []
    sources: List[str] = []
    seen_sources: set = set()
    similarities: List[float] = []
    
    for chunk in relevant_chunks:
        chunk_info = chunk.get("chunk", {}) or {}
        source = chunk_info.get("source", "Desconhecido")
        content = chunk_info.get("content", "")
        similarity = float(chunk.get("similarity", 0.0))
        
        if source not in seen_sources:
            sources.append(source)
            seen_sources.add(source)
        
        similarities.append(similarity)
        context_sections.append(f"Documento: {source}\nConteúdo: {content}")
    
    context = "\n\n".join(context_sections)
    logger.info("Context: %s", context)
    
    confidence = (
        sum(max(score, 0.0) for score in similarities) / len(similarities) if similarities else 0.0
    )
    
    answer = (
        "Encontrei trechos relevantes, mas não consegui sintetizar uma resposta a partir deles. "
        "Use o contexto abaixo para responder manualmente."
    )
    
    try:
        config = get_config()
        client = get_async_client()
        completion = await client.responses.create(
            model=config.default_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Você é um especialista no domínio deste produto. Use apenas o contexto fornecido para "
                        "responder de forma objetiva. Se não houver informação suficiente, informe isso."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Pergunta: {question}\n\n"
                        f"Contexto:\n{context}\n\n"
                        "Responda em português, destacando os passos principais e cite os documentos utilizados."
                    ),
                },
            ],
        )
        
        if hasattr(completion, "output_text"):
            answer_candidate = completion.output_text.strip()
            if answer_candidate:
                answer = answer_candidate
        else:
            parts: List[str] = []
            for output in getattr(completion, "output", []):
                for content in getattr(output, "content", []):
                    text_part = getattr(content, "text", None)
                    if text_part:
                        parts.append(text_part)
            if parts:
                answer = "\n".join(parts).strip()
    except Exception as exc:
        logger.error("Failed to synthesize answer: %s", exc)
    
    return KnowledgeToolResult(
        answer=answer,
        context=context,
        sources=sources,
        confidence=confidence,
    )


def create_knowledge_agent(
    knowledge_about: str = "",
    knowledge_template: str = "",
    knowledge_format: str = "",
    embeddings_path: Optional[Path] = None,
    data_sources_description: str = "",
    include_rag_tool: bool = True,
    handoffs: Optional[List] = None,
    tools: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Knowledge Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> KnowledgeAgent:
    """
    Create a Knowledge Agent instance.
    
    The knowledge agent handles document research (RAG) and structured data queries.
    It can be configured to use:
    - Document-based RAG with embeddings
    - Structured data sources (CSV, databases, APIs) via custom tools
    - Both simultaneously
    
    Args:
        knowledge_about: Description of available knowledge documents.
        knowledge_template: Document metadata template.
        knowledge_format: Response format template.
        embeddings_path: Path to the embeddings file for RAG.
        data_sources_description: Description of available structured data sources.
        include_rag_tool: Whether to include the go_to_rag tool (default True if embeddings_path).
        handoffs: List of agents to hand off to.
        tools: Additional tools for structured data queries.
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Knowledge Agent instance.
    """
    # Set embeddings path if provided
    if embeddings_path:
        set_embeddings_path(embeddings_path)
    
    # Build about section including data sources
    full_about = knowledge_about
    if data_sources_description:
        full_about = f"{knowledge_about}\n\nFontes de dados estruturados disponíveis:\n{data_sources_description}"
    
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        prompt = get_knowledge_prompt(
            knowledge_about=full_about,
            knowledge_template=knowledge_template,
            knowledge_format=knowledge_format,
        )
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {prompt}"
    
    # Append style instructions if provided
    if style_instructions:
        instructions += style_instructions
    
    # Single reply mode: respond once then return to triage
    if single_reply:
        instructions += "\n\nIMPORTANTE: Após fornecer sua resposta, transfira IMEDIATAMENTE para o triage_agent. Você só pode dar UMA resposta antes de transferir."
    
    # Build tools list
    agent_tools: List = []
    
    # Include RAG tool if embeddings are configured
    if include_rag_tool and embeddings_path:
        agent_tools.append(go_to_rag)
    
    # Add custom tools for structured data
    if tools:
        agent_tools.extend(tools)
    
    # Build handoff description based on capabilities
    capabilities = []
    if embeddings_path:
        capabilities.append("pesquisar documentos")
    if tools:
        capabilities.append("consultar dados estruturados")
    
    handoff_desc = (
        f"Agente voltado a {' e '.join(capabilities) if capabilities else 'recuperar informações'} "
        "quando é preciso descobrir ou contextualizar algo novo."
    )
    
    return Agent[ContextNote](
        name=name,
        handoff_description=handoff_desc,
        instructions=instructions,
        tools=agent_tools,
        handoffs=handoffs or [],
        input_guardrails=guardrails or [],
    )

