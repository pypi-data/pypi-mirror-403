"""
Tests for scope rule limits enforcement.
"""

import pytest
from k_judgment_gate import JudgmentGate, JudgmentRole
from k_judgment_gate.scope import ScopeRule, validate_scope_rules


def test_max_scope_rules_enforced():
    """Test that more than 2 scope rules raises ValueError."""
    rules = [
        ScopeRule(id="rule1", include=["term1"]),
        ScopeRule(id="rule2", include=["term2"]),
        ScopeRule(id="rule3", include=["term3"]),
    ]

    with pytest.raises(ValueError) as excinfo:
        validate_scope_rules(rules, JudgmentRole.DIRECTIVE.value)

    assert "maximum is 2" in str(excinfo.value)


def test_max_scope_rules_in_gate_init():
    """Test that JudgmentGate init enforces scope rule limits."""
    rules = [
        ScopeRule(id="rule1", include=["term1"]),
        ScopeRule(id="rule2", include=["term2"]),
        ScopeRule(id="rule3", include=["term3"]),
    ]

    with pytest.raises(ValueError) as excinfo:
        JudgmentGate(
            role_stems={JudgmentRole.DIRECTIVE.value: ["test"]},
            role_scopes={JudgmentRole.DIRECTIVE.value: rules}
        )

    assert "maximum is 2" in str(excinfo.value)


def test_two_scope_rules_allowed():
    """Test that exactly 2 scope rules is allowed."""
    rules = [
        ScopeRule(id="rule1", include=["의료"]),
        ScopeRule(id="rule2", include=["건강"]),
    ]

    gate = JudgmentGate(
        role_stems={JudgmentRole.DIRECTIVE.value: ["해야 합니다"]},
        role_scopes={JudgmentRole.DIRECTIVE.value: rules}
    )

    result = gate.inspect("의료 절차를 해야 합니다")
    assert result.blocked is True
    assert "rule1" in result.scope_applied


def test_one_scope_rule_allowed():
    """Test that 1 scope rule is allowed."""
    rules = [
        ScopeRule(id="rule1", include=["의료"]),
    ]

    gate = JudgmentGate(
        role_stems={JudgmentRole.DIRECTIVE.value: ["해야 합니다"]},
        role_scopes={JudgmentRole.DIRECTIVE.value: rules}
    )

    result = gate.inspect("의료 절차를 해야 합니다")
    assert result.blocked is True


def test_zero_scope_rules_allowed():
    """Test that 0 scope rules is allowed."""
    gate = JudgmentGate(
        role_stems={JudgmentRole.DIRECTIVE.value: ["해야 합니다"]},
        role_scopes={}
    )

    result = gate.inspect("이것을 해야 합니다")
    assert result.blocked is True
    assert result.scope_applied == []
