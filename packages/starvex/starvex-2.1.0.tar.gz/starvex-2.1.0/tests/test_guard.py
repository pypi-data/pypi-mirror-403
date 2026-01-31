"""
Tests for StarvexGuard class

Tests the main StarvexGuard class including:
- Initialization with different configurations
- check_input() and check_output() methods
- @guard.protect decorator (sync and async)
- Rule management (add_rule, remove_rule, get_rules)
- Context manager support
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from starvex.guard import StarvexGuard, CheckResult, GuardedResponse
from starvex.rules import (
    GuardRule,
    RuleResult,
    RuleAction,
    BlockPII,
    BlockJailbreak,
    BlockToxicity,
    TopicRestriction,
    CustomBlocklist,
    default_rules,
)


class TestStarvexGuardInit:
    """Tests for StarvexGuard initialization"""

    def test_init_with_no_rules(self, patch_engines):
        """Should initialize with empty rules list"""
        guard = StarvexGuard(rules=[], enable_tracing=False)
        assert guard.rules == []
        assert guard.api_key is None
        assert guard.enable_tracing is False

    def test_init_with_default_rules(self, patch_engines):
        """Should use default rules when none provided"""
        guard = StarvexGuard(enable_tracing=False)
        assert len(guard.rules) == 3  # BlockJailbreak, BlockPII, BlockToxicity

    def test_init_with_custom_rules(self, patch_engines):
        """Should accept custom rules list"""
        rules = [BlockPII(), BlockJailbreak()]
        guard = StarvexGuard(rules=rules, enable_tracing=False)
        assert len(guard.rules) == 2

    def test_init_with_api_key(self, patch_engines):
        """Should accept API key and enable tracing"""
        with patch("starvex.guard.InternalTracer") as mock_tracer:
            guard = StarvexGuard(
                rules=[],
                api_key="sv_live_test123",
                enable_tracing=True,
            )
            assert guard.api_key == "sv_live_test123"
            mock_tracer.assert_called_once()

    def test_init_with_custom_handlers(self, patch_engines):
        """Should accept custom on_block and on_flag handlers"""
        custom_block = Mock(return_value="Custom blocked message")
        custom_flag = Mock()

        guard = StarvexGuard(
            rules=[],
            on_block=custom_block,
            on_flag=custom_flag,
            enable_tracing=False,
        )

        assert guard.on_block == custom_block
        assert guard.on_flag == custom_flag


class TestCheckInput:
    """Tests for check_input() method"""

    def test_check_input_passes_clean_text(self, simple_guard):
        """Should pass clean text with no rule violations"""
        result = simple_guard.check_input("Hello, how are you?")
        assert result.passed is True
        assert result.blocked_by is None
        assert result.message == "All checks passed"

    def test_check_input_blocks_pii(self, guard_with_pii, sample_pii_texts):
        """Should block text containing PII"""
        result = guard_with_pii.check_input(sample_pii_texts["ssn"])
        assert result.passed is False
        assert result.blocked_by == "block_pii"
        assert "PII detected" in result.message

    def test_check_input_blocks_jailbreak(self, guard_with_jailbreak, sample_jailbreak_texts):
        """Should block jailbreak attempts"""
        result = guard_with_jailbreak.check_input(sample_jailbreak_texts["ignore_instructions"])
        assert result.passed is False
        assert result.blocked_by == "block_jailbreak"

    def test_check_input_returns_latency(self, simple_guard):
        """Should return latency_ms in result"""
        result = simple_guard.check_input("Test text")
        assert result.latency_ms >= 0

    def test_check_input_returns_all_results(self, guard_with_all_rules):
        """Should return all rule results in all_results"""
        result = guard_with_all_rules.check_input("Clean text here")
        assert len(result.all_results) == len(guard_with_all_rules.rules)

    def test_check_input_with_redaction(self, patch_engines):
        """Should return redacted text when PII rule uses redaction"""
        guard = StarvexGuard(
            rules=[BlockPII(redact_instead=True)],
            enable_tracing=False,
        )
        result = guard.check_input("My SSN is 123-45-6789")
        assert result.passed is True  # Passes with redaction
        assert result.redacted_text is not None
        assert "[REDACTED_SSN]" in result.redacted_text

    def test_check_input_stops_on_first_block(self, guard_with_all_rules, sample_jailbreak_texts):
        """Should stop checking on first blocking rule"""
        result = guard_with_all_rules.check_input(sample_jailbreak_texts["dan_mode"])
        # Should be blocked before all rules are checked
        assert result.passed is False
        # Number of results should be <= number of rules
        assert len(result.all_results) <= len(guard_with_all_rules.rules)


class TestCheckOutput:
    """Tests for check_output() method"""

    def test_check_output_passes_clean_text(self, simple_guard):
        """Should pass clean output text"""
        result = simple_guard.check_output("This is a helpful response")
        assert result.passed is True

    def test_check_output_blocks_pii_in_output(self, guard_with_pii, sample_pii_texts):
        """Should block PII in agent output"""
        result = guard_with_pii.check_output(sample_pii_texts["email"])
        assert result.passed is False
        assert result.blocked_by == "block_pii"

    def test_check_output_with_input_context(self, patch_engines):
        """Should pass input_text to rules that need it"""
        guard = StarvexGuard(
            rules=[PolicyCompliance(policies=["Refunds require manager approval"])],
            enable_tracing=False,
        )

        # This should detect a policy violation
        result = guard.check_output(
            output_text="I've processed your refund request.",
            input_text="Can I get a refund?",
        )
        assert result.passed is False
        assert result.blocked_by == "policy_compliance"


class TestProtectDecorator:
    """Tests for @guard.protect decorator"""

    def test_protect_sync_function(self, simple_guard):
        """Should protect a synchronous function"""

        @simple_guard.protect
        def my_agent(message: str) -> str:
            return f"Response to: {message}"

        result = my_agent("Hello")
        assert result == "Response to: Hello"

    def test_protect_sync_blocks_input(self, guard_with_jailbreak, sample_jailbreak_texts):
        """Should block dangerous input in sync function"""

        @guard_with_jailbreak.protect
        def my_agent(message: str) -> str:
            return f"Response to: {message}"

        result = my_agent(sample_jailbreak_texts["ignore_instructions"])
        assert "cannot process" in result.lower()

    def test_protect_sync_blocks_output(self, guard_with_pii, sample_pii_texts):
        """Should block dangerous output in sync function"""

        @guard_with_pii.protect
        def my_agent(message: str) -> str:
            # Agent accidentally returns PII
            return sample_pii_texts["email"]

        result = my_agent("What's your email?")
        assert "cannot process" in result.lower() or "personal information" in result.lower()

    @pytest.mark.asyncio
    async def test_protect_async_function(self, simple_guard):
        """Should protect an async function"""

        @simple_guard.protect
        async def my_agent(message: str) -> str:
            await asyncio.sleep(0.01)
            return f"Response to: {message}"

        result = await my_agent("Hello")
        assert result == "Response to: Hello"

    @pytest.mark.asyncio
    async def test_protect_async_blocks_input(self, guard_with_jailbreak, sample_jailbreak_texts):
        """Should block dangerous input in async function"""

        @guard_with_jailbreak.protect
        async def my_agent(message: str) -> str:
            await asyncio.sleep(0.01)
            return f"Response to: {message}"

        result = await my_agent(sample_jailbreak_texts["developer_mode"])
        assert "cannot process" in result.lower()

    def test_protect_with_options(self, guard_with_pii, sample_pii_texts):
        """Should respect check_input and check_output options"""

        @guard_with_pii.protect(check_input=False, check_output=False)
        def my_agent(message: str) -> str:
            return sample_pii_texts["ssn"]  # Returns PII

        # Should not block since checks are disabled
        result = my_agent(sample_pii_texts["ssn"])
        assert sample_pii_texts["ssn"] in result

    def test_protect_with_redaction(self, patch_engines):
        """Should use redacted text in function call"""
        guard = StarvexGuard(
            rules=[BlockPII(redact_instead=True)],
            enable_tracing=False,
        )
        received_message = None

        @guard.protect
        def my_agent(message: str) -> str:
            nonlocal received_message
            received_message = message
            return "OK"

        my_agent("My SSN is 123-45-6789")
        assert "[REDACTED_SSN]" in received_message

    def test_protect_preserves_function_metadata(self, simple_guard):
        """Should preserve function name and docstring"""

        @simple_guard.protect
        def my_agent_function(message: str) -> str:
            """This is my agent docstring."""
            return message

        assert my_agent_function.__name__ == "my_agent_function"
        assert "This is my agent docstring" in my_agent_function.__doc__

    def test_protect_extracts_input_from_kwargs(self, guard_with_jailbreak, sample_jailbreak_texts):
        """Should extract input from common kwarg names"""

        @guard_with_jailbreak.protect
        def my_agent(prompt: str) -> str:
            return f"Response: {prompt}"

        result = my_agent(prompt=sample_jailbreak_texts["ignore_instructions"])
        assert "cannot process" in result.lower()

    def test_protect_custom_block_handler(self, patch_engines, sample_jailbreak_texts):
        """Should use custom on_block handler"""
        custom_message = "Custom blocked response"

        guard = StarvexGuard(
            rules=[BlockJailbreak()],
            on_block=lambda r: custom_message,
            enable_tracing=False,
        )

        @guard.protect
        def my_agent(message: str) -> str:
            return message

        result = my_agent(sample_jailbreak_texts["ignore_instructions"])
        assert result == custom_message


class TestRuleManagement:
    """Tests for rule management methods"""

    def test_add_rule(self, simple_guard, patch_engines):
        """Should add a new rule"""
        assert len(simple_guard.rules) == 0
        simple_guard.add_rule(BlockPII())
        assert len(simple_guard.rules) == 1

    def test_remove_rule(self, patch_engines):
        """Should remove a rule by name"""
        guard = StarvexGuard(rules=[BlockPII(), BlockJailbreak()], enable_tracing=False)
        assert len(guard.rules) == 2

        removed = guard.remove_rule("block_pii")
        assert removed is True
        assert len(guard.rules) == 1
        assert guard.rules[0].name == "block_jailbreak"

    def test_remove_nonexistent_rule(self, simple_guard):
        """Should return False when removing non-existent rule"""
        removed = simple_guard.remove_rule("nonexistent_rule")
        assert removed is False

    def test_get_rules(self, patch_engines):
        """Should return list of rule names"""
        guard = StarvexGuard(
            rules=[BlockPII(), BlockJailbreak(), BlockToxicity()],
            enable_tracing=False,
        )
        names = guard.get_rules()
        assert names == ["block_pii", "block_jailbreak", "block_toxicity"]


class TestContextManager:
    """Tests for context manager support"""

    def test_sync_context_manager(self, simple_guard, mock_tracer):
        """Should work as sync context manager"""
        simple_guard._tracer = mock_tracer

        with simple_guard as guard:
            assert guard is simple_guard

        mock_tracer.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, simple_guard, mock_tracer):
        """Should work as async context manager"""
        simple_guard._tracer = mock_tracer

        async with simple_guard as guard:
            assert guard is simple_guard

        mock_tracer.flush.assert_called_once()


class TestDefaultBlockHandler:
    """Tests for default block handler messages"""

    def test_default_block_message_pii(self, patch_engines):
        """Should return appropriate message for PII block"""
        guard = StarvexGuard(rules=[], enable_tracing=False)
        result = CheckResult(passed=False, blocked_by="block_pii")
        message = guard._default_block_handler(result)
        assert "personal information" in message.lower()

    def test_default_block_message_jailbreak(self, patch_engines):
        """Should return appropriate message for jailbreak block"""
        guard = StarvexGuard(rules=[], enable_tracing=False)
        result = CheckResult(passed=False, blocked_by="block_jailbreak")
        message = guard._default_block_handler(result)
        assert "cannot process" in message.lower()

    def test_default_block_message_topic(self, patch_engines):
        """Should return appropriate message for topic restriction"""
        guard = StarvexGuard(rules=[], enable_tracing=False)
        result = CheckResult(passed=False, blocked_by="topic_restriction")
        message = guard._default_block_handler(result)
        assert "topic" in message.lower()

    def test_default_block_message_toxicity(self, patch_engines):
        """Should return appropriate message for toxicity block"""
        guard = StarvexGuard(rules=[], enable_tracing=False)
        result = CheckResult(passed=False, blocked_by="block_toxicity")
        message = guard._default_block_handler(result)
        assert "inappropriate" in message.lower()

    def test_default_block_message_unknown(self, patch_engines):
        """Should return generic message for unknown block type"""
        guard = StarvexGuard(rules=[], enable_tracing=False)
        result = CheckResult(passed=False, blocked_by="unknown_rule")
        message = guard._default_block_handler(result)
        assert "safety policies" in message.lower()


class TestGuardAlias:
    """Tests for Guard alias"""

    def test_guard_alias_exists(self):
        """Guard should be an alias for StarvexGuard"""
        from starvex.guard import Guard

        assert Guard is StarvexGuard


class TestCheckResultDataclass:
    """Tests for CheckResult dataclass"""

    def test_check_result_defaults(self):
        """Should have correct default values"""
        result = CheckResult(passed=True)
        assert result.passed is True
        assert result.blocked_by is None
        assert result.action is None
        assert result.message == ""
        assert result.confidence == 1.0
        assert result.all_results == []
        assert result.redacted_text is None
        assert result.latency_ms == 0.0
        assert result.trace_id  # Should have a UUID

    def test_check_result_with_values(self):
        """Should accept all values"""
        result = CheckResult(
            passed=False,
            blocked_by="test_rule",
            action=RuleAction.BLOCK,
            message="Test message",
            confidence=0.95,
            latency_ms=15.5,
        )
        assert result.passed is False
        assert result.blocked_by == "test_rule"
        assert result.action == RuleAction.BLOCK
        assert result.message == "Test message"
        assert result.confidence == 0.95
        assert result.latency_ms == 15.5
