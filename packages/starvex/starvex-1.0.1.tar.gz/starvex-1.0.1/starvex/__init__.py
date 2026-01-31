"""
Starvex - Production-ready AI agents with guardrails, observability, and security

Build AI agents that are safe, measurable, and ready to ship.

Quick Start:
    ```python
    from starvex import Starvex

    # Initialize with API key from starvex.in/dashboard
    vex = Starvex(api_key="sv_live_xxx")

    # Define your AI agent
    async def my_agent(prompt: str) -> str:
        return "Agent response"

    # Secure your agent interactions
    result = await vex.secure(
        prompt="User input",
        agent_function=my_agent
    )

    if result.status == "success":
        print(result.response)
    elif result.status == "blocked":
        print(f"Blocked: {result.verdict.value}")
    ```

Get your API key at: https://starvex.in/dashboard
Documentation: https://starvex.in/docs
"""

from .core import Starvex
from .models import (
    GuardVerdict,
    GuardRule,
    GuardRuleType,
    GuardConfig,
    GuardInput,
    GuardResponse,
    GuardCheckResult,
    EvalMetrics,
    DashboardConfig,
)
from .utils import (
    generate_api_key,
    validate_api_key_format,
    redact_sensitive_data,
    setup_logging,
)

__version__ = "1.0.1"
__author__ = "Starvex Team"
__all__ = [
    # Main class
    "Starvex",
    # Models
    "GuardVerdict",
    "GuardRule",
    "GuardRuleType",
    "GuardConfig",
    "GuardInput",
    "GuardResponse",
    "GuardCheckResult",
    "EvalMetrics",
    "DashboardConfig",
    # Utilities
    "generate_api_key",
    "validate_api_key_format",
    "redact_sensitive_data",
    "setup_logging",
]
