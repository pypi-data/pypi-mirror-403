# -*- coding: utf-8 -*-
"""
Agent Network for AtendentePro.

Provides functions to create and configure the agent network with proper handoffs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional


# =============================================================================
# Agent Style Configuration
# =============================================================================

@dataclass
class AgentStyle:
    """
    Configuration for agent conversation style and tone.
    
    Allows customizing how agents communicate with users,
    including tone, language style, response length, and custom rules.
    
    Attributes:
        tone: Conversation tone (e.g., "profissional", "empático", "consultivo")
        language_style: Language formality ("formal", "informal", "neutro")
        response_length: Response verbosity ("conciso", "moderado", "detalhado")
        custom_rules: Additional custom rules as text
        
    Example:
        >>> style = AgentStyle(
        ...     tone="empático e acolhedor",
        ...     language_style="formal",
        ...     response_length="moderado",
        ...     custom_rules="Sempre se apresente como assistente da empresa."
        ... )
        >>> print(style.build_style_prompt())
    """
    
    tone: str = ""
    language_style: str = ""  # formal, informal, neutro
    response_length: str = ""  # conciso, moderado, detalhado
    custom_rules: str = ""
    
    def build_style_prompt(self) -> str:
        """
        Build style instructions to append to agent prompts.
        
        Returns:
            Formatted style instructions as a string.
        """
        parts = []
        
        if self.tone:
            parts.append(f"**Tom de conversa:** {self.tone}.")
        
        if self.language_style:
            style_map = {
                "formal": "Use linguagem formal e respeitosa, evitando gírias e expressões coloquiais.",
                "informal": "Use linguagem informal e descontraída, aproximando-se do usuário.",
                "neutro": "Use linguagem neutra e objetiva, focando na clareza.",
            }
            instruction = style_map.get(
                self.language_style.lower(), 
                f"Estilo de linguagem: {self.language_style}"
            )
            parts.append(f"**Linguagem:** {instruction}")
        
        if self.response_length:
            length_map = {
                "conciso": "Seja conciso e direto nas respostas, evitando informações desnecessárias.",
                "moderado": "Forneça respostas com nível médio de detalhe, equilibrando clareza e completude.",
                "detalhado": "Forneça respostas detalhadas e completas, explicando cada ponto relevante.",
            }
            instruction = length_map.get(
                self.response_length.lower(),
                f"Tamanho das respostas: {self.response_length}"
            )
            parts.append(f"**Respostas:** {instruction}")
        
        if self.custom_rules:
            parts.append(f"**Regras adicionais:**\n{self.custom_rules}")
        
        if not parts:
            return ""
        
        return "\n\n## Estilo de Comunicação\n" + "\n\n".join(parts)

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
)
from atendentepro.guardrails import get_guardrails_for_agent, set_guardrails_client
from atendentepro.license import require_activation
from atendentepro.templates import (
    TemplateManager,
    configure_template_manager,
    load_flow_config,
    load_interview_config,
    load_triage_config,
    load_knowledge_config,
    load_confirmation_config,
    load_onboarding_config,
    load_access_config,
    AccessConfig,
    AccessFilterConfig,
)
from atendentepro.models import (
    UserContext,
    AccessFilter,
    FilteredPromptSection,
    FilteredTool,
)


@dataclass
class AgentNetwork:
    """
    Container for all agents in the network.
    
    Provides access to individual agents and methods to configure
    the network for different clients.
    """
    
    triage: Optional[TriageAgent] = None
    flow: Optional[FlowAgent] = None
    interview: Optional[InterviewAgent] = None
    answer: Optional[AnswerAgent] = None
    knowledge: Optional[KnowledgeAgent] = None
    confirmation: Optional[ConfirmationAgent] = None
    usage: Optional[UsageAgent] = None
    onboarding: Optional[OnboardingAgent] = None
    escalation: Optional[EscalationAgent] = None
    feedback: Optional[FeedbackAgent] = None
    
    templates_root: Optional[Path] = None
    current_client: str = "standard"
    
    def get_all_agents(self) -> List:
        """Get list of all configured agents."""
        agents = []
        for attr in ["triage", "flow", "interview", "answer", "knowledge", 
                     "confirmation", "usage", "onboarding", "escalation", "feedback"]:
            agent = getattr(self, attr, None)
            if agent:
                agents.append(agent)
        return agents
    
    def add_escalation_to_all(self) -> None:
        """Add escalation agent as handoff to all other agents."""
        if not self.escalation:
            return
        
        for agent in self.get_all_agents():
            if agent != self.escalation and self.escalation not in agent.handoffs:
                agent.handoffs.append(self.escalation)
    
    def add_feedback_to_all(self) -> None:
        """Add feedback agent as handoff to all other agents."""
        if not self.feedback:
            return
        
        for agent in self.get_all_agents():
            if agent != self.feedback and self.feedback not in agent.handoffs:
                agent.handoffs.append(self.feedback)


def create_standard_network(
    templates_root: Path,
    client: str = "standard",
    # Agents to include
    include_flow: bool = True,
    include_interview: bool = True,
    include_answer: bool = True,
    include_knowledge: bool = True,
    include_confirmation: bool = True,
    include_usage: bool = True,
    include_onboarding: bool = False,
    include_escalation: bool = True,
    include_feedback: bool = True,
    # Agent-specific configurations
    escalation_channels: str = "",
    feedback_protocol_prefix: str = "TKT",
    feedback_brand_color: str = "#4A90D9",
    feedback_brand_name: str = "Atendimento",
    custom_tools: Optional[Dict[str, List]] = None,
    # Style configuration
    global_style: Optional[AgentStyle] = None,
    agent_styles: Optional[Dict[str, AgentStyle]] = None,
    # Single reply mode (auto-return to triage after one response)
    global_single_reply: bool = False,
    single_reply_agents: Optional[Dict[str, bool]] = None,
    # Access filtering (role/user based)
    user_context: Optional[UserContext] = None,
    agent_filters: Optional[Dict[str, AccessFilter]] = None,
    conditional_prompts: Optional[Dict[str, List[FilteredPromptSection]]] = None,
    filtered_tools: Optional[Dict[str, List[FilteredTool]]] = None,
) -> AgentNetwork:
    """
    Create a standard agent network with proper handoff configuration.
    
    This creates a configurable network where you can enable/disable specific agents.
    The Triage agent is always included as it's the entry point.
    
    Default handoff configuration (when all agents are enabled):
    - Triage -> Flow, Confirmation, Knowledge, Usage, Escalation, Feedback
    - Flow -> Interview, Triage, Escalation, Feedback
    - Interview -> Answer, Escalation, Feedback
    - Answer -> Triage, Escalation, Feedback
    - Confirmation -> Triage, Escalation, Feedback
    - Knowledge -> Triage, Escalation, Feedback
    - Usage -> Triage, Escalation, Feedback
    - Escalation -> Triage, Feedback
    - Feedback -> Triage, Escalation
    
    Args:
        templates_root: Root directory for template configurations.
        client: Client key to load configurations for.
        include_flow: Whether to include the flow agent (default True).
        include_interview: Whether to include the interview agent (default True).
        include_answer: Whether to include the answer agent (default True).
        include_knowledge: Whether to include the knowledge agent (default True).
        include_confirmation: Whether to include the confirmation agent (default True).
        include_usage: Whether to include the usage agent (default True).
        include_onboarding: Whether to include the onboarding agent (default False).
        include_escalation: Whether to include the escalation agent (default True).
        include_feedback: Whether to include the feedback agent (default True).
        escalation_channels: Description of available escalation channels.
        feedback_protocol_prefix: Prefix for ticket protocols (e.g., "SAC", "TKT").
        feedback_brand_color: Brand color for feedback emails.
        feedback_brand_name: Brand name for feedback emails.
        custom_tools: Optional dict of custom tools by agent name.
        global_style: Style configuration applied to all agents (tone, language, etc.).
        agent_styles: Dict mapping agent names to specific styles (overrides global).
        global_single_reply: If True, all agents respond once then transfer to triage.
        single_reply_agents: Dict mapping agent names to single_reply mode (overrides global).
        user_context: User context for access filtering (user_id, role, metadata).
        agent_filters: Dict mapping agent names to AccessFilter (controls agent access).
        conditional_prompts: Dict mapping agent names to list of FilteredPromptSection.
        filtered_tools: Dict mapping agent names to list of FilteredTool.
        
    Returns:
        Configured AgentNetwork instance.
        
    Raises:
        LicenseNotActivatedError: If the library is not activated.
        
    Example:
        # Create network without Knowledge agent
        network = create_standard_network(
            templates_root=Path("templates"),
            client="my_client",
            include_knowledge=False,
        )
        
        # Create network with role-based access filtering
        from atendentepro import UserContext, AccessFilter, FilteredPromptSection
        
        user = UserContext(user_id="user123", role="vendedor")
        
        network = create_standard_network(
            templates_root=Path("templates"),
            client="my_client",
            user_context=user,
            agent_filters={
                "knowledge": AccessFilter(allowed_roles=["admin", "vendedor"]),
                "escalation": AccessFilter(denied_roles=["cliente"]),
            },
            conditional_prompts={
                "knowledge": [
                    FilteredPromptSection(
                        content="\\n## Descontos\\nVocê pode oferecer até 15% de desconto.",
                        filter=AccessFilter(allowed_roles=["vendedor"]),
                    ),
                ],
            },
        )
        
        # Create network with custom communication style
        network = create_standard_network(
            templates_root=Path("templates"),
            client="my_client",
            global_style=AgentStyle(
                tone="profissional e consultivo",
                language_style="formal",
                response_length="moderado",
            ),
        )
    """
    # Verificar licença
    require_activation()
    
    # Configure template manager
    manager = configure_template_manager(templates_root, default_client=client)
    
    # Load access config from YAML if not provided via code
    yaml_access_config = None
    try:
        yaml_access_config = load_access_config(client)
    except FileNotFoundError:
        pass
    
    # Helper function to check if agent is allowed for user
    def is_agent_allowed(agent_name: str) -> bool:
        """Check if agent should be included based on user context."""
        if user_context is None:
            return True  # No filtering if no user context
        
        # Code-level filter takes precedence
        if agent_filters and agent_name in agent_filters:
            return agent_filters[agent_name].is_allowed(user_context)
        
        # Fall back to YAML config
        if yaml_access_config:
            yaml_filter = yaml_access_config.get_agent_filter(agent_name)
            if yaml_filter:
                # Convert AccessFilterConfig to AccessFilter
                access_filter = AccessFilter(
                    allowed_roles=yaml_filter.allowed_roles,
                    denied_roles=yaml_filter.denied_roles,
                    allowed_users=yaml_filter.allowed_users,
                    denied_users=yaml_filter.denied_users,
                )
                return access_filter.is_allowed(user_context)
        
        return True  # No filter = allowed
    
    # Helper function to get conditional prompts for agent
    def get_conditional_prompts_for_agent(agent_name: str) -> str:
        """Get all allowed conditional prompt sections for an agent."""
        sections = []
        
        # Code-level prompts take precedence
        if conditional_prompts and agent_name in conditional_prompts:
            for section in conditional_prompts[agent_name]:
                content = section.get_content_if_allowed(user_context)
                if content:
                    sections.append(content)
        
        # Add YAML-level prompts
        if yaml_access_config:
            for prompt_cfg in yaml_access_config.get_conditional_prompts(agent_name):
                # Convert to AccessFilter and check
                access_filter = AccessFilter(
                    allowed_roles=prompt_cfg.filter.allowed_roles,
                    denied_roles=prompt_cfg.filter.denied_roles,
                    allowed_users=prompt_cfg.filter.allowed_users,
                    denied_users=prompt_cfg.filter.denied_users,
                )
                if access_filter.is_allowed(user_context):
                    sections.append(prompt_cfg.content)
        
        return "\n".join(sections)
    
    # Helper function to get filtered tools for agent
    def get_filtered_tools_for_agent(agent_name: str, base_tools: List) -> List:
        """Get tools filtered by user context."""
        result_tools = list(base_tools) if base_tools else []
        
        # Add code-level filtered tools
        if filtered_tools and agent_name in filtered_tools:
            for ft in filtered_tools[agent_name]:
                tool = ft.get_tool_if_allowed(user_context)
                if tool:
                    result_tools.append(tool)
        
        return result_tools
    
    # Load configurations
    try:
        flow_config = load_flow_config(client)
        flow_template = flow_config.get_flow_template()
        flow_keywords = flow_config.get_flow_keywords()
    except FileNotFoundError:
        flow_template = ""
        flow_keywords = ""
    
    try:
        interview_config = load_interview_config(client)
        interview_questions = interview_config.interview_questions
    except FileNotFoundError:
        interview_questions = ""
    
    try:
        triage_config = load_triage_config(client)
        triage_keywords = triage_config.get_keywords_text()
    except FileNotFoundError:
        triage_keywords = ""
    
    try:
        knowledge_config = load_knowledge_config(client)
        knowledge_about = knowledge_config.about
        knowledge_template = knowledge_config.template
        knowledge_format = knowledge_config.format
        embeddings_path = (
            Path(knowledge_config.embeddings_path) 
            if knowledge_config.embeddings_path 
            else None
        )
        data_sources_description = knowledge_config.get_data_source_description()
        has_embeddings = knowledge_config.has_documents()
    except FileNotFoundError:
        knowledge_about = ""
        knowledge_template = ""
        knowledge_format = ""
        embeddings_path = None
        data_sources_description = ""
        has_embeddings = False
    
    try:
        confirmation_config = load_confirmation_config(client)
        confirmation_about = confirmation_config.about
        confirmation_template = confirmation_config.template
        confirmation_format = confirmation_config.format
    except FileNotFoundError:
        confirmation_about = ""
        confirmation_template = ""
        confirmation_format = ""
    
    # Load guardrails
    try:
        set_guardrails_client(client, templates_root=templates_root)
    except FileNotFoundError:
        pass
    
    # Get custom tools
    tools = custom_tools or {}
    
    # Style helper function
    def get_style_for_agent(agent_name: str) -> str:
        """Get style instructions for a specific agent."""
        # Agent-specific style takes precedence
        if agent_styles and agent_name in agent_styles:
            return agent_styles[agent_name].build_style_prompt()
        # Fall back to global style
        if global_style:
            return global_style.build_style_prompt()
        return ""
    
    # Single reply helper function
    def get_single_reply_for_agent(agent_name: str) -> bool:
        """Get single_reply setting for a specific agent."""
        # Agent-specific setting takes precedence
        if single_reply_agents and agent_name in single_reply_agents:
            return single_reply_agents[agent_name]
        # Fall back to global setting
        return global_single_reply
    
    # Helper to build full style instructions with conditional prompts
    def get_full_instructions(agent_name: str) -> str:
        """Get style + conditional prompt instructions for an agent."""
        style = get_style_for_agent(agent_name)
        conditional = get_conditional_prompts_for_agent(agent_name)
        return f"{style}{conditional}" if conditional else style
    
    # Create agents without handoffs first
    # Triage is always created (entry point)
    triage = create_triage_agent(
        keywords_text=triage_keywords,
        guardrails=get_guardrails_for_agent("Triage Agent", templates_root),
        style_instructions=get_full_instructions("triage"),
    )
    
    # Create optional agents based on include flags AND access filters
    flow = None
    if include_flow and is_agent_allowed("flow"):
        flow = create_flow_agent(
            flow_template=flow_template,
            flow_keywords=flow_keywords,
            guardrails=get_guardrails_for_agent("Flow Agent", templates_root),
            style_instructions=get_full_instructions("flow"),
            single_reply=get_single_reply_for_agent("flow"),
        )
    
    interview = None
    if include_interview and is_agent_allowed("interview"):
        interview = create_interview_agent(
            interview_template=flow_template,
            interview_questions=interview_questions,
            tools=get_filtered_tools_for_agent("interview", tools.get("interview", [])),
            guardrails=get_guardrails_for_agent("Interview Agent", templates_root),
            style_instructions=get_full_instructions("interview"),
            single_reply=get_single_reply_for_agent("interview"),
        )
    
    answer = None
    if include_answer and is_agent_allowed("answer"):
        answer = create_answer_agent(
            answer_template="",
            guardrails=get_guardrails_for_agent("Answer Agent", templates_root),
            style_instructions=get_full_instructions("answer"),
            single_reply=get_single_reply_for_agent("answer"),
        )
    
    knowledge = None
    if include_knowledge and is_agent_allowed("knowledge"):
        knowledge = create_knowledge_agent(
            knowledge_about=knowledge_about,
            knowledge_template=knowledge_template,
            knowledge_format=knowledge_format,
            embeddings_path=embeddings_path,
            data_sources_description=data_sources_description,
            include_rag_tool=has_embeddings,
            tools=get_filtered_tools_for_agent("knowledge", tools.get("knowledge", [])),
            guardrails=get_guardrails_for_agent("Knowledge Agent", templates_root),
            style_instructions=get_full_instructions("knowledge"),
            single_reply=get_single_reply_for_agent("knowledge"),
        )
    
    confirmation = None
    if include_confirmation and is_agent_allowed("confirmation"):
        confirmation = create_confirmation_agent(
            confirmation_about=confirmation_about,
            confirmation_template=confirmation_template,
            confirmation_format=confirmation_format,
            guardrails=get_guardrails_for_agent("Confirmation Agent", templates_root),
            style_instructions=get_full_instructions("confirmation"),
            single_reply=get_single_reply_for_agent("confirmation"),
        )
    
    usage = None
    if include_usage and is_agent_allowed("usage"):
        usage = create_usage_agent(
            guardrails=get_guardrails_for_agent("Usage Agent", templates_root),
            style_instructions=get_full_instructions("usage"),
            single_reply=get_single_reply_for_agent("usage"),
        )
    
    # Create escalation agent if requested and allowed
    escalation = None
    if include_escalation and is_agent_allowed("escalation"):
        escalation = create_escalation_agent(
            escalation_channels=escalation_channels,
            tools=get_filtered_tools_for_agent("escalation", tools.get("escalation", [])),
            guardrails=get_guardrails_for_agent("Escalation Agent", templates_root),
            style_instructions=get_full_instructions("escalation"),
            single_reply=get_single_reply_for_agent("escalation"),
        )
    
    # Create feedback agent if requested and allowed
    feedback = None
    if include_feedback and is_agent_allowed("feedback"):
        feedback = create_feedback_agent(
            protocol_prefix=feedback_protocol_prefix,
            email_brand_color=feedback_brand_color,
            email_brand_name=feedback_brand_name,
            tools=get_filtered_tools_for_agent("feedback", tools.get("feedback", [])),
            guardrails=get_guardrails_for_agent("Feedback Agent", templates_root),
            style_instructions=get_full_instructions("feedback"),
            single_reply=get_single_reply_for_agent("feedback"),
        )
    
    # Configure handoffs dynamically based on which agents are included
    # Helper function to filter None values
    def filter_agents(*agents):
        return [a for a in agents if a is not None]
    
    # Build triage handoffs (main routing)
    triage_handoffs = filter_agents(flow, confirmation, knowledge, usage)
    
    # Other agent handoffs
    flow_handoffs = filter_agents(interview, triage) if flow else []
    confirmation_handoffs = [triage] if confirmation else []
    knowledge_handoffs = [triage] if knowledge else []
    usage_handoffs = [triage] if usage else []
    interview_handoffs = filter_agents(answer) if interview else []
    answer_handoffs = [triage] if answer else []
    escalation_handoffs = [triage] if escalation else []
    feedback_handoffs = [triage] if feedback else []
    
    # Add escalation to all agents if enabled
    if escalation:
        triage_handoffs.append(escalation)
        if flow:
            flow_handoffs.append(escalation)
        if confirmation:
            confirmation_handoffs.append(escalation)
        if knowledge:
            knowledge_handoffs.append(escalation)
        if usage:
            usage_handoffs.append(escalation)
        if interview:
            interview_handoffs.append(escalation)
        if answer:
            answer_handoffs.append(escalation)
        if feedback:
            feedback_handoffs.append(escalation)
    
    # Add feedback to all agents if enabled
    if feedback:
        triage_handoffs.append(feedback)
        if flow:
            flow_handoffs.append(feedback)
        if confirmation:
            confirmation_handoffs.append(feedback)
        if knowledge:
            knowledge_handoffs.append(feedback)
        if usage:
            usage_handoffs.append(feedback)
        if interview:
            interview_handoffs.append(feedback)
        if answer:
            answer_handoffs.append(feedback)
        if escalation:
            escalation_handoffs.append(feedback)
    
    # Apply handoffs to agents
    triage.handoffs = triage_handoffs
    if flow:
        flow.handoffs = flow_handoffs
    if confirmation:
        confirmation.handoffs = confirmation_handoffs
    if knowledge:
        knowledge.handoffs = knowledge_handoffs
    if usage:
        usage.handoffs = usage_handoffs
    if interview:
        interview.handoffs = interview_handoffs
    if answer:
        answer.handoffs = answer_handoffs
    if escalation:
        escalation.handoffs = escalation_handoffs
    if feedback:
        feedback.handoffs = feedback_handoffs
    
    network = AgentNetwork(
        triage=triage,
        flow=flow,
        interview=interview,
        answer=answer,
        knowledge=knowledge,
        confirmation=confirmation,
        usage=usage,
        escalation=escalation,
        feedback=feedback,
        templates_root=templates_root,
        current_client=client,
    )
    
    # Add onboarding if requested
    if include_onboarding and is_agent_allowed("onboarding"):
        try:
            onboarding_config = load_onboarding_config(client)
            from atendentepro.prompts.onboarding import OnboardingField as PromptField
            
            fields = [
                PromptField(
                    name=f.name,
                    prompt=f.prompt,
                    priority=f.priority,
                )
                for f in onboarding_config.required_fields
            ]
        except FileNotFoundError:
            fields = []
        
        onboarding = create_onboarding_agent(
            required_fields=fields,
            tools=get_filtered_tools_for_agent("onboarding", tools.get("onboarding", [])),
            guardrails=get_guardrails_for_agent("Onboarding Agent", templates_root),
            style_instructions=get_full_instructions("onboarding"),
            single_reply=get_single_reply_for_agent("onboarding"),
        )
        
        network.onboarding = onboarding
        onboarding.handoffs = [triage]
    
    return network


def create_custom_network(
    templates_root: Path,
    client: str,
    network_config: Dict[str, List[str]],
    custom_tools: Optional[Dict[str, List]] = None,
) -> AgentNetwork:
    """
    Create a custom agent network with specified handoff configuration.
    
    Args:
        templates_root: Root directory for template configurations.
        client: Client key to load configurations for.
        network_config: Dict mapping agent names to list of handoff agent names.
        custom_tools: Optional dict of custom tools by agent name.
        
    Returns:
        Configured AgentNetwork instance.
        
    Raises:
        LicenseNotActivatedError: If the library is not activated.
    """
    # Verificar licença (já é feito em create_standard_network, mas verificamos novamente)
    require_activation()
    
    # First create the standard network
    network = create_standard_network(
        templates_root=templates_root,
        client=client,
        include_onboarding="onboarding" in network_config,
        custom_tools=custom_tools,
    )
    
    # Map agent names to instances
    agent_map = {
        "triage": network.triage,
        "flow": network.flow,
        "interview": network.interview,
        "answer": network.answer,
        "knowledge": network.knowledge,
        "confirmation": network.confirmation,
        "usage": network.usage,
        "onboarding": network.onboarding,
        "escalation": network.escalation,
        "feedback": network.feedback,
    }
    
    # Apply custom handoff configuration
    for agent_name, handoff_names in network_config.items():
        agent = agent_map.get(agent_name)
        if agent:
            handoffs = [
                agent_map[h] for h in handoff_names 
                if h in agent_map and agent_map[h] is not None
            ]
            agent.handoffs = handoffs
    
    return network

