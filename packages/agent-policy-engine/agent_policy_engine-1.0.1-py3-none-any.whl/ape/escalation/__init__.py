"""
APE Escalation Module

Agent Policy Engine
Version v1.0.1
https://github.com/kahalewai/agent-policy-engine

Contains escalation handling (stub for v1.0).
"""

from ape.escalation.handler import (
    EscalationHandler,
    EscalationResolver,
    EscalationRequest,
    EscalationResult,
    EscalationDecision,
    DefaultDenyResolver,
)

__all__ = [
    "EscalationHandler",
    "EscalationResolver",
    "EscalationRequest",
    "EscalationResult",
    "EscalationDecision",
    "DefaultDenyResolver",
]
