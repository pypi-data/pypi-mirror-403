# -*- coding: utf-8 -*-
"""
Escalation Agent for AtendentePro.

Handles transfers to human support when:
- User explicitly requests
- Topic is not covered by the system
- Agent cannot resolve the issue
- User shows frustration or confusion
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

from agents import Agent, function_tool

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote
from atendentepro.prompts.escalation import (
    get_escalation_prompt,
    EscalationPromptBuilder,
    ESCALATION_INTRO,
    DEFAULT_ESCALATION_TRIGGERS,
)

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Escalation Agent
EscalationAgent = Agent[ContextNote]


# =============================================================================
# Configurações de Escalação
# =============================================================================

# Horário de atendimento padrão (pode ser sobrescrito via config)
DEFAULT_BUSINESS_HOURS = {
    "start": 8,
    "end": 18,
    "days": [0, 1, 2, 3, 4],  # Seg-Sex
}


# =============================================================================
# Storage de Escalações (em memória - substituir por DB em produção)
# =============================================================================

@dataclass
class Escalation:
    """Representa uma escalação para atendimento humano."""
    protocolo: str
    motivo: str
    categoria: str  # solicitacao, frustração, topico_nao_coberto, incerteza
    nome_usuario: str
    contato: str
    tipo_contato: str  # telefone, email, whatsapp
    resumo_conversa: str
    prioridade: str  # baixa, normal, alta, urgente
    status: str  # pendente, em_atendimento, concluido, cancelado
    data_criacao: datetime = field(default_factory=datetime.now)
    data_atualizacao: datetime = field(default_factory=datetime.now)
    atendente: Optional[str] = None
    observacoes: Optional[str] = None


# Storage em memória
_escalations_storage: Dict[str, Escalation] = {}


def _gerar_protocolo_escalacao() -> str:
    """Gera um protocolo único para escalação."""
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:6].upper()
    return f"ESC-{timestamp}-{unique_id}"


def _salvar_escalacao(escalation: Escalation) -> None:
    """Salva escalação no storage."""
    _escalations_storage[escalation.protocolo] = escalation


def _buscar_escalacao(protocolo: str) -> Optional[Escalation]:
    """Busca escalação pelo protocolo."""
    return _escalations_storage.get(protocolo.upper())


def _listar_escalacoes_pendentes() -> List[Escalation]:
    """Lista escalações pendentes."""
    return [
        e for e in _escalations_storage.values()
        if e.status == "pendente"
    ]


# =============================================================================
# Funções de Notificação (implementar conforme necessidade)
# =============================================================================

def _notificar_equipe(escalation: Escalation) -> bool:
    """
    Notifica a equipe sobre nova escalação.
    
    Em produção, integrar com:
    - Email (SMTP)
    - Slack/Teams
    - Sistema de tickets
    - Webhook
    """
    webhook_url = os.getenv("ESCALATION_WEBHOOK_URL")
    
    if webhook_url:
        try:
            import requests
            payload = {
                "protocolo": escalation.protocolo,
                "motivo": escalation.motivo,
                "prioridade": escalation.prioridade,
                "usuario": escalation.nome_usuario,
                "contato": escalation.contato,
                "resumo": escalation.resumo_conversa,
            }
            requests.post(webhook_url, json=payload, timeout=5)
            return True
        except Exception as e:
            print(f"[Escalation] Erro ao notificar: {e}")
            return False
    
    # Modo simulação
    print(f"[Escalation] Nova escalação: {escalation.protocolo}")
    return True


def _verificar_disponibilidade() -> Dict[str, Any]:
    """Verifica se atendimento humano está disponível."""
    agora = datetime.now()
    hora = agora.hour
    dia = agora.weekday()
    
    # Verificar variáveis de ambiente para horário customizado
    hora_inicio = int(os.getenv("ESCALATION_HOUR_START", DEFAULT_BUSINESS_HOURS["start"]))
    hora_fim = int(os.getenv("ESCALATION_HOUR_END", DEFAULT_BUSINESS_HOURS["end"]))
    
    disponivel = dia in DEFAULT_BUSINESS_HOURS["days"] and hora_inicio <= hora < hora_fim
    
    return {
        "disponivel": disponivel,
        "hora_atual": agora.strftime("%H:%M"),
        "dia_semana": ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][dia],
        "horario_atendimento": f"{hora_inicio:02d}:00 - {hora_fim:02d}:00",
        "dias_atendimento": "Segunda a Sexta",
    }


# =============================================================================
# Classificação Automática de Prioridade
# =============================================================================

def _classificar_prioridade(motivo: str, categoria: str) -> str:
    """
    Classifica automaticamente a prioridade baseado no motivo e categoria.
    """
    motivo_lower = motivo.lower()
    
    # Palavras que indicam urgência
    palavras_urgentes = [
        "urgente", "emergência", "emergencia", "crítico", "critico",
        "não funciona", "parou", "bloqueado", "cancelar", "prejuízo"
    ]
    
    palavras_alta = [
        "reclamação", "reclamacao", "insatisfeito", "problema grave",
        "já tentei", "terceira vez", "não resolve"
    ]
    
    # Verificar urgência
    for palavra in palavras_urgentes:
        if palavra in motivo_lower:
            return "urgente"
    
    # Verificar alta prioridade
    for palavra in palavras_alta:
        if palavra in motivo_lower:
            return "alta"
    
    # Frustração do usuário = alta
    if categoria == "frustracao":
        return "alta"
    
    return "normal"


# =============================================================================
# Tools do Agente de Escalação
# =============================================================================

@function_tool
def verificar_horario_atendimento() -> str:
    """
    Verifica se o atendimento humano está disponível no momento atual.
    Use esta ferramenta ANTES de registrar a escalação para informar o usuário.
    
    Returns:
        Status de disponibilidade do atendimento humano
    """
    info = _verificar_disponibilidade()
    
    if info["disponivel"]:
        return f"""✅ **Atendimento Humano DISPONÍVEL**

📅 {info['dia_semana']}, {info['hora_atual']}
⏰ Horário de atendimento: {info['horario_atendimento']}

Um atendente poderá retornar em breve após o registro."""
    else:
        return f"""⚠️ **Atendimento Humano FORA DO HORÁRIO**

📅 {info['dia_semana']}, {info['hora_atual']}
⏰ Horário de atendimento: {info['horario_atendimento']}
📆 Dias: {info['dias_atendimento']}

Você pode deixar seus dados e retornaremos no próximo horário disponível."""


@function_tool
def registrar_escalacao(
    motivo: str,
    nome_usuario: str,
    contato: str,
    tipo_contato: str = "telefone",
    resumo_conversa: str = "",
    categoria: str = "solicitacao",
) -> str:
    """
    Registra uma escalação para atendimento humano e notifica a equipe.
    
    IMPORTANTE: Use esta ferramenta quando:
    - O usuário solicitar falar com um humano
    - O tópico não for coberto pelo sistema
    - Não conseguir resolver o problema do usuário
    - O usuário demonstrar frustração
    
    Args:
        motivo: Motivo da escalação (descrição do que o usuário precisa)
        nome_usuario: Nome do usuário para contato
        contato: Telefone, email ou WhatsApp do usuário
        tipo_contato: Tipo de contato preferido ("telefone", "email", "whatsapp")
        resumo_conversa: Breve resumo do que foi discutido antes da escalação
        categoria: Categoria da escalação:
                  - "solicitacao": Usuário pediu para falar com humano
                  - "frustracao": Usuário demonstrou frustração
                  - "topico_nao_coberto": Assunto fora do escopo
                  - "incerteza": Agente não conseguiu resolver
              
    Returns:
        Confirmação com protocolo e próximos passos
    """
    # Validações
    if not nome_usuario or len(nome_usuario.strip()) < 2:
        return "❌ Por favor, informe seu nome completo para que possamos retornar."
    
    if not contato or len(contato.strip()) < 5:
        return "❌ Por favor, informe um contato válido (telefone, email ou WhatsApp)."
    
    if not motivo or len(motivo.strip()) < 5:
        return "❌ Por favor, descreva brevemente o motivo do contato."
    
    # Normalizar tipo de contato
    tipo_contato_norm = tipo_contato.lower().strip()
    if tipo_contato_norm not in ["telefone", "email", "whatsapp"]:
        tipo_contato_norm = "telefone"
    
    # Normalizar categoria
    categorias_validas = ["solicitacao", "frustracao", "topico_nao_coberto", "incerteza"]
    categoria_norm = categoria.lower().strip()
    if categoria_norm not in categorias_validas:
        categoria_norm = "solicitacao"
    
    # Classificar prioridade automaticamente
    prioridade = _classificar_prioridade(motivo, categoria_norm)
    
    # Criar escalação
    escalation = Escalation(
        protocolo=_gerar_protocolo_escalacao(),
        motivo=motivo.strip(),
        categoria=categoria_norm,
        nome_usuario=nome_usuario.strip(),
        contato=contato.strip(),
        tipo_contato=tipo_contato_norm,
        resumo_conversa=resumo_conversa.strip() if resumo_conversa else "",
        prioridade=prioridade,
        status="pendente",
    )
    
    # Salvar
    _salvar_escalacao(escalation)
    
    # Notificar equipe
    notificado = _notificar_equipe(escalation)
    
    # Verificar disponibilidade
    disp = _verificar_disponibilidade()
    
    # Ícones por prioridade
    icone_prioridade = {
        "baixa": "🟢",
        "normal": "🟡",
        "alta": "🟠",
        "urgente": "🔴",
    }.get(prioridade, "🟡")
    
    # Ícones por tipo de contato
    icone_contato = {
        "telefone": "📞",
        "email": "📧",
        "whatsapp": "💬",
    }.get(tipo_contato_norm, "📞")
    
    resposta = f"""
✅ **Escalação Registrada com Sucesso!**

═══════════════════════════════════════
📋 **Protocolo:** {escalation.protocolo}
═══════════════════════════════════════

👤 **Nome:** {escalation.nome_usuario}
{icone_contato} **Contato ({tipo_contato_norm}):** {escalation.contato}
{icone_prioridade} **Prioridade:** {prioridade.upper()}
📅 **Data:** {escalation.data_criacao.strftime('%d/%m/%Y às %H:%M')}

📝 **Motivo:**
{escalation.motivo}
"""
    
    if escalation.resumo_conversa:
        resposta += f"""
📄 **Resumo da conversa:**
{escalation.resumo_conversa[:200]}{'...' if len(escalation.resumo_conversa) > 200 else ''}
"""
    
    resposta += "\n═══════════════════════════════════════\n"
    
    if disp["disponivel"]:
        resposta += """
⏳ **Próximos Passos:**
Um atendente humano entrará em contato em breve.
"""
    else:
        resposta += f"""
⏳ **Próximos Passos:**
Estamos fora do horário de atendimento ({disp['horario_atendimento']}).
Um atendente retornará no próximo dia útil.
"""
    
    resposta += f"""
💡 **Dica:** Guarde o protocolo **{escalation.protocolo}** para acompanhamento.
"""
    
    if notificado:
        resposta += "\n✅ Nossa equipe foi notificada."
    
    return resposta


@function_tool
def consultar_escalacao(protocolo: str) -> str:
    """
    Consulta o status de uma escalação pelo protocolo.
    
    Args:
        protocolo: Número do protocolo (ex: ESC-20240105-ABC123)
        
    Returns:
        Status e detalhes da escalação
    """
    escalation = _buscar_escalacao(protocolo)
    
    if not escalation:
        return f"""❌ **Escalação não encontrada:** {protocolo}

Verifique se o número do protocolo está correto.
Formato esperado: ESC-YYYYMMDD-XXXXXX"""
    
    # Ícones de status
    icone_status = {
        "pendente": "🟡",
        "em_atendimento": "🔵",
        "concluido": "🟢",
        "cancelado": "⚫",
    }.get(escalation.status, "⚪")
    
    resposta = f"""
📋 **Consulta de Escalação**

═══════════════════════════════════════
🔖 **Protocolo:** {escalation.protocolo}
{icone_status} **Status:** {escalation.status.upper().replace('_', ' ')}
═══════════════════════════════════════

👤 **Solicitante:** {escalation.nome_usuario}
📞 **Contato:** {escalation.contato} ({escalation.tipo_contato})
⚡ **Prioridade:** {escalation.prioridade.upper()}

📅 **Criado em:** {escalation.data_criacao.strftime('%d/%m/%Y às %H:%M')}
📅 **Atualizado em:** {escalation.data_atualizacao.strftime('%d/%m/%Y às %H:%M')}

📝 **Motivo:**
{escalation.motivo}
"""
    
    if escalation.atendente:
        resposta += f"\n👨‍💼 **Atendente:** {escalation.atendente}"
    
    if escalation.observacoes:
        resposta += f"\n\n📌 **Observações:**\n{escalation.observacoes}"
    
    return resposta


# =============================================================================
# Lista de Tools
# =============================================================================

ESCALATION_TOOLS = [
    verificar_horario_atendimento,
    registrar_escalacao,
    consultar_escalacao,
]


# =============================================================================
# Triggers e Instruções movidos para atendentepro/prompts/escalation.py
# =============================================================================

# Re-exportar para compatibilidade
# DEFAULT_ESCALATION_TRIGGERS e ESCALATION_INTRO estão em prompts/escalation.py


# =============================================================================
# Criar Escalation Agent
# =============================================================================

def create_escalation_agent(
    escalation_triggers: str = "",
    escalation_channels: str = "",
    handoffs: Optional[List] = None,
    tools: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Escalation Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> EscalationAgent:
    """
    Create an Escalation Agent instance.
    
    The escalation agent handles transfers to human support when:
    - User explicitly requests to talk to a human
    - Topic is not covered by the automated system
    - Agent cannot resolve the issue after attempts
    - User shows frustration or confusion
    
    This agent should be added as a handoff option to ALL other agents
    in the network to ensure users can always escalate when needed.
    
    Args:
        escalation_triggers: Custom triggers for escalation (keywords, situations).
        escalation_channels: Available contact channels description.
        handoffs: List of agents to hand off to (usually triage to return).
        tools: Additional tools (custom notifications, integrations).
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Optional custom instructions to override default.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Escalation Agent instance.
        
    Example:
        >>> escalation = create_escalation_agent(
        ...     escalation_channels="Telefone: 0800-123-4567 (Seg-Sex 8h-18h)",
        ...     handoffs=[triage],
        ... )
        >>> # Add to all agents
        >>> triage.handoffs.append(escalation)
        >>> flow.handoffs.append(escalation)
    """
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        # Usar o prompt builder do módulo prompts
        instructions = f"{RECOMMENDED_PROMPT_PREFIX}\n{get_escalation_prompt(escalation_triggers=escalation_triggers, escalation_channels=escalation_channels)}"
    
    # Append style instructions if provided
    if style_instructions:
        instructions += style_instructions
    
    # Single reply mode: respond once then return to triage
    if single_reply:
        instructions += "\n\nIMPORTANTE: Após fornecer sua resposta, transfira IMEDIATAMENTE para o triage_agent. Você só pode dar UMA resposta antes de transferir."
    
    # Combinar tools padrão com customizadas
    agent_tools = list(ESCALATION_TOOLS)
    if tools:
        agent_tools.extend(tools)
    
    return Agent[ContextNote](
        name=name,
        handoff_description="Transfere para atendimento humano quando o agente não consegue resolver, o tópico não é coberto, ou o usuário solicita.",
        instructions=instructions,
        tools=agent_tools,
        handoffs=handoffs or [],
        input_guardrails=guardrails or [],
    )

