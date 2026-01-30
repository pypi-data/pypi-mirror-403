# -*- coding: utf-8 -*-
"""Prompts module for AtendentePro library."""

from .triage import get_triage_prompt, TRIAGE_INTRO
from .flow import get_flow_prompt, FlowPromptBuilder
from .interview import get_interview_prompt, InterviewPromptBuilder
from .answer import get_answer_prompt, AnswerPromptBuilder
from .knowledge import get_knowledge_prompt, KnowledgePromptBuilder
from .confirmation import get_confirmation_prompt, ConfirmationPromptBuilder
from .onboarding import get_onboarding_prompt, OnboardingPromptBuilder
from .escalation import get_escalation_prompt, EscalationPromptBuilder, ESCALATION_INTRO
from .feedback import get_feedback_prompt, FeedbackPromptBuilder, FEEDBACK_INTRO

__all__ = [
    # Triage
    "get_triage_prompt",
    "TRIAGE_INTRO",
    # Flow
    "get_flow_prompt",
    "FlowPromptBuilder",
    # Interview
    "get_interview_prompt",
    "InterviewPromptBuilder",
    # Answer
    "get_answer_prompt",
    "AnswerPromptBuilder",
    # Knowledge
    "get_knowledge_prompt",
    "KnowledgePromptBuilder",
    # Confirmation
    "get_confirmation_prompt",
    "ConfirmationPromptBuilder",
    # Onboarding
    "get_onboarding_prompt",
    "OnboardingPromptBuilder",
    # Escalation
    "get_escalation_prompt",
    "EscalationPromptBuilder",
    "ESCALATION_INTRO",
    # Feedback
    "get_feedback_prompt",
    "FeedbackPromptBuilder",
    "FEEDBACK_INTRO",
]

