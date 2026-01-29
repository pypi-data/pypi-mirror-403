"""Tests for ClipSlot operations."""

import time

import pytest

SETTLE_TIME = 0.1  # Time for Ableton to process changes


def test_has_clip(clip_slot):
    """Test checking if slot has a clip."""
    has = clip_slot.has_clip(0, 0)
    assert isinstance(has, bool)


def test_create_and_delete_clip(clip_slot, song):
    """Test creating and deleting a clip."""
    # Find an empty slot to test with
    num_scenes = song.get_num_scenes()

    # Use a slot that's likely empty (high scene index)
    test_scene = num_scenes - 1

    # Skip if slot already has a clip
    if clip_slot.has_clip(0, test_scene):
        # Try to find an empty slot
        empty_slot = None
        for i in range(num_scenes):
            if not clip_slot.has_clip(0, i):
                empty_slot = i
                break
        if empty_slot is None:
            pytest.skip("No empty clip slots available for testing")
        test_scene = empty_slot

    # Create a clip
    clip_slot.create_clip(0, test_scene, 4.0)
    time.sleep(SETTLE_TIME)

    # Verify it exists
    assert clip_slot.has_clip(0, test_scene) is True

    # Delete it
    clip_slot.delete_clip(0, test_scene)
    time.sleep(SETTLE_TIME)

    # Verify it's gone
    assert clip_slot.has_clip(0, test_scene) is False


def test_get_is_playing(clip_slot):
    """Test checking if slot is playing."""
    is_playing = clip_slot.get_is_playing(0, 0)
    assert isinstance(is_playing, bool)


def test_get_is_triggered(clip_slot):
    """Test checking if slot is triggered."""
    is_triggered = clip_slot.get_is_triggered(0, 0)
    assert isinstance(is_triggered, bool)


def test_get_is_recording(clip_slot):
    """Test checking if slot is recording."""
    is_recording = clip_slot.get_is_recording(0, 0)
    assert isinstance(is_recording, bool)


# New endpoint tests (Gap Coverage)


def test_get_has_stop_button(clip_slot):
    """Test checking if slot has stop button."""
    has_stop = clip_slot.get_has_stop_button(0, 0)
    assert isinstance(has_stop, bool)


def test_set_has_stop_button(clip_slot):
    """Test setting stop button state."""
    original = clip_slot.get_has_stop_button(0, 0)
    try:
        clip_slot.set_has_stop_button(0, 0, False)
        assert clip_slot.get_has_stop_button(0, 0) is False
        clip_slot.set_has_stop_button(0, 0, True)
        assert clip_slot.get_has_stop_button(0, 0) is True
    finally:
        clip_slot.set_has_stop_button(0, 0, original)
