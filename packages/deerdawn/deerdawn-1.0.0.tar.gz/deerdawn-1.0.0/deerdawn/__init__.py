"""
DeerDawn Python SDK

Official Python client library for DeerDawn - AI governance and decision control platform.

Example:
    >>> from deerdawn import Deerdawn
    >>> client = Deerdawn(api_key='dd_prod_xxxxx')
    >>> result = client.evaluate_decision(
    ...     action_type='send_email',
    ...     trace_id='user-123',
    ...     payload={'recipient': 'user@example.com'}
    ... )
    >>> print(result.decision)  # 'allow', 'deny', or 'escalate'
"""

from .client import Deerdawn, DeerDawnAPIError
from .types import (
    DeerDawnConfig,
    EvaluateDecisionRequest,
    EvaluateDecisionResponse,
    Policy,
    Decision,
    DecisionResult,
)

__version__ = "1.0.0"
__all__ = [
    "Deerdawn",
    "DeerDawnAPIError",
    "DeerDawnConfig",
    "EvaluateDecisionRequest",
    "EvaluateDecisionResponse",
    "Policy",
    "Decision",
    "DecisionResult",
]
