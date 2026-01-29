"""
Intent detection for automatic flow triggering.

Analyzes user input to detect feature requests and other work types,
automatically suggesting or triggering the appropriate flow.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class WorkIntent(Enum):
    """Types of work intents that can be detected."""

    FEATURE = "feature"  # New feature request
    BUG_FIX = "bug_fix"  # Bug fix or error resolution
    REFACTOR = "refactor"  # Code refactoring
    DOCUMENTATION = "documentation"  # Documentation changes
    TESTING = "testing"  # Adding or updating tests
    REVIEW = "review"  # Code review
    QUESTION = "question"  # Question about code/project
    TRIVIAL = "trivial"  # Trivial change (typo, small tweak)
    UNKNOWN = "unknown"  # Cannot determine intent


@dataclass
class IntentMatch:
    """A detected intent with confidence and details."""

    intent: WorkIntent
    confidence: float  # 0.0 to 1.0
    triggers: List[str]  # Matched trigger phrases
    suggested_flow: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    extracted_info: Dict[str, Any] = field(default_factory=dict)

    def is_planning_required(self) -> bool:
        """Check if this intent requires planning mode."""
        return (
            self.intent == WorkIntent.FEATURE
            and self.confidence >= 0.7
        ) or (
            self.intent == WorkIntent.REFACTOR
            and self.confidence >= 0.8
        )


# Pattern definitions for intent detection
INTENT_PATTERNS: Dict[WorkIntent, List[Tuple[str, float]]] = {
    WorkIntent.FEATURE: [
        # High confidence patterns
        (r"\b(build|create|implement|add|develop)\s+(a|an|the|new)?\s*\w+", 0.9),
        (r"\b(i\s+want|we\s+need|let's\s+build|let's\s+create)", 0.9),
        (r"\bnew\s+feature\b", 0.95),
        (r"\badd\s+support\s+for\b", 0.9),
        (r"\bimplement\s+\w+\s+(feature|functionality|capability)", 0.95),

        # Medium confidence patterns
        (r"\b(want|need)\s+(to\s+)?(be\s+able\s+to|have)\b", 0.75),
        (r"\bshould\s+(be\s+able\s+to|have|support)\b", 0.7),
        (r"\bintegrate\s+(with\s+)?\w+", 0.75),
        (r"\badd\s+\w+\s+(to|for|into)\b", 0.7),

        # Lower confidence patterns
        (r"\b(feature|functionality|capability)\b", 0.5),
        (r"\bmake\s+it\s+(possible|easier|able)\b", 0.6),
    ],

    WorkIntent.BUG_FIX: [
        # High confidence patterns
        (r"\b(fix|repair|resolve|debug)\s+(the\s+)?(bug|error|issue|problem)", 0.95),
        (r"\b(doesn't|does\s+not|isn't|is\s+not)\s+work(ing)?\b", 0.85),
        (r"\b(broken|fails|failing|crashed|crashing)\b", 0.9),
        (r"\berror\s+(message|code)?:?\s*", 0.85),
        (r"\bexception\s*:?\s*\w+Error", 0.9),

        # Medium confidence patterns
        (r"\b(wrong|incorrect|unexpected)\s+(behavior|output|result)", 0.8),
        (r"\b(not\s+)?working\s+(as\s+expected|correctly|properly)\b", 0.75),
        (r"\bregression\b", 0.85),
    ],

    WorkIntent.REFACTOR: [
        # High confidence patterns
        (r"\brefactor\b", 0.95),
        (r"\brestructure\b", 0.9),
        (r"\breorganize\b", 0.85),
        (r"\bclean\s*up\b", 0.8),
        (r"\bimprove\s+(the\s+)?(code|architecture|structure)", 0.85),

        # Medium confidence patterns
        (r"\bmove\s+\w+\s+(to|into|from)\b", 0.7),
        (r"\brename\s+\w+\b", 0.65),
        (r"\bsplit\s+\w+\s+(into|up)\b", 0.75),
        (r"\bextract\s+\w+\b", 0.75),
    ],

    WorkIntent.DOCUMENTATION: [
        (r"\b(document|documentation|docs|readme)\b", 0.9),
        (r"\bwrite\s+(up|about)\b", 0.7),
        (r"\bexplain\s+(how|what|why)\b", 0.6),
        (r"\badd\s+comments?\b", 0.8),
        (r"\bupdate\s+(the\s+)?(docs|documentation|readme)\b", 0.9),
    ],

    WorkIntent.TESTING: [
        (r"\b(write|add|create)\s+(unit\s+)?tests?\b", 0.9),
        (r"\btest\s+(coverage|case|suite)\b", 0.85),
        (r"\b(increase|improve)\s+test\s+coverage\b", 0.9),
        (r"\bverify\b", 0.5),
    ],

    WorkIntent.REVIEW: [
        (r"\breview\b", 0.9),
        (r"\bcheck\s+(the\s+)?(code|changes|pr)\b", 0.85),
        (r"\blook\s+(at|over)\b", 0.7),
        (r"\bfeedback\b", 0.65),
    ],

    WorkIntent.QUESTION: [
        (r"\b(what|how|why|where|when|which)\s+(is|are|do|does|can|should)\b", 0.9),
        (r"\bcan\s+you\s+explain\b", 0.95),
        (r"\bwhat's\s+the\b", 0.85),
        (r"\bhow\s+does\s+\w+\s+work\b", 0.9),
        (r"\?\s*$", 0.6),  # Ends with question mark
    ],

    WorkIntent.TRIVIAL: [
        (r"\b(typo|spelling|grammar)\b", 0.9),
        (r"\bsimple\s+(change|fix|update)\b", 0.75),
        (r"\bquick\s+(fix|change)\b", 0.8),
        (r"\bminor\b", 0.6),
        (r"\bjust\s+(change|update|fix)\b", 0.7),
    ],
}

# Flow suggestions based on intent
FLOW_SUGGESTIONS: Dict[WorkIntent, str] = {
    WorkIntent.FEATURE: "design-plan-implement",
    WorkIntent.BUG_FIX: "tdd-implement",
    WorkIntent.REFACTOR: "design-plan-implement",
    WorkIntent.REVIEW: "review",
    WorkIntent.TESTING: "tdd-implement",
}


class IntentDetector:
    """Detects work intent from user input."""

    def __init__(
        self,
        custom_patterns: Optional[Dict[WorkIntent, List[Tuple[str, float]]]] = None,
        confidence_threshold: float = 0.6,
    ):
        """Initialize intent detector.

        Args:
            custom_patterns: Additional patterns to include
            confidence_threshold: Minimum confidence for detection
        """
        self.patterns = dict(INTENT_PATTERNS)
        if custom_patterns:
            for intent, patterns in custom_patterns.items():
                if intent in self.patterns:
                    self.patterns[intent].extend(patterns)
                else:
                    self.patterns[intent] = patterns

        self.confidence_threshold = confidence_threshold

    def detect(self, text: str) -> IntentMatch:
        """Detect the primary intent from text.

        Args:
            text: User input text

        Returns:
            IntentMatch with detected intent and confidence
        """
        matches = self.detect_all(text)
        if matches:
            return matches[0]

        return IntentMatch(
            intent=WorkIntent.UNKNOWN,
            confidence=0.0,
            triggers=[],
            reasons=["No patterns matched"],
        )

    def detect_all(self, text: str) -> List[IntentMatch]:
        """Detect all possible intents from text.

        Args:
            text: User input text

        Returns:
            List of IntentMatch sorted by confidence (highest first)
        """
        text_lower = text.lower()
        matches: List[IntentMatch] = []

        for intent, patterns in self.patterns.items():
            triggers = []
            max_confidence = 0.0
            reasons = []

            for pattern, base_confidence in patterns:
                regex_matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if regex_matches:
                    # Boost confidence for multiple matches
                    confidence = min(base_confidence + 0.05 * (len(regex_matches) - 1), 1.0)

                    if confidence > max_confidence:
                        max_confidence = confidence

                    triggers.extend(
                        m if isinstance(m, str) else " ".join(m)
                        for m in regex_matches
                    )
                    reasons.append(f"Matched: {pattern[:50]}...")

            if max_confidence >= self.confidence_threshold:
                matches.append(IntentMatch(
                    intent=intent,
                    confidence=max_confidence,
                    triggers=triggers[:5],  # Limit triggers
                    suggested_flow=FLOW_SUGGESTIONS.get(intent),
                    reasons=reasons[:3],
                    extracted_info=self._extract_info(text, intent),
                ))

        # Sort by confidence
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def _extract_info(self, text: str, intent: WorkIntent) -> Dict[str, Any]:
        """Extract additional information based on intent.

        Args:
            text: User input text
            intent: Detected intent

        Returns:
            Dict of extracted information
        """
        info: Dict[str, Any] = {}

        # Extract potential feature/component names
        if intent == WorkIntent.FEATURE:
            # Look for quoted strings
            quoted = re.findall(r'"([^"]+)"', text)
            if quoted:
                info["quoted_items"] = quoted

            # Look for "called X" or "named X" patterns
            named = re.search(r'(?:called|named)\s+["\']?(\w+)["\']?', text, re.IGNORECASE)
            if named:
                info["name"] = named.group(1)

        # Extract error messages for bug fixes
        elif intent == WorkIntent.BUG_FIX:
            errors = re.findall(r'\b(\w+Error|\w+Exception)\b', text)
            if errors:
                info["errors"] = errors

        # Extract file paths if mentioned
        files = re.findall(r'[\w/.-]+\.\w{1,4}', text)
        if files:
            info["mentioned_files"] = files

        return info

    def should_enter_planning_mode(self, text: str) -> Tuple[bool, Optional[IntentMatch]]:
        """Determine if planning mode should be entered.

        Args:
            text: User input text

        Returns:
            Tuple of (should_enter, intent_match)
        """
        match = self.detect(text)

        should_enter = (
            match.is_planning_required()
            or (
                match.intent in [WorkIntent.FEATURE, WorkIntent.REFACTOR]
                and match.confidence >= 0.7
                and len(text.split()) >= 10  # Substantial request
            )
        )

        return should_enter, match if should_enter else None

    def get_flow_suggestion(self, text: str) -> Optional[str]:
        """Get suggested flow for user input.

        Args:
            text: User input text

        Returns:
            Flow name or None
        """
        match = self.detect(text)
        return match.suggested_flow


class PlanningModeManager:
    """Manages automatic entry into planning mode."""

    def __init__(
        self,
        detector: Optional[IntentDetector] = None,
        auto_enter: bool = True,
    ):
        """Initialize planning mode manager.

        Args:
            detector: Intent detector instance
            auto_enter: Whether to automatically enter planning mode
        """
        self.detector = detector or IntentDetector()
        self.auto_enter = auto_enter
        self._in_planning_mode = False
        self._current_intent: Optional[IntentMatch] = None

    @property
    def in_planning_mode(self) -> bool:
        """Check if currently in planning mode."""
        return self._in_planning_mode

    @property
    def current_intent(self) -> Optional[IntentMatch]:
        """Get the current detected intent."""
        return self._current_intent

    def process_input(self, text: str) -> Dict[str, Any]:
        """Process user input and determine if planning mode should be entered.

        Args:
            text: User input text

        Returns:
            Dict with processing results
        """
        result: Dict[str, Any] = {
            "should_enter_planning": False,
            "suggested_flow": None,
            "intent": None,
            "confidence": 0.0,
            "message": None,
        }

        if not self.auto_enter:
            return result

        should_enter, match = self.detector.should_enter_planning_mode(text)

        if should_enter and match:
            self._in_planning_mode = True
            self._current_intent = match

            result["should_enter_planning"] = True
            result["suggested_flow"] = match.suggested_flow
            result["intent"] = match.intent.value
            result["confidence"] = match.confidence
            result["message"] = self._generate_planning_message(match)

        return result

    def _generate_planning_message(self, match: IntentMatch) -> str:
        """Generate a message about entering planning mode.

        Args:
            match: The detected intent match

        Returns:
            Message string
        """
        intent_descriptions = {
            WorkIntent.FEATURE: "a new feature request",
            WorkIntent.REFACTOR: "a refactoring task",
        }

        description = intent_descriptions.get(match.intent, "a substantial task")

        return (
            f"Detected {description} (confidence: {match.confidence:.0%}). "
            f"Entering planning mode with '{match.suggested_flow}' flow."
        )

    def exit_planning_mode(self):
        """Exit planning mode."""
        self._in_planning_mode = False
        self._current_intent = None

    def get_status(self) -> Dict[str, Any]:
        """Get current planning mode status.

        Returns:
            Status dict
        """
        return {
            "in_planning_mode": self._in_planning_mode,
            "auto_enter": self.auto_enter,
            "current_intent": self._current_intent.intent.value if self._current_intent else None,
            "suggested_flow": self._current_intent.suggested_flow if self._current_intent else None,
        }
