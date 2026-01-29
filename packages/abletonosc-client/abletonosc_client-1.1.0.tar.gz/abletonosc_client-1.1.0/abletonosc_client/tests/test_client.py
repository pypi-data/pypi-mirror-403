"""Tests for the core AbletonOSC client."""


def test_query_responds(client):
    """Test that basic query/response works."""
    result = client.query("/live/test")
    assert result is not None


def test_query_timeout_without_ableton():
    """Test that timeout works when nothing is listening."""
    import pytest

    from abletonosc_client.client import AbletonOSCClient

    # Use a port that nothing is listening on
    c = AbletonOSCClient(send_port=19999, receive_port=19998)
    try:
        with pytest.raises(TimeoutError):
            c.query("/live/test", timeout=0.5)
    finally:
        c.close()


def test_application_test(application):
    """Test that Application.test() returns True."""
    assert application.test() is True


def test_application_get_version(application):
    """Test getting Ableton version."""
    version = application.get_version()
    assert version  # Non-empty string
    assert isinstance(version, str)
