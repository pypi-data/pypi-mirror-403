# DeerDawn Python SDK

Official Python client library for [DeerDawn](https://deerdawn.com) - AI governance and decision control platform.

## Installation

```bash
pip install deerdawn
```

## Quick Start

```python
from deerdawn import Deerdawn

# Initialize client
client = Deerdawn(api_key='dd_prod_xxxxx')  # Get from https://app.deerdawn.com/api-keys

# Evaluate a decision
result = client.evaluate_decision(
    action_type='send_email',
    trace_id='user-123-action-456',
    payload={
        'recipient': 'user@example.com',
        'subject': 'Hello World'
    }
)

if result['decision'] == 'allow':
    print('Action allowed')
    # Proceed with sending email
else:
    print(f"Action blocked: {result['reason']}")
```

## Type Hints

The SDK includes full type hints for Python 3.7+:

```python
from deerdawn import Deerdawn, EvaluateDecisionResponse, Policy
from typing import List

client = Deerdawn(api_key='dd_prod_xxxxx')

# Type-checked decision evaluation
result: EvaluateDecisionResponse = client.evaluate_decision(
    action_type='database_write',
    trace_id='req-789',
    payload={'table': 'users', 'operation': 'delete'}
)

# Type-checked policy list
policies: List[Policy] = client.list_policies()
```

## Configuration

```python
client = Deerdawn(
    api_key='dd_prod_xxxxx',           # Required: Your API key
    base_url='https://api.deerdawn.com',  # Optional: API base URL (default shown)
    timeout=5,                         # Optional: Request timeout in seconds (default: 5)
    max_retries=3,                     # Optional: Max retry attempts (default: 3)
    debug=False                        # Optional: Enable debug logging (default: False)
)
```

## API Reference

### `evaluate_decision(action_type, trace_id, payload=None)`

Evaluate an action against your policies.

**Parameters:**
- `action_type` (str, required): Type of action (e.g., "send_email", "database_write")
- `trace_id` (str, required): Unique trace identifier for correlation
- `payload` (dict, optional): Additional context data

**Returns:** `dict` with:
- `decision`: "allow" | "deny" | "escalate"
- `reason`: Human-readable explanation
- `policy_id`: ID of matched policy (if any)
- `latency_ms`: Evaluation latency
- `decision_id`: Decision log ID

**Example:**

```python
result = client.evaluate_decision(
    action_type='refund_payment',
    trace_id='order-12345',
    payload={
        'amount': 99.99,
        'currency': 'USD',
        'reason': 'customer_request'
    }
)

print(f"Decision: {result['decision']}")
print(f"Reason: {result['reason']}")
print(f"Latency: {result['latency_ms']}ms")
```

### `list_policies()`

Get all policies for your organization.

**Returns:** `List[dict]` - List of policy objects

**Example:**

```python
policies = client.list_policies()

for policy in policies:
    print(f"{policy['name']}: {policy['decision']} (priority: {policy['priority']})")
```

### `create_policy(...)`

Create a new policy.

**Parameters:**
- `name` (str): Policy name
- `action_types` (list): Action types this policy applies to
- `conditions` (list): Condition expressions
- `decision` (str): "allow", "deny", or "escalate"
- `priority` (int): Evaluation priority (lower = higher priority)
- `enabled` (bool): Whether policy is active
- `description` (str, optional): Policy description

**Returns:** `dict` - Created policy

**Example:**

```python
policy = client.create_policy(
    name='Auto-approve refunds under $100',
    action_types=['refund_payment'],
    conditions=[
        {
            'field': 'payload.amount',
            'operator': 'lt',
            'value': 100
        }
    ],
    decision='allow',
    priority=10,
    enabled=True,
    description='Automatically approve small refunds'
)
```

### `delete_policy(policy_id)`

Delete a policy.

**Parameters:**
- `policy_id` (str): Policy ID to delete

**Example:**

```python
client.delete_policy('pol_abc123')
```

### `list_decisions(decision=None, trace_id=None)`

Get decision logs with optional filters.

**Parameters:**
- `decision` (str, optional): Filter by decision type ("allow", "deny", "escalate")
- `trace_id` (str, optional): Filter by trace ID

**Returns:** `List[dict]` - List of decision objects

**Example:**

```python
# Get all denied decisions
denied_decisions = client.list_decisions(decision='deny')

# Get decisions for a specific trace
trace_decisions = client.list_decisions(trace_id='user-123')
```

### `get_decision(decision_id)`

Get a specific decision by ID.

**Parameters:**
- `decision_id` (str): Decision ID

**Returns:** `dict` - Decision object

**Example:**

```python
decision = client.get_decision('dec_xyz789')
print(decision['payload'])
```

## Error Handling

The SDK raises `DeerDawnAPIError` for API errors:

```python
from deerdawn import Deerdawn, DeerDawnAPIError

client = Deerdawn(api_key='dd_prod_xxxxx')

try:
    result = client.evaluate_decision(
        action_type='send_email',
        trace_id='test-123'
    )
except DeerDawnAPIError as error:
    print(f"API Error ({error.status}): {error}")
    print(f"Error code: {error.code}")
except Exception as error:
    print(f"Unexpected error: {error}")
```

## Common Error Codes

- `401 Unauthorized`: Invalid API key
- `402 Payment Required`: Plan limit exceeded
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error (automatically retried)

## Retry Logic

The SDK automatically retries failed requests with exponential backoff:
- Retries on 5xx errors
- Default: 3 retry attempts
- Backoff: 1s, 2s, 4s

Configure retry behavior:

```python
client = Deerdawn(
    api_key='dd_prod_xxxxx',
    max_retries=5  # More aggressive retries
)
```

## Debug Mode

Enable debug logging to troubleshoot issues:

```python
client = Deerdawn(
    api_key='dd_prod_xxxxx',
    debug=True
)

# Outputs:
# [DeerDawn] POST https://api.deerdawn.com/api/v1/decisions:evaluate
# [DeerDawn] Request body: {'action_type': 'send_email', ...}
# [DeerDawn] Response status: 200
# [DeerDawn] Response body: {'decision': 'allow', ...}
```

## Context Manager Support

The SDK supports context managers for automatic cleanup:

```python
with Deerdawn(api_key='dd_prod_xxxxx') as client:
    result = client.evaluate_decision(
        action_type='send_email',
        trace_id='test-123'
    )
# Session automatically closed
```

## Examples

### AI Agent with DeerDawn Guardrails

```python
from deerdawn import Deerdawn, DeerDawnAPIError
import os

client = Deerdawn(api_key=os.environ['DEERDAWN_API_KEY'])

def execute_agent_action(action_type, params):
    """Execute AI agent action with DeerDawn guardrails"""
    try:
        # Check permission before executing
        decision = client.evaluate_decision(
            action_type=action_type,
            trace_id=f"agent-{int(time.time())}",
            payload=params
        )

        if decision['decision'] == 'deny':
            raise PermissionError(f"Action blocked: {decision['reason']}")

        if decision['decision'] == 'escalate':
            print('Action requires human approval')
            # Queue for manual review
            return {'status': 'pending', 'reason': decision['reason']}

        # Proceed with action
        return perform_action(action_type, params)

    except DeerDawnAPIError as e:
        print(f"Decision check failed: {e}")
        raise

# Use in your agent
execute_agent_action('send_email', {
    'recipient': 'user@example.com',
    'subject': 'AI-generated report'
})
```

### Flask Decorator

```python
from functools import wraps
from flask import request, jsonify
from deerdawn import Deerdawn

client = Deerdawn(api_key=os.environ['DEERDAWN_API_KEY'])

def require_permission(action_type):
    """Decorator to check permissions via DeerDawn"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                decision = client.evaluate_decision(
                    action_type=action_type,
                    trace_id=request.headers.get('X-Trace-ID', f"req-{int(time.time())}"),
                    payload={
                        'user': getattr(request, 'user', None),
                        **request.get_json(silent=True) or {}
                    }
                )

                if decision['decision'] != 'allow':
                    return jsonify({
                        'error': 'forbidden',
                        'reason': decision['reason']
                    }), 403

                return f(*args, **kwargs)

            except Exception as e:
                return jsonify({'error': 'decision_check_failed'}), 500

        return decorated_function
    return decorator

# Use on routes
@app.route('/api/refunds', methods=['POST'])
@require_permission('refund_payment')
def process_refund():
    # Process refund
    pass
```

### Django Middleware

```python
from deerdawn import Deerdawn
from django.http import JsonResponse
import os

class DeerDawnMiddleware:
    """Django middleware for DeerDawn decision control"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.client = Deerdawn(api_key=os.environ['DEERDAWN_API_KEY'])

    def __call__(self, request):
        # Check permissions for protected endpoints
        if request.path.startswith('/api/protected/'):
            action_type = f"{request.method.lower()}_{request.path.split('/')[-1]}"

            try:
                decision = self.client.evaluate_decision(
                    action_type=action_type,
                    trace_id=request.META.get('HTTP_X_TRACE_ID', f"req-{int(time.time())}"),
                    payload={
                        'user': getattr(request, 'user', None),
                        'method': request.method,
                        'path': request.path
                    }
                )

                if decision['decision'] != 'allow':
                    return JsonResponse({
                        'error': 'forbidden',
                        'reason': decision['reason']
                    }, status=403)

            except Exception as e:
                return JsonResponse({'error': 'decision_check_failed'}, status=500)

        return self.get_response(request)
```

## Support

- **Documentation**: https://deerdawn.com/docs
- **API Reference**: https://deerdawn.com/docs/api-reference
- **Issues**: https://github.com/deerdawn/deerdawn-sdk-python/issues
- **Email**: support@deerdawn.com

## License

MIT
