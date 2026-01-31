"""
Starvex Core - Main SDK Interface
The primary interface for interacting with Starvex guardrails.
"""

import uuid
import time
import logging
import asyncio
from typing import Optional, Callable, Any, Dict, List

from .models import (
    GuardVerdict,
    GuardConfig,
    GuardRule,
    GuardRuleType,
    GuardResponse,
    GuardCheckResult,
    DashboardConfig,
)
from ._internals.tracer import InternalTracer
from ._internals.engine_nemo import NemoEngine
from ._internals.engine_eval import EvalEngine
from .utils import redact_sensitive_data, get_config_from_env, setup_logging, load_api_key

logger = logging.getLogger(__name__)


class Starvex:
    """
    Starvex - Production-ready AI agents with guardrails, observability, and security.

    Example Usage:
        ```python
        from starvex import Starvex

        vex = Starvex(api_key="sv_live_xxx")

        async def my_agent(prompt):
            return "Agent response"

        result = await vex.secure(prompt="Hello", agent_function=my_agent)
        ```

    Get your API key at: https://starvex.in/dashboard
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[GuardConfig] = None,
        redact_pii: bool = False,
        api_host: str = "https://decqadhkqnacujoyirkh.supabase.co/functions/v1",
        nemo_config_path: Optional[str] = None,
        enable_tracing: bool = True,
        log_level: str = "INFO",
    ):
        """
        Initialize Starvex SDK.

        Args:
            api_key: Your Starvex API key (sv_live_xxx or sv_test_xxx)
                     Get one at https://starvex.in/dashboard
            config: Optional GuardConfig for custom settings
            redact_pii: If True, PII will be masked before sending logs
            api_host: Starvex API host
            nemo_config_path: Path to NeMo Guardrails config directory
            enable_tracing: Enable/disable observability tracing
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        setup_logging(log_level)

        # Load from environment or saved config if not provided
        env_config = get_config_from_env()
        self.api_key = api_key or env_config.get("api_key") or load_api_key()
        self.api_host = api_host or env_config.get("api_host")
        self.redact_pii = redact_pii or env_config.get("redact_pii", False)

        # Initialize configuration
        self.config = config or GuardConfig()

        # Initialize internal engines
        self.tracer = InternalTracer(
            api_key=self.api_key or "",
            host=self.api_host,
            enabled=enable_tracing and bool(self.api_key),
        )
        self.guard_engine = NemoEngine(config_path=nemo_config_path)
        self.eval_engine = EvalEngine()

        # Dashboard config (fetched from API or set locally)
        self._dashboard_config: Optional[DashboardConfig] = None

        if self.api_key:
            logger.info("Starvex SDK initialized with API key")
        else:
            logger.warning(
                "Starvex SDK initialized without API key - run 'starvex login' or set STARVEX_API_KEY"
            )

    async def secure(
        self,
        prompt: str,
        agent_function: Callable[[str], Any],
        context: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        skip_input_check: bool = False,
        skip_output_check: bool = False,
    ) -> GuardResponse:
        """
        The Master Function - Secures an AI agent interaction.

        1. Checks Input Safety (jailbreak, PII, toxicity)
        2. Calls the Agent Function
        3. Checks Output Quality (hallucination, toxicity)
        4. Logs everything to observability platform

        Args:
            prompt: User input prompt
            agent_function: Async or sync function that takes prompt and returns response
            context: Optional context for hallucination checking
            user_id: Optional user identifier for tracing
            session_id: Optional session identifier for tracing
            metadata: Optional additional metadata
            skip_input_check: Skip pre-flight input safety check
            skip_output_check: Skip post-flight output quality check

        Returns:
            GuardResponse with status, response, and detailed checks
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        all_checks: List[GuardCheckResult] = []

        # Prepare logging text (potentially redacted)
        log_prompt = redact_sensitive_data(prompt) if self.redact_pii else prompt

        # --- STEP 1: PRE-FLIGHT CHECK ---
        if not skip_input_check:
            is_safe, block_msg, input_checks = await self.guard_engine.check_input(
                prompt,
                check_jailbreak=True,
                check_pii=self._should_block_pii(),
                check_toxicity=True,
            )
            all_checks.extend(input_checks)

            if not is_safe:
                verdict = self._get_verdict_from_checks(input_checks)
                latency_ms = (time.time() - start_time) * 1000

                self.tracer.log_event(
                    trace_id=trace_id,
                    input_text=log_prompt,
                    output_text=block_msg,
                    verdict=verdict,
                    confidence_score=1.0,
                    user_id=user_id,
                    session_id=session_id,
                    latency_ms=latency_ms,
                    checks=all_checks,
                    metadata=metadata,
                )

                return GuardResponse(
                    status="blocked",
                    response=block_msg,
                    verdict=verdict,
                    checks=all_checks,
                    trace_id=trace_id,
                    latency_ms=latency_ms,
                )

        # --- STEP 2: AGENT EXECUTION ---
        try:
            if asyncio.iscoroutinefunction(agent_function):
                agent_response = await agent_function(prompt)
            else:
                agent_response = agent_function(prompt)

            if not isinstance(agent_response, str):
                agent_response = str(agent_response)

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            self.tracer.log_event(
                trace_id=trace_id,
                input_text=log_prompt,
                output_text=str(e),
                verdict=GuardVerdict.FAILED_SYSTEM,
                confidence_score=0.0,
                user_id=user_id,
                session_id=session_id,
                latency_ms=latency_ms,
                checks=all_checks,
                metadata={"error": str(e), **(metadata or {})},
            )

            raise

        log_response = redact_sensitive_data(agent_response) if self.redact_pii else agent_response

        # --- STEP 3: POST-FLIGHT CHECK ---
        warning = None
        final_verdict = GuardVerdict.PASSED

        if not skip_output_check:
            is_safe, block_msg, output_checks = await self.guard_engine.check_output(
                prompt, agent_response, check_pii=self._should_block_pii(), check_toxicity=True
            )
            all_checks.extend(output_checks)

            if not is_safe:
                final_verdict = self._get_verdict_from_checks(output_checks)
                latency_ms = (time.time() - start_time) * 1000

                self.tracer.log_event(
                    trace_id=trace_id,
                    input_text=log_prompt,
                    output_text=log_response,
                    verdict=final_verdict,
                    confidence_score=1.0,
                    user_id=user_id,
                    session_id=session_id,
                    latency_ms=latency_ms,
                    checks=all_checks,
                    metadata=metadata,
                )

                return GuardResponse(
                    status="blocked",
                    response=block_msg,
                    verdict=final_verdict,
                    checks=all_checks,
                    trace_id=trace_id,
                    latency_ms=latency_ms,
                )

            # Hallucination check
            hallucination_result = self.eval_engine.evaluate_with_result(
                prompt, agent_response, context
            )
            all_checks.append(hallucination_result)

            if not hallucination_result.passed:
                final_verdict = GuardVerdict.FAILED_HALLUCINATION
                warning = f"High hallucination risk (score: {hallucination_result.confidence:.2f})"

        # --- STEP 4: SUCCESS ---
        latency_ms = (time.time() - start_time) * 1000
        status = "flagged" if warning else "success"

        confidence = 0.0
        if final_verdict != GuardVerdict.PASSED:
            for check in all_checks:
                if check.rule_type == GuardRuleType.HALLUCINATION and not check.passed:
                    confidence = check.confidence
                    break

        self.tracer.log_event(
            trace_id=trace_id,
            input_text=log_prompt,
            output_text=log_response,
            verdict=final_verdict,
            confidence_score=confidence,
            user_id=user_id,
            session_id=session_id,
            latency_ms=latency_ms,
            checks=all_checks,
            metadata=metadata,
        )

        return GuardResponse(
            status=status,
            response=agent_response,
            verdict=final_verdict,
            checks=all_checks,
            trace_id=trace_id,
            latency_ms=latency_ms,
            warning=warning,
        )

    async def protect(
        self, prompt: str, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> GuardResponse:
        """
        Check input only (no agent execution).
        Use this for pre-screening prompts before sending to any LLM.

        Args:
            prompt: User input to check
            user_id: Optional user identifier
            session_id: Optional session identifier

        Returns:
            GuardResponse with check results
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()

        log_prompt = redact_sensitive_data(prompt) if self.redact_pii else prompt

        is_safe, block_msg, checks = await self.guard_engine.check_input(prompt)

        latency_ms = (time.time() - start_time) * 1000
        verdict = GuardVerdict.PASSED if is_safe else self._get_verdict_from_checks(checks)

        self.tracer.log_event(
            trace_id=trace_id,
            input_text=log_prompt,
            output_text=block_msg,
            verdict=verdict,
            confidence_score=0.0 if is_safe else 1.0,
            user_id=user_id,
            session_id=session_id,
            latency_ms=latency_ms,
            checks=checks,
        )

        return GuardResponse(
            status="success" if is_safe else "blocked",
            response=block_msg,
            verdict=verdict,
            checks=checks,
            trace_id=trace_id,
            latency_ms=latency_ms,
        )

    def test(
        self, prompt: str, response: str, context: Optional[List[str]] = None
    ) -> GuardResponse:
        """
        Test mode - evaluate a prompt/response pair without tracing.
        Use this for testing and development.

        Args:
            prompt: Test prompt
            response: Test response
            context: Optional context for evaluation

        Returns:
            GuardResponse with evaluation results
        """
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        checks: List[GuardCheckResult] = []

        metrics = self.eval_engine.full_evaluation(prompt, response, context)

        checks.append(
            GuardCheckResult(
                rule_type=GuardRuleType.HALLUCINATION,
                passed=metrics.hallucination_score < 0.5,
                confidence=metrics.hallucination_score,
                message=f"Hallucination score: {metrics.hallucination_score:.2f}",
            )
        )

        checks.append(
            GuardCheckResult(
                rule_type=GuardRuleType.TOXICITY,
                passed=metrics.toxicity_score < 0.3,
                confidence=metrics.toxicity_score,
                message=f"Toxicity score: {metrics.toxicity_score:.2f}",
            )
        )

        latency_ms = (time.time() - start_time) * 1000

        all_passed = all(c.passed for c in checks)
        verdict = GuardVerdict.PASSED if all_passed else self._get_verdict_from_checks(checks)

        return GuardResponse(
            status="success" if all_passed else "flagged",
            response=response,
            verdict=verdict,
            checks=checks,
            trace_id=trace_id,
            latency_ms=latency_ms,
            metadata={"metrics": metrics.model_dump()},
        )

    def add_rule(self, rule: GuardRule):
        """Add a guard rule to the configuration"""
        self.config.rules.append(rule)
        logger.info(f"Added rule: {rule.rule_type.value}")

    def remove_rule(self, rule_type: GuardRuleType):
        """Remove all rules of a specific type"""
        self.config.rules = [r for r in self.config.rules if r.rule_type != rule_type]
        logger.info(f"Removed rules of type: {rule_type.value}")

    async def sync_config(self) -> DashboardConfig:
        """
        Sync configuration from Starvex Dashboard.
        Call this on startup to get latest rules from dashboard.
        """
        if not self.api_key:
            logger.warning("Cannot sync config without API key")
            return DashboardConfig()

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_host}/get-settings",
                    headers={"x-api-key": self.api_key},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    self._dashboard_config = DashboardConfig(**data)
                    logger.info("Dashboard configuration synced")
                    return self._dashboard_config
        except Exception as e:
            logger.warning(f"Failed to sync config: {e}")

        if not self._dashboard_config:
            self._dashboard_config = DashboardConfig()
        return self._dashboard_config

    def set_dashboard_config(self, config: DashboardConfig):
        """Set dashboard configuration locally"""
        self._dashboard_config = config
        logger.info("Dashboard configuration updated")

    def _should_block_pii(self) -> bool:
        """Check if PII should be blocked based on config"""
        if self._dashboard_config:
            return self._dashboard_config.block_pii

        for rule in self.config.rules:
            if rule.rule_type == GuardRuleType.PII and rule.enabled:
                return True

        return True  # Default to blocking PII

    def _get_verdict_from_checks(self, checks: List[GuardCheckResult]) -> GuardVerdict:
        """Determine verdict from check results"""
        for check in checks:
            if not check.passed:
                if check.rule_type == GuardRuleType.JAILBREAK:
                    return GuardVerdict.BLOCKED_JAILBREAK
                elif check.rule_type == GuardRuleType.PII:
                    return GuardVerdict.BLOCKED_PII
                elif check.rule_type == GuardRuleType.TOXICITY:
                    return GuardVerdict.BLOCKED_TOXICITY
                elif check.rule_type == GuardRuleType.COMPETITOR:
                    return GuardVerdict.BLOCKED_COMPETITOR
                elif check.rule_type == GuardRuleType.HALLUCINATION:
                    return GuardVerdict.FAILED_HALLUCINATION

        return GuardVerdict.PASSED

    def flush(self):
        """Flush pending events to the server"""
        self.tracer.flush()

    def shutdown(self):
        """Shutdown the SDK gracefully"""
        self.tracer.shutdown()
        logger.info("Starvex SDK shutdown complete")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
