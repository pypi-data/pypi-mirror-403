"""Tests for Scene operations."""

import time

SETTLE_TIME = 0.1  # Time for Ableton to process changes


def test_get_name(scene):
    """Test getting scene name."""
    name = scene.get_name(0)
    assert isinstance(name, str)


def test_set_name(scene):
    """Test setting scene name."""
    original = scene.get_name(0)
    try:
        scene.set_name(0, "Test Scene")
        time.sleep(SETTLE_TIME)
        assert scene.get_name(0) == "Test Scene"
    finally:
        scene.set_name(0, original)


def test_get_color(scene):
    """Test getting scene color."""
    color = scene.get_color(0)
    assert isinstance(color, int)


def test_get_is_triggered(scene):
    """Test checking if scene is triggered."""
    is_triggered = scene.get_is_triggered(0)
    assert isinstance(is_triggered, bool)


# New endpoint tests (Gap Coverage)


def test_get_color_index(scene):
    """Test getting scene color index."""
    color_index = scene.get_color_index(0)
    assert isinstance(color_index, int)
    assert 0 <= color_index <= 69


def test_get_is_empty(scene):
    """Test checking if scene is empty."""
    is_empty = scene.get_is_empty(0)
    assert isinstance(is_empty, bool)


def test_get_tempo_enabled(scene):
    """Test getting scene tempo enabled state."""
    tempo_enabled = scene.get_tempo_enabled(0)
    assert isinstance(tempo_enabled, bool)


def test_get_time_signature_numerator(scene):
    """Test getting scene time signature numerator."""
    numerator = scene.get_time_signature_numerator(0)
    assert isinstance(numerator, int)
    assert numerator > 0


def test_get_time_signature_denominator(scene):
    """Test getting scene time signature denominator."""
    denominator = scene.get_time_signature_denominator(0)
    assert isinstance(denominator, int)
    assert denominator > 0


def test_get_time_signature_enabled(scene):
    """Test getting scene time signature enabled state."""
    enabled = scene.get_time_signature_enabled(0)
    assert isinstance(enabled, bool)
