"""
k-judgment-gate: Governance-first judgment detection for Korean LLM systems.

This package does NOT make policy decisions. It only detects judgment attempts
(directive/recommendation/obligation) and marks the boundary where human oversight is required.
"""

__version__ = "0.1.0"

from .roles import JudgmentRole, validate_role
from .schema import GateResult
from .scope import ScopeRule
from .gate import JudgmentGate

__all__ = [
    "JudgmentRole",
    "validate_role",
    "GateResult",
    "ScopeRule",
    "JudgmentGate",
    "__version__",
]
