"""Tests for Clip operations.

Uses the test_clip_with_notes fixture which creates a temporary MIDI track
with an audible clip for testing. This ensures tests are self-contained
and don't require manual setup.
"""

import pytest

from abletonosc_client.clip import Note


def test_note_creation():
    """Test Note namedtuple creation."""
    note = Note(pitch=60, start_time=0.0, duration=0.5, velocity=100)
    assert note.pitch == 60
    assert note.start_time == 0.0
    assert note.duration == 0.5
    assert note.velocity == 100
    assert note.mute is False

    muted_note = Note(pitch=60, start_time=0.0, duration=0.5, velocity=100, mute=True)
    assert muted_note.mute is True


def test_get_name(clip, test_clip_with_notes):
    """Test getting clip name."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    name = clip.get_name(t, s)
    assert isinstance(name, str)


def test_set_name(clip, test_clip_with_notes):
    """Test setting clip name."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    original = clip.get_name(t, s)
    try:
        clip.set_name(t, s, "Test Clip")
        assert clip.get_name(t, s) == "Test Clip"
    finally:
        clip.set_name(t, s, original)


def test_get_length(clip, test_clip_with_notes):
    """Test getting clip length."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    length = clip.get_length(t, s)
    assert length == 4.0  # We created a 4-beat clip


def test_get_is_playing(clip, test_clip_with_notes):
    """Test checking if clip is playing."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    is_playing = clip.get_is_playing(t, s)
    assert isinstance(is_playing, bool)


def test_get_color(clip, test_clip_with_notes):
    """Test getting clip color."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    color = clip.get_color(t, s)
    assert isinstance(color, int)


def test_get_loop_start(clip, test_clip_with_notes):
    """Test getting loop start."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    loop_start = clip.get_loop_start(t, s)
    assert isinstance(loop_start, float)
    assert loop_start >= 0


def test_get_loop_end(clip, test_clip_with_notes):
    """Test getting loop end."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    loop_end = clip.get_loop_end(t, s)
    assert isinstance(loop_end, float)
    assert loop_end > 0


def test_get_notes(clip, test_clip_with_notes):
    """Test getting notes from a clip."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    notes = clip.get_notes(t, s)
    assert len(notes) == 3  # C major chord (C, E, G)
    pitches = [n.pitch for n in notes]
    assert 60 in pitches  # C4
    assert 64 in pitches  # E4
    assert 67 in pitches  # G4


def test_is_midi_clip(clip, test_clip_with_notes):
    """Test checking if clip is a MIDI clip."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    assert clip.get_is_midi_clip(t, s) is True
    assert clip.get_is_audio_clip(t, s) is False


# Phase 8: Clip properties tests


def test_get_start_time(clip, test_clip_with_notes):
    """Test getting clip start time."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    start_time = clip.get_start_time(t, s)
    assert isinstance(start_time, float)


def test_get_end_time(clip, test_clip_with_notes):
    """Test getting clip end time."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    end_time = clip.get_end_time(t, s)
    assert isinstance(end_time, float)
    assert end_time > 0


def test_get_looping(clip, test_clip_with_notes):
    """Test getting clip looping state."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    looping = clip.get_looping(t, s)
    assert isinstance(looping, bool)


def test_set_looping(clip, test_clip_with_notes):
    """Test setting clip looping state."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    original = clip.get_looping(t, s)
    try:
        clip.set_looping(t, s, True)
        assert clip.get_looping(t, s) is True

        clip.set_looping(t, s, False)
        assert clip.get_looping(t, s) is False
    finally:
        clip.set_looping(t, s, original)


def test_duplicate_loop(clip, test_clip_with_notes):
    """Test duplicating loop (just verify no error)."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    # Just verify method executes without error
    clip.duplicate_loop(t, s)


def test_get_pitch_coarse(clip, test_clip_with_notes):
    """Test getting coarse pitch adjustment (returns 0 for MIDI clips)."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    pitch = clip.get_pitch_coarse(t, s)
    assert isinstance(pitch, int)
    # MIDI clips return 0, audio clips return -48 to +48
    assert -48 <= pitch <= 48


def test_get_pitch_fine(clip, test_clip_with_notes):
    """Test getting fine pitch adjustment (returns 0 for MIDI clips)."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    pitch = clip.get_pitch_fine(t, s)
    assert isinstance(pitch, float)
    # MIDI clips return 0, audio clips return -50 to +50
    assert -50 <= pitch <= 50


# New endpoint tests (Gap Coverage)


def test_get_muted(clip, test_clip_with_notes):
    """Test getting clip muted state."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    muted = clip.get_muted(t, s)
    assert isinstance(muted, bool)


def test_set_muted(clip, test_clip_with_notes):
    """Test setting clip muted state."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    original = clip.get_muted(t, s)
    try:
        clip.set_muted(t, s, True)
        assert clip.get_muted(t, s) is True
        clip.set_muted(t, s, False)
        assert clip.get_muted(t, s) is False
    finally:
        clip.set_muted(t, s, original)


def test_get_color_index(clip, test_clip_with_notes):
    """Test getting clip color index."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    color_index = clip.get_color_index(t, s)
    assert isinstance(color_index, int)
    assert 0 <= color_index <= 69


def test_get_launch_mode(clip, test_clip_with_notes):
    """Test getting clip launch mode."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    launch_mode = clip.get_launch_mode(t, s)
    assert isinstance(launch_mode, int)
    assert 0 <= launch_mode <= 3  # Trigger, Gate, Toggle, Repeat


def test_get_launch_quantization(clip, test_clip_with_notes):
    """Test getting clip launch quantization."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    quant = clip.get_launch_quantization(t, s)
    assert isinstance(quant, int)


def test_get_legato(clip, test_clip_with_notes):
    """Test getting legato mode for MIDI clip."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    legato = clip.get_legato(t, s)
    assert isinstance(legato, bool)


def test_get_velocity_amount(clip, test_clip_with_notes):
    """Test getting velocity amount for MIDI clip."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    velocity = clip.get_velocity_amount(t, s)
    assert isinstance(velocity, float)


def test_get_is_recording(clip, test_clip_with_notes):
    """Test getting clip recording state."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    is_recording = clip.get_is_recording(t, s)
    assert isinstance(is_recording, bool)
    # Our test clip should not be recording
    assert is_recording is False


def test_get_is_overdubbing(clip, test_clip_with_notes):
    """Test getting clip overdubbing state."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    is_overdubbing = clip.get_is_overdubbing(t, s)
    assert isinstance(is_overdubbing, bool)


def test_get_position(clip, test_clip_with_notes):
    """Test getting clip position."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    position = clip.get_position(t, s)
    assert isinstance(position, float)


def test_get_start_marker(clip, test_clip_with_notes):
    """Test getting clip start marker."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    marker = clip.get_start_marker(t, s)
    assert isinstance(marker, float)


def test_get_end_marker(clip, test_clip_with_notes):
    """Test getting clip end marker."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    marker = clip.get_end_marker(t, s)
    assert isinstance(marker, float)
    assert marker > 0


def test_get_has_groove(clip, test_clip_with_notes):
    """Test getting has_groove state."""
    t, s = test_clip_with_notes["track"], test_clip_with_notes["scene"]
    has_groove = clip.get_has_groove(t, s)
    assert isinstance(has_groove, bool)
