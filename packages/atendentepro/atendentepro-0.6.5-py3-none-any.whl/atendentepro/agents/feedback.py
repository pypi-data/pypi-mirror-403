# -*- coding: utf-8 -*-
"""
Feedback Agent for AtendentePro.

Handles user feedback, questions, complaints, and suggestions through
a ticket-based system with email notifications.

This is a universal module for all customer service systems,
allowing users to:
- Register questions (dúvidas)
- Send feedback
- File complaints (reclamações)
- Submit suggestions (sugestões)
- Give compliments (elogios)
- Report problems

All tickets are tracked with unique protocol numbers and can be
configured with custom email templates per client.
"""

from __future__ import annotations

import os
import re
import smtplib
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Callable
from dataclasses import dataclass, field
from enum import Enum

from agents import Agent, function_tool

from atendentepro.config import RECOMMENDED_PROMPT_PREFIX
from atendentepro.models import ContextNote
from atendentepro.prompts.feedback import (
    get_feedback_prompt,
    FeedbackPromptBuilder,
    FEEDBACK_INTRO,
    DEFAULT_TICKET_TYPES,
)

if TYPE_CHECKING:
    from atendentepro.guardrails import GuardrailCallable


# Type alias for the Feedback Agent
FeedbackAgent = Agent[ContextNote]


# =============================================================================
# Enums for Ticket Properties
# =============================================================================

class TicketType(str, Enum):
    """Default ticket types."""
    DUVIDA = "duvida"
    FEEDBACK = "feedback"
    RECLAMACAO = "reclamacao"
    SUGESTAO = "sugestao"
    ELOGIO = "elogio"
    PROBLEMA = "problema"
    OUTRO = "outro"


class TicketPriority(str, Enum):
    """Ticket priority levels."""
    BAIXA = "baixa"
    NORMAL = "normal"
    ALTA = "alta"
    URGENTE = "urgente"


class TicketStatus(str, Enum):
    """Ticket status states."""
    ABERTO = "aberto"
    EM_ANDAMENTO = "em_andamento"
    AGUARDANDO = "aguardando_usuario"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"
    CANCELADO = "cancelado"


# =============================================================================
# Ticket Data Model
# =============================================================================

@dataclass
class Ticket:
    """Represents a feedback/support ticket."""
    protocolo: str
    tipo: str
    descricao: str
    email_usuario: str
    nome_usuario: str = ""
    telefone_usuario: str = ""
    prioridade: str = "normal"
    status: str = "aberto"
    categoria: str = ""
    data_criacao: datetime = field(default_factory=datetime.now)
    data_atualizacao: datetime = field(default_factory=datetime.now)
    resposta: Optional[str] = None
    atendente: Optional[str] = None
    historico: List[Dict[str, Any]] = field(default_factory=list)
    
    def adicionar_historico(self, acao: str, detalhes: str = "") -> None:
        """Add entry to ticket history."""
        self.historico.append({
            "data": datetime.now().isoformat(),
            "acao": acao,
            "detalhes": detalhes,
        })
        self.data_atualizacao = datetime.now()


# =============================================================================
# Storage (in-memory, replace with DB in production)
# =============================================================================

_tickets_storage: Dict[str, Ticket] = {}

# Protocol prefix (can be customized per client)
_protocol_prefix: str = "TKT"

# Email configuration
_email_config: Dict[str, Any] = {
    "enabled": True,
    "brand_color": "#4A90D9",
    "brand_name": "Atendimento",
    "sla_message": "Retornaremos em até 24h úteis.",
}


def configure_feedback_storage(
    protocol_prefix: str = "TKT",
    email_brand_color: str = "#4A90D9",
    email_brand_name: str = "Atendimento",
    email_sla_message: str = "Retornaremos em até 24h úteis.",
) -> None:
    """
    Configure feedback storage settings.
    
    Args:
        protocol_prefix: Prefix for ticket protocols (e.g., "SAC", "TKT", "SUP")
        email_brand_color: Hex color for email template branding
        email_brand_name: Brand name for email template
        email_sla_message: SLA message shown in confirmation email
    """
    global _protocol_prefix, _email_config
    _protocol_prefix = protocol_prefix
    _email_config.update({
        "brand_color": email_brand_color,
        "brand_name": email_brand_name,
        "sla_message": email_sla_message,
    })


def _gerar_protocolo() -> str:
    """Generate unique ticket protocol."""
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:6].upper()
    return f"{_protocol_prefix}-{timestamp}-{unique_id}"


def _salvar_ticket(ticket: Ticket) -> None:
    """Save ticket to storage."""
    _tickets_storage[ticket.protocolo.upper()] = ticket


def _buscar_ticket(protocolo: str) -> Optional[Ticket]:
    """Find ticket by protocol."""
    return _tickets_storage.get(protocolo.upper())


def _listar_tickets(email: Optional[str] = None, status: Optional[str] = None) -> List[Ticket]:
    """List tickets, optionally filtered."""
    tickets = list(_tickets_storage.values())
    
    if email:
        tickets = [t for t in tickets if t.email_usuario.lower() == email.lower()]
    
    if status:
        tickets = [t for t in tickets if t.status.lower() == status.lower()]
    
    return sorted(tickets, key=lambda x: x.data_criacao, reverse=True)


# =============================================================================
# Email Functions
# =============================================================================

# SMTP configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "sac@empresa.com")
FEEDBACK_EMAIL_DESTINO = os.getenv("FEEDBACK_EMAIL_DESTINO", "")


def _validar_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _enviar_email(
    destinatario: str,
    assunto: str,
    corpo_html: str,
    corpo_texto: Optional[str] = None,
) -> bool:
    """
    Send email via SMTP.
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[Feedback] ⚠️ SMTP não configurado - email não enviado para {destinatario}")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = SMTP_FROM
        msg["To"] = destinatario
        
        if corpo_texto:
            part_texto = MIMEText(corpo_texto, "plain", "utf-8")
            msg.attach(part_texto)
        
        part_html = MIMEText(corpo_html, "html", "utf-8")
        msg.attach(part_html)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"[Feedback] ✅ Email enviado para {destinatario}")
        return True
        
    except Exception as e:
        print(f"[Feedback] ❌ Erro ao enviar email: {e}")
        return False


def _gerar_email_confirmacao(ticket: Ticket) -> str:
    """Generate HTML email template for ticket confirmation."""
    tipo_display = {
        "duvida": "Dúvida",
        "feedback": "Feedback",
        "reclamacao": "Reclamação",
        "sugestao": "Sugestão",
        "elogio": "Elogio",
        "problema": "Problema",
        "outro": "Outro",
    }.get(ticket.tipo.lower(), ticket.tipo.title())
    
    prioridade_display = {
        "baixa": "🟢 Baixa",
        "normal": "🟡 Normal",
        "alta": "🟠 Alta",
        "urgente": "🔴 Urgente",
    }.get(ticket.prioridade.lower(), ticket.prioridade.title())
    
    nome = ticket.nome_usuario or "Cliente"
    brand_color = _email_config.get("brand_color", "#4A90D9")
    brand_name = _email_config.get("brand_name", "Atendimento")
    sla_message = _email_config.get("sla_message", "Retornaremos em breve.")
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f5f5f5; padding: 20px;">
    <div style="background-color: {brand_color}; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">{brand_name}</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">Ticket Registrado com Sucesso</p>
    </div>
    
    <div style="background-color: white; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <p style="font-size: 16px; color: #333;">Olá <strong>{nome}</strong>,</p>
        
        <p style="color: #666;">Recebemos sua solicitação e ela foi registrada com sucesso!</p>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {brand_color};">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; color: #666;">📋 Protocolo:</td>
                    <td style="padding: 8px 0; font-weight: bold; color: {brand_color};">{ticket.protocolo}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666;">📌 Tipo:</td>
                    <td style="padding: 8px 0;">{tipo_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666;">⚡ Prioridade:</td>
                    <td style="padding: 8px 0;">{prioridade_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; color: #666;">📅 Data:</td>
                    <td style="padding: 8px 0;">{ticket.data_criacao.strftime('%d/%m/%Y às %H:%M')}</td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #fff; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; margin: 20px 0;">
            <p style="color: #666; margin: 0 0 10px 0; font-weight: bold;">📝 Descrição:</p>
            <p style="color: #333; margin: 0; line-height: 1.6;">{ticket.descricao}</p>
        </div>
        
        <p style="color: #666; font-size: 14px;">{sla_message}</p>
        
        <p style="color: #888; font-size: 13px; margin-top: 25px;">
            💡 Guarde o protocolo <strong>{ticket.protocolo}</strong> para acompanhamento.
        </p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 25px 0;">
        
        <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
            Este email foi enviado automaticamente. Por favor, não responda.
        </p>
    </div>
</body>
</html>
"""


def _gerar_email_equipe(ticket: Ticket) -> str:
    """Generate HTML email template for team notification."""
    tipo_display = {
        "duvida": "❓ Dúvida",
        "feedback": "💬 Feedback",
        "reclamacao": "📢 Reclamação",
        "sugestao": "💡 Sugestão",
        "elogio": "⭐ Elogio",
        "problema": "⚠️ Problema",
        "outro": "📋 Outro",
    }.get(ticket.tipo.lower(), ticket.tipo.title())
    
    prioridade_colors = {
        "baixa": "#28a745",
        "normal": "#ffc107",
        "alta": "#fd7e14",
        "urgente": "#dc3545",
    }
    prioridade_color = prioridade_colors.get(ticket.prioridade.lower(), "#6c757d")
    
    brand_color = _email_config.get("brand_color", "#4A90D9")
    brand_name = _email_config.get("brand_name", "Atendimento")
    
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background-color: {brand_color}; color: white; padding: 20px; text-align: center;">
        <h2 style="margin: 0;">🎫 Novo Ticket - {brand_name}</h2>
    </div>
    
    <div style="padding: 20px; background-color: #f9f9f9;">
        <div style="background-color: white; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
            <h3 style="margin: 0 0 15px 0; color: #333;">
                {tipo_display}
                <span style="background-color: {prioridade_color}; color: white; padding: 3px 10px; border-radius: 4px; font-size: 12px; margin-left: 10px;">
                    {ticket.prioridade.upper()}
                </span>
            </h3>
            
            <table style="width: 100%;">
                <tr>
                    <td style="padding: 5px 0; color: #666; width: 120px;">Protocolo:</td>
                    <td style="padding: 5px 0; font-weight: bold;">{ticket.protocolo}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0; color: #666;">Nome:</td>
                    <td style="padding: 5px 0;">{ticket.nome_usuario or 'Não informado'}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0; color: #666;">Email:</td>
                    <td style="padding: 5px 0;"><a href="mailto:{ticket.email_usuario}">{ticket.email_usuario}</a></td>
                </tr>
                <tr>
                    <td style="padding: 5px 0; color: #666;">Telefone:</td>
                    <td style="padding: 5px 0;">{ticket.telefone_usuario or 'Não informado'}</td>
                </tr>
                <tr>
                    <td style="padding: 5px 0; color: #666;">Data:</td>
                    <td style="padding: 5px 0;">{ticket.data_criacao.strftime('%d/%m/%Y às %H:%M')}</td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: white; padding: 20px; border-radius: 8px;">
            <h4 style="margin: 0 0 10px 0; color: #666;">📝 Descrição:</h4>
            <p style="margin: 0; color: #333; line-height: 1.6; white-space: pre-wrap;">{ticket.descricao}</p>
        </div>
    </div>
</body>
</html>
"""


# =============================================================================
# Feedback Tools
# =============================================================================

@function_tool
def criar_ticket(
    tipo: str,
    descricao: str,
    email_usuario: str,
    nome_usuario: str = "",
    telefone_usuario: str = "",
    prioridade: str = "normal",
    categoria: str = "",
) -> str:
    """
    Cria um ticket de feedback, dúvida, reclamação ou sugestão.
    
    IMPORTANTE: Esta ferramenta registra solicitações para análise posterior.
    Use quando o usuário quer:
    - Tirar uma dúvida que precisa de pesquisa
    - Enviar feedback sobre produto/serviço
    - Fazer uma reclamação formal
    - Dar uma sugestão de melhoria
    - Fazer um elogio
    - Reportar um problema técnico
    
    Args:
        tipo: Tipo do ticket. Valores aceitos:
              - "duvida": Pergunta que precisa de pesquisa
              - "feedback": Opinião sobre produto/serviço
              - "reclamacao": Reclamação formal
              - "sugestao": Sugestão de melhoria
              - "elogio": Elogio ou agradecimento
              - "problema": Problema técnico ou bug
        descricao: Descrição detalhada da solicitação (mínimo 10 caracteres)
        email_usuario: Email do usuário para resposta e acompanhamento
        nome_usuario: Nome do usuário (opcional, mas recomendado)
        telefone_usuario: Telefone para contato alternativo (opcional)
        prioridade: Nível de urgência. Valores aceitos:
                   - "baixa": Pode aguardar
                   - "normal": Atendimento padrão (default)
                   - "alta": Requer atenção prioritária
                   - "urgente": Crítico, precisa de ação imediata
        categoria: Categoria adicional do ticket (opcional)
        
    Returns:
        Confirmação com número do protocolo e detalhes
    """
    # Validar tipo
    tipos_validos = ["duvida", "feedback", "reclamacao", "sugestao", "elogio", "problema", "outro"]
    tipo_norm = tipo.lower().strip().replace("ã", "a").replace("ç", "c")
    
    if tipo_norm not in tipos_validos:
        return f"""❌ **Tipo inválido:** {tipo}

📋 **Tipos aceitos:**
- `duvida` - Pergunta que precisa de pesquisa
- `feedback` - Opinião sobre produto/serviço  
- `reclamacao` - Reclamação formal
- `sugestao` - Sugestão de melhoria
- `elogio` - Elogio ou agradecimento
- `problema` - Problema técnico"""
    
    # Validar descrição
    if not descricao or len(descricao.strip()) < 10:
        return "❌ **Descrição muito curta.** Por favor, forneça mais detalhes (mínimo 10 caracteres)."
    
    # Validar email
    email_norm = email_usuario.strip().lower()
    if not _validar_email(email_norm):
        return f"❌ **Email inválido:** {email_usuario}\n\nPor favor, informe um email válido para que possamos responder."
    
    # Validar prioridade
    prioridades_validas = ["baixa", "normal", "alta", "urgente"]
    prioridade_norm = prioridade.lower().strip()
    if prioridade_norm not in prioridades_validas:
        prioridade_norm = "normal"
    
    # Auto-classificar prioridade para reclamações
    if tipo_norm == "reclamacao" and prioridade_norm == "normal":
        prioridade_norm = "alta"
    
    # Criar ticket
    protocolo = _gerar_protocolo()
    ticket = Ticket(
        protocolo=protocolo,
        tipo=tipo_norm,
        descricao=descricao.strip(),
        email_usuario=email_norm,
        nome_usuario=nome_usuario.strip() if nome_usuario else "",
        telefone_usuario=telefone_usuario.strip() if telefone_usuario else "",
        prioridade=prioridade_norm,
        status="aberto",
        categoria=categoria.strip() if categoria else "",
    )
    
    ticket.adicionar_historico(
        "Ticket criado",
        f"Tipo: {tipo_norm}, Prioridade: {prioridade_norm}"
    )
    
    _salvar_ticket(ticket)
    
    # Ícones
    icone_tipo = {
        "duvida": "❓",
        "feedback": "💬",
        "reclamacao": "📢",
        "sugestao": "💡",
        "elogio": "⭐",
        "problema": "⚠️",
        "outro": "📋",
    }.get(tipo_norm, "📋")
    
    icone_prioridade = {
        "baixa": "🟢",
        "normal": "🟡",
        "alta": "🟠",
        "urgente": "🔴",
    }.get(prioridade_norm, "🟡")
    
    tipo_display = {
        "duvida": "Dúvida",
        "feedback": "Feedback",
        "reclamacao": "Reclamação",
        "sugestao": "Sugestão",
        "elogio": "Elogio",
        "problema": "Problema",
        "outro": "Outro",
    }.get(tipo_norm, tipo_norm.title())
    
    return f"""
✅ **Ticket Criado com Sucesso!**

═══════════════════════════════════════
📋 **Protocolo:** {protocolo}
═══════════════════════════════════════

{icone_tipo} **Tipo:** {tipo_display}
{icone_prioridade} **Prioridade:** {prioridade_norm.upper()}
📅 **Data:** {ticket.data_criacao.strftime('%d/%m/%Y às %H:%M')}

👤 **Dados de Contato:**
- Nome: {nome_usuario or 'Não informado'}
- Email: {email_norm}
- Telefone: {telefone_usuario or 'Não informado'}

📝 **Descrição:**
{descricao[:200]}{'...' if len(descricao) > 200 else ''}

═══════════════════════════════════════

💡 **Guarde o protocolo {protocolo}** para consultar o status.

📧 Use `enviar_email_confirmacao("{protocolo}")` para enviar confirmação ao usuário.
"""


@function_tool
def enviar_email_confirmacao(protocolo: str) -> str:
    """
    Envia email de confirmação do ticket para o usuário.
    
    IMPORTANTE: Chame esta ferramenta APÓS criar o ticket para
    enviar a confirmação oficial por email.
    
    Args:
        protocolo: Número do protocolo do ticket (ex: TKT-20240106-ABC123)
        
    Returns:
        Confirmação do envio ou mensagem de erro
    """
    ticket = _buscar_ticket(protocolo)
    
    if not ticket:
        return f"""❌ **Ticket não encontrado:** {protocolo}

Verifique se o número do protocolo está correto.
Formato esperado: {_protocol_prefix}-YYYYMMDD-XXXXXX"""
    
    # Enviar para usuário
    assunto = f"[{_email_config.get('brand_name', 'Atendimento')}] Ticket {ticket.protocolo} - Recebemos sua solicitação"
    corpo_html = _gerar_email_confirmacao(ticket)
    
    enviado_usuario = _enviar_email(ticket.email_usuario, assunto, corpo_html)
    
    # Enviar para equipe (se configurado)
    enviado_equipe = False
    if FEEDBACK_EMAIL_DESTINO:
        assunto_equipe = f"[NOVO TICKET] {ticket.tipo.upper()} - {ticket.protocolo}"
        corpo_equipe = _gerar_email_equipe(ticket)
        enviado_equipe = _enviar_email(FEEDBACK_EMAIL_DESTINO, assunto_equipe, corpo_equipe)
    
    # Registrar no histórico
    ticket.adicionar_historico(
        "Email de confirmação",
        f"Usuário: {'✅' if enviado_usuario else '❌'}, Equipe: {'✅' if enviado_equipe else '❌ (não configurado)' if not FEEDBACK_EMAIL_DESTINO else '❌'}"
    )
    _salvar_ticket(ticket)
    
    if enviado_usuario:
        return f"""✅ **Email de confirmação enviado!**

📧 Destinatário: {ticket.email_usuario}
📋 Protocolo: {ticket.protocolo}
{"📧 Equipe também notificada!" if enviado_equipe else ""}

O usuário receberá o email em alguns minutos.
"""
    else:
        return f"""⚠️ **Email não enviado** (SMTP não configurado)

📋 Protocolo: {ticket.protocolo}
📧 Destinatário: {ticket.email_usuario}

💡 Para habilitar envio de emails, configure as variáveis de ambiente:
- SMTP_HOST
- SMTP_PORT
- SMTP_USER
- SMTP_PASSWORD
- SMTP_FROM

O ticket foi criado e pode ser consultado pelo protocolo.
"""


@function_tool
def consultar_ticket(protocolo: str) -> str:
    """
    Consulta detalhes e status de um ticket pelo protocolo.
    
    Args:
        protocolo: Número do protocolo (ex: TKT-20240106-ABC123, SAC-20240106-XYZ789)
        
    Returns:
        Detalhes completos do ticket ou mensagem de não encontrado
    """
    ticket = _buscar_ticket(protocolo)
    
    if not ticket:
        return f"""❌ **Ticket não encontrado:** {protocolo}

Verifique se o número do protocolo está correto.
Formato esperado: {_protocol_prefix}-YYYYMMDD-XXXXXX

💡 Use `listar_meus_tickets("email@exemplo.com")` para ver todos os seus tickets.
"""
    
    # Ícones
    icone_tipo = {
        "duvida": "❓",
        "feedback": "💬",
        "reclamacao": "📢",
        "sugestao": "💡",
        "elogio": "⭐",
        "problema": "⚠️",
        "outro": "📋",
    }.get(ticket.tipo.lower(), "📋")
    
    icone_status = {
        "aberto": "🟡",
        "em_andamento": "🔵",
        "aguardando_usuario": "🟠",
        "resolvido": "🟢",
        "fechado": "⚫",
        "cancelado": "🔴",
    }.get(ticket.status.lower(), "⚪")
    
    icone_prioridade = {
        "baixa": "🟢",
        "normal": "🟡",
        "alta": "🟠",
        "urgente": "🔴",
    }.get(ticket.prioridade.lower(), "🟡")
    
    tipo_display = ticket.tipo.replace("_", " ").title()
    status_display = ticket.status.replace("_", " ").upper()
    
    resultado = f"""
📋 **Consulta de Ticket**

═══════════════════════════════════════
🔖 **Protocolo:** {ticket.protocolo}
{icone_status} **Status:** {status_display}
═══════════════════════════════════════

{icone_tipo} **Tipo:** {tipo_display}
{icone_prioridade} **Prioridade:** {ticket.prioridade.upper()}

👤 **Solicitante:**
- Nome: {ticket.nome_usuario or 'Não informado'}
- Email: {ticket.email_usuario}
- Telefone: {ticket.telefone_usuario or 'Não informado'}

📅 **Datas:**
- Criado: {ticket.data_criacao.strftime('%d/%m/%Y às %H:%M')}
- Atualizado: {ticket.data_atualizacao.strftime('%d/%m/%Y às %H:%M')}

📝 **Descrição:**
{ticket.descricao}
"""
    
    if ticket.resposta:
        resultado += f"""
💬 **Resposta:**
{ticket.resposta}
"""
    
    if ticket.atendente:
        resultado += f"\n👨‍💼 **Atendente:** {ticket.atendente}"
    
    if ticket.historico:
        resultado += "\n\n📜 **Histórico:**\n"
        for h in ticket.historico[-5:]:  # Últimos 5 registros
            data = h.get("data", "")[:16].replace("T", " ")
            resultado += f"- [{data}] {h.get('acao', '')}"
            if h.get("detalhes"):
                resultado += f" - {h.get('detalhes')}"
            resultado += "\n"
    
    return resultado


@function_tool
def listar_meus_tickets(email: str, status: str = "") -> str:
    """
    Lista todos os tickets de um usuário pelo email.
    
    Args:
        email: Email do usuário
        status: Filtrar por status (opcional): aberto, em_andamento, resolvido, fechado
        
    Returns:
        Lista de tickets ou mensagem se não houver nenhum
    """
    if not _validar_email(email):
        return f"❌ **Email inválido:** {email}"
    
    tickets = _listar_tickets(email=email.lower(), status=status if status else None)
    
    if not tickets:
        msg = f"📭 **Nenhum ticket encontrado** para {email}"
        if status:
            msg += f" com status '{status}'"
        return msg
    
    resultado = f"""
📋 **Tickets de {email}**

Total: {len(tickets)} ticket(s)
{'Status: ' + status.upper() if status else ''}

═══════════════════════════════════════
"""
    
    for t in tickets[:10]:  # Mostrar até 10
        icone_status = {
            "aberto": "🟡",
            "em_andamento": "🔵",
            "aguardando_usuario": "🟠",
            "resolvido": "🟢",
            "fechado": "⚫",
            "cancelado": "🔴",
        }.get(t.status.lower(), "⚪")
        
        icone_tipo = {
            "duvida": "❓",
            "feedback": "💬",
            "reclamacao": "📢",
            "sugestao": "💡",
            "elogio": "⭐",
            "problema": "⚠️",
        }.get(t.tipo.lower(), "📋")
        
        resultado += f"""
{icone_status} **{t.protocolo}** {icone_tipo}
   📅 {t.data_criacao.strftime('%d/%m/%Y')} | {t.tipo.title()} | {t.status.replace('_', ' ').title()}
   📝 {t.descricao[:50]}{'...' if len(t.descricao) > 50 else ''}
"""
    
    if len(tickets) > 10:
        resultado += f"\n... e mais {len(tickets) - 10} ticket(s)"
    
    resultado += "\n═══════════════════════════════════════"
    resultado += "\n💡 Use `consultar_ticket(\"PROTOCOLO\")` para ver detalhes."
    
    return resultado


@function_tool
def atualizar_ticket(
    protocolo: str,
    status: str = "",
    resposta: str = "",
    atendente: str = "",
) -> str:
    """
    Atualiza o status ou adiciona resposta a um ticket.
    
    Args:
        protocolo: Número do protocolo do ticket
        status: Novo status (aberto, em_andamento, aguardando_usuario, resolvido, fechado, cancelado)
        resposta: Resposta ou comentário a adicionar
        atendente: Nome do atendente responsável
        
    Returns:
        Confirmação da atualização
    """
    ticket = _buscar_ticket(protocolo)
    
    if not ticket:
        return f"❌ **Ticket não encontrado:** {protocolo}"
    
    atualizacoes = []
    
    if status:
        status_validos = ["aberto", "em_andamento", "aguardando_usuario", "resolvido", "fechado", "cancelado"]
        status_norm = status.lower().strip().replace(" ", "_")
        if status_norm in status_validos:
            status_anterior = ticket.status
            ticket.status = status_norm
            ticket.adicionar_historico("Status alterado", f"{status_anterior} → {status_norm}")
            atualizacoes.append(f"Status: {status_norm.upper()}")
    
    if resposta:
        ticket.resposta = resposta.strip()
        ticket.adicionar_historico("Resposta adicionada", resposta[:50] + "...")
        atualizacoes.append("Resposta adicionada")
    
    if atendente:
        ticket.atendente = atendente.strip()
        ticket.adicionar_historico("Atendente atribuído", atendente)
        atualizacoes.append(f"Atendente: {atendente}")
    
    if not atualizacoes:
        return "⚠️ Nenhuma atualização fornecida. Informe status, resposta ou atendente."
    
    _salvar_ticket(ticket)
    
    return f"""✅ **Ticket atualizado!**

📋 **Protocolo:** {ticket.protocolo}

📝 **Atualizações:**
{chr(10).join('- ' + a for a in atualizacoes)}

📅 **Atualizado em:** {ticket.data_atualizacao.strftime('%d/%m/%Y às %H:%M')}
"""


# =============================================================================
# List of Tools
# =============================================================================

FEEDBACK_TOOLS = [
    criar_ticket,
    enviar_email_confirmacao,
    consultar_ticket,
    listar_meus_tickets,
    atualizar_ticket,
]


# =============================================================================
# Instruções movidas para atendentepro/prompts/feedback.py
# =============================================================================

# DEFAULT_FEEDBACK_INSTRUCTIONS, FEEDBACK_INTRO e DEFAULT_TICKET_TYPES
# estão em prompts/feedback.py


# =============================================================================
# Create Feedback Agent
# =============================================================================

def create_feedback_agent(
    protocol_prefix: str = "TKT",
    email_brand_color: str = "#4A90D9",
    email_brand_name: str = "Atendimento",
    email_sla_message: str = "Retornaremos em até 24h úteis.",
    ticket_types: Optional[List[str]] = None,
    handoffs: Optional[List] = None,
    tools: Optional[List] = None,
    guardrails: Optional[List["GuardrailCallable"]] = None,
    name: str = "Feedback Agent",
    custom_instructions: Optional[str] = None,
    style_instructions: str = "",
    single_reply: bool = False,
) -> FeedbackAgent:
    """
    Create a Feedback Agent for collecting user feedback, questions, and complaints.
    
    The feedback agent handles:
    - Questions (dúvidas) that need research
    - Product/service feedback
    - Formal complaints (reclamações)
    - Improvement suggestions
    - Compliments (elogios)
    - Technical problems
    
    All interactions are tracked with unique protocol numbers.
    
    Args:
        protocol_prefix: Prefix for ticket protocols (e.g., "SAC", "TKT", "SUP").
        email_brand_color: Hex color for email branding (e.g., "#660099").
        email_brand_name: Brand name shown in emails.
        email_sla_message: SLA message shown in confirmation emails.
        ticket_types: Custom list of allowed ticket types (default: all).
        handoffs: List of agents to hand off to.
        tools: Additional custom tools.
        guardrails: List of input guardrails.
        name: Agent name.
        custom_instructions: Override default instructions.
        style_instructions: Optional style/tone instructions to append.
        single_reply: If True, agent responds once then transfers to triage.
        
    Returns:
        Configured Feedback Agent instance.
        
    Example:
        >>> feedback = create_feedback_agent(
        ...     protocol_prefix="SAC",
        ...     email_brand_color="#660099",
        ...     email_brand_name="Vivo Empresas",
        ... )
    """
    # Configure storage settings
    configure_feedback_storage(
        protocol_prefix=protocol_prefix,
        email_brand_color=email_brand_color,
        email_brand_name=email_brand_name,
        email_sla_message=email_sla_message,
    )
    
    # Build instructions using prompt builder
    if custom_instructions:
        instructions = f"{RECOMMENDED_PROMPT_PREFIX} {custom_instructions}"
    else:
        # Usar o prompt builder do módulo prompts
        instructions = f"{RECOMMENDED_PROMPT_PREFIX}\n{get_feedback_prompt(ticket_types=ticket_types, protocol_prefix=protocol_prefix, brand_name=email_brand_name, sla_message=email_sla_message)}"
    
    # Append style instructions if provided
    if style_instructions:
        instructions += style_instructions
    
    # Single reply mode: respond once then return to triage
    if single_reply:
        instructions += "\n\nIMPORTANTE: Após fornecer sua resposta, transfira IMEDIATAMENTE para o triage_agent. Você só pode dar UMA resposta antes de transferir."
    
    # Combine tools
    agent_tools = list(FEEDBACK_TOOLS)
    if tools:
        agent_tools.extend(tools)
    
    return Agent[ContextNote](
        name=name,
        handoff_description="Registra dúvidas, feedbacks, reclamações, sugestões e elogios dos usuários através de tickets com protocolo.",
        instructions=instructions,
        tools=agent_tools,
        handoffs=handoffs or [],
        input_guardrails=guardrails or [],
    )

