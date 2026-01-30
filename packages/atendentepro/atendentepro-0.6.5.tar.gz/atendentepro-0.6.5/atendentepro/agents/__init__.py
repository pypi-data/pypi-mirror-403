# -*- coding: utf-8 -*-
"""
Agents module for AtendentePro library.

This module provides factory functions for creating agents with customizable
configurations. Templates can be loaded from external directories.
"""

from .triage import create_triage_agent, TriageAgent
from .flow import create_flow_agent, FlowAgent
from .interview import create_interview_agent, InterviewAgent
from .answer import create_answer_agent, AnswerAgent
from .knowledge import create_knowledge_agent, KnowledgeAgent, go_to_rag
from .confirmation import create_confirmation_agent, ConfirmationAgent
from .usage import create_usage_agent, UsageAgent
from .onboarding import create_onboarding_agent, OnboardingAgent
from .escalation import create_escalation_agent, EscalationAgent, ESCALATION_TOOLS
from .feedback import create_feedback_agent, FeedbackAgent, FEEDBACK_TOOLS, configure_feedback_storage

__all__ = [
    # Triage
    "create_triage_agent",
    "TriageAgent",
    # Flow
    "create_flow_agent",
    "FlowAgent",
    # Interview
    "create_interview_agent",
    "InterviewAgent",
    # Answer
    "create_answer_agent",
    "AnswerAgent",
    # Knowledge
    "create_knowledge_agent",
    "KnowledgeAgent",
    "go_to_rag",
    # Confirmation
    "create_confirmation_agent",
    "ConfirmationAgent",
    # Usage
    "create_usage_agent",
    "UsageAgent",
    # Onboarding
    "create_onboarding_agent",
    "OnboardingAgent",
    # Escalation
    "create_escalation_agent",
    "EscalationAgent",
    "ESCALATION_TOOLS",
    # Feedback
    "create_feedback_agent",
    "FeedbackAgent",
    "FEEDBACK_TOOLS",
    "configure_feedback_storage",
]

