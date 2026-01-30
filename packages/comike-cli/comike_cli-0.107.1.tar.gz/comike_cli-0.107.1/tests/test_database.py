"""Tests for database module."""

from comike_cli.database import normalize_block_for_search, blocks_match


def test_normalize_block_hiragana():
    """Hiragana should be preserved."""
    assert normalize_block_for_search("あ") == "あ"
    assert normalize_block_for_search("い") == "い"


def test_normalize_block_katakana():
    """Katakana should be preserved."""
    assert normalize_block_for_search("ア") == "ア"
    assert normalize_block_for_search("イ") == "イ"


def test_normalize_block_english():
    """English should be normalized to lowercase."""
    assert normalize_block_for_search("A") == "a"
    assert normalize_block_for_search("a") == "a"
    assert normalize_block_for_search("Z") == "z"


def test_normalize_block_fullwidth():
    """Full-width English should be normalized to half-width lowercase."""
    assert normalize_block_for_search("Ａ") == "a"
    assert normalize_block_for_search("ａ") == "a"
    assert normalize_block_for_search("Ｚ") == "z"


def test_blocks_match_same():
    """Same blocks should match."""
    assert blocks_match("あ", "あ")
    assert blocks_match("ア", "ア")
    assert blocks_match("A", "A")


def test_blocks_match_hiragana_katakana():
    """Hiragana and Katakana should NOT match."""
    assert not blocks_match("あ", "ア")
    assert not blocks_match("い", "イ")


def test_blocks_match_english_case():
    """English should match case-insensitively."""
    assert blocks_match("A", "a")
    assert blocks_match("a", "A")


def test_blocks_match_english_width():
    """Full-width and half-width English should match."""
    assert blocks_match("A", "Ａ")
    assert blocks_match("a", "ａ")
    assert blocks_match("Ａ", "a")
