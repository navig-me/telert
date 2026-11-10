"""Tests for Provider.from_string value handling."""

import pytest

from telert.messaging import Provider


def test_from_string_valid():
    assert Provider.from_string("telegram") is Provider.TELEGRAM
    assert Provider.from_string("slack") is Provider.SLACK


def test_from_string_case_insensitive():
    assert Provider.from_string("Telegram") is Provider.TELEGRAM
    assert Provider.from_string("SLACK") is Provider.SLACK


def test_from_string_unknown_raises_value_error():
    with pytest.raises(ValueError):
        Provider.from_string("carrier-pigeon")


def test_from_string_none_raises_value_error():
    # Callers (config/status CLI paths) catch ValueError; a missing value
    # must surface as ValueError, not an AttributeError traceback.
    with pytest.raises(ValueError):
        Provider.from_string(None)


def test_from_string_non_string_raises_value_error():
    with pytest.raises(ValueError):
        Provider.from_string(123)
