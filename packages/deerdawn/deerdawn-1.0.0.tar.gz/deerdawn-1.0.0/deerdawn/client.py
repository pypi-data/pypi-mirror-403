"""
DeerDawn Python SDK Client
"""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .types import (
    DeerDawnConfig,
    EvaluateDecisionRequest,
    EvaluateDecisionResponse,
    Policy,
    Decision,
    ListPoliciesResponse,
    ListDecisionsResponse,
)


class DeerDawnAPIError(Exception):
    """Custom exception for DeerDawn API errors"""

    def __init__(self, message: str, status: Optional[int] = None, code: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.code = code


class Deerdawn:
    """
    DeerDawn Python SDK Client

    Initialize with your API key to start evaluating decisions.

    Args:
        api_key: Your DeerDawn API key (get from https://app.deerdawn.com/api-keys)
        base_url: API base URL (default: https://api.deerdawn.com)
        timeout: Request timeout in seconds (default: 5)
        max_retries: Maximum retry attempts for failed requests (default: 3)
        debug: Enable debug logging (default: False)

    Example:
        >>> client = Deerdawn(api_key='dd_prod_xxxxx')
        >>> result = client.evaluate_decision(
        ...     action_type='send_email',
        ...     trace_id='user-123'
        ... )
        >>> print(result['decision'])
        'allow'
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deerdawn.com",
        timeout: int = 5,
        max_retries: int = 3,
        debug: bool = False,
    ):
        if not api_key:
            raise ValueError("DeerDawn API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug

        # Configure session with retry logic
        self.session = requests.Session()

        # Set up retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[500, 502, 503, 504],  # Retry on server errors
            allowed_methods=["HEAD", "GET", "POST", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=1,  # Exponential backoff: 1s, 2s, 4s
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "deerdawn-python-sdk/1.0.0",
        })

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Make HTTP request with error handling

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API endpoint path
            json: Request body (for POST requests)
            params: Query parameters (for GET requests)

        Returns:
            Parsed JSON response

        Raises:
            DeerDawnAPIError: On API errors
        """
        url = urljoin(self.base_url, path)

        if self.debug:
            print(f"[DeerDawn] {method} {url}")
            if json:
                print(f"[DeerDawn] Request body: {json}")
            if params:
                print(f"[DeerDawn] Query params: {params}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                timeout=self.timeout,
            )

            if self.debug:
                print(f"[DeerDawn] Response status: {response.status_code}")
                print(f"[DeerDawn] Response body: {response.text}")

            # Handle successful responses
            if 200 <= response.status_code < 300:
                if response.status_code == 204:  # No content
                    return None
                return response.json()

            # Handle error responses
            try:
                error_data = response.json()
                error_message = error_data.get("message") or error_data.get("error") or "API request failed"
                error_code = error_data.get("error")
            except ValueError:
                error_message = response.text or f"HTTP {response.status_code}"
                error_code = None

            raise DeerDawnAPIError(
                error_message,
                status=response.status_code,
                code=error_code,
            )

        except requests.exceptions.Timeout:
            raise DeerDawnAPIError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise DeerDawnAPIError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise DeerDawnAPIError(f"Request failed: {str(e)}")

    def evaluate_decision(
        self,
        action_type: str,
        trace_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> EvaluateDecisionResponse:
        """
        Evaluate a decision against your policies

        Args:
            action_type: Type of action (e.g., 'send_email', 'database_write')
            trace_id: Unique trace identifier for correlation
            payload: Additional context data for policy evaluation

        Returns:
            Decision response with 'decision', 'reason', 'policy_id', etc.

        Raises:
            DeerDawnAPIError: On API errors

        Example:
            >>> result = client.evaluate_decision(
            ...     action_type='send_email',
            ...     trace_id='user-123-action-456',
            ...     payload={
            ...         'recipient': 'user@example.com',
            ...         'subject': 'Hello World'
            ...     }
            ... )
            >>> if result['decision'] == 'allow':
            ...     print('Action allowed')
            >>> else:
            ...     print(f"Action blocked: {result['reason']}")
        """
        request_body: EvaluateDecisionRequest = {
            "action_type": action_type,
            "trace_id": trace_id,
        }
        if payload is not None:
            request_body["payload"] = payload

        return self._request("POST", "/api/v1/decisions:evaluate", json=request_body)

    def list_policies(self) -> List[Policy]:
        """
        List all policies for your organization

        Returns:
            List of policy objects

        Example:
            >>> policies = client.list_policies()
            >>> for policy in policies:
            ...     print(f"{policy['name']}: {policy['decision']}")
        """
        response: ListPoliciesResponse = self._request("GET", "/api/v1/policies")
        return response["policies"]

    def create_policy(
        self,
        name: str,
        action_types: List[str],
        conditions: List[Any],
        decision: str,
        priority: int,
        enabled: bool = True,
        description: Optional[str] = None,
    ) -> Policy:
        """
        Create a new policy

        Args:
            name: Policy name
            action_types: Action types this policy applies to
            conditions: Condition expressions
            decision: 'allow', 'deny', or 'escalate'
            priority: Evaluation priority (lower = higher priority)
            enabled: Whether policy is active
            description: Optional policy description

        Returns:
            Created policy object

        Example:
            >>> policy = client.create_policy(
            ...     name='Auto-approve small refunds',
            ...     action_types=['refund_payment'],
            ...     conditions=[
            ...         {'field': 'payload.amount', 'operator': 'lt', 'value': 100}
            ...     ],
            ...     decision='allow',
            ...     priority=10,
            ...     enabled=True
            ... )
        """
        policy_data = {
            "name": name,
            "action_types": action_types,
            "conditions": conditions,
            "decision": decision,
            "priority": priority,
            "enabled": enabled,
        }
        if description is not None:
            policy_data["description"] = description

        return self._request("POST", "/api/v1/policies", json={"policy": policy_data})

    def delete_policy(self, policy_id: str) -> None:
        """
        Delete a policy

        Args:
            policy_id: Policy ID to delete

        Example:
            >>> client.delete_policy('pol_abc123')
        """
        self._request("DELETE", f"/api/v1/policies/{policy_id}")

    def list_decisions(
        self,
        decision: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> List[Decision]:
        """
        List decision logs with optional filters

        Args:
            decision: Filter by decision type ('allow', 'deny', 'escalate')
            trace_id: Filter by trace ID

        Returns:
            List of decision objects

        Example:
            >>> # Get all denied decisions
            >>> denied = client.list_decisions(decision='deny')
            >>>
            >>> # Get decisions for specific trace
            >>> trace_decisions = client.list_decisions(trace_id='user-123')
        """
        params = {}
        if decision:
            params["decision"] = decision
        if trace_id:
            params["trace_id"] = trace_id

        response: ListDecisionsResponse = self._request(
            "GET",
            "/api/v1/decisions",
            params=params if params else None,
        )
        return response["decisions"]

    def get_decision(self, decision_id: str) -> Decision:
        """
        Get a specific decision by ID

        Args:
            decision_id: Decision ID

        Returns:
            Decision object

        Example:
            >>> decision = client.get_decision('dec_xyz789')
            >>> print(decision['reason'])
        """
        return self._request("GET", f"/api/v1/decisions/{decision_id}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session"""
        self.session.close()
