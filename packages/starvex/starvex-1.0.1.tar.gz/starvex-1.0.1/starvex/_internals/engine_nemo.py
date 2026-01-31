"""
Starvex NeMo Guardrails Engine
"""

import logging
import re
from typing import Tuple, List, Optional

from ..models import GuardCheckResult, GuardRuleType

logger = logging.getLogger(__name__)


# Jailbreak detection patterns
JAILBREAK_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)?\s*(instructions|prompts|rules)",
    r"forget\s+(everything|all)\s+(you\s+)?(know|learned)",
    r"you\s+are\s+now\s+(a|an)?\s*(evil|malicious|unrestricted)",
    r"pretend\s+(you\s+are|to\s+be|you\s+have)\s+(a|an|no)",
    r"act\s+as\s+(if\s+)?(you\s+are|a|an)",
    r"disregard\s+(your|the|all)\s+(rules|guidelines|instructions)",
    r"bypass\s+(your|the|safety|security)",
    r"jailbreak",
    r"DAN\s+mode",
    r"developer\s+mode",
    r"do\s+anything\s+now",
    r"no\s+(restrictions|rules|limits|limitations|guidelines)",
    r"without\s+(any\s+)?(restrictions|rules|limits)",
    r"override\s+(your|the|all)\s+(programming|training|rules)",
    r"system\s+prompt",
    r"reveal\s+(your|the)\s+(instructions|prompt|system)",
]

# Toxicity patterns
TOXICITY_PATTERNS = [
    r"\b(kill|murder|destroy|harm|hurt|attack)\b.*\b(you|them|people|someone)\b",
    r"\b(hate|despise)\b.*\b(you|them|people)\b",
    r"(die|death)\s+(to|for)",
    r"\b(stupid|idiot|dumb|moron|retard)\b",
]

# PII patterns
PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}


class NemoEngine:
    """NeMo Guardrails Engine for input/output safety checks"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._nemo_rails = None
        self._load_nemo()
        logger.debug("NemoEngine initialized")

    def _load_nemo(self):
        """Attempt to load NeMo Guardrails if available"""
        try:
            from nemoguardrails import RailsConfig, LLMRails

            if self.config_path:
                config = RailsConfig.from_path(self.config_path)
                self._nemo_rails = LLMRails(config)
                logger.info("NeMo Guardrails loaded successfully")
        except ImportError:
            logger.debug("NeMo Guardrails not installed, using pattern-based detection")
        except Exception as e:
            logger.warning(f"Failed to load NeMo Guardrails: {e}")

    async def check_input(
        self,
        text: str,
        check_jailbreak: bool = True,
        check_pii: bool = True,
        check_toxicity: bool = True,
    ) -> Tuple[bool, str, List[GuardCheckResult]]:
        """
        Check input text for safety issues.
        Returns (is_safe, block_message, checks)
        """
        checks: List[GuardCheckResult] = []
        is_safe = True
        block_message = ""

        # Jailbreak check
        if check_jailbreak:
            jailbreak_result = self._check_jailbreak(text)
            checks.append(jailbreak_result)
            if not jailbreak_result.passed:
                is_safe = False
                block_message = "Request blocked: Jailbreak attempt detected."

        # PII check
        if check_pii and is_safe:
            pii_result = self._check_pii(text)
            checks.append(pii_result)
            if not pii_result.passed:
                is_safe = False
                block_message = "Request blocked: PII detected in input."

        # Toxicity check
        if check_toxicity and is_safe:
            toxicity_result = self._check_toxicity(text)
            checks.append(toxicity_result)
            if not toxicity_result.passed:
                is_safe = False
                block_message = "Request blocked: Toxic content detected."

        if is_safe:
            block_message = "Input passed all safety checks."

        return is_safe, block_message, checks

    async def check_output(
        self,
        input_text: str,
        output_text: str,
        check_pii: bool = True,
        check_toxicity: bool = True,
    ) -> Tuple[bool, str, List[GuardCheckResult]]:
        """
        Check output text for safety issues.
        Returns (is_safe, block_message, checks)
        """
        checks: List[GuardCheckResult] = []
        is_safe = True
        block_message = ""

        # PII check
        if check_pii:
            pii_result = self._check_pii(output_text)
            checks.append(pii_result)
            if not pii_result.passed:
                is_safe = False
                block_message = "Response blocked: Contains PII."

        # Toxicity check
        if check_toxicity and is_safe:
            toxicity_result = self._check_toxicity(output_text)
            checks.append(toxicity_result)
            if not toxicity_result.passed:
                is_safe = False
                block_message = "Response blocked: Contains toxic content."

        if is_safe:
            block_message = output_text

        return is_safe, block_message, checks

    def _check_jailbreak(self, text: str) -> GuardCheckResult:
        """Check for jailbreak attempts"""
        text_lower = text.lower()
        confidence = 0.0
        matched_patterns = []

        for pattern in JAILBREAK_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matched_patterns.append(pattern)
                confidence = max(confidence, 0.9)

        passed = len(matched_patterns) == 0

        return GuardCheckResult(
            rule_type=GuardRuleType.JAILBREAK,
            passed=passed,
            confidence=confidence if not passed else 0.0,
            message=f"Jailbreak patterns matched: {len(matched_patterns)}"
            if not passed
            else "No jailbreak detected",
            details={"matched_patterns": len(matched_patterns)} if not passed else None,
        )

    def _check_pii(self, text: str) -> GuardCheckResult:
        """Check for PII in text"""
        found_pii = {}
        confidence = 0.0

        for pii_type, pattern in PII_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_pii[pii_type] = len(matches)
                confidence = 0.95

        passed = len(found_pii) == 0

        return GuardCheckResult(
            rule_type=GuardRuleType.PII,
            passed=passed,
            confidence=confidence if not passed else 0.0,
            message=f"PII detected: {list(found_pii.keys())}" if not passed else "No PII detected",
            details=found_pii if not passed else None,
        )

    def _check_toxicity(self, text: str) -> GuardCheckResult:
        """Check for toxic content"""
        text_lower = text.lower()
        matched = 0
        confidence = 0.0

        for pattern in TOXICITY_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matched += 1
                confidence = max(confidence, 0.8)

        passed = matched == 0

        return GuardCheckResult(
            rule_type=GuardRuleType.TOXICITY,
            passed=passed,
            confidence=confidence if not passed else 0.0,
            message=f"Toxicity patterns matched: {matched}"
            if not passed
            else "No toxicity detected",
            details={"matched_count": matched} if not passed else None,
        )
