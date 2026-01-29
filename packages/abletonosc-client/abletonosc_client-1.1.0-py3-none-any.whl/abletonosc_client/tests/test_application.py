"""Tests for Application operations."""

import time

import pytest

SETTLE_TIME = 0.1  # Time for Ableton to process changes


def test_get_version(application):
    """Test getting Ableton version."""
    version = application.get_version()
    assert isinstance(version, str)
    assert len(version) > 0  # Should be something like "12.0.1"


def test_get_api_version(application):
    """Test getting AbletonOSC API version."""
    try:
        api_version = application.get_api_version()
        assert isinstance(api_version, int)
        assert api_version >= 0
    except TimeoutError:
        # Some AbletonOSC versions don't support this endpoint
        import pytest
        pytest.skip("AbletonOSC version doesn't support /live/api/get/version")


def test_connection(application):
    """Test OSC connection."""
    result = application.test()
    assert result is True


def test_get_log_level(application):
    """Test getting log level."""
    level = application.get_log_level()
    assert isinstance(level, str)
    assert level in {"debug", "info", "warning", "error", "critical"}


def test_set_log_level(application):
    """Test setting log level."""
    original = application.get_log_level()
    try:
        application.set_log_level("debug")
        time.sleep(SETTLE_TIME)
        assert application.get_log_level() == "debug"

        application.set_log_level("info")
        time.sleep(SETTLE_TIME)
        assert application.get_log_level() == "info"
    finally:
        application.set_log_level(original)


def test_set_log_level_invalid(application):
    """Test setting invalid log level raises ValueError."""
    with pytest.raises(ValueError):
        application.set_log_level("invalid_level")


def test_show_message(application):
    """Test showing message in Ableton status bar."""
    # Just verify the method executes without error
    # Visual verification needed to confirm it appears in Ableton
    application.show_message("Test message from OSC client")


def test_reload(application):
    """Test reloading AbletonOSC script."""
    # Just verify the method executes without error
    # This reloads the script, so connection should still work after
    application.reload()
    time.sleep(0.5)  # Give it time to reload
    # Verify connection still works
    assert application.test() is True
