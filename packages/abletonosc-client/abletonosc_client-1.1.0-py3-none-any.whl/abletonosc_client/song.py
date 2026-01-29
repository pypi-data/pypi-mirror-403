"""Song-level operations for AbletonOSC.

Covers /live/song/* endpoints for global song properties and transport.
"""

from typing import Callable

from abletonosc_client.client import AbletonOSCClient


class Song:
    """Song-level operations like tempo, transport, and song structure."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client

    # Tempo

    def get_tempo(self) -> float:
        """Get the current song tempo in BPM.

        Returns:
            Tempo in beats per minute (20-999)
        """
        result = self._client.query("/live/song/get/tempo")
        return float(result[0])

    def set_tempo(self, bpm: float) -> None:
        """Set the song tempo.

        Args:
            bpm: Tempo in beats per minute (20-999)
        """
        self._client.send("/live/song/set/tempo", float(bpm))

    # Transport

    def get_is_playing(self) -> bool:
        """Check if the song is currently playing.

        Returns:
            True if playing, False if stopped
        """
        result = self._client.query("/live/song/get/is_playing")
        return bool(result[0])

    def start_playing(self) -> None:
        """Start playback."""
        self._client.send("/live/song/start_playing")

    def stop_playing(self) -> None:
        """Stop playback."""
        self._client.send("/live/song/stop_playing")

    def continue_playing(self) -> None:
        """Continue playback from current position."""
        self._client.send("/live/song/continue_playing")

    # Time signature

    def get_signature_numerator(self) -> int:
        """Get the time signature numerator.

        Returns:
            Time signature numerator (e.g., 4 for 4/4)
        """
        result = self._client.query("/live/song/get/signature_numerator")
        return int(result[0])

    def get_signature_denominator(self) -> int:
        """Get the time signature denominator.

        Returns:
            Time signature denominator (e.g., 4 for 4/4)
        """
        result = self._client.query("/live/song/get/signature_denominator")
        return int(result[0])

    def set_signature_numerator(self, numerator: int) -> None:
        """Set the time signature numerator.

        Args:
            numerator: Time signature numerator
        """
        self._client.send("/live/song/set/signature_numerator", int(numerator))

    def set_signature_denominator(self, denominator: int) -> None:
        """Set the time signature denominator.

        Args:
            denominator: Time signature denominator (must be power of 2)
        """
        self._client.send("/live/song/set/signature_denominator", int(denominator))

    # Song structure

    def get_num_tracks(self) -> int:
        """Get the number of tracks in the song.

        Returns:
            Number of tracks (including return tracks and master)
        """
        result = self._client.query("/live/song/get/num_tracks")
        return int(result[0])

    def get_num_scenes(self) -> int:
        """Get the number of scenes in the song.

        Returns:
            Number of scenes
        """
        result = self._client.query("/live/song/get/num_scenes")
        return int(result[0])

    # Position

    def get_current_song_time(self) -> float:
        """Get the current playback position in beats.

        Returns:
            Current position in beats
        """
        result = self._client.query("/live/song/get/current_song_time")
        return float(result[0])

    def set_current_song_time(self, beats: float) -> None:
        """Set the playback position.

        Args:
            beats: Position in beats
        """
        self._client.send("/live/song/set/current_song_time", float(beats))

    # Metronome

    def get_metronome(self) -> bool:
        """Check if the metronome is enabled.

        Returns:
            True if metronome is on
        """
        result = self._client.query("/live/song/get/metronome")
        return bool(result[0])

    def set_metronome(self, enabled: bool) -> None:
        """Enable or disable the metronome.

        Args:
            enabled: True to enable metronome
        """
        self._client.send("/live/song/set/metronome", int(enabled))

    # Record

    def get_record_mode(self) -> bool:
        """Check if record mode is enabled.

        Returns:
            True if record mode is on
        """
        result = self._client.query("/live/song/get/record_mode")
        return bool(result[0])

    def set_record_mode(self, enabled: bool) -> None:
        """Enable or disable record mode.

        Args:
            enabled: True to enable record mode
        """
        self._client.send("/live/song/set/record_mode", int(enabled))

    # Listeners

    def on_tempo_change(self, callback: Callable[[float], None]) -> None:
        """Register a callback for tempo changes.

        Args:
            callback: Function(tempo) called when tempo changes
        """
        self._client.send("/live/song/start_listen/tempo")
        self._client.start_listener(
            "/live/song/get/tempo", lambda addr, *args: callback(float(args[0]))
        )

    def stop_tempo_listener(self) -> None:
        """Stop listening for tempo changes."""
        self._client.send("/live/song/stop_listen/tempo")
        self._client.stop_listener("/live/song/get/tempo")

    def on_is_playing_change(self, callback: Callable[[bool], None]) -> None:
        """Register a callback for play state changes.

        Args:
            callback: Function(is_playing) called when play state changes
        """
        self._client.send("/live/song/start_listen/is_playing")
        self._client.start_listener(
            "/live/song/get/is_playing", lambda addr, *args: callback(bool(args[0]))
        )

    def stop_is_playing_listener(self) -> None:
        """Stop listening for play state changes."""
        self._client.send("/live/song/stop_listen/is_playing")
        self._client.stop_listener("/live/song/get/is_playing")

    # Track management

    def create_midi_track(self, index: int = -1) -> None:
        """Create a new MIDI track.

        Args:
            index: Position to insert track (-1 appends to end)
        """
        self._client.send("/live/song/create_midi_track", index)

    def create_audio_track(self, index: int = -1) -> None:
        """Create a new audio track.

        Args:
            index: Position to insert track (-1 appends to end)
        """
        self._client.send("/live/song/create_audio_track", index)

    def create_return_track(self) -> None:
        """Create a new return track."""
        self._client.send("/live/song/create_return_track")

    def delete_track(self, index: int) -> None:
        """Delete track at index.

        Args:
            index: Track index to delete (0-based)
        """
        self._client.send("/live/song/delete_track", index)

    def delete_return_track(self, index: int) -> None:
        """Delete return track at index.

        Args:
            index: Return track index to delete (0-based)
        """
        self._client.send("/live/song/delete_return_track", index)

    def duplicate_track(self, index: int) -> None:
        """Duplicate track at index.

        Args:
            index: Track index to duplicate (0-based)
        """
        self._client.send("/live/song/duplicate_track", index)

    # Groove

    def get_groove_amount(self) -> float:
        """Get the global groove amount.

        Returns:
            Groove amount (0.0-1.0)
        """
        result = self._client.query("/live/song/get/groove_amount")
        return float(result[0])

    def set_groove_amount(self, amount: float) -> None:
        """Set the global groove amount.

        Args:
            amount: Groove amount (0.0-1.0)
        """
        self._client.send("/live/song/set/groove_amount", float(amount))

    # Undo/Redo

    def undo(self) -> None:
        """Undo the last action."""
        self._client.send("/live/song/undo")

    def redo(self) -> None:
        """Redo the last undone action."""
        self._client.send("/live/song/redo")

    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if undo is possible
        """
        result = self._client.query("/live/song/get/can_undo")
        return bool(result[0])

    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if redo is possible
        """
        result = self._client.query("/live/song/get/can_redo")
        return bool(result[0])

    # Clip control

    def stop_all_clips(self) -> None:
        """Stop all playing clips in the session."""
        self._client.send("/live/song/stop_all_clips")

    # MIDI capture

    def capture_midi(self) -> None:
        """Capture recently played MIDI notes into a clip.

        Creates a new clip from MIDI notes that were played
        while not recording (requires armed track).
        """
        self._client.send("/live/song/capture_midi")

    # Scene management

    def create_scene(self, index: int = -1) -> None:
        """Create a new scene.

        Args:
            index: Position to insert scene (-1 appends to end)
        """
        self._client.send("/live/song/create_scene", index)

    def delete_scene(self, index: int) -> None:
        """Delete scene at index.

        Args:
            index: Scene index to delete (0-based)
        """
        self._client.send("/live/song/delete_scene", index)

    def duplicate_scene(self, index: int) -> None:
        """Duplicate scene at index.

        Args:
            index: Scene index to duplicate (0-based)
        """
        self._client.send("/live/song/duplicate_scene", index)

    def get_song_length(self) -> float:
        """Get the total song length in beats.

        Returns:
            Song length in beats
        """
        result = self._client.query("/live/song/get/song_length")
        return float(result[0])

    # Loop control

    def get_loop(self) -> bool:
        """Check if loop is enabled.

        Returns:
            True if loop is enabled
        """
        result = self._client.query("/live/song/get/loop")
        return bool(result[0])

    def set_loop(self, enabled: bool) -> None:
        """Enable or disable loop.

        Args:
            enabled: True to enable loop
        """
        self._client.send("/live/song/set/loop", int(enabled))

    def get_loop_start(self) -> float:
        """Get the loop start position in beats.

        Returns:
            Loop start position in beats
        """
        result = self._client.query("/live/song/get/loop_start")
        return float(result[0])

    def set_loop_start(self, beats: float) -> None:
        """Set the loop start position.

        Args:
            beats: Loop start position in beats
        """
        self._client.send("/live/song/set/loop_start", float(beats))

    def get_loop_length(self) -> float:
        """Get the loop length in beats.

        Returns:
            Loop length in beats
        """
        result = self._client.query("/live/song/get/loop_length")
        return float(result[0])

    def set_loop_length(self, beats: float) -> None:
        """Set the loop length.

        Args:
            beats: Loop length in beats
        """
        self._client.send("/live/song/set/loop_length", float(beats))

    # Quantization

    def get_midi_recording_quantization(self) -> int:
        """Get the MIDI recording quantization setting.

        Returns:
            Quantization value (0=None, 1=1/4, 2=1/8, 3=1/8T, 4=1/8+1/8T,
            5=1/16, 6=1/16T, 7=1/16+1/16T, 8=1/32)
        """
        result = self._client.query("/live/song/get/midi_recording_quantization")
        return int(result[0])

    def set_midi_recording_quantization(self, value: int) -> None:
        """Set the MIDI recording quantization.

        Args:
            value: Quantization value (0=None, 1=1/4, 2=1/8, 3=1/8T, 4=1/8+1/8T,
                   5=1/16, 6=1/16T, 7=1/16+1/16T, 8=1/32)
        """
        self._client.send("/live/song/set/midi_recording_quantization", int(value))

    def get_clip_trigger_quantization(self) -> int:
        """Get the clip trigger quantization setting.

        Returns:
            Quantization value (0=None, 1=8 bars, 2=4 bars, 3=2 bars,
            4=1 bar, 5=1/2, 6=1/2T, 7=1/4, 8=1/4T, 9=1/8, 10=1/8T,
            11=1/16, 12=1/16T, 13=1/32)
        """
        result = self._client.query("/live/song/get/clip_trigger_quantization")
        return int(result[0])

    def set_clip_trigger_quantization(self, value: int) -> None:
        """Set the clip trigger quantization.

        Args:
            value: Quantization value (0=None, 1=8 bars, 2=4 bars, 3=2 bars,
                   4=1 bar, 5=1/2, 6=1/2T, 7=1/4, 8=1/4T, 9=1/8, 10=1/8T,
                   11=1/16, 12=1/16T, 13=1/32)
        """
        self._client.send("/live/song/set/clip_trigger_quantization", int(value))

    # Session recording

    def trigger_session_record(self) -> None:
        """Trigger session recording.

        Starts recording into the session view.
        """
        self._client.send("/live/song/trigger_session_record")

    def get_session_record(self) -> bool:
        """Check if session recording is enabled.

        Returns:
            True if session recording is enabled
        """
        result = self._client.query("/live/song/get/session_record")
        return bool(result[0])

    def set_session_record(self, enabled: bool) -> None:
        """Enable or disable session recording.

        Args:
            enabled: True to enable session recording
        """
        self._client.send("/live/song/set/session_record", int(enabled))

    # Arrangement recording

    def get_arrangement_overdub(self) -> bool:
        """Check if arrangement overdub is enabled.

        Returns:
            True if arrangement overdub is enabled
        """
        result = self._client.query("/live/song/get/arrangement_overdub")
        return bool(result[0])

    def set_arrangement_overdub(self, enabled: bool) -> None:
        """Enable or disable arrangement overdub.

        Args:
            enabled: True to enable arrangement overdub
        """
        self._client.send("/live/song/set/arrangement_overdub", int(enabled))

    # Punch in/out

    def get_punch_in(self) -> bool:
        """Check if punch-in is enabled.

        Returns:
            True if punch-in is enabled
        """
        result = self._client.query("/live/song/get/punch_in")
        return bool(result[0])

    def set_punch_in(self, enabled: bool) -> None:
        """Enable or disable punch-in.

        Args:
            enabled: True to enable punch-in
        """
        self._client.send("/live/song/set/punch_in", int(enabled))

    def get_punch_out(self) -> bool:
        """Check if punch-out is enabled.

        Returns:
            True if punch-out is enabled
        """
        result = self._client.query("/live/song/get/punch_out")
        return bool(result[0])

    def set_punch_out(self, enabled: bool) -> None:
        """Enable or disable punch-out.

        Args:
            enabled: True to enable punch-out
        """
        self._client.send("/live/song/set/punch_out", int(enabled))

    # Navigation

    def tap_tempo(self) -> None:
        """Tap tempo - call repeatedly to set tempo by tapping."""
        self._client.send("/live/song/tap_tempo")

    def jump_by(self, beats: float) -> None:
        """Jump forward or backward by a number of beats.

        Args:
            beats: Number of beats to jump (negative to go backward)
        """
        self._client.send("/live/song/jump_by", float(beats))

    def jump_to_next_cue(self) -> None:
        """Jump to the next cue point."""
        self._client.send("/live/song/jump_to_next_cue")

    def jump_to_prev_cue(self) -> None:
        """Jump to the previous cue point."""
        self._client.send("/live/song/jump_to_prev_cue")

    # Cue points

    def get_cue_points(self) -> tuple:
        """Get all cue points in the song.

        Returns:
            Tuple of cue point data (name, time pairs)
        """
        result = self._client.query("/live/song/get/cue_points")
        return result

    def cue_point_jump(self, cue_index: int) -> None:
        """Jump to a specific cue point by index.

        Args:
            cue_index: Cue point index (0-based)
        """
        self._client.send("/live/song/cue_point/jump", cue_index)

    def cue_point_add_or_delete(self) -> None:
        """Add or delete a cue point at the current position.

        If a cue point exists at the current position, it will be deleted.
        Otherwise, a new cue point will be created.
        """
        self._client.send("/live/song/cue_point/add_or_delete")

    def cue_point_set_name(self, cue_index: int, name: str) -> None:
        """Set the name of a cue point.

        Args:
            cue_index: Cue point index (0-based)
            name: New name for the cue point
        """
        self._client.send("/live/song/cue_point/set/name", cue_index, name)

    # Key and scale

    def get_root_note(self) -> int:
        """Get the root note of the song's key.

        Returns:
            Root note as MIDI note number (0-11, where 0=C, 1=C#, etc.)
        """
        result = self._client.query("/live/song/get/root_note")
        return int(result[0])

    def set_root_note(self, note: int) -> None:
        """Set the root note of the song's key.

        Args:
            note: Root note as MIDI note number (0-11, where 0=C, 1=C#, etc.)
        """
        self._client.send("/live/song/set/root_note", int(note))

    def get_scale_name(self) -> str:
        """Get the scale name of the song.

        Returns:
            Scale name (e.g., "Major", "Minor", "Dorian")
        """
        result = self._client.query("/live/song/get/scale_name")
        return str(result[0])

    def set_scale_name(self, name: str) -> None:
        """Set the scale name of the song.

        Args:
            name: Scale name (e.g., "Major", "Minor", "Dorian")
        """
        self._client.send("/live/song/set/scale_name", name)

    # Bulk queries

    def get_track_names(self, start: int = 0, end: int = -1) -> tuple:
        """Get names of all tracks in a range.

        Args:
            start: Starting track index (default 0)
            end: Ending track index, exclusive (-1 for all)

        Returns:
            Tuple of track names
        """
        if end == -1:
            end = self.get_num_tracks()
        result = self._client.query("/live/song/get/track_names", start, end)
        return result

    def get_back_to_arranger(self) -> bool:
        """Check if back-to-arranger button is highlighted.

        Returns:
            True if back-to-arranger is active (session changes pending)
        """
        result = self._client.query("/live/song/get/back_to_arranger")
        return bool(result[0])

    def set_back_to_arranger(self, enabled: bool) -> None:
        """Trigger back-to-arranger.

        When enabled=True, returns to arrangement view from session recording.

        Args:
            enabled: True to trigger back-to-arranger
        """
        self._client.send("/live/song/set/back_to_arranger", int(enabled))

    def nudge_down(self) -> None:
        """Nudge tempo down (temporary slow down)."""
        self._client.send("/live/song/set/nudge_down", 1)

    def nudge_up(self) -> None:
        """Nudge tempo up (temporary speed up)."""
        self._client.send("/live/song/set/nudge_up", 1)

    # Additional Listeners

    def on_beat(self, callback: Callable[[int], None]) -> None:
        """Register a callback for beat notifications.

        The callback is called on each beat during playback.

        Args:
            callback: Function(beat) called on each beat
        """
        self._client.send("/live/song/start_listen/beat")
        self._client.start_listener(
            "/live/song/get/beat", lambda addr, *args: callback(int(args[0]))
        )

    def stop_beat_listener(self) -> None:
        """Stop listening for beat notifications."""
        self._client.send("/live/song/stop_listen/beat")
        self._client.stop_listener("/live/song/get/beat")

    def on_loop_change(self, callback: Callable[[bool], None]) -> None:
        """Register a callback for loop state changes.

        Args:
            callback: Function(enabled) called when loop state changes
        """
        self._client.send("/live/song/start_listen/loop")
        self._client.start_listener(
            "/live/song/get/loop", lambda addr, *args: callback(bool(args[0]))
        )

    def stop_loop_listener(self) -> None:
        """Stop listening for loop state changes."""
        self._client.send("/live/song/stop_listen/loop")
        self._client.stop_listener("/live/song/get/loop")

    def on_record_mode_change(self, callback: Callable[[bool], None]) -> None:
        """Register a callback for record mode changes.

        Args:
            callback: Function(enabled) called when record mode changes
        """
        self._client.send("/live/song/start_listen/record_mode")
        self._client.start_listener(
            "/live/song/get/record_mode", lambda addr, *args: callback(bool(args[0]))
        )

    def stop_record_mode_listener(self) -> None:
        """Stop listening for record mode changes."""
        self._client.send("/live/song/stop_listen/record_mode")
        self._client.stop_listener("/live/song/get/record_mode")

    def on_current_song_time_change(self, callback: Callable[[float], None]) -> None:
        """Register a callback for playhead position changes.

        Args:
            callback: Function(beats) called when playhead moves
        """
        self._client.send("/live/song/start_listen/current_song_time")
        self._client.start_listener(
            "/live/song/get/current_song_time",
            lambda addr, *args: callback(float(args[0])),
        )

    def stop_current_song_time_listener(self) -> None:
        """Stop listening for playhead position changes."""
        self._client.send("/live/song/stop_listen/current_song_time")
        self._client.stop_listener("/live/song/get/current_song_time")

    # Session record status

    def get_session_record_status(self) -> int:
        """Get the session record status.

        Returns:
            Session record status (0=Off, 1=On, 2=Transition)
        """
        result = self._client.query("/live/song/get/session_record_status")
        return int(result[0]) if result else 0

    # Beat getter

    def get_beat(self) -> float:
        """Get the current beat position.

        Returns:
            Current beat position
        """
        result = self._client.query("/live/song/get/beat")
        return float(result[0]) if result else 0.0
