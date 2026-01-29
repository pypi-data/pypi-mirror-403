"""
GateResult schema for judgment detection output.

This defines the structured result returned by the judgment gate.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GateResult:
    """
    Result from judgment gate inspection.

    Fields:
        blocked: True if judgment detected and handoff required (NOT a policy decision)
        role: The detected judgment role (directive/recommendation/obligation) or None
        reason: Human-readable explanation of why this result was produced
        confidence: Informational confidence score (0.0-1.0). NOT for decision-making.
        matched_stem: The stem pattern that matched, if any
        scope_applied: List of scope rule IDs that were applied to this detection
    """
    blocked: bool
    role: Optional[str] = None
    reason: str = ""
    confidence: float = 0.0
    matched_stem: Optional[str] = None
    scope_applied: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence is in range [0, 1]."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

    def to_dict(self) -> dict:
        """
        Convert GateResult to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the result
        """
        return {
            "blocked": self.blocked,
            "role": self.role,
            "reason": self.reason,
            "confidence": self.confidence,
            "matched_stem": self.matched_stem,
            "scope_applied": self.scope_applied,
        }
