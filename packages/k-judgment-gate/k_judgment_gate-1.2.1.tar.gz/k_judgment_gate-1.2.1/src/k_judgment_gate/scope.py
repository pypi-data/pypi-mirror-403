"""
Scope rule enforcement with hard limits.

Each role can have a maximum of 2 scope rules. This constraint is enforced by code.
"""

from dataclasses import dataclass, field
from .stemmer import normalize_text


MAX_SCOPE_RULES_PER_ROLE = 2


@dataclass
class ScopeRule:
    """
    Scope rule for filtering judgment detection.

    A scope rule defines include/exclude patterns that must be satisfied
    for a judgment to be considered valid.

    Fields:
        id: Unique identifier for this rule
        include: List of terms - at least one must appear if non-empty
        exclude: List of terms - if any appear, rule fails
    """
    id: str
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    def evaluate(self, text: str) -> bool:
        """
        Evaluate whether this scope rule passes for the given text.

        Logic:
        1. If exclude list is non-empty and any exclude term appears, return False
        2. If include list is non-empty, at least one include term must appear
        3. Otherwise, return True

        Args:
            text: Normalized text to evaluate

        Returns:
            True if scope rule passes, False otherwise
        """
        normalized = normalize_text(text)

        if self.exclude:
            for exclude_term in self.exclude:
                normalized_term = normalize_text(exclude_term)
                if normalized_term in normalized:
                    return False

        if self.include:
            for include_term in self.include:
                normalized_term = normalize_text(include_term)
                if normalized_term in normalized:
                    return True
            return False

        return True


def validate_scope_rules(rules: list[ScopeRule], role: str) -> None:
    """
    Validate that scope rules do not exceed the limit.

    Args:
        rules: List of scope rules for a role
        role: Role name (for error message)

    Raises:
        ValueError: If more than MAX_SCOPE_RULES_PER_ROLE rules are provided
    """
    if len(rules) > MAX_SCOPE_RULES_PER_ROLE:
        raise ValueError(
            f"Role '{role}' has {len(rules)} scope rules, "
            f"but maximum is {MAX_SCOPE_RULES_PER_ROLE}"
        )


def evaluate_scope_rules(rules: list[ScopeRule], text: str) -> list[str]:
    """
    Evaluate all scope rules and return list of passing rule IDs.

    Args:
        rules: List of scope rules to evaluate
        text: Text to evaluate against

    Returns:
        List of rule IDs that passed evaluation
    """
    applied = []
    for rule in rules:
        if rule.evaluate(text):
            applied.append(rule.id)
    return applied
