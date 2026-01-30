# -*- coding: utf-8 -*-
"""
Template Manager for AtendentePro.

Provides dynamic client-specific configuration loading from external template directories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field


@dataclass
class ClientTemplate:
    """Metadata required to load and configure a client profile."""
    
    key: str
    template_name: str
    aliases: tuple[str, ...] = ()
    configurator: Optional[Callable[[str], None]] = None


class FlowTopic(BaseModel):
    """Model for a flow topic."""
    
    id: str
    label: str
    keywords: List[str] = Field(default_factory=list)


class FlowConfig(BaseModel):
    """Configuration model for Flow Agent."""
    
    topics: List[FlowTopic] = Field(default_factory=list)
    keywords: List[Dict[str, Any]] = Field(default_factory=list)
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "FlowConfig":
        """Load flow configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Flow config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        topics = []
        for topic_data in data.get("topics", []):
            topics.append(FlowTopic(
                id=topic_data.get("id", ""),
                label=topic_data.get("label", ""),
                keywords=topic_data.get("keywords", []),
            ))
        
        return cls(
            topics=topics,
            keywords=data.get("keywords", []),
        )
    
    def get_flow_template(self) -> str:
        """Generate formatted topic template."""
        return "\n".join(
            f"{idx}. {topic.label}"
            for idx, topic in enumerate(self.topics, start=1)
        )
    
    def get_flow_keywords(self) -> str:
        """Generate formatted keywords text."""
        lines = []
        for topic in self.topics:
            if topic.keywords:
                formatted_terms = ", ".join(f'"{term}"' for term in topic.keywords)
                lines.append(f"- {topic.label}: {formatted_terms}")
        return "\n".join(lines)


class InterviewConfig(BaseModel):
    """Configuration model for Interview Agent."""
    
    interview_questions: str = ""
    topics: List[Dict[str, Any]] = Field(default_factory=list)
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "InterviewConfig":
        """Load interview configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Interview config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return cls(
            interview_questions=data.get("interview_questions", ""),
            topics=data.get("topics", []),
        )


class TriageConfig(BaseModel):
    """Configuration model for Triage Agent keywords."""
    
    keywords: Dict[str, List[str]] = Field(default_factory=dict)
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "TriageConfig":
        """Load triage configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Triage config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        keywords = {}
        for agent, entry in data.get("keywords", {}).items():
            if isinstance(entry, dict):
                keywords[agent] = entry.get("keywords", [])
            elif isinstance(entry, list):
                keywords[agent] = entry
        
        return cls(keywords=keywords)
    
    def get_keywords_text(self) -> str:
        """Format keywords for agent instructions."""
        lines = []
        for agent, kws in self.keywords.items():
            if kws:
                formatted = ", ".join(f'"{kw}"' for kw in kws)
                lines.append(f"- {agent}: {formatted}")
        return "\n".join(lines)


class DataSourceColumn(BaseModel):
    """Model for a data source column."""
    
    name: str
    description: str = ""
    type: str = "string"  # string, number, date, boolean


class DataSourceConfig(BaseModel):
    """Configuration for structured data sources."""
    
    type: str = "csv"  # csv, database, api
    path: Optional[str] = None  # For CSV files
    connection_env: Optional[str] = None  # For database connections
    api_url: Optional[str] = None  # For API endpoints
    encoding: str = "utf-8"
    columns: List[DataSourceColumn] = Field(default_factory=list)
    tables: List[Dict[str, str]] = Field(default_factory=list)  # For databases


class DocumentConfig(BaseModel):
    """Configuration for a knowledge document."""
    
    name: str
    path: str
    description: str = ""


class KnowledgeConfig(BaseModel):
    """Configuration model for Knowledge Agent.
    
    Supports both document-based RAG and structured data sources.
    """
    
    about: str = ""
    template: str = ""
    format: str = ""
    
    # Document-based RAG
    embeddings_path: Optional[str] = None
    documents: List[DocumentConfig] = Field(default_factory=list)
    
    # Structured data sources
    data_sources: List[DataSourceConfig] = Field(default_factory=list)
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "KnowledgeConfig":
        """Load knowledge configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Knowledge config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        # Parse documents
        documents = []
        for doc_data in data.get("documents", []):
            documents.append(DocumentConfig(
                name=doc_data.get("name", ""),
                path=doc_data.get("path", ""),
                description=doc_data.get("description", ""),
            ))
        
        # Parse data sources
        data_sources = []
        
        # Check for single data_source (backwards compatibility)
        if "data_source" in data:
            ds = data["data_source"]
            columns = [
                DataSourceColumn(
                    name=c.get("name", ""),
                    description=c.get("description", ""),
                    type=c.get("type", "string"),
                )
                for c in ds.get("columns", [])
            ]
            data_sources.append(DataSourceConfig(
                type=ds.get("type", "csv"),
                path=ds.get("path"),
                connection_env=ds.get("connection_env"),
                api_url=ds.get("api_url"),
                encoding=ds.get("encoding", "utf-8"),
                columns=columns,
                tables=ds.get("tables", []),
            ))
        
        # Check for multiple data_sources
        for ds in data.get("data_sources", []):
            columns = [
                DataSourceColumn(
                    name=c.get("name", ""),
                    description=c.get("description", ""),
                    type=c.get("type", "string"),
                )
                for c in ds.get("columns", [])
            ]
            data_sources.append(DataSourceConfig(
                type=ds.get("type", "csv"),
                path=ds.get("path"),
                connection_env=ds.get("connection_env"),
                api_url=ds.get("api_url"),
                encoding=ds.get("encoding", "utf-8"),
                columns=columns,
                tables=ds.get("tables", []),
            ))
        
        return cls(
            about=data.get("about", ""),
            template=data.get("template", ""),
            format=data.get("format", ""),
            embeddings_path=data.get("embeddings_path"),
            documents=documents,
            data_sources=data_sources,
        )
    
    def has_documents(self) -> bool:
        """Check if document-based RAG is configured."""
        return bool(self.embeddings_path or self.documents)
    
    def has_data_sources(self) -> bool:
        """Check if structured data sources are configured."""
        return bool(self.data_sources)
    
    def get_data_source_description(self) -> str:
        """Generate description of available data sources."""
        parts = []
        
        if self.documents:
            doc_list = ", ".join(d.name for d in self.documents)
            parts.append(f"Documentos: {doc_list}")
        
        for ds in self.data_sources:
            if ds.type == "csv":
                cols = ", ".join(c.name for c in ds.columns)
                parts.append(f"CSV ({ds.path}): {cols}")
            elif ds.type == "database":
                tables = ", ".join(t.get("name", "") for t in ds.tables)
                parts.append(f"Database: {tables}")
            elif ds.type == "api":
                parts.append(f"API: {ds.api_url}")
        
        return "\n".join(parts)


class ConfirmationConfig(BaseModel):
    """Configuration model for Confirmation Agent."""
    
    about: str = ""
    template: str = ""
    format: str = ""
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "ConfirmationConfig":
        """Load confirmation configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Confirmation config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return cls(
            about=data.get("about", ""),
            template=data.get("template", ""),
            format=data.get("format", ""),
        )


class OnboardingField(BaseModel):
    """Model for an onboarding required field."""
    
    name: str
    prompt: str
    priority: int = 0


class AgentStyleConfig(BaseModel):
    """Configuration for individual agent style."""
    
    tone: str = ""
    language_style: str = ""  # formal, informal, neutro
    response_length: str = ""  # conciso, moderado, detalhado
    custom_rules: str = ""


class StyleConfig(BaseModel):
    """Configuration model for agent communication styles.
    
    Allows customizing tone, language, and response style globally
    or per-agent through YAML configuration.
    
    Example YAML:
        global:
          tone: "profissional e cordial"
          language_style: "formal"
          response_length: "moderado"
          
        agents:
          escalation:
            tone: "empático e acolhedor"
            custom_rules: "Demonstre compreensão"
    """
    
    global_style: AgentStyleConfig = Field(default_factory=AgentStyleConfig)
    agents: Dict[str, AgentStyleConfig] = Field(default_factory=dict)
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "StyleConfig":
        """Load style configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Style config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        # Parse global style
        global_data = data.get("global", {})
        global_style = AgentStyleConfig(
            tone=global_data.get("tone", ""),
            language_style=global_data.get("language_style", ""),
            response_length=global_data.get("response_length", ""),
            custom_rules=global_data.get("custom_rules", ""),
        )
        
        # Parse agent-specific styles
        agents = {}
        for agent_name, agent_data in data.get("agents", {}).items():
            agents[agent_name] = AgentStyleConfig(
                tone=agent_data.get("tone", ""),
                language_style=agent_data.get("language_style", ""),
                response_length=agent_data.get("response_length", ""),
                custom_rules=agent_data.get("custom_rules", ""),
            )
        
        return cls(global_style=global_style, agents=agents)
    
    def get_style_for_agent(self, agent_name: str) -> AgentStyleConfig:
        """Get style configuration for a specific agent."""
        # Agent-specific style takes precedence
        if agent_name in self.agents:
            agent_style = self.agents[agent_name]
            # Merge with global (agent-specific overrides global)
            return AgentStyleConfig(
                tone=agent_style.tone or self.global_style.tone,
                language_style=agent_style.language_style or self.global_style.language_style,
                response_length=agent_style.response_length or self.global_style.response_length,
                custom_rules=agent_style.custom_rules or self.global_style.custom_rules,
            )
        # Fall back to global
        return self.global_style


class SingleReplyConfig(BaseModel):
    """Configuration model for single reply mode.
    
    When single_reply is enabled for an agent, it will respond once
    and automatically transfer back to the Triage agent. This prevents
    conversations from getting stuck in a specific agent.
    
    Example YAML:
        global: false
        
        agents:
          knowledge: true
          confirmation: true
          answer: true
    """
    
    global_enabled: bool = False
    agents: Dict[str, bool] = Field(default_factory=dict)
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "SingleReplyConfig":
        """Load single reply configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Single reply config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return cls(
            global_enabled=data.get("global", False),
            agents=data.get("agents", {}),
        )
    
    def get_single_reply_for_agent(self, agent_name: str) -> bool:
        """Get single_reply setting for a specific agent."""
        # Agent-specific setting takes precedence
        if agent_name in self.agents:
            return self.agents[agent_name]
        # Fall back to global
        return self.global_enabled


# =============================================================================
# ACCESS FILTER CONFIGURATION (Role/User based access control)
# =============================================================================

class AccessFilterConfig(BaseModel):
    """Configuration for a single access filter."""
    
    allowed_roles: Optional[List[str]] = None
    denied_roles: Optional[List[str]] = None
    allowed_users: Optional[List[str]] = None
    denied_users: Optional[List[str]] = None


class ConditionalPromptConfig(BaseModel):
    """Configuration for a conditional prompt section."""
    
    content: str = ""
    filter: AccessFilterConfig = Field(default_factory=AccessFilterConfig)


class AccessConfig(BaseModel):
    """
    Configuration model for role/user based access control.
    
    Allows controlling access to agents, prompts, and tools based on
    user identity or role. Supports both whitelist and blacklist patterns.
    
    Example YAML:
        # Filter entire agents by role
        agent_filters:
          knowledge:
            allowed_roles: ["admin", "vendedor"]
          escalation:
            denied_roles: ["cliente"]
        
        # Conditional prompt sections
        conditional_prompts:
          knowledge:
            - content: |
                ## Admin Tools
                You have access to admin features.
              filter:
                allowed_roles: ["admin"]
            - content: |
                ## Sales Tools
                You can offer up to 15% discount.
              filter:
                allowed_roles: ["vendedor"]
        
        # Tool access control
        tool_access:
          delete_user:
            allowed_roles: ["admin"]
          approve_discount:
            allowed_roles: ["gerente", "admin"]
    """
    
    agent_filters: Dict[str, AccessFilterConfig] = Field(default_factory=dict)
    conditional_prompts: Dict[str, List[ConditionalPromptConfig]] = Field(default_factory=dict)
    tool_access: Dict[str, AccessFilterConfig] = Field(default_factory=dict)
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "AccessConfig":
        """Load access configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Access config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        # Parse agent filters
        agent_filters = {}
        for agent_name, filter_data in data.get("agent_filters", {}).items():
            agent_filters[agent_name] = AccessFilterConfig(
                allowed_roles=filter_data.get("allowed_roles"),
                denied_roles=filter_data.get("denied_roles"),
                allowed_users=filter_data.get("allowed_users"),
                denied_users=filter_data.get("denied_users"),
            )
        
        # Parse conditional prompts
        conditional_prompts = {}
        for agent_name, prompts_data in data.get("conditional_prompts", {}).items():
            prompts_list = []
            for prompt_data in prompts_data:
                filter_data = prompt_data.get("filter", {})
                prompts_list.append(ConditionalPromptConfig(
                    content=prompt_data.get("content", ""),
                    filter=AccessFilterConfig(
                        allowed_roles=filter_data.get("allowed_roles"),
                        denied_roles=filter_data.get("denied_roles"),
                        allowed_users=filter_data.get("allowed_users"),
                        denied_users=filter_data.get("denied_users"),
                    ),
                ))
            conditional_prompts[agent_name] = prompts_list
        
        # Parse tool access
        tool_access = {}
        for tool_name, filter_data in data.get("tool_access", {}).items():
            tool_access[tool_name] = AccessFilterConfig(
                allowed_roles=filter_data.get("allowed_roles"),
                denied_roles=filter_data.get("denied_roles"),
                allowed_users=filter_data.get("allowed_users"),
                denied_users=filter_data.get("denied_users"),
            )
        
        return cls(
            agent_filters=agent_filters,
            conditional_prompts=conditional_prompts,
            tool_access=tool_access,
        )
    
    def get_agent_filter(self, agent_name: str) -> Optional[AccessFilterConfig]:
        """Get access filter for a specific agent."""
        return self.agent_filters.get(agent_name)
    
    def get_conditional_prompts(self, agent_name: str) -> List[ConditionalPromptConfig]:
        """Get conditional prompts for a specific agent."""
        return self.conditional_prompts.get(agent_name, [])
    
    def get_tool_filter(self, tool_name: str) -> Optional[AccessFilterConfig]:
        """Get access filter for a specific tool."""
        return self.tool_access.get(tool_name)


class OnboardingConfig(BaseModel):
    """Configuration model for Onboarding Agent."""
    
    required_fields: List[OnboardingField] = Field(default_factory=list)
    
    @classmethod
    @lru_cache(maxsize=4)
    def load(cls, path: Path) -> "OnboardingConfig":
        """Load onboarding configuration from YAML file."""
        if not path.exists():
            raise FileNotFoundError(f"Onboarding config not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        fields = []
        for field_data in data.get("required_fields", []):
            fields.append(OnboardingField(
                name=field_data.get("name", ""),
                prompt=field_data.get("prompt", ""),
                priority=field_data.get("priority", 0),
            ))
        
        # Sort by priority
        fields.sort(key=lambda x: x.priority)
        
        return cls(required_fields=fields)


# Global template manager instance
_template_manager: Optional["TemplateManager"] = None


class TemplateManager:
    """
    Coordinates dynamic client-specific configuration loading.
    
    The manager handles loading configuration files from external template
    directories and provides access to client-specific settings.
    """
    
    def __init__(
        self,
        templates_root: Optional[Path] = None,
        default_client: str = "standard",
    ) -> None:
        """
        Initialize the TemplateManager.
        
        Args:
            templates_root: Root directory for template configurations.
            default_client: Default client key to use.
        """
        self.templates_root = templates_root
        self.default_client = default_client
        
        self._client_templates: Dict[str, ClientTemplate] = {}
        self._client_aliases: Dict[str, str] = {}
        self._configured_clients: Dict[str, bool] = {}
    
    def register_client(self, template: ClientTemplate) -> None:
        """Register or update a client template."""
        self._client_templates[template.key] = template
        for alias in template.aliases:
            normalized = alias.strip().lower()
            if normalized:
                self._client_aliases[normalized] = template.key
    
    def normalize_client_key(self, client: Optional[str]) -> str:
        """Normalize client aliases to a canonical key."""
        if not client:
            return self.default_client
        key = client.strip().lower()
        return self._client_aliases.get(key, key)
    
    def get_template_folder(self, client: Optional[str] = None) -> Path:
        """Return the Path for the requested client's template directory."""
        if not self.templates_root:
            raise ValueError("templates_root not configured")
        
        client_key = self.normalize_client_key(client)
        template = self._client_templates.get(client_key)
        
        if template:
            return self.templates_root / template.template_name
        
        return self.templates_root / client_key
    
    def load_flow_config(self, client: Optional[str] = None) -> FlowConfig:
        """Load flow configuration for the specified client."""
        folder = self.get_template_folder(client)
        return FlowConfig.load(folder / "flow_config.yaml")
    
    def load_interview_config(self, client: Optional[str] = None) -> InterviewConfig:
        """Load interview configuration for the specified client."""
        folder = self.get_template_folder(client)
        return InterviewConfig.load(folder / "interview_config.yaml")
    
    def load_triage_config(self, client: Optional[str] = None) -> TriageConfig:
        """Load triage configuration for the specified client."""
        folder = self.get_template_folder(client)
        return TriageConfig.load(folder / "triage_config.yaml")
    
    def load_knowledge_config(self, client: Optional[str] = None) -> KnowledgeConfig:
        """Load knowledge configuration for the specified client."""
        folder = self.get_template_folder(client)
        return KnowledgeConfig.load(folder / "knowledge_config.yaml")
    
    def load_confirmation_config(self, client: Optional[str] = None) -> ConfirmationConfig:
        """Load confirmation configuration for the specified client."""
        folder = self.get_template_folder(client)
        return ConfirmationConfig.load(folder / "confirmation_config.yaml")
    
    def load_onboarding_config(self, client: Optional[str] = None) -> OnboardingConfig:
        """Load onboarding configuration for the specified client."""
        folder = self.get_template_folder(client)
        return OnboardingConfig.load(folder / "onboarding_config.yaml")
    
    def load_style_config(self, client: Optional[str] = None) -> StyleConfig:
        """Load style configuration for the specified client."""
        folder = self.get_template_folder(client)
        return StyleConfig.load(folder / "style_config.yaml")
    
    def load_single_reply_config(self, client: Optional[str] = None) -> SingleReplyConfig:
        """Load single reply configuration for the specified client."""
        folder = self.get_template_folder(client)
        return SingleReplyConfig.load(folder / "single_reply_config.yaml")
    
    def load_access_config(self, client: Optional[str] = None) -> AccessConfig:
        """Load access configuration for the specified client."""
        folder = self.get_template_folder(client)
        return AccessConfig.load(folder / "access_config.yaml")
    
    def clear_caches(self) -> None:
        """Clear all configuration caches."""
        FlowConfig.load.cache_clear()
        InterviewConfig.load.cache_clear()
        TriageConfig.load.cache_clear()
        KnowledgeConfig.load.cache_clear()
        ConfirmationConfig.load.cache_clear()
        OnboardingConfig.load.cache_clear()
        StyleConfig.load.cache_clear()
        SingleReplyConfig.load.cache_clear()
        AccessConfig.load.cache_clear()


def get_template_manager() -> TemplateManager:
    """Get the global template manager instance."""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager


def configure_template_manager(
    templates_root: Path,
    default_client: str = "standard",
) -> TemplateManager:
    """
    Configure the global template manager.
    
    Args:
        templates_root: Root directory for template configurations.
        default_client: Default client key to use.
        
    Returns:
        Configured TemplateManager instance.
    """
    global _template_manager
    _template_manager = TemplateManager(
        templates_root=templates_root,
        default_client=default_client,
    )
    return _template_manager


def configure_client(
    client: Optional[str] = None,
    templates_root: Optional[Path] = None,
) -> str:
    """
    Configure the template manager for a specific client.
    
    Args:
        client: Client key or alias.
        templates_root: Optional templates root to configure.
        
    Returns:
        Normalized client key.
    """
    manager = get_template_manager()
    
    if templates_root:
        manager.templates_root = templates_root
    
    return manager.normalize_client_key(client)


def get_template_folder(client: Optional[str] = None) -> Path:
    """Get the template folder for the specified client."""
    return get_template_manager().get_template_folder(client)


def load_flow_config(client: Optional[str] = None) -> FlowConfig:
    """Load flow configuration for the specified client."""
    return get_template_manager().load_flow_config(client)


def load_interview_config(client: Optional[str] = None) -> InterviewConfig:
    """Load interview configuration for the specified client."""
    return get_template_manager().load_interview_config(client)


def load_triage_config(client: Optional[str] = None) -> TriageConfig:
    """Load triage configuration for the specified client."""
    return get_template_manager().load_triage_config(client)


def load_knowledge_config(client: Optional[str] = None) -> KnowledgeConfig:
    """Load knowledge configuration for the specified client."""
    return get_template_manager().load_knowledge_config(client)


def load_confirmation_config(client: Optional[str] = None) -> ConfirmationConfig:
    """Load confirmation configuration for the specified client."""
    return get_template_manager().load_confirmation_config(client)


def load_onboarding_config(client: Optional[str] = None) -> OnboardingConfig:
    """Load onboarding configuration for the specified client."""
    return get_template_manager().load_onboarding_config(client)


def load_style_config(client: Optional[str] = None) -> StyleConfig:
    """Load style configuration for the specified client."""
    return get_template_manager().load_style_config(client)


def load_single_reply_config(client: Optional[str] = None) -> SingleReplyConfig:
    """Load single reply configuration for the specified client."""
    return get_template_manager().load_single_reply_config(client)


def load_access_config(client: Optional[str] = None) -> AccessConfig:
    """Load access configuration for the specified client."""
    return get_template_manager().load_access_config(client)

