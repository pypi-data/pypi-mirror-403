"""
Starvex Internal Tracer - Logs events to Supabase with retry logic
"""

import logging
import threading
import queue
import time
from typing import Optional, Dict, Any

import httpx

from ..models import GuardVerdict

logger = logging.getLogger(__name__)


class InternalTracer:
    """Internal tracer that logs events to Starvex API (Supabase Edge Functions)"""

    def __init__(
        self,
        api_key: str,
        host: str = "https://decqadhkqnacujoyirkh.supabase.co/functions/v1",
        enabled: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        batch_size: int = 10,
        flush_interval: float = 5.0,
    ):
        self.api_key = api_key
        self.host = host
        self.enabled = enabled
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        self._queue: queue.Queue = queue.Queue()
        self._failed_events: list = []
        self._shutdown = threading.Event()
        self._lock = threading.Lock()
        self._stats = {
            "events_queued": 0,
            "events_sent": 0,
            "events_failed": 0,
            "retries": 0,
        }

        if self.enabled and self.api_key:
            self._worker = threading.Thread(target=self._process_queue, daemon=True)
            self._worker.start()
            logger.debug("Starvex tracer initialized with retry logic")

    def log_event(
        self,
        trace_id: str,
        input_text: str,
        output_text: Optional[str],
        verdict: GuardVerdict,
        confidence_score: float,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        latency_ms: float = 0,
        checks: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Queue an event for logging"""
        if not self.enabled or not self.api_key:
            return

        event = {
            "trace_id": trace_id,
            "input_text": input_text,
            "output_text": output_text,
            "verdict": verdict.value if isinstance(verdict, GuardVerdict) else verdict,
            "status": self._get_status_from_verdict(verdict),
            "confidence_score": confidence_score,
            "user_id_external": user_id,
            "session_id": session_id,
            "latency_ms": latency_ms,
            "checks": [c.model_dump() if hasattr(c, "model_dump") else c for c in (checks or [])],
            "metadata": metadata or {},
        }

        self._queue.put(event)
        with self._lock:
            self._stats["events_queued"] += 1
        logger.debug(f"Event queued: {trace_id}")

    def _get_status_from_verdict(self, verdict: GuardVerdict) -> str:
        """Convert verdict to status"""
        if isinstance(verdict, str):
            verdict_str = verdict
        else:
            verdict_str = verdict.value

        if verdict_str == "PASSED":
            return "success"
        elif verdict_str.startswith("BLOCKED"):
            return "blocked"
        elif verdict_str.startswith("FAILED"):
            return "flagged"
        return "success"

    def _process_queue(self):
        """Background worker to process event queue with batching"""
        batch: list = []
        last_flush = time.time()

        while not self._shutdown.is_set():
            try:
                # Try to get an event with timeout
                try:
                    event = self._queue.get(timeout=0.5)
                    batch.append(event)
                except queue.Empty:
                    pass

                # Check if we should flush
                should_flush = len(batch) >= self.batch_size or (
                    batch and time.time() - last_flush >= self.flush_interval
                )

                if should_flush and batch:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()

            except Exception as e:
                logger.error(f"Error processing event queue: {e}")

        # Flush remaining events on shutdown
        if batch:
            self._send_batch(batch)

    def _send_batch(self, batch: list):
        """Send a batch of events (currently sends one by one, can be optimized)"""
        for event in batch:
            self._send_event_with_retry(event)

    def _send_event_with_retry(self, event: Dict[str, Any]) -> bool:
        """Send event with exponential backoff retry"""
        for attempt in range(self.max_retries):
            try:
                success = self._send_event(event)
                if success:
                    with self._lock:
                        self._stats["events_sent"] += 1
                    return True

                # Retry on failure
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.debug(
                        f"Retrying event {event['trace_id']} in {delay}s (attempt {attempt + 1})"
                    )
                    with self._lock:
                        self._stats["retries"] += 1
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"Error sending event (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    time.sleep(delay)

        # All retries failed
        with self._lock:
            self._stats["events_failed"] += 1
            self._failed_events.append(event)

        logger.warning(
            f"Failed to send event after {self.max_retries} attempts: {event['trace_id']}"
        )
        return False

    def _send_event(self, event: Dict[str, Any]) -> bool:
        """Send event to Starvex API"""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.host}/log-event",
                    json=event,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                    },
                )

                if response.status_code == 200:
                    logger.debug(f"Event logged: {event['trace_id']}")
                    return True
                elif response.status_code == 429:
                    # Rate limited - should retry
                    logger.warning(f"Rate limited when logging event: {event['trace_id']}")
                    return False
                elif response.status_code >= 500:
                    # Server error - should retry
                    logger.warning(
                        f"Server error {response.status_code} logging event: {event['trace_id']}"
                    )
                    return False
                else:
                    # Client error - don't retry
                    logger.warning(f"Failed to log event: {response.status_code} - {response.text}")
                    return True  # Return True to avoid retrying client errors

        except httpx.TimeoutException:
            logger.warning(f"Timeout sending event: {event['trace_id']}")
            return False
        except httpx.ConnectError:
            logger.warning(f"Connection error sending event: {event['trace_id']}")
            return False
        except Exception as e:
            logger.error(f"Error sending event: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Get tracer statistics"""
        with self._lock:
            return self._stats.copy()

    def get_failed_events(self) -> list:
        """Get list of failed events for manual retry"""
        with self._lock:
            return self._failed_events.copy()

    def retry_failed_events(self):
        """Retry sending failed events"""
        with self._lock:
            events_to_retry = self._failed_events.copy()
            self._failed_events = []

        for event in events_to_retry:
            self._queue.put(event)
            logger.debug(f"Re-queued failed event: {event['trace_id']}")

    def flush(self):
        """Flush pending events"""
        # Wait for queue to empty
        timeout = 10.0
        start = time.time()

        while not self._queue.empty() and time.time() - start < timeout:
            time.sleep(0.1)

        if not self._queue.empty():
            logger.warning(f"Flush timeout: {self._queue.qsize()} events remaining")

    def shutdown(self):
        """Shutdown the tracer gracefully"""
        self._shutdown.set()
        self.flush()

        stats = self.get_stats()
        logger.debug(
            f"Starvex tracer shutdown - "
            f"Sent: {stats['events_sent']}, "
            f"Failed: {stats['events_failed']}, "
            f"Retries: {stats['retries']}"
        )
