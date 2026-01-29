"""
Sealed role definitions for judgment detection.

Only three roles are permitted: directive, recommendation, obligation.
This is a hard constraint and cannot be extended.
"""

from enum import Enum
from typing import Optional


class JudgmentRole(str, Enum):
    """
    Sealed enum of exactly 3 judgment roles.

    - DIRECTIVE: Commands, imperatives, direct instructions
    - RECOMMENDATION: Suggestions, advice, guidance
    - OBLIGATION: Requirements, duties, must-do statements
    """
    DIRECTIVE = "directive"
    RECOMMENDATION = "recommendation"
    OBLIGATION = "obligation"


def validate_role(role: Optional[str]) -> Optional[JudgmentRole]:
    """
    Validate and convert a string to a JudgmentRole.

    Args:
        role: Role string or None

    Returns:
        JudgmentRole enum value or None if input is None

    Raises:
        ValueError: If role is not one of the 3 permitted roles
    """
    if role is None:
        return None

    try:
        return JudgmentRole(role)
    except ValueError:
        valid_roles = [r.value for r in JudgmentRole]
        raise ValueError(
            f"Invalid role '{role}'. Must be one of: {valid_roles}"
        )
