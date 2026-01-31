# Starvex

Production-ready AI agents with guardrails, observability, and security.

## Installation

```bash
pip install starvex
```

## Quick Start

1. **Get your API key** at [starvex.in/dashboard](https://starvex.in/dashboard)

2. **Login with your API key**:
```bash
starvex login
```

3. **Use in your code**:
```python
from starvex import Starvex

vex = Starvex()

async def my_agent(prompt: str) -> str:
    # Your AI agent logic here
    return "Agent response"

# Secure your agent with guardrails
result = await vex.secure(
    prompt="User input",
    agent_function=my_agent
)

if result.status == "success":
    print(result.response)
elif result.status == "blocked":
    print(f"Blocked: {result.verdict.value}")
```

## Features

### Guardrails
Automatically detect and block:
- **Jailbreak attempts** - Prompt injection attacks
- **PII leakage** - Email, phone, SSN, credit cards
- **Toxic content** - Harmful or inappropriate text
- **Competitor mentions** - Block competitor references (configurable)

### Observability
Full visibility into your AI agent behavior:
- Real-time event tracing
- Latency monitoring
- Success/failure analytics
- Dashboard at [starvex.in/dashboard](https://starvex.in/dashboard)

### Evaluation
Quality checks on agent outputs:
- Hallucination detection
- Faithfulness scoring
- Relevancy analysis

## CLI Commands

```bash
# Login with your API key
starvex login

# Check connection status
starvex status

# Check a prompt for safety
starvex check "Your prompt here"

# Test a prompt/response pair
starvex test --prompt "Question" --response "Answer"

# Show current configuration
starvex config --show

# Show version
starvex version

# Logout
starvex logout
```

## API Reference

### Starvex

```python
from starvex import Starvex

vex = Starvex(
    api_key="sv_live_xxx",  # Or set STARVEX_API_KEY env var
    redact_pii=False,       # Mask PII before logging
    enable_tracing=True,    # Enable observability
)
```

### Methods

#### `secure(prompt, agent_function, context=None)`
The main method - secures an AI agent interaction:
1. Checks input safety (jailbreak, PII, toxicity)
2. Calls your agent function
3. Checks output quality (hallucination, toxicity)
4. Logs everything to the dashboard

```python
result = await vex.secure(
    prompt="User input",
    agent_function=my_agent,
    context=["Optional context for hallucination checking"],
    user_id="optional-user-id",
    session_id="optional-session-id",
)
```

#### `protect(prompt)`
Check input only (no agent execution):

```python
result = await vex.protect("User input")
if result.status == "blocked":
    print("Input blocked!")
```

#### `test(prompt, response, context=None)`
Test mode - evaluate a prompt/response pair without tracing:

```python
result = vex.test(
    prompt="What is 2+2?",
    response="2+2 equals 4",
    context=["Math fact: 2+2=4"]
)
```

### Response Object

```python
class GuardResponse:
    status: str          # "success", "blocked", "flagged"
    response: str        # The agent response (or block message)
    verdict: str         # PASSED, BLOCKED_JAILBREAK, BLOCKED_PII, etc.
    checks: list         # Detailed check results
    trace_id: str        # Unique trace ID for debugging
    latency_ms: float    # Total processing time
    warning: str | None  # Warning message if flagged
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `STARVEX_API_KEY` | Your Starvex API key |
| `STARVEX_API_HOST` | Custom API host (optional) |
| `STARVEX_REDACT_PII` | Set to "true" to mask PII |
| `STARVEX_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Dashboard

View your metrics and manage API keys at [starvex.in/dashboard](https://starvex.in/dashboard)

- Real-time request monitoring
- Block rate analytics
- Latency tracking
- API key management
- Guardrail configuration

## Links

- Website: [starvex.in](https://starvex.in)
- Dashboard: [starvex.in/dashboard](https://starvex.in/dashboard)
- Documentation: [starvex.in/docs](https://starvex.in/docs)

## License

MIT
