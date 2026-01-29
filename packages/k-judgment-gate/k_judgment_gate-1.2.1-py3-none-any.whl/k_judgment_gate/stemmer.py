"""
Minimal Korean stem matching for judgment detection.

This is deliberately lightweight and does NOT use heavy NLP dependencies.
It performs basic normalization and substring/pattern matching.
"""

import re
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for matching.

    - Convert to lowercase
    - Strip leading/trailing whitespace
    - Normalize internal whitespace to single spaces
    - Remove common punctuation

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    text = text.lower()
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[.,!?;:()]', '', text)
    return text


class StemMatcher:
    """
    Simple stem matcher using substring and regex patterns.

    This matcher is intentionally minimal and does not perform
    morphological analysis or use external NLP libraries.
    """

    def __init__(self, stems: list[str]):
        """
        Initialize stem matcher.

        Args:
            stems: List of stem patterns to match (strings)
        """
        self.stems = stems

    def match(self, text: str) -> Optional[str]:
        """
        Check if any stem pattern matches the normalized text.

        Args:
            text: Input text to check

        Returns:
            The matched stem pattern, or None if no match
        """
        normalized = normalize_text(text)

        for stem in self.stems:
            normalized_stem = normalize_text(stem)

            if normalized_stem in normalized:
                return stem

            try:
                pattern = re.compile(re.escape(normalized_stem))
                if pattern.search(normalized):
                    return stem
            except re.error:
                continue

        return None
