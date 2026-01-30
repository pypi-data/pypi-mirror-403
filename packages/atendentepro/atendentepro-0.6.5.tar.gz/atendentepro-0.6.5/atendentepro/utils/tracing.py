# -*- coding: utf-8 -*-
"""
Tracing configuration for AtendentePro.

Provides optional tracing integrations:
- MonkAI Trace (recommended): Full agent tracking with token segmentation
- Application Insights: Azure telemetry

MonkAI Trace: https://github.com/BeMonkAI/monkai-trace
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Any, TYPE_CHECKING

from atendentepro.config import get_config

if TYPE_CHECKING:
    from agents import Agent

logger = logging.getLogger(__name__)


# =============================================================================
# MONKAI TRACE INTEGRATION
# =============================================================================

_MONKAI_HOOKS: Optional[Any] = None


def configure_monkai_trace(
    tracer_token: Optional[str] = None,
    namespace: Optional[str] = None,
    inactivity_timeout: int = 120,
    batch_size: int = 1,
) -> bool:
    """
    Configure MonkAI Trace for agent tracking.
    
    MonkAI Trace provides comprehensive agent monitoring with:
    - Automatic session management
    - Token segmentation (input, output, process, memory)
    - Multi-agent handoff tracking
    - Web search and tool tracking
    
    Args:
        tracer_token: MonkAI tracer token (or env MONKAI_TRACER_TOKEN)
        namespace: Namespace for grouping traces (default: "atendentepro")
        inactivity_timeout: Session timeout in seconds (default: 120)
        batch_size: Upload batch size, 1 for real-time (default: 1)
        
    Returns:
        True if MonkAI Trace was configured, False otherwise.
        
    Example:
        >>> from atendentepro.utils import configure_monkai_trace
        >>> configure_monkai_trace(tracer_token="tk_your_token")
        True
        
        >>> # Or via environment variable
        >>> # export MONKAI_TRACER_TOKEN="tk_your_token"
        >>> configure_monkai_trace()
        True
    """
    global _MONKAI_HOOKS
    
    # Get token from parameter or environment
    token = tracer_token or os.environ.get("MONKAI_TRACER_TOKEN")
    
    if not token:
        logger.debug("No MonkAI tracer token provided. MonkAI Trace disabled.")
        return False
    
    try:
        from monkai_trace.integrations.openai_agents import MonkAIRunHooks
        
        _MONKAI_HOOKS = MonkAIRunHooks(
            tracer_token=token,
            namespace=namespace or "atendentepro",
            inactivity_timeout=inactivity_timeout,
            batch_size=batch_size,
        )
        
        logger.info(f"MonkAI Trace configured successfully (namespace: {namespace or 'atendentepro'})")
        return True
        
    except ImportError:
        logger.warning(
            "MonkAI Trace not available. "
            "Install 'monkai-trace' for agent tracking: pip install monkai-trace"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to configure MonkAI Trace: {e}")
        return False


def get_monkai_hooks() -> Optional[Any]:
    """
    Get the configured MonkAI Run Hooks.
    
    Returns:
        MonkAIRunHooks instance if configured, None otherwise.
        
    Example:
        >>> hooks = get_monkai_hooks()
        >>> if hooks:
        ...     result = await Runner.run(agent, messages, hooks=hooks)
    """
    return _MONKAI_HOOKS


def set_monkai_user(user_id: str) -> None:
    """
    Set the user ID for MonkAI session tracking.
    
    Useful for multi-user scenarios like WhatsApp bots.
    
    Args:
        user_id: Unique user identifier (phone, email, etc.)
        
    Example:
        >>> set_monkai_user("5511999999999")  # WhatsApp
        >>> set_monkai_user("user@email.com")  # Email
    """
    if _MONKAI_HOOKS:
        _MONKAI_HOOKS.set_user_id(user_id)


def set_monkai_input(user_input: str) -> None:
    """
    Set the user input for MonkAI tracking.
    
    Call this before running the agent to capture the user message.
    
    Args:
        user_input: The user's message/query
        
    Example:
        >>> set_monkai_input("Como faço para cancelar minha assinatura?")
        >>> result = await Runner.run(agent, messages, hooks=get_monkai_hooks())
    """
    if _MONKAI_HOOKS:
        _MONKAI_HOOKS.set_user_input(user_input)


async def run_with_monkai_tracking(
    agent: "Agent",
    user_input: str,
    user_id: Optional[str] = None,
) -> Any:
    """
    Run an agent with MonkAI tracking enabled.
    
    This is the recommended way to run agents with full tracking.
    Captures internal tools (web_search, file_search) automatically.
    
    Args:
        agent: The agent to run
        user_input: User's message/query
        user_id: Optional user identifier for session management
        
    Returns:
        RunResult from the agent execution
        
    Example:
        >>> from atendentepro.utils import configure_monkai_trace, run_with_monkai_tracking
        >>> configure_monkai_trace(tracer_token="tk_your_token")
        >>> result = await run_with_monkai_tracking(network.triage, "Olá!")
    """
    if not _MONKAI_HOOKS:
        # Fallback to normal execution without tracking
        from agents import Runner
        return await Runner.run(agent, user_input)
    
    try:
        from monkai_trace.integrations.openai_agents import MonkAIRunHooks
        
        if user_id:
            _MONKAI_HOOKS.set_user_id(user_id)
        
        # Use run_with_tracking for full internal tools capture
        return await MonkAIRunHooks.run_with_tracking(agent, user_input, _MONKAI_HOOKS)
        
    except Exception as e:
        logger.error(f"Error running with MonkAI tracking: {e}")
        # Fallback to normal execution
        from agents import Runner
        return await Runner.run(agent, user_input)


# =============================================================================
# APPLICATION INSIGHTS INTEGRATION (Azure)
# =============================================================================

def configure_application_insights(connection_string: Optional[str] = None) -> bool:
    """
    Configure Application Insights tracing if connection string is available.
    
    Args:
        connection_string: Optional connection string. If not provided,
                          uses the value from configuration.
                          
    Returns:
        True if tracing was configured, False otherwise.
    """
    config = get_config()
    conn_str = connection_string or config.application_insights_connection_string
    
    if not conn_str:
        logger.debug("No Application Insights connection string provided. Tracing disabled.")
        return False
    
    try:
        # Try to configure Application Insights
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        
        # Check if azure monitor is available
        try:
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
            
            exporter = AzureMonitorTraceExporter(connection_string=conn_str)
            provider = TracerProvider()
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            
            logger.info("Application Insights tracing configured successfully.")
            return True
            
        except ImportError:
            logger.warning(
                "Azure Monitor exporter not available. "
                "Install 'azure-monitor-opentelemetry-exporter' for Application Insights support."
            )
            return False
            
    except ImportError:
        logger.warning(
            "OpenTelemetry not available. "
            "Install 'opentelemetry-sdk' for tracing support."
        )
        return False
    except Exception as e:
        logger.error(f"Failed to configure tracing: {e}")
        return False


# =============================================================================
# LEGACY ALIAS
# =============================================================================

def configure_tracing(connection_string: Optional[str] = None) -> bool:
    """
    Legacy alias for configure_application_insights.
    
    Deprecated: Use configure_monkai_trace() or configure_application_insights().
    """
    return configure_application_insights(connection_string)
