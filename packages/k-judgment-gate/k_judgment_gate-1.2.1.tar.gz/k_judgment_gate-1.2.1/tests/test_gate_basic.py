"""
Basic tests for JudgmentGate functionality.
"""

import pytest
from k_judgment_gate import JudgmentGate, JudgmentRole
from k_judgment_gate.scope import ScopeRule


def test_directive_detection():
    """Test that directive patterns are detected."""
    gate = JudgmentGate(
        role_stems={
            JudgmentRole.DIRECTIVE.value: ["해야 합니다", "하십시오"],
            JudgmentRole.RECOMMENDATION.value: ["권장합니다"],
            JudgmentRole.OBLIGATION.value: ["의무입니다"],
        }
    )

    result = gate.inspect("이 작업을 해야 합니다")

    assert result.blocked is True
    assert result.role == JudgmentRole.DIRECTIVE.value
    assert result.matched_stem == "해야 합니다"
    assert "directive" in result.reason


def test_recommendation_detection():
    """Test that recommendation patterns are detected."""
    gate = JudgmentGate(
        role_stems={
            JudgmentRole.DIRECTIVE.value: ["해야 합니다"],
            JudgmentRole.RECOMMENDATION.value: ["권장합니다", "추천합니다"],
            JudgmentRole.OBLIGATION.value: ["의무입니다"],
        }
    )

    result = gate.inspect("이 방법을 권장합니다")

    assert result.blocked is True
    assert result.role == JudgmentRole.RECOMMENDATION.value
    assert result.matched_stem == "권장합니다"


def test_no_judgment_detected():
    """Test that neutral text is not blocked."""
    gate = JudgmentGate(
        role_stems={
            JudgmentRole.DIRECTIVE.value: ["해야 합니다"],
            JudgmentRole.RECOMMENDATION.value: ["권장합니다"],
            JudgmentRole.OBLIGATION.value: ["의무입니다"],
        }
    )

    result = gate.inspect("오늘 날씨가 좋습니다")

    assert result.blocked is False
    assert result.role is None
    assert "No judgment" in result.reason
    assert result.matched_stem is None


def test_scope_rule_filtering():
    """Test that scope rules correctly filter detections."""
    scope_rule = ScopeRule(
        id="medical_only",
        include=["의료", "건강"],
        exclude=[]
    )

    gate = JudgmentGate(
        role_stems={
            JudgmentRole.DIRECTIVE.value: ["해야 합니다"],
        },
        role_scopes={
            JudgmentRole.DIRECTIVE.value: [scope_rule],
        }
    )

    result_pass = gate.inspect("의료 절차를 해야 합니다")
    assert result_pass.blocked is True
    assert "medical_only" in result_pass.scope_applied

    result_fail = gate.inspect("일반 작업을 해야 합니다")
    assert result_fail.blocked is False


def test_confidence_values():
    """Test that confidence values are set correctly."""
    gate = JudgmentGate(
        role_stems={
            JudgmentRole.DIRECTIVE.value: ["해야 합니다"],
        }
    )

    result_match = gate.inspect("이것을 해야 합니다")
    assert 0.0 <= result_match.confidence <= 1.0
    assert result_match.confidence > 0.0

    result_no_match = gate.inspect("일반 텍스트")
    assert result_no_match.confidence == 0.0
