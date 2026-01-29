"""Tests for Song operations."""

import threading
import time

SETTLE_TIME = 0.1  # Time for Ableton to process changes


def test_get_tempo(song):
    """Test getting current tempo."""
    tempo = song.get_tempo()
    assert 20 <= tempo <= 999  # Valid BPM range


def test_set_tempo(song):
    """Test setting tempo."""
    original = song.get_tempo()
    try:
        song.set_tempo(120.0)
        assert song.get_tempo() == 120.0

        song.set_tempo(140.5)
        assert song.get_tempo() == 140.5
    finally:
        song.set_tempo(original)  # Restore


def test_get_is_playing(song):
    """Test getting play state."""
    is_playing = song.get_is_playing()
    assert isinstance(is_playing, bool)


def test_start_stop_playing(song):
    """Test transport controls."""
    original_playing = song.get_is_playing()
    try:
        song.stop_playing()
        time.sleep(SETTLE_TIME)
        assert song.get_is_playing() is False

        song.start_playing()
        time.sleep(SETTLE_TIME)
        assert song.get_is_playing() is True

        song.stop_playing()
        time.sleep(SETTLE_TIME)
        assert song.get_is_playing() is False
    finally:
        if original_playing:
            song.start_playing()
        else:
            song.stop_playing()


def test_get_num_tracks(song):
    """Test getting track count."""
    num_tracks = song.get_num_tracks()
    assert num_tracks >= 1  # Always at least one track


def test_get_num_scenes(song):
    """Test getting scene count."""
    num_scenes = song.get_num_scenes()
    assert num_scenes >= 1  # Always at least one scene


def test_get_signature(song):
    """Test getting time signature."""
    numerator = song.get_signature_numerator()
    denominator = song.get_signature_denominator()

    assert 1 <= numerator <= 99
    assert denominator in [1, 2, 4, 8, 16]  # Powers of 2


def test_set_signature(song):
    """Test setting time signature."""
    original_num = song.get_signature_numerator()
    original_denom = song.get_signature_denominator()
    try:
        song.set_signature_numerator(3)
        song.set_signature_denominator(4)

        assert song.get_signature_numerator() == 3
        assert song.get_signature_denominator() == 4
    finally:
        song.set_signature_numerator(original_num)
        song.set_signature_denominator(original_denom)


def test_get_metronome(song):
    """Test getting metronome state."""
    metronome = song.get_metronome()
    assert isinstance(metronome, bool)


def test_set_metronome(song):
    """Test toggling metronome."""
    original = song.get_metronome()
    try:
        song.set_metronome(True)
        assert song.get_metronome() is True

        song.set_metronome(False)
        assert song.get_metronome() is False
    finally:
        song.set_metronome(original)


def test_get_current_song_time(song):
    """Test getting playback position."""
    position = song.get_current_song_time()
    assert isinstance(position, float)
    assert position >= 0


def test_create_and_delete_midi_track(song):
    """Test creating and deleting a MIDI track."""
    original_count = song.get_num_tracks()

    # Create MIDI track at end
    song.create_midi_track(-1)
    time.sleep(SETTLE_TIME)
    assert song.get_num_tracks() == original_count + 1

    # Delete the new track
    song.delete_track(original_count)
    time.sleep(SETTLE_TIME)
    assert song.get_num_tracks() == original_count


def test_create_and_delete_audio_track(song):
    """Test creating and deleting an audio track."""
    original_count = song.get_num_tracks()

    # Create audio track at end
    song.create_audio_track(-1)
    time.sleep(SETTLE_TIME)
    assert song.get_num_tracks() == original_count + 1

    # Delete the new track
    song.delete_track(original_count)
    time.sleep(SETTLE_TIME)
    assert song.get_num_tracks() == original_count


def test_duplicate_track(song):
    """Test duplicating a track."""
    original_count = song.get_num_tracks()

    # Duplicate track 0
    song.duplicate_track(0)
    time.sleep(SETTLE_TIME)
    assert song.get_num_tracks() == original_count + 1

    # Delete the duplicate (it appears at index 1)
    song.delete_track(1)
    time.sleep(SETTLE_TIME)
    assert song.get_num_tracks() == original_count


def test_get_groove_amount(song):
    """Test getting groove amount."""
    groove = song.get_groove_amount()
    assert 0.0 <= groove <= 1.0


def test_set_groove_amount(song):
    """Test setting groove amount."""
    original = song.get_groove_amount()
    try:
        song.set_groove_amount(0.5)
        time.sleep(SETTLE_TIME)
        assert abs(song.get_groove_amount() - 0.5) < 0.01

        song.set_groove_amount(0.0)
        time.sleep(SETTLE_TIME)
        assert abs(song.get_groove_amount()) < 0.01
    finally:
        song.set_groove_amount(original)


def test_can_undo_redo(song):
    """Test undo/redo availability checks."""
    can_undo = song.can_undo()
    can_redo = song.can_redo()

    # These return bools regardless of state
    assert isinstance(can_undo, bool)
    assert isinstance(can_redo, bool)


def test_undo_redo(song):
    """Test undo and redo functionality."""
    # Make a change we can undo
    original_tempo = song.get_tempo()
    new_tempo = 130.0 if original_tempo != 130.0 else 125.0

    song.set_tempo(new_tempo)
    time.sleep(SETTLE_TIME)
    assert song.get_tempo() == new_tempo

    # Undo should revert
    if song.can_undo():
        song.undo()
        time.sleep(SETTLE_TIME)
        # Tempo should be back to original
        assert song.get_tempo() == original_tempo

        # Redo should reapply
        if song.can_redo():
            song.redo()
            time.sleep(SETTLE_TIME)
            assert song.get_tempo() == new_tempo

            # Clean up - undo back to original
            song.undo()
            time.sleep(SETTLE_TIME)


def test_stop_all_clips(song):
    """Test stopping all clips."""
    # Just verify the method executes without error
    # We can't easily verify clips stopped without playing one first
    song.stop_all_clips()


def test_capture_midi(song):
    """Test MIDI capture (just verify no error)."""
    # capture_midi requires recently played MIDI, so we just
    # verify it doesn't raise an exception
    song.capture_midi()


# Scene management tests


def test_create_and_delete_scene(song):
    """Test creating and deleting a scene."""
    original_count = song.get_num_scenes()

    # Create scene at end
    song.create_scene(-1)
    time.sleep(SETTLE_TIME)
    assert song.get_num_scenes() == original_count + 1

    # Delete the new scene
    song.delete_scene(original_count)
    time.sleep(SETTLE_TIME)
    assert song.get_num_scenes() == original_count


def test_duplicate_scene(song):
    """Test duplicating a scene."""
    original_count = song.get_num_scenes()

    # Duplicate scene 0
    song.duplicate_scene(0)
    time.sleep(SETTLE_TIME)
    assert song.get_num_scenes() == original_count + 1

    # Delete the duplicate (it appears at index 1)
    song.delete_scene(1)
    time.sleep(SETTLE_TIME)
    assert song.get_num_scenes() == original_count


def test_get_song_length(song):
    """Test getting song length."""
    length = song.get_song_length()
    assert isinstance(length, float)
    assert length >= 0


# Loop control tests


def test_get_loop(song):
    """Test getting loop state."""
    loop = song.get_loop()
    assert isinstance(loop, bool)


def test_set_loop(song):
    """Test setting loop state."""
    original = song.get_loop()
    try:
        song.set_loop(True)
        time.sleep(SETTLE_TIME)
        assert song.get_loop() is True

        song.set_loop(False)
        time.sleep(SETTLE_TIME)
        assert song.get_loop() is False
    finally:
        song.set_loop(original)


def test_get_loop_start(song):
    """Test getting loop start."""
    start = song.get_loop_start()
    assert isinstance(start, float)
    assert start >= 0


def test_set_loop_start(song):
    """Test setting loop start."""
    original = song.get_loop_start()
    try:
        song.set_loop_start(4.0)
        time.sleep(SETTLE_TIME)
        assert abs(song.get_loop_start() - 4.0) < 0.01
    finally:
        song.set_loop_start(original)


def test_get_loop_length(song):
    """Test getting loop length."""
    length = song.get_loop_length()
    assert isinstance(length, float)
    assert length > 0


def test_set_loop_length(song):
    """Test setting loop length."""
    original = song.get_loop_length()
    try:
        song.set_loop_length(8.0)
        time.sleep(SETTLE_TIME)
        assert abs(song.get_loop_length() - 8.0) < 0.01
    finally:
        song.set_loop_length(original)


# Quantization tests


def test_get_midi_recording_quantization(song):
    """Test getting MIDI recording quantization."""
    quant = song.get_midi_recording_quantization()
    assert isinstance(quant, int)
    assert 0 <= quant <= 8


def test_set_midi_recording_quantization(song):
    """Test setting MIDI recording quantization."""
    original = song.get_midi_recording_quantization()
    try:
        song.set_midi_recording_quantization(2)  # 1/8
        time.sleep(SETTLE_TIME)
        assert song.get_midi_recording_quantization() == 2
    finally:
        song.set_midi_recording_quantization(original)


def test_get_clip_trigger_quantization(song):
    """Test getting clip trigger quantization."""
    quant = song.get_clip_trigger_quantization()
    assert isinstance(quant, int)
    assert 0 <= quant <= 13


def test_set_clip_trigger_quantization(song):
    """Test setting clip trigger quantization."""
    original = song.get_clip_trigger_quantization()
    try:
        song.set_clip_trigger_quantization(4)  # 1 bar
        time.sleep(SETTLE_TIME)
        assert song.get_clip_trigger_quantization() == 4
    finally:
        song.set_clip_trigger_quantization(original)


# Session recording tests


def test_get_session_record(song):
    """Test getting session record state."""
    recording = song.get_session_record()
    assert isinstance(recording, bool)


def test_set_session_record(song):
    """Test setting session record state."""
    original = song.get_session_record()
    try:
        song.set_session_record(False)
        time.sleep(SETTLE_TIME)
        assert song.get_session_record() is False
    finally:
        song.set_session_record(original)


def test_trigger_session_record(song):
    """Test triggering session record (just verify no error)."""
    # Just verify method executes without error
    # Actual recording behavior depends on track state
    song.trigger_session_record()
    time.sleep(SETTLE_TIME)
    # Turn it off to clean up
    song.set_session_record(False)


# Arrangement recording tests


def test_get_arrangement_overdub(song):
    """Test getting arrangement overdub state."""
    overdub = song.get_arrangement_overdub()
    assert isinstance(overdub, bool)


def test_set_arrangement_overdub(song):
    """Test setting arrangement overdub state."""
    original = song.get_arrangement_overdub()
    try:
        song.set_arrangement_overdub(True)
        time.sleep(SETTLE_TIME)
        assert song.get_arrangement_overdub() is True

        song.set_arrangement_overdub(False)
        time.sleep(SETTLE_TIME)
        assert song.get_arrangement_overdub() is False
    finally:
        song.set_arrangement_overdub(original)


# Punch in/out tests


def test_get_punch_in(song):
    """Test getting punch-in state."""
    punch_in = song.get_punch_in()
    assert isinstance(punch_in, bool)


def test_set_punch_in(song):
    """Test setting punch-in state."""
    original = song.get_punch_in()
    try:
        song.set_punch_in(True)
        time.sleep(SETTLE_TIME)
        assert song.get_punch_in() is True

        song.set_punch_in(False)
        time.sleep(SETTLE_TIME)
        assert song.get_punch_in() is False
    finally:
        song.set_punch_in(original)


def test_get_punch_out(song):
    """Test getting punch-out state."""
    punch_out = song.get_punch_out()
    assert isinstance(punch_out, bool)


def test_set_punch_out(song):
    """Test setting punch-out state."""
    original = song.get_punch_out()
    try:
        song.set_punch_out(True)
        time.sleep(SETTLE_TIME)
        assert song.get_punch_out() is True

        song.set_punch_out(False)
        time.sleep(SETTLE_TIME)
        assert song.get_punch_out() is False
    finally:
        song.set_punch_out(original)


# Navigation tests


def test_tap_tempo(song):
    """Test tap tempo (just verify no error)."""
    # Just verify method executes without error
    song.tap_tempo()


def test_jump_by(song):
    """Test jumping by beats (just verify no error)."""
    # jump_by may only work during playback
    # Just verify the method executes without error
    song.jump_by(4.0)
    song.jump_by(-4.0)


def test_jump_to_cues(song):
    """Test jumping to cue points (just verify no error)."""
    # These may not do anything if no cue points exist,
    # but should not raise errors
    song.jump_to_next_cue()
    song.jump_to_prev_cue()


# Cue point tests


def test_get_cue_points(song):
    """Test getting cue points."""
    cue_points = song.get_cue_points()
    assert isinstance(cue_points, tuple)


def test_cue_point_add_and_delete(song):
    """Test adding and deleting cue points."""
    # Get initial cue points
    initial_cues = song.get_cue_points()

    # Set position and add a cue point
    song.set_current_song_time(8.0)
    time.sleep(SETTLE_TIME)
    song.cue_point_add_or_delete()
    time.sleep(SETTLE_TIME)

    # Delete it (calling again at same position deletes)
    song.cue_point_add_or_delete()
    time.sleep(SETTLE_TIME)


# Key and scale tests


def test_get_root_note(song):
    """Test getting root note."""
    root = song.get_root_note()
    assert isinstance(root, int)
    assert 0 <= root <= 11


def test_set_root_note(song):
    """Test setting root note."""
    original = song.get_root_note()
    try:
        song.set_root_note(2)  # D
        time.sleep(SETTLE_TIME)
        assert song.get_root_note() == 2

        song.set_root_note(0)  # C
        time.sleep(SETTLE_TIME)
        assert song.get_root_note() == 0
    finally:
        song.set_root_note(original)


def test_get_scale_name(song):
    """Test getting scale name."""
    scale = song.get_scale_name()
    assert isinstance(scale, str)


def test_set_scale_name(song):
    """Test setting scale name."""
    original = song.get_scale_name()
    try:
        song.set_scale_name("Minor")
        time.sleep(SETTLE_TIME)
        assert song.get_scale_name() == "Minor"

        song.set_scale_name("Major")
        time.sleep(SETTLE_TIME)
        assert song.get_scale_name() == "Major"
    finally:
        song.set_scale_name(original)


# Bulk query tests


def test_get_track_names(song):
    """Test getting track names."""
    names = song.get_track_names()
    assert isinstance(names, tuple)
    # Should have at least one track name
    assert len(names) >= 1
    for name in names:
        assert isinstance(name, str)


def test_get_track_names_range(song):
    """Test getting track names with range."""
    num_tracks = song.get_num_tracks()
    if num_tracks >= 2:
        # Get first 2 tracks
        names = song.get_track_names(0, 2)
        assert len(names) == 2


def test_get_back_to_arranger(song):
    """Test getting back-to-arranger state."""
    back_to_arranger = song.get_back_to_arranger()
    assert isinstance(back_to_arranger, bool)


def test_set_back_to_arranger(song):
    """Test triggering back-to-arranger."""
    # Just verify the method executes without error
    # Setting to True triggers the back-to-arranger action
    song.set_back_to_arranger(True)
    time.sleep(SETTLE_TIME)
    # State should be False after triggering (it's a one-shot action)


def test_nudge_down(song):
    """Test nudge down (just verify no error)."""
    # Nudge is a momentary action, just verify it executes
    song.nudge_down()


def test_nudge_up(song):
    """Test nudge up (just verify no error)."""
    # Nudge is a momentary action, just verify it executes
    song.nudge_up()


# Listener tests


def test_on_tempo_change(song):
    """Test tempo change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(tempo):
        received_value[0] = tempo
        received.set()

    original = song.get_tempo()
    new_tempo = 130.0 if original != 130.0 else 125.0
    try:
        song.on_tempo_change(callback)
        # Wait for initial callback (listener sends current value when started)
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        song.set_tempo(new_tempo)
        assert received.wait(timeout=2.0), "Tempo callback not triggered"
        assert received_value[0] == new_tempo
    finally:
        song.stop_tempo_listener()
        song.set_tempo(original)


def test_on_is_playing_change(song):
    """Test is_playing change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(is_playing):
        received_value[0] = is_playing
        received.set()

    original = song.get_is_playing()
    try:
        song.on_is_playing_change(callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        if original:
            song.stop_playing()
        else:
            song.start_playing()
        assert received.wait(timeout=2.0), "is_playing callback not triggered"
        assert received_value[0] == (not original)
    finally:
        song.stop_is_playing_listener()
        if original:
            song.start_playing()
        else:
            song.stop_playing()


def test_on_loop_change(song):
    """Test loop change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(enabled):
        received_value[0] = enabled
        received.set()

    original = song.get_loop()
    try:
        song.on_loop_change(callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        song.set_loop(not original)
        assert received.wait(timeout=2.0), "Loop callback not triggered"
        assert received_value[0] == (not original)
    finally:
        song.stop_loop_listener()
        song.set_loop(original)


def test_on_record_mode_change(song):
    """Test record mode change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(enabled):
        received_value[0] = enabled
        received.set()

    original = song.get_record_mode()
    try:
        song.on_record_mode_change(callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        song.set_record_mode(not original)
        assert received.wait(timeout=2.0), "Record mode callback not triggered"
        assert received_value[0] == (not original)
    finally:
        song.stop_record_mode_listener()
        song.set_record_mode(original)


def test_on_beat(song):
    """Test beat listener (requires playback)."""
    received = threading.Event()
    received_value = [None]

    def callback(beat):
        received_value[0] = beat
        received.set()

    original_playing = song.get_is_playing()
    try:
        song.on_beat(callback)
        time.sleep(SETTLE_TIME)  # Let listener establish
        song.start_playing()
        # Beat listener should fire within ~1 beat (depends on tempo)
        assert received.wait(timeout=3.0), "Beat callback not triggered"
        assert isinstance(received_value[0], int)
    finally:
        song.stop_beat_listener()
        if not original_playing:
            song.stop_playing()


def test_on_current_song_time_change(song):
    """Test current song time change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(beats):
        received_value[0] = beats
        received.set()

    original_playing = song.get_is_playing()
    try:
        song.on_current_song_time_change(callback)
        time.sleep(SETTLE_TIME)  # Let listener establish
        song.start_playing()
        # Should receive position updates during playback
        assert received.wait(timeout=2.0), "Current song time callback not triggered"
        assert isinstance(received_value[0], float)
    finally:
        song.stop_current_song_time_listener()
        if not original_playing:
            song.stop_playing()


# New endpoint tests (Gap Coverage)


def test_get_session_record_status(song):
    """Test getting session record status."""
    status = song.get_session_record_status()
    assert isinstance(status, int)
    # 0=Off, 1=On, 2=Transition
    assert 0 <= status <= 2


def test_get_beat(song):
    """Test getting current beat."""
    beat = song.get_beat()
    assert isinstance(beat, float)
