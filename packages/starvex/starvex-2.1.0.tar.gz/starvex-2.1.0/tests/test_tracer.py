"""
Tests for InternalTracer

Tests the internal tracer including:
- Initialization with different configurations
- Event logging
- Queue processing with batching
- Retry logic with exponential backoff
- Stats tracking
- Graceful shutdown
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import queue

from starvex._internals.tracer import InternalTracer, SDK_VERSION, DEFAULT_API_HOST
from starvex.models import GuardVerdict


class TestTracerInit:
    """Tests for InternalTracer initialization"""

    def test_init_with_defaults(self):
        """Should initialize with default values"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        assert tracer.api_key == "sv_live_test123"
        assert tracer.host == DEFAULT_API_HOST
        assert tracer.enabled is True
        assert tracer.max_retries == 3
        assert tracer.retry_delay == 1.0
        assert tracer.batch_size == 10
        assert tracer.flush_interval == 5.0

    def test_init_with_custom_host(self):
        """Should accept custom host"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(
                api_key="sv_live_test123",
                host="https://custom-api.example.com",
            )

        assert tracer.host == "https://custom-api.example.com"

    def test_init_with_custom_options(self):
        """Should accept all configuration options"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(
                api_key="sv_live_test123",
                enabled=True,
                max_retries=5,
                retry_delay=2.0,
                batch_size=20,
                flush_interval=10.0,
            )

        assert tracer.max_retries == 5
        assert tracer.retry_delay == 2.0
        assert tracer.batch_size == 20
        assert tracer.flush_interval == 10.0

    def test_init_disabled(self):
        """Should not start worker when disabled"""
        tracer = InternalTracer(
            api_key="sv_live_test123",
            enabled=False,
        )

        assert tracer.enabled is False

    def test_init_without_api_key(self):
        """Should handle missing API key gracefully"""
        tracer = InternalTracer(api_key="", enabled=True)
        # Should not crash, just not send events

    def test_init_stats(self):
        """Should initialize stats counters"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        stats = tracer.get_stats()
        assert stats["events_queued"] == 0
        assert stats["events_sent"] == 0
        assert stats["events_failed"] == 0
        assert stats["retries"] == 0


class TestLogEvent:
    """Tests for log_event() method"""

    def test_log_event_queues_event(self):
        """Should add event to queue"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        tracer.log_event(
            trace_id="test-trace-id",
            input_text="Hello",
            output_text="Hi there",
            verdict=GuardVerdict.PASSED,
            confidence_score=1.0,
        )

        assert not tracer._queue.empty()
        stats = tracer.get_stats()
        assert stats["events_queued"] == 1

    def test_log_event_when_disabled(self):
        """Should not queue events when disabled"""
        tracer = InternalTracer(api_key="sv_live_test123", enabled=False)

        tracer.log_event(
            trace_id="test-trace-id",
            input_text="Hello",
            output_text="Hi there",
            verdict=GuardVerdict.PASSED,
            confidence_score=1.0,
        )

        assert tracer._queue.empty()

    def test_log_event_without_api_key(self):
        """Should not queue events without API key"""
        tracer = InternalTracer(api_key="", enabled=True)

        tracer.log_event(
            trace_id="test-trace-id",
            input_text="Hello",
            output_text="Hi there",
            verdict=GuardVerdict.PASSED,
            confidence_score=1.0,
        )

        assert tracer._queue.empty()

    def test_log_event_with_all_fields(self):
        """Should accept all event fields"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        tracer.log_event(
            trace_id="test-trace-id",
            input_text="Hello",
            output_text="Hi there",
            verdict=GuardVerdict.BLOCKED_PII,
            confidence_score=0.95,
            user_id="user-123",
            session_id="session-456",
            latency_ms=150.5,
            checks=[{"name": "pii", "passed": False}],
            metadata={"custom": "data"},
            input_tokens=10,
            output_tokens=20,
            model_name="gpt-4",
            blocked_reason="pii_detected",
            blocked_content="SSN",
            rules_triggered=[{"name": "block_pii", "score": 0.95}],
            environment="production",
            processing_time_ms=100.0,
            guardrail_latency_ms=50.0,
            agent_latency_ms=50.0,
        )

        event = tracer._queue.get()

        assert event["trace_id"] == "test-trace-id"
        assert event["input_text"] == "Hello"
        assert event["output_text"] == "Hi there"
        assert event["verdict"] == "BLOCKED_PII"
        assert event["confidence_score"] == 0.95
        assert event["user_id_external"] == "user-123"
        assert event["session_id"] == "session-456"
        assert event["latency_ms"] == 150.5
        assert event["input_tokens"] == 10
        assert event["output_tokens"] == 20
        assert event["total_tokens"] == 30
        assert event["model_name"] == "gpt-4"
        assert event["blocked_reason"] == "pii_detected"
        assert event["environment"] == "production"
        assert event["sdk_version"] == SDK_VERSION

    def test_log_event_infers_environment_from_key(self):
        """Should infer environment from API key prefix"""
        with patch.object(InternalTracer, "_process_queue"):
            test_tracer = InternalTracer(api_key="sv_test_123")
            live_tracer = InternalTracer(api_key="sv_live_456")

        test_tracer.log_event(
            trace_id="test-1",
            input_text="Hello",
            output_text=None,
            verdict=GuardVerdict.PASSED,
            confidence_score=1.0,
        )

        live_tracer.log_event(
            trace_id="test-2",
            input_text="Hello",
            output_text=None,
            verdict=GuardVerdict.PASSED,
            confidence_score=1.0,
        )

        test_event = test_tracer._queue.get()
        live_event = live_tracer._queue.get()

        assert test_event["environment"] == "test"
        assert live_event["environment"] == "production"

    def test_log_event_extracts_blocked_reason(self):
        """Should extract blocked reason from verdict"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        tracer.log_event(
            trace_id="test-1",
            input_text="Hello",
            output_text=None,
            verdict=GuardVerdict.BLOCKED_JAILBREAK,
            confidence_score=0.9,
        )

        event = tracer._queue.get()
        assert event["blocked_reason"] == "jailbreak"


class TestGetStatusFromVerdict:
    """Tests for _get_status_from_verdict() method"""

    def test_passed_verdict(self):
        """PASSED verdict should return 'success'"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        status = tracer._get_status_from_verdict(GuardVerdict.PASSED)
        assert status == "success"

    def test_blocked_verdicts(self):
        """BLOCKED_* verdicts should return 'blocked'"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        blocked_verdicts = [
            GuardVerdict.BLOCKED_JAILBREAK,
            GuardVerdict.BLOCKED_PII,
            GuardVerdict.BLOCKED_TOXICITY,
            GuardVerdict.BLOCKED_COMPETITOR,
            GuardVerdict.BLOCKED_CUSTOM,
        ]

        for verdict in blocked_verdicts:
            status = tracer._get_status_from_verdict(verdict)
            assert status == "blocked", f"Expected 'blocked' for {verdict}"

    def test_failed_verdicts(self):
        """FAILED_* verdicts should return 'flagged'"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        failed_verdicts = [
            GuardVerdict.FAILED_HALLUCINATION,
            GuardVerdict.FAILED_SYSTEM,
        ]

        for verdict in failed_verdicts:
            status = tracer._get_status_from_verdict(verdict)
            assert status == "flagged", f"Expected 'flagged' for {verdict}"

    def test_string_verdict(self):
        """Should handle string verdicts"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        assert tracer._get_status_from_verdict("PASSED") == "success"
        assert tracer._get_status_from_verdict("BLOCKED_PII") == "blocked"
        assert tracer._get_status_from_verdict("FAILED_SYSTEM") == "flagged"


class TestSendEvent:
    """Tests for _send_event() method"""

    def test_send_event_success(self):
        """Should return True on successful send"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        mock_response = Mock()
        mock_response.status_code = 200

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = Mock(return_value=mock_client.return_value)
            mock_client.return_value.__exit__ = Mock(return_value=False)
            mock_client.return_value.post.return_value = mock_response

            result = tracer._send_event({"trace_id": "test", "input_text": "Hello"})

        assert result is True

    def test_send_event_auth_error(self):
        """Should return True on auth error (don't retry)"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = Mock(return_value=mock_client.return_value)
            mock_client.return_value.__exit__ = Mock(return_value=False)
            mock_client.return_value.post.return_value = mock_response

            result = tracer._send_event({"trace_id": "test", "input_text": "Hello"})

        # Returns True to avoid retrying auth errors
        assert result is True

    def test_send_event_rate_limited(self):
        """Should return False on rate limit (should retry)"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        mock_response = Mock()
        mock_response.status_code = 429

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = Mock(return_value=mock_client.return_value)
            mock_client.return_value.__exit__ = Mock(return_value=False)
            mock_client.return_value.post.return_value = mock_response

            result = tracer._send_event({"trace_id": "test", "input_text": "Hello"})

        assert result is False

    def test_send_event_server_error(self):
        """Should return False on server error (should retry)"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        mock_response = Mock()
        mock_response.status_code = 500

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = Mock(return_value=mock_client.return_value)
            mock_client.return_value.__exit__ = Mock(return_value=False)
            mock_client.return_value.post.return_value = mock_response

            result = tracer._send_event({"trace_id": "test", "input_text": "Hello"})

        assert result is False

    def test_send_event_timeout(self):
        """Should return False on timeout (should retry)"""
        import httpx

        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = Mock(return_value=mock_client.return_value)
            mock_client.return_value.__exit__ = Mock(return_value=False)
            mock_client.return_value.post.side_effect = httpx.TimeoutException("Timeout")

            result = tracer._send_event({"trace_id": "test", "input_text": "Hello"})

        assert result is False

    def test_send_event_connection_error(self):
        """Should return False on connection error (should retry)"""
        import httpx

        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__ = Mock(return_value=mock_client.return_value)
            mock_client.return_value.__exit__ = Mock(return_value=False)
            mock_client.return_value.post.side_effect = httpx.ConnectError("Connection failed")

            result = tracer._send_event({"trace_id": "test", "input_text": "Hello"})

        assert result is False


class TestSendEventWithRetry:
    """Tests for _send_event_with_retry() method"""

    def test_retry_on_failure(self):
        """Should retry on failure with exponential backoff"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(
                api_key="sv_live_test123",
                max_retries=3,
                retry_delay=0.01,  # Short delay for testing
            )

        call_count = 0

        def mock_send(event):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return False  # Fail first two attempts
            return True  # Succeed on third

        with patch.object(tracer, "_send_event", side_effect=mock_send):
            result = tracer._send_event_with_retry({"trace_id": "test"})

        assert result is True
        assert call_count == 3
        stats = tracer.get_stats()
        assert stats["retries"] == 2  # Two retries before success

    def test_max_retries_exceeded(self):
        """Should track failed events after max retries"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(
                api_key="sv_live_test123",
                max_retries=2,
                retry_delay=0.01,
            )

        with patch.object(tracer, "_send_event", return_value=False):
            result = tracer._send_event_with_retry({"trace_id": "test"})

        assert result is False
        stats = tracer.get_stats()
        assert stats["events_failed"] == 1

        # Failed event should be stored for manual retry
        failed = tracer.get_failed_events()
        assert len(failed) == 1
        assert failed[0]["trace_id"] == "test"


class TestStatsAndFailedEvents:
    """Tests for stats and failed events tracking"""

    def test_get_stats_thread_safe(self):
        """get_stats() should return a copy, not the actual dict"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        stats = tracer.get_stats()
        stats["events_queued"] = 999

        # Original should be unchanged
        original_stats = tracer.get_stats()
        assert original_stats["events_queued"] == 0

    def test_get_failed_events_thread_safe(self):
        """get_failed_events() should return a copy"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        tracer._failed_events.append({"trace_id": "test"})

        failed = tracer.get_failed_events()
        failed.clear()

        # Original should be unchanged
        original_failed = tracer.get_failed_events()
        assert len(original_failed) == 1

    def test_retry_failed_events(self):
        """retry_failed_events() should re-queue failed events"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        # Add some failed events
        tracer._failed_events = [
            {"trace_id": "failed-1"},
            {"trace_id": "failed-2"},
        ]

        tracer.retry_failed_events()

        # Failed events should be cleared
        assert len(tracer._failed_events) == 0

        # Events should be in queue
        assert tracer._queue.qsize() == 2


class TestFlushAndShutdown:
    """Tests for flush() and shutdown() methods"""

    def test_flush_waits_for_queue(self):
        """flush() should wait for queue to empty"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        # Start with empty queue
        tracer.flush()  # Should return immediately

    def test_shutdown_sets_event(self):
        """shutdown() should set shutdown event"""
        with patch.object(InternalTracer, "_process_queue"):
            tracer = InternalTracer(api_key="sv_live_test123")

        assert not tracer._shutdown.is_set()
        tracer.shutdown()
        assert tracer._shutdown.is_set()


class TestSDKVersion:
    """Tests for SDK version constant"""

    def test_sdk_version_is_set(self):
        """SDK_VERSION should be set"""
        assert SDK_VERSION is not None
        assert SDK_VERSION == "2.0.0"


class TestDefaultAPIHost:
    """Tests for default API host constant"""

    def test_default_host_is_set(self):
        """DEFAULT_API_HOST should be set"""
        assert DEFAULT_API_HOST is not None
        assert "supabase.co" in DEFAULT_API_HOST
