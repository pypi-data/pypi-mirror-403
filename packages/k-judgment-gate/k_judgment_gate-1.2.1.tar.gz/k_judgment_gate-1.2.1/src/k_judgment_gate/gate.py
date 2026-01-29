"""
Core judgment gate implementation.

This module implements the JudgmentGate that detects judgment attempts
and returns structured results. It does NOT make policy decisions.
"""

from typing import Optional
from .roles import JudgmentRole
from .schema import GateResult
from .scope import ScopeRule, validate_scope_rules, evaluate_scope_rules
from .stemmer import StemMatcher, normalize_text


class JudgmentGate:
    """
    Core judgment detection gate.

    This gate inspects text for judgment patterns (directive/recommendation/obligation)
    and returns a structured result indicating whether human oversight is required.

    IMPORTANT: blocked=True means "handoff required", NOT "policy block".
    """

    def __init__(
        self,
        role_stems: dict[str, list[str]],
        role_scopes: Optional[dict[str, list[ScopeRule]]] = None
    ):
        """
        Initialize judgment gate.

        Args:
            role_stems: Dict mapping role name to list of stem patterns
            role_scopes: Dict mapping role name to list of scope rules (max 2 per role)

        Raises:
            ValueError: If more than 2 scope rules provided for any role
        """
        self.role_stems = role_stems
        self.role_scopes = role_scopes or {}

        for role, rules in self.role_scopes.items():
            validate_scope_rules(rules, role)

        self.matchers = {
            role: StemMatcher(stems)
            for role, stems in role_stems.items()
        }

    def inspect(self, text: str) -> GateResult:
        """
        Inspect text for judgment patterns.

        Logic:
        1. Normalize text
        2. For each role, check if stem matches
        3. If stem matched, evaluate scope rules for that role
        4. If scope passes (or no scope rules exist), mark as blocked
        5. Return structured result

        Args:
            text: Input text to inspect

        Returns:
            GateResult with detection information
        """
        normalized = normalize_text(text)

        for role_name, matcher in self.matchers.items():
            matched_stem = matcher.match(normalized)

            if matched_stem:
                scope_rules = self.role_scopes.get(role_name, [])

                if scope_rules:
                    applied_rules = evaluate_scope_rules(scope_rules, normalized)

                    if applied_rules:
                        return GateResult(
                            blocked=True,
                            role=role_name,
                            reason=f"Judgment detected: {role_name} pattern '{matched_stem}' "
                                   f"with scope rules {applied_rules}",
                            confidence=0.85,
                            matched_stem=matched_stem,
                            scope_applied=applied_rules
                        )
                else:
                    return GateResult(
                        blocked=True,
                        role=role_name,
                        reason=f"Judgment detected: {role_name} pattern '{matched_stem}' "
                               f"(no scope filter)",
                        confidence=0.80,
                        matched_stem=matched_stem,
                        scope_applied=[]
                    )

        return GateResult(
            blocked=False,
            role=None,
            reason="No judgment pattern detected",
            confidence=0.0,
            matched_stem=None,
            scope_applied=[]
        )
