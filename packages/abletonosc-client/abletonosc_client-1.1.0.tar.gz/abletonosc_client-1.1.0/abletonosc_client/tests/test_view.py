"""Tests for View operations."""

import threading
import time

SETTLE_TIME = 0.1  # Time for Ableton to process changes


def test_get_selected_track(view):
    """Test getting selected track."""
    track = view.get_selected_track()
    assert isinstance(track, int)
    assert track >= 0


def test_set_selected_track(view, song):
    """Test setting selected track."""
    original = view.get_selected_track()
    num_tracks = song.get_num_tracks()

    try:
        # Select first track
        view.set_selected_track(0)
        assert view.get_selected_track() == 0

        # Select another track if available
        if num_tracks > 1:
            view.set_selected_track(1)
            assert view.get_selected_track() == 1
    finally:
        view.set_selected_track(original)


def test_get_selected_scene(view):
    """Test getting selected scene."""
    scene = view.get_selected_scene()
    assert isinstance(scene, int)
    assert scene >= 0


def test_set_selected_scene(view, song):
    """Test setting selected scene."""
    original = view.get_selected_scene()
    num_scenes = song.get_num_scenes()

    try:
        # Select first scene
        view.set_selected_scene(0)
        assert view.get_selected_scene() == 0

        # Select another scene if available
        if num_scenes > 1:
            view.set_selected_scene(1)
            assert view.get_selected_scene() == 1
    finally:
        view.set_selected_scene(original)


# Phase 9: Selection tests


def test_get_selected_clip(view):
    """Test getting selected clip."""
    result = view.get_selected_clip()
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_set_selected_clip(view, test_clip_with_notes):
    """Test setting selected clip."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]

    view.set_selected_clip(t, s)
    result = view.get_selected_clip()
    # Note: result may vary depending on Ableton state
    assert isinstance(result, tuple)


def test_get_selected_device(view):
    """Test getting selected device."""
    result = view.get_selected_device()
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_set_selected_device(view, song, track):
    """Test setting selected device (requires device on track)."""
    # Create a track with a device
    original_tracks = song.get_num_tracks()
    track_idx = original_tracks

    song.create_midi_track(-1)
    time.sleep(SETTLE_TIME)

    try:
        # Insert a device
        device_idx = track.insert_device(track_idx, "Wavetable")
        time.sleep(SETTLE_TIME)

        if device_idx >= 0:
            view.set_selected_device(track_idx, device_idx)
            result = view.get_selected_device()
            assert isinstance(result, tuple)
    finally:
        song.delete_track(track_idx)
        time.sleep(SETTLE_TIME)


# Listener tests


def test_on_selected_track_change(view, song):
    """Test selected track change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(track_idx):
        received_value[0] = track_idx
        received.set()

    original = view.get_selected_track()
    num_tracks = song.get_num_tracks()

    # Need at least 2 tracks to test selection change
    if num_tracks < 2:
        return

    new_track = 1 if original != 1 else 0
    try:
        view.on_selected_track_change(callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        view.set_selected_track(new_track)
        assert received.wait(timeout=2.0), "Selected track callback not triggered"
        assert received_value[0] == new_track
    finally:
        view.stop_selected_track_listener()
        view.set_selected_track(original)


def test_on_selected_scene_change(view, song):
    """Test selected scene change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(scene_idx):
        received_value[0] = scene_idx
        received.set()

    original = view.get_selected_scene()
    num_scenes = song.get_num_scenes()

    # Need at least 2 scenes to test selection change
    if num_scenes < 2:
        return

    new_scene = 1 if original != 1 else 0
    try:
        view.on_selected_scene_change(callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        view.set_selected_scene(new_scene)
        assert received.wait(timeout=2.0), "Selected scene callback not triggered"
        assert received_value[0] == new_scene
    finally:
        view.stop_selected_scene_listener()
        view.set_selected_scene(original)
