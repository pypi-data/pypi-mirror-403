"""
Type definitions for DeerDawn Python SDK
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict

# Type alias for decision results
DecisionResult = Literal["allow", "deny", "escalate"]


class DeerDawnConfig(TypedDict, total=False):
    """Configuration options for DeerDawn client"""
    api_key: str  # Required
    base_url: Optional[str]
    timeout: Optional[int]
    max_retries: Optional[int]
    debug: Optional[bool]


class EvaluateDecisionRequest(TypedDict, total=False):
    """Request payload for decision evaluation"""
    action_type: str  # Required
    trace_id: str  # Required
    payload: Optional[Dict[str, Any]]


class EvaluateDecisionResponse(TypedDict, total=False):
    """Response from decision evaluation"""
    decision: DecisionResult
    reason: str
    policy_id: Optional[str]
    latency_ms: Optional[float]
    decision_id: Optional[str]


class Policy(TypedDict, total=False):
    """Policy definition"""
    policy_id: str
    name: str
    action_types: List[str]
    conditions: List[Any]
    decision: DecisionResult
    priority: int
    enabled: bool
    description: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class Decision(TypedDict, total=False):
    """Decision log entry"""
    decision_id: str
    org_id: str
    action_type: str
    trace_id: str
    decision: DecisionResult
    policy_id: Optional[str]
    reason: str
    payload: Optional[Dict[str, Any]]
    latency_ms: Optional[float]
    created_at: str


class ListPoliciesResponse(TypedDict):
    """Response from list policies endpoint"""
    policies: List[Policy]


class ListDecisionsResponse(TypedDict):
    """Response from list decisions endpoint"""
    decisions: List[Decision]


class DeerDawnErrorResponse(TypedDict, total=False):
    """Error response from API"""
    error: str
    message: Optional[str]
    status: Optional[int]
