"""
OpenTelemetry-style attribute generation for judgment gate results.

This module provides functions to convert GateResult into OTel-compatible
attributes dict. No actual OTel dependency is required.
"""

from typing import Any
from .schema import GateResult


def gate_attributes(result: GateResult) -> dict[str, Any]:
    """
    Generate OpenTelemetry-style attributes dict from GateResult.

    This produces a namespaced attributes dictionary that can be used
    with OpenTelemetry spans or logged for observability.

    Args:
        result: GateResult from judgment gate inspection

    Returns:
        Dictionary of namespaced attributes
    """
    attrs = {
        "judgment.gate.present": True,
        "judgment.gate.blocked": result.blocked,
        "judgment.gate.confidence": result.confidence,
    }

    if result.role:
        attrs["judgment.gate.role"] = result.role

    if result.matched_stem:
        attrs["judgment.gate.matched_stem"] = result.matched_stem

    if result.scope_applied:
        attrs["judgment.gate.scope_applied"] = ",".join(result.scope_applied)

    if result.reason:
        attrs["judgment.gate.reason"] = result.reason

    return attrs
