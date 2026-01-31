"""Unit tests for text preprocessing behavior."""

from spam_classifier.data.preprocess import preprocess_text


def test_preprocess_replaces_patterns() -> None:
    """Replace URLs/emails/phones with tokens to reduce sparsity."""
    text = "Visit https://example.com or email me@test.com. Call +1 555 123 4567!"
    processed = preprocess_text(text)
    assert "__URL__" in processed
    assert "__EMAIL__" in processed
    assert "__PHONE__" in processed


def test_preprocess_handles_numbers_and_repeats() -> None:
    """Normalize repeated characters and numbers."""
    text = "Winnnn!!! You won 1000 dollars!!!"
    processed = preprocess_text(text)
    assert "__NUM__" in processed
    assert "winn" in processed


def test_preprocess_non_string_returns_empty() -> None:
    """Return empty string for non-text inputs."""
    assert preprocess_text(None) == ""
