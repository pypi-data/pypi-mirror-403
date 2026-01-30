# -*- coding: utf-8 -*-
"""
AtendentePro - Sistema de Atendimento Inteligente com Múltiplos Agentes IA

Uma biblioteca Python modular para criar sistemas de atendimento automatizado
usando múltiplos agentes de IA especializados.

⚠️ ATIVAÇÃO NECESSÁRIA:

    Esta biblioteca requer um token de licença para funcionar.
    
    Opção 1 - Ativar programaticamente:
    
        from atendentepro import activate
        activate("seu-token-de-acesso")
        
    Opção 2 - Variável de ambiente:
    
        export ATENDENTEPRO_LICENSE_KEY="seu-token-de-acesso"

Exemplo de uso básico:

    from atendentepro import activate, create_standard_network, configure
    from pathlib import Path
    
    # 1. Ativar a biblioteca
    activate("seu-token-de-acesso")
    
    # 2. Configurar a biblioteca
    configure(provider="openai", openai_api_key="sua-chave")
    
    # 3. Criar rede de agentes
    network = create_standard_network(
        templates_root=Path("./client_templates"),
        client="standard"
    )
    
    # 4. Usar o agente de triagem como ponto de entrada
    triage_agent = network.triage

Para obter um token de licença, entre em contato: contato@monkai.com.br
Para mais informações, consulte a documentação.
"""

__version__ = "0.5.0"
__author__ = "BeMonkAI"
__email__ = "contato@monkai.com.br"
__license__ = "Proprietary"

# License (deve ser importado primeiro)
from atendentepro.license import (
    activate,
    deactivate,
    is_activated,
    get_license_info,
    require_activation,
    has_feature,
    generate_license_token,
    LicenseInfo,
    LicenseError,
    LicenseNotActivatedError,
    LicenseExpiredError,
    InvalidTokenError,
)

# Configuration
from atendentepro.config import (
    AtendentProConfig,
    get_config,
    configure,
    RECOMMENDED_PROMPT_PREFIX,
    DEFAULT_MODEL,
)

# Models
from atendentepro.models import (
    ContextNote,
    FlowTopic,
    FlowOutput,
    InterviewOutput,
    KnowledgeToolResult,
    GuardrailValidationOutput,
    # Access filtering
    UserContext,
    AccessFilter,
    FilteredPromptSection,
    FilteredTool,
)

# Agents
from atendentepro.agents import (
    create_triage_agent,
    create_flow_agent,
    create_interview_agent,
    create_answer_agent,
    create_knowledge_agent,
    create_confirmation_agent,
    create_usage_agent,
    create_onboarding_agent,
    create_escalation_agent,
    create_feedback_agent,
    TriageAgent,
    FlowAgent,
    InterviewAgent,
    AnswerAgent,
    KnowledgeAgent,
    ConfirmationAgent,
    UsageAgent,
    OnboardingAgent,
    EscalationAgent,
    FeedbackAgent,
    go_to_rag,
    ESCALATION_TOOLS,
    FEEDBACK_TOOLS,
    configure_feedback_storage,
)

# Network
from atendentepro.network import (
    AgentNetwork,
    AgentStyle,
    create_standard_network,
    create_custom_network,
)

# Templates
from atendentepro.templates import (
    TemplateManager,
    ClientTemplate,
    configure_client,
    get_template_folder,
    load_flow_config,
    load_interview_config,
    load_triage_config,
    load_knowledge_config,
    load_confirmation_config,
    load_onboarding_config,
)

# Guardrails
from atendentepro.guardrails import (
    GuardrailManager,
    get_guardrails_for_agent,
    get_out_of_scope_message,
    set_guardrails_client,
)

# Utils
from atendentepro.utils import (
    get_async_client,
    get_provider,
    configure_tracing,
    # MonkAI Trace
    configure_monkai_trace,
    get_monkai_hooks,
    set_monkai_user,
    set_monkai_input,
    run_with_monkai_tracking,
    # Application Insights
    configure_application_insights,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    # License
    "activate",
    "deactivate",
    "is_activated",
    "get_license_info",
    "require_activation",
    "has_feature",
    "generate_license_token",
    "LicenseInfo",
    "LicenseError",
    "LicenseNotActivatedError",
    "LicenseExpiredError",
    "InvalidTokenError",
    # Configuration
    "AtendentProConfig",
    "get_config",
    "configure",
    "RECOMMENDED_PROMPT_PREFIX",
    "DEFAULT_MODEL",
    # Models
    "ContextNote",
    "FlowTopic",
    "FlowOutput",
    "InterviewOutput",
    "KnowledgeToolResult",
    "GuardrailValidationOutput",
    # Access filtering
    "UserContext",
    "AccessFilter",
    "FilteredPromptSection",
    "FilteredTool",
    # Agents
    "create_triage_agent",
    "create_flow_agent",
    "create_interview_agent",
    "create_answer_agent",
    "create_knowledge_agent",
    "create_confirmation_agent",
    "create_usage_agent",
    "create_onboarding_agent",
    "create_escalation_agent",
    "create_feedback_agent",
    "TriageAgent",
    "FlowAgent",
    "InterviewAgent",
    "AnswerAgent",
    "KnowledgeAgent",
    "ConfirmationAgent",
    "UsageAgent",
    "OnboardingAgent",
    "EscalationAgent",
    "FeedbackAgent",
    "go_to_rag",
    "ESCALATION_TOOLS",
    "FEEDBACK_TOOLS",
    "configure_feedback_storage",
    # Network
    "AgentNetwork",
    "AgentStyle",
    "create_standard_network",
    "create_custom_network",
    # Templates
    "TemplateManager",
    "ClientTemplate",
    "configure_client",
    "get_template_folder",
    "load_flow_config",
    "load_interview_config",
    "load_triage_config",
    "load_knowledge_config",
    "load_confirmation_config",
    "load_onboarding_config",
    # Guardrails
    "GuardrailManager",
    "get_guardrails_for_agent",
    "get_out_of_scope_message",
    "set_guardrails_client",
    # Utils
    "get_async_client",
    "get_provider",
    "configure_tracing",
    # MonkAI Trace
    "configure_monkai_trace",
    "get_monkai_hooks",
    "set_monkai_user",
    "set_monkai_input",
    "run_with_monkai_tracking",
    # Application Insights
    "configure_application_insights",
]

