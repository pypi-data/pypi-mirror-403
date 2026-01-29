"""Tests for Track operations."""

import threading
import time

SETTLE_TIME = 0.1  # Time for Ableton to process changes


def test_get_name(track):
    """Test getting track name."""
    name = track.get_name(0)
    assert isinstance(name, str)


def test_set_name(track):
    """Test setting track name."""
    original = track.get_name(0)
    try:
        track.set_name(0, "Test Track")
        time.sleep(SETTLE_TIME)
        assert track.get_name(0) == "Test Track"
    finally:
        track.set_name(0, original)


def test_get_volume(track):
    """Test getting track volume."""
    volume = track.get_volume(0)
    assert 0.0 <= volume <= 1.0


def test_set_volume(track):
    """Test setting track volume."""
    original = track.get_volume(0)
    try:
        track.set_volume(0, 0.5)
        time.sleep(SETTLE_TIME)
        assert abs(track.get_volume(0) - 0.5) < 0.01

        track.set_volume(0, 0.85)  # 0dB
        time.sleep(SETTLE_TIME)
        assert abs(track.get_volume(0) - 0.85) < 0.01
    finally:
        track.set_volume(0, original)


def test_get_panning(track):
    """Test getting track pan."""
    pan = track.get_panning(0)
    assert -1.0 <= pan <= 1.0


def test_set_panning(track):
    """Test setting track pan."""
    original = track.get_panning(0)
    try:
        track.set_panning(0, -0.5)  # Pan left
        time.sleep(SETTLE_TIME)
        assert abs(track.get_panning(0) - (-0.5)) < 0.01

        track.set_panning(0, 0.5)  # Pan right
        time.sleep(SETTLE_TIME)
        assert abs(track.get_panning(0) - 0.5) < 0.01

        track.set_panning(0, 0.0)  # Center
        time.sleep(SETTLE_TIME)
        assert abs(track.get_panning(0)) < 0.01
    finally:
        track.set_panning(0, original)


def test_get_mute(track):
    """Test getting track mute state."""
    muted = track.get_mute(0)
    assert isinstance(muted, bool)


def test_set_mute(track):
    """Test muting/unmuting track."""
    original = track.get_mute(0)
    try:
        track.set_mute(0, True)
        time.sleep(SETTLE_TIME)
        assert track.get_mute(0) is True

        track.set_mute(0, False)
        time.sleep(SETTLE_TIME)
        assert track.get_mute(0) is False
    finally:
        track.set_mute(0, original)


def test_get_solo(track):
    """Test getting track solo state."""
    soloed = track.get_solo(0)
    assert isinstance(soloed, bool)


def test_set_solo(track):
    """Test soloing/unsoloing track."""
    original = track.get_solo(0)
    try:
        track.set_solo(0, True)
        time.sleep(SETTLE_TIME)
        assert track.get_solo(0) is True

        track.set_solo(0, False)
        time.sleep(SETTLE_TIME)
        assert track.get_solo(0) is False
    finally:
        track.set_solo(0, original)


def test_get_arm(track):
    """Test getting track arm state."""
    armed = track.get_arm(0)
    assert isinstance(armed, bool)


def test_get_color(track):
    """Test getting track color."""
    color = track.get_color(0)
    assert isinstance(color, int)


def test_get_num_devices(track):
    """Test getting device count on track."""
    num_devices = track.get_num_devices(0)
    assert num_devices >= 0


def test_get_send(song, track):
    """Test getting send level (requires return track)."""
    # Create a return track if needed
    original_tracks = song.get_num_tracks()
    song.create_return_track()
    time.sleep(SETTLE_TIME)

    try:
        # Get send 0 level on track 0
        send_level = track.get_send(0, 0)
        assert 0.0 <= send_level <= 1.0
    finally:
        # Clean up - delete the return track
        song.delete_return_track(0)
        time.sleep(SETTLE_TIME)


def test_set_send(song, track):
    """Test setting send level (requires return track)."""
    # Create a return track
    song.create_return_track()
    time.sleep(SETTLE_TIME)

    try:
        original = track.get_send(0, 0)

        track.set_send(0, 0, 0.5)
        time.sleep(SETTLE_TIME)
        assert abs(track.get_send(0, 0) - 0.5) < 0.01

        track.set_send(0, 0, 0.0)
        time.sleep(SETTLE_TIME)
        assert abs(track.get_send(0, 0)) < 0.01

        # Restore
        track.set_send(0, 0, original)
    finally:
        # Clean up - delete the return track
        song.delete_return_track(0)
        time.sleep(SETTLE_TIME)


def test_stop_all_clips(track):
    """Test stopping all clips on a track."""
    # Just verify the method executes without error
    track.stop_all_clips(0)


def test_insert_device(song, track):
    """Test inserting a device onto a track.

    Creates a MIDI track, inserts Wavetable, verifies it appears,
    then cleans up.
    """
    original_tracks = song.get_num_tracks()
    track_idx = original_tracks  # New track will be at this index

    # Create MIDI track at end
    song.create_midi_track(-1)
    time.sleep(SETTLE_TIME)

    try:
        # Insert Wavetable onto the track
        device_idx = track.insert_device(track_idx, "Wavetable")
        time.sleep(SETTLE_TIME)

        # Verify device was inserted
        assert device_idx >= 0, "Device insertion failed"

        # Verify device count increased
        num_devices = track.get_num_devices(track_idx)
        assert num_devices >= 1, "Device not found on track"

        # Verify device name
        device_names = track.get_device_names(track_idx)
        assert "Wavetable" in device_names, f"Wavetable not in {device_names}"
    finally:
        # Cleanup - delete the track
        song.delete_track(track_idx)
        time.sleep(SETTLE_TIME)


def test_insert_audio_effect(song, track):
    """Test inserting an audio effect onto a track."""
    original_tracks = song.get_num_tracks()
    track_idx = original_tracks

    # Create audio track
    song.create_audio_track(-1)
    time.sleep(SETTLE_TIME)

    try:
        # Insert Compressor (more unique name than Reverb)
        device_idx = track.insert_device(track_idx, "Compressor")
        time.sleep(SETTLE_TIME)

        assert device_idx >= 0, "Compressor insertion failed"

        device_names = track.get_device_names(track_idx)
        assert any("Compressor" in name for name in device_names), (
            f"Compressor not in {device_names}"
        )
    finally:
        song.delete_track(track_idx)
        time.sleep(SETTLE_TIME)


def test_insert_nonexistent_device(song, track):
    """Test that inserting a nonexistent device returns -1."""
    original_tracks = song.get_num_tracks()
    track_idx = original_tracks

    song.create_midi_track(-1)
    time.sleep(SETTLE_TIME)

    try:
        device_idx = track.insert_device(track_idx, "NonexistentDevice12345")
        time.sleep(SETTLE_TIME)

        assert device_idx == -1, "Should return -1 for nonexistent device"
    finally:
        song.delete_track(track_idx)
        time.sleep(SETTLE_TIME)


def test_get_device_names(song, track):
    """Test getting device names from a track."""
    original_tracks = song.get_num_tracks()
    track_idx = original_tracks

    song.create_midi_track(-1)
    time.sleep(SETTLE_TIME)

    try:
        # Empty track should have no devices
        device_names = track.get_device_names(track_idx)
        assert isinstance(device_names, tuple)

        # Add a device
        track.insert_device(track_idx, "Wavetable")
        time.sleep(SETTLE_TIME)

        device_names = track.get_device_names(track_idx)
        assert len(device_names) >= 1
    finally:
        song.delete_track(track_idx)
        time.sleep(SETTLE_TIME)


def test_delete_device(song, track):
    """Test deleting a device from a track."""
    original_tracks = song.get_num_tracks()
    track_idx = original_tracks

    song.create_midi_track(-1)
    time.sleep(SETTLE_TIME)

    try:
        # Add device
        track.insert_device(track_idx, "Wavetable")
        time.sleep(SETTLE_TIME)

        initial_count = track.get_num_devices(track_idx)
        assert initial_count >= 1

        # Delete device
        track.delete_device(track_idx, 0)
        time.sleep(SETTLE_TIME)

        final_count = track.get_num_devices(track_idx)
        assert final_count == initial_count - 1
    finally:
        song.delete_track(track_idx)
        time.sleep(SETTLE_TIME)


# Routing tests


def test_get_input_routing_type(track):
    """Test getting input routing type."""
    routing_type = track.get_input_routing_type(0)
    assert isinstance(routing_type, str)


def test_get_input_routing_channel(track):
    """Test getting input routing channel."""
    channel = track.get_input_routing_channel(0)
    assert isinstance(channel, str)


def test_get_output_routing_type(track):
    """Test getting output routing type."""
    routing_type = track.get_output_routing_type(0)
    assert isinstance(routing_type, str)


def test_get_output_routing_channel(track):
    """Test getting output routing channel."""
    channel = track.get_output_routing_channel(0)
    assert isinstance(channel, str)


def test_get_available_input_routing_types(track):
    """Test getting available input routing types."""
    types = track.get_available_input_routing_types(0)
    assert isinstance(types, tuple)


def test_get_available_output_routing_types(track):
    """Test getting available output routing types."""
    types = track.get_available_output_routing_types(0)
    assert isinstance(types, tuple)


# Monitoring tests


def test_get_current_monitoring_state(track):
    """Test getting current monitoring state."""
    state = track.get_current_monitoring_state(0)
    assert isinstance(state, int)
    assert state in (0, 1, 2)  # In, Auto, Off


# Track capability tests


def test_get_can_be_armed(track):
    """Test checking if track can be armed."""
    can_arm = track.get_can_be_armed(0)
    assert isinstance(can_arm, bool)


def test_get_has_midi_input(track):
    """Test checking if track has MIDI input."""
    has_midi = track.get_has_midi_input(0)
    assert isinstance(has_midi, bool)


def test_get_has_midi_output(track):
    """Test checking if track has MIDI output."""
    has_midi = track.get_has_midi_output(0)
    assert isinstance(has_midi, bool)


def test_get_has_audio_input(track):
    """Test checking if track has audio input."""
    has_audio = track.get_has_audio_input(0)
    assert isinstance(has_audio, bool)


def test_get_has_audio_output(track):
    """Test checking if track has audio output."""
    has_audio = track.get_has_audio_output(0)
    assert isinstance(has_audio, bool)


# Track state tests


def test_get_fired_slot_index(track):
    """Test getting fired slot index."""
    slot_idx = track.get_fired_slot_index(0)
    assert isinstance(slot_idx, int)


def test_get_playing_slot_index(track):
    """Test getting playing slot index."""
    slot_idx = track.get_playing_slot_index(0)
    assert isinstance(slot_idx, int)


def test_get_color_index(track):
    """Test getting track color index."""
    color_idx = track.get_color_index(0)
    assert isinstance(color_idx, int)
    assert 0 <= color_idx <= 69


def test_set_color_index(track):
    """Test setting track color index."""
    original = track.get_color_index(0)
    try:
        track.set_color_index(0, 5)
        time.sleep(SETTLE_TIME)
        assert track.get_color_index(0) == 5
    finally:
        track.set_color_index(0, original)


def test_get_is_visible(track):
    """Test checking if track is visible."""
    is_visible = track.get_is_visible(0)
    assert isinstance(is_visible, bool)


# Meter tests


def test_get_output_meter_level(track):
    """Test getting output meter level."""
    level = track.get_output_meter_level(0)
    assert isinstance(level, float)
    assert 0.0 <= level <= 1.0


def test_get_output_meter_left(track):
    """Test getting left output meter level."""
    level = track.get_output_meter_left(0)
    assert isinstance(level, float)
    assert 0.0 <= level <= 1.0


def test_get_output_meter_right(track):
    """Test getting right output meter level."""
    level = track.get_output_meter_right(0)
    assert isinstance(level, float)
    assert 0.0 <= level <= 1.0


# Listener tests


def test_on_volume_change(track):
    """Test volume change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(track_idx, volume):
        received_value[0] = (track_idx, volume)
        received.set()

    original = track.get_volume(0)
    new_volume = 0.5 if abs(original - 0.5) > 0.1 else 0.7
    try:
        track.on_volume_change(0, callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        track.set_volume(0, new_volume)
        assert received.wait(timeout=2.0), "Volume callback not triggered"
        assert received_value[0][0] == 0  # track index
        assert abs(received_value[0][1] - new_volume) < 0.01  # volume value
    finally:
        track.stop_volume_listener(0)
        track.set_volume(0, original)


def test_on_mute_change(track):
    """Test mute change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(track_idx, muted):
        received_value[0] = (track_idx, muted)
        received.set()

    original = track.get_mute(0)
    try:
        track.on_mute_change(0, callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        track.set_mute(0, not original)
        assert received.wait(timeout=2.0), "Mute callback not triggered"
        assert received_value[0][0] == 0  # track index
        assert received_value[0][1] == (not original)  # muted value
    finally:
        track.stop_mute_listener(0)
        track.set_mute(0, original)


def test_on_solo_change(track):
    """Test solo change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(track_idx, soloed):
        received_value[0] = (track_idx, soloed)
        received.set()

    original = track.get_solo(0)
    try:
        track.on_solo_change(0, callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        track.set_solo(0, not original)
        assert received.wait(timeout=2.0), "Solo callback not triggered"
        assert received_value[0][0] == 0  # track index
        assert received_value[0][1] == (not original)  # soloed value
    finally:
        track.stop_solo_listener(0)
        track.set_solo(0, original)


def test_on_panning_change(track):
    """Test panning change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(track_idx, pan):
        received_value[0] = (track_idx, pan)
        received.set()

    original = track.get_panning(0)
    new_pan = 0.5 if abs(original - 0.5) > 0.1 else -0.5
    try:
        track.on_panning_change(0, callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        track.set_panning(0, new_pan)
        assert received.wait(timeout=2.0), "Panning callback not triggered"
        assert received_value[0][0] == 0  # track index
        assert abs(received_value[0][1] - new_pan) < 0.01  # pan value
    finally:
        track.stop_panning_listener(0)
        track.set_panning(0, original)


def test_on_name_change(track):
    """Test name change listener."""
    received = threading.Event()
    received_value = [None]

    def callback(track_idx, name):
        received_value[0] = (track_idx, name)
        received.set()

    original = track.get_name(0)
    new_name = "Test Track Listener"
    try:
        track.on_name_change(0, callback)
        # Wait for initial callback
        received.wait(timeout=2.0)
        received.clear()
        received_value[0] = None

        track.set_name(0, new_name)
        assert received.wait(timeout=2.0), "Name callback not triggered"
        assert received_value[0][0] == 0  # track index
        assert received_value[0][1] == new_name  # name value
    finally:
        track.stop_name_listener(0)
        track.set_name(0, original)


def test_multiple_track_listeners(track):
    """Test listening to the same property on multiple tracks."""
    received_0 = threading.Event()
    received_1 = threading.Event()
    values = [None, None]

    def callback_0(track_idx, volume):
        values[0] = (track_idx, volume)
        received_0.set()

    def callback_1(track_idx, volume):
        values[1] = (track_idx, volume)
        received_1.set()

    original_0 = track.get_volume(0)
    original_1 = track.get_volume(1) if track.get_num_devices(1) >= 0 else None

    # This test requires at least 2 tracks
    try:
        num_devices_1 = track.get_num_devices(1)  # Will fail if track 1 doesn't exist
    except Exception:
        return  # Skip if only 1 track

    try:
        track.on_volume_change(0, callback_0)
        track.on_volume_change(1, callback_1)
        time.sleep(SETTLE_TIME)

        # Change track 0 volume
        track.set_volume(0, 0.4)
        assert received_0.wait(timeout=2.0), "Track 0 volume callback not triggered"
        assert values[0][0] == 0

        # Change track 1 volume
        track.set_volume(1, 0.6)
        assert received_1.wait(timeout=2.0), "Track 1 volume callback not triggered"
        assert values[1][0] == 1
    finally:
        track.stop_volume_listener(0)
        track.stop_volume_listener(1)
        track.set_volume(0, original_0)
        if original_1 is not None:
            track.set_volume(1, original_1)


# New endpoint tests (Gap Coverage)


def test_set_current_monitoring_state(track):
    """Test setting current monitoring state."""
    original = track.get_current_monitoring_state(0)
    try:
        # 0=In, 1=Auto, 2=Off
        track.set_current_monitoring_state(0, 1)
        assert track.get_current_monitoring_state(0) == 1
    finally:
        track.set_current_monitoring_state(0, original)


def test_get_available_input_routing_channels(track):
    """Test getting available input routing channels."""
    channels = track.get_available_input_routing_channels(0)
    assert isinstance(channels, tuple)


def test_get_available_output_routing_channels(track):
    """Test getting available output routing channels."""
    channels = track.get_available_output_routing_channels(0)
    assert isinstance(channels, tuple)


def test_get_clips_names(track):
    """Test getting bulk clip names for a track."""
    names = track.get_clips_names(0)
    assert isinstance(names, tuple)


def test_get_clips_lengths(track):
    """Test getting bulk clip lengths for a track."""
    lengths = track.get_clips_lengths(0)
    assert isinstance(lengths, tuple)


def test_get_clips_colors(track):
    """Test getting bulk clip colors for a track."""
    colors = track.get_clips_colors(0)
    assert isinstance(colors, tuple)


def test_get_devices_class_names(track):
    """Test getting bulk device class names for a track."""
    class_names = track.get_devices_class_names(0)
    assert isinstance(class_names, tuple)
