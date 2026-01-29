"""
Tests for minimal Korean stem matching.
"""

import pytest
from k_judgment_gate.stemmer import StemMatcher, normalize_text


def test_normalize_text_lowercase():
    """Test that normalization converts to lowercase."""
    result = normalize_text("HELLO World")
    assert result == "hello world"


def test_normalize_text_whitespace():
    """Test that normalization handles whitespace."""
    result = normalize_text("  hello   world  ")
    assert result == "hello world"


def test_normalize_text_punctuation():
    """Test that normalization removes punctuation."""
    result = normalize_text("hello, world!")
    assert result == "hello world"


def test_stem_matcher_exact_match():
    """Test exact substring matching."""
    matcher = StemMatcher(["해야 합니다", "권장합니다"])

    result = matcher.match("이 작업을 해야 합니다")
    assert result == "해야 합니다"


def test_stem_matcher_no_match():
    """Test that no match returns None."""
    matcher = StemMatcher(["해야 합니다", "권장합니다"])

    result = matcher.match("일반 텍스트입니다")
    assert result is None


def test_stem_matcher_case_insensitive():
    """Test that matching is case-insensitive."""
    matcher = StemMatcher(["MUST", "should"])

    result = matcher.match("You must complete this")
    assert result == "MUST"


def test_stem_matcher_multiple_stems():
    """Test matching with multiple stem patterns."""
    matcher = StemMatcher(["해야", "권장", "의무"])

    result1 = matcher.match("이것을 해야 합니다")
    assert result1 == "해야"

    result2 = matcher.match("이것을 권장합니다")
    assert result2 == "권장"

    result3 = matcher.match("이것은 의무입니다")
    assert result3 == "의무"


def test_stem_matcher_korean_text():
    """Test Korean text matching."""
    matcher = StemMatcher(["해야 합니다", "하십시오", "권장합니다"])

    result = matcher.match("사용자는 이 절차를 따라 해야 합니다.")
    assert result == "해야 합니다"
