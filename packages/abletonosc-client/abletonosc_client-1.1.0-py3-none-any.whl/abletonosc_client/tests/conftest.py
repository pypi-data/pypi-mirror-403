"""Pytest configuration and fixtures for OSC client tests.

These are integration tests that require a running Ableton Live instance
with AbletonOSC enabled.
"""

import time

import pytest

from abletonosc_client.client import AbletonOSCClient


# Global to track if we've already checked for Ableton
_ableton_available = None


@pytest.fixture(scope="session")
def client():
    """Provide a connected AbletonOSC client.

    Skips the test if Ableton is not running or AbletonOSC is not responding.
    Session-scoped to avoid port binding issues.
    """
    global _ableton_available

    c = AbletonOSCClient()
    try:
        c.query("/live/test", timeout=1.0)
        _ableton_available = True
    except TimeoutError:
        c.close()
        _ableton_available = False
        pytest.skip("Ableton not running or AbletonOSC not enabled")

    yield c
    c.close()


@pytest.fixture(scope="session")
def song(client):
    """Provide a Song instance."""
    from abletonosc_client.song import Song

    return Song(client)


@pytest.fixture(scope="session")
def track(client):
    """Provide a Track instance."""
    from abletonosc_client.track import Track

    return Track(client)


@pytest.fixture(scope="session")
def clip(client):
    """Provide a Clip instance."""
    from abletonosc_client.clip import Clip

    return Clip(client)


@pytest.fixture(scope="session")
def clip_slot(client):
    """Provide a ClipSlot instance."""
    from abletonosc_client.clip_slot import ClipSlot

    return ClipSlot(client)


@pytest.fixture(scope="session")
def device(client):
    """Provide a Device instance."""
    from abletonosc_client.device import Device

    return Device(client)


@pytest.fixture(scope="session")
def scene(client):
    """Provide a Scene instance."""
    from abletonosc_client.scene import Scene

    return Scene(client)


@pytest.fixture(scope="session")
def view(client):
    """Provide a View instance."""
    from abletonosc_client.view import View

    return View(client)


@pytest.fixture(scope="session")
def application(client):
    """Provide an Application instance."""
    from abletonosc_client.application import Application

    return Application(client)


@pytest.fixture(scope="session")
def midimap(client):
    """Provide a MidiMap instance."""
    from abletonosc_client.midimap import MidiMap

    return MidiMap(client)


@pytest.fixture
def test_clip_with_notes(client, song, clip_slot, clip):
    """Create a temporary MIDI track with an audible clip for testing.

    Creates a new MIDI track at the end, adds a 4-beat clip with a C major chord,
    yields the track/scene indices, then cleans up.

    The user should hear the chord briefly when clip tests run (proves end-to-end).
    """
    from abletonosc_client.clip import Note

    original_tracks = song.get_num_tracks()
    track_idx = original_tracks  # New track will be at this index
    scene_idx = 0

    # Create MIDI track at end
    song.create_midi_track(-1)
    time.sleep(0.2)

    # Create 4-beat clip
    clip_slot.create_clip(track_idx, scene_idx, 4.0)
    time.sleep(0.1)

    # Add audible notes (C major chord)
    notes = [
        Note(pitch=60, start_time=0.0, duration=1.0, velocity=100),  # C4
        Note(pitch=64, start_time=0.0, duration=1.0, velocity=100),  # E4
        Note(pitch=67, start_time=0.0, duration=1.0, velocity=100),  # G4
    ]
    clip.add_notes(track_idx, scene_idx, notes)
    time.sleep(0.1)

    yield {"track": track_idx, "scene": scene_idx}

    # Cleanup
    clip_slot.delete_clip(track_idx, scene_idx)
    time.sleep(0.1)
    song.delete_track(track_idx)
    time.sleep(0.1)
