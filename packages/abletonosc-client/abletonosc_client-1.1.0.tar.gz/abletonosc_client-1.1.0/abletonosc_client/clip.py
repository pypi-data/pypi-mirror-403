"""Clip operations for AbletonOSC.

Covers /live/clip/* endpoints for individual clip control and note editing.
"""

from typing import Callable, NamedTuple

from abletonosc_client.client import AbletonOSCClient


class Note(NamedTuple):
    """Represents a MIDI note in a clip.

    Attributes:
        pitch: MIDI pitch (0-127)
        start_time: Start position in beats
        duration: Duration in beats
        velocity: Velocity (0-127)
        mute: Whether the note is muted
    """

    pitch: int
    start_time: float
    duration: float
    velocity: int
    mute: bool = False


class Clip:
    """Clip operations like notes, properties, and playback."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client
        # Listener callbacks: {"property": {(track_idx, clip_idx): callback}}
        self._clip_callbacks: dict[str, dict[tuple[int, int], Callable]] = {}
        # Set of properties with dispatchers registered
        self._dispatcher_registered: set[str] = set()

    # Name

    def get_name(self, track_index: int, clip_index: int) -> str:
        """Get the clip name.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Clip name
        """
        result = self._client.query("/live/clip/get/name", track_index, clip_index)
        # Response format: (track_index, clip_index, name)
        return str(result[2]) if len(result) > 2 else ""

    def set_name(self, track_index: int, clip_index: int, name: str) -> None:
        """Set the clip name.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            name: New clip name
        """
        self._client.send("/live/clip/set/name", track_index, clip_index, name)

    # Playback

    def fire(self, track_index: int, clip_index: int) -> None:
        """Fire (launch) a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
        """
        self._client.send("/live/clip/fire", track_index, clip_index)

    def stop(self, track_index: int, clip_index: int) -> None:
        """Stop a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
        """
        self._client.send("/live/clip/stop", track_index, clip_index)

    # Clip properties

    def get_length(self, track_index: int, clip_index: int) -> float:
        """Get the clip length in beats.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Clip length in beats
        """
        result = self._client.query("/live/clip/get/length", track_index, clip_index)
        # Response format: (track_index, clip_index, length)
        return float(result[2])

    def get_is_midi_clip(self, track_index: int, clip_index: int) -> bool:
        """Check if clip is a MIDI clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if MIDI clip, False if audio clip
        """
        result = self._client.query(
            "/live/clip/get/is_midi_clip", track_index, clip_index
        )
        # Response format: (track_index, clip_index, is_midi_clip)
        return bool(result[2])

    def get_is_audio_clip(self, track_index: int, clip_index: int) -> bool:
        """Check if clip is an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if audio clip, False if MIDI clip
        """
        result = self._client.query(
            "/live/clip/get/is_audio_clip", track_index, clip_index
        )
        # Response format: (track_index, clip_index, is_audio_clip)
        return bool(result[2])

    def get_is_playing(self, track_index: int, clip_index: int) -> bool:
        """Check if clip is currently playing.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if playing
        """
        result = self._client.query(
            "/live/clip/get/is_playing", track_index, clip_index
        )
        # Response format: (track_index, clip_index, is_playing)
        return bool(result[2])

    def get_color(self, track_index: int, clip_index: int) -> int:
        """Get the clip color.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Color as integer
        """
        result = self._client.query("/live/clip/get/color", track_index, clip_index)
        # Response format: (track_index, clip_index, color)
        return int(result[2])

    def set_color(self, track_index: int, clip_index: int, color: int) -> None:
        """Set the clip color.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            color: Color as integer
        """
        self._client.send("/live/clip/set/color", track_index, clip_index, color)

    # Notes (MIDI clips only)

    def get_notes(self, track_index: int, clip_index: int) -> list[Note]:
        """Get all notes from a MIDI clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            List of Note objects
        """
        result = self._client.query("/live/clip/get/notes", track_index, clip_index)
        notes = []

        # Result format: (track_index, scene_index, pitch, start_time, duration, velocity, mute, ...)
        # Skip first 2 values (indices), then each note is 5 values
        if result and len(result) > 2:
            values = list(result)[2:]  # Skip track_index, scene_index
            for i in range(0, len(values), 5):
                if i + 4 < len(values):
                    notes.append(
                        Note(
                            pitch=int(values[i]),
                            start_time=float(values[i + 1]),
                            duration=float(values[i + 2]),
                            velocity=int(values[i + 3]),
                            mute=bool(values[i + 4]),
                        )
                    )
        return notes

    def add_notes(self, track_index: int, clip_index: int, notes: list[Note]) -> None:
        """Add notes to a MIDI clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            notes: List of Note objects to add
        """
        # Build flat list: pitch, start_time, duration, velocity, mute for each note
        args = [track_index, clip_index]
        for note in notes:
            args.extend(
                [note.pitch, note.start_time, note.duration, note.velocity, int(note.mute)]
            )
        self._client.send("/live/clip/add/notes", *args)

    def remove_notes(
        self,
        track_index: int,
        clip_index: int,
        start_time: float = 0.0,
        end_time: float = 128.0,
        pitch_start: int = 0,
        pitch_end: int = 127,
    ) -> None:
        """Remove notes from a MIDI clip within a range.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            start_time: Start of time range in beats
            end_time: End of time range in beats
            pitch_start: Lowest pitch to remove
            pitch_end: Highest pitch to remove
        """
        self._client.send(
            "/live/clip/remove/notes",
            track_index,
            clip_index,
            start_time,
            pitch_start,
            end_time - start_time,  # duration
            pitch_end - pitch_start + 1,  # pitch span
        )

    # Loop settings

    def get_loop_start(self, track_index: int, clip_index: int) -> float:
        """Get the loop start position in beats.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Loop start position in beats
        """
        result = self._client.query(
            "/live/clip/get/loop_start", track_index, clip_index
        )
        # Response format: (track_index, clip_index, loop_start)
        return float(result[2])

    def set_loop_start(
        self, track_index: int, clip_index: int, start: float
    ) -> None:
        """Set the loop start position.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            start: Loop start in beats
        """
        self._client.send(
            "/live/clip/set/loop_start", track_index, clip_index, float(start)
        )

    def get_loop_end(self, track_index: int, clip_index: int) -> float:
        """Get the loop end position in beats.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Loop end position in beats
        """
        result = self._client.query("/live/clip/get/loop_end", track_index, clip_index)
        # Response format: (track_index, clip_index, loop_end)
        return float(result[2])

    def set_loop_end(self, track_index: int, clip_index: int, end: float) -> None:
        """Set the loop end position.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            end: Loop end in beats
        """
        self._client.send(
            "/live/clip/set/loop_end", track_index, clip_index, float(end)
        )

    # Start/end time

    def get_start_time(self, track_index: int, clip_index: int) -> float:
        """Get the clip start time in beats.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Start time in beats
        """
        result = self._client.query(
            "/live/clip/get/start_time", track_index, clip_index
        )
        return float(result[2])

    def set_start_time(
        self, track_index: int, clip_index: int, time: float
    ) -> None:
        """Set the clip start time.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            time: Start time in beats
        """
        self._client.send(
            "/live/clip/set/start_time", track_index, clip_index, float(time)
        )

    def get_end_time(self, track_index: int, clip_index: int) -> float:
        """Get the clip end time in beats.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            End time in beats
        """
        result = self._client.query(
            "/live/clip/get/end_time", track_index, clip_index
        )
        return float(result[2])

    def set_end_time(
        self, track_index: int, clip_index: int, time: float
    ) -> None:
        """Set the clip end time.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            time: End time in beats
        """
        self._client.send(
            "/live/clip/set/end_time", track_index, clip_index, float(time)
        )

    # Looping

    def get_looping(self, track_index: int, clip_index: int) -> bool:
        """Check if clip looping is enabled.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if looping is enabled
        """
        result = self._client.query(
            "/live/clip/get/looping", track_index, clip_index
        )
        return bool(result[2])

    def set_looping(
        self, track_index: int, clip_index: int, enabled: bool
    ) -> None:
        """Enable or disable clip looping.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            enabled: True to enable looping
        """
        self._client.send(
            "/live/clip/set/looping", track_index, clip_index, int(enabled)
        )

    def duplicate_loop(self, track_index: int, clip_index: int) -> None:
        """Duplicate the loop content of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
        """
        self._client.send("/live/clip/duplicate_loop", track_index, clip_index)

    # Warp (audio clips)

    def get_warp_mode(self, track_index: int, clip_index: int) -> int:
        """Get the warp mode for an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Warp mode (0=Beats, 1=Tones, 2=Texture, 3=Re-Pitch, 4=Complex, 5=Complex Pro)
        """
        result = self._client.query(
            "/live/clip/get/warp_mode", track_index, clip_index
        )
        return int(result[2])

    def set_warp_mode(
        self, track_index: int, clip_index: int, mode: int
    ) -> None:
        """Set the warp mode for an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            mode: Warp mode (0=Beats, 1=Tones, 2=Texture, 3=Re-Pitch, 4=Complex, 5=Complex Pro)
        """
        self._client.send(
            "/live/clip/set/warp_mode", track_index, clip_index, int(mode)
        )

    # Pitch

    def get_pitch_coarse(self, track_index: int, clip_index: int) -> int:
        """Get the coarse pitch adjustment for a clip (audio clips only).

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Pitch adjustment in semitones (-48 to +48), or 0 for MIDI clips
        """
        result = self._client.query(
            "/live/clip/get/pitch_coarse", track_index, clip_index
        )
        return int(result[2]) if len(result) > 2 and result[2] is not None else 0

    def set_pitch_coarse(
        self, track_index: int, clip_index: int, pitch: int
    ) -> None:
        """Set the coarse pitch adjustment for a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            pitch: Pitch adjustment in semitones (-48 to +48)
        """
        self._client.send(
            "/live/clip/set/pitch_coarse", track_index, clip_index, int(pitch)
        )

    def get_pitch_fine(self, track_index: int, clip_index: int) -> float:
        """Get the fine pitch adjustment for a clip (audio clips only).

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Fine pitch adjustment in cents (-50 to +50), or 0.0 for MIDI clips
        """
        result = self._client.query(
            "/live/clip/get/pitch_fine", track_index, clip_index
        )
        return float(result[2]) if len(result) > 2 and result[2] is not None else 0.0

    def set_pitch_fine(
        self, track_index: int, clip_index: int, cents: float
    ) -> None:
        """Set the fine pitch adjustment for a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            cents: Fine pitch adjustment in cents (-50 to +50)
        """
        self._client.send(
            "/live/clip/set/pitch_fine", track_index, clip_index, float(cents)
        )

    # Gain (audio clips)

    def get_gain(self, track_index: int, clip_index: int) -> float:
        """Get the gain for an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Gain level (typically 0.0-1.0, where 1.0 is unity gain)
        """
        result = self._client.query(
            "/live/clip/get/gain", track_index, clip_index
        )
        return float(result[2]) if len(result) > 2 else 1.0

    def set_gain(self, track_index: int, clip_index: int, gain: float) -> None:
        """Set the gain for an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            gain: Gain level (typically 0.0-1.0)
        """
        self._client.send(
            "/live/clip/set/gain", track_index, clip_index, float(gain)
        )

    # Warping (audio clips)

    def get_warping(self, track_index: int, clip_index: int) -> bool:
        """Check if warping is enabled for an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if warping is enabled
        """
        result = self._client.query(
            "/live/clip/get/warping", track_index, clip_index
        )
        return bool(result[2]) if len(result) > 2 else False

    def set_warping(
        self, track_index: int, clip_index: int, enabled: bool
    ) -> None:
        """Enable or disable warping for an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            enabled: True to enable warping
        """
        self._client.send(
            "/live/clip/set/warping", track_index, clip_index, int(enabled)
        )

    # Muted

    def get_muted(self, track_index: int, clip_index: int) -> bool:
        """Check if clip is muted.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if clip is muted
        """
        result = self._client.query(
            "/live/clip/get/muted", track_index, clip_index
        )
        return bool(result[2]) if len(result) > 2 else False

    def set_muted(
        self, track_index: int, clip_index: int, muted: bool
    ) -> None:
        """Mute or unmute a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            muted: True to mute the clip
        """
        self._client.send(
            "/live/clip/set/muted", track_index, clip_index, int(muted)
        )

    # Playing position

    def get_playing_position(self, track_index: int, clip_index: int) -> float:
        """Get the current playhead position in the clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Playhead position in beats
        """
        result = self._client.query(
            "/live/clip/get/playing_position", track_index, clip_index
        )
        return float(result[2]) if len(result) > 2 else 0.0

    # Color index

    def get_color_index(self, track_index: int, clip_index: int) -> int:
        """Get the color index of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Color index (0-69)
        """
        result = self._client.query(
            "/live/clip/get/color_index", track_index, clip_index
        )
        return int(result[2]) if len(result) > 2 else 0

    def set_color_index(
        self, track_index: int, clip_index: int, color_index: int
    ) -> None:
        """Set the color index of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            color_index: Color index (0-69)
        """
        self._client.send(
            "/live/clip/set/color_index", track_index, clip_index, int(color_index)
        )

    # Markers

    def get_start_marker(self, track_index: int, clip_index: int) -> float:
        """Get the start marker position.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Start marker position in beats
        """
        result = self._client.query(
            "/live/clip/get/start_marker", track_index, clip_index
        )
        return float(result[2]) if len(result) > 2 else 0.0

    def set_start_marker(
        self, track_index: int, clip_index: int, position: float
    ) -> None:
        """Set the start marker position.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            position: Start marker position in beats
        """
        self._client.send(
            "/live/clip/set/start_marker", track_index, clip_index, float(position)
        )

    def get_end_marker(self, track_index: int, clip_index: int) -> float:
        """Get the end marker position.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            End marker position in beats
        """
        result = self._client.query(
            "/live/clip/get/end_marker", track_index, clip_index
        )
        return float(result[2]) if len(result) > 2 else 0.0

    def set_end_marker(
        self, track_index: int, clip_index: int, position: float
    ) -> None:
        """Set the end marker position.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            position: End marker position in beats
        """
        self._client.send(
            "/live/clip/set/end_marker", track_index, clip_index, float(position)
        )

    # Sample length (audio clips)

    def get_sample_length(self, track_index: int, clip_index: int) -> float:
        """Get the sample length of an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Sample length in samples
        """
        result = self._client.query(
            "/live/clip/get/sample_length", track_index, clip_index
        )
        return float(result[2]) if len(result) > 2 else 0.0

    # Recording state

    def get_is_overdubbing(self, track_index: int, clip_index: int) -> bool:
        """Check if clip is currently overdubbing.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if overdubbing
        """
        result = self._client.query(
            "/live/clip/get/is_overdubbing", track_index, clip_index
        )
        return bool(result[2]) if len(result) > 2 else False

    def get_is_recording(self, track_index: int, clip_index: int) -> bool:
        """Check if clip is currently recording.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if recording
        """
        result = self._client.query(
            "/live/clip/get/is_recording", track_index, clip_index
        )
        return bool(result[2]) if len(result) > 2 else False

    def get_will_record_on_start(self, track_index: int, clip_index: int) -> bool:
        """Check if clip will start recording when launched.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if will record on start
        """
        result = self._client.query(
            "/live/clip/get/will_record_on_start", track_index, clip_index
        )
        return bool(result[2]) if len(result) > 2 else False

    # Launch mode

    def get_launch_mode(self, track_index: int, clip_index: int) -> int:
        """Get the launch mode of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Launch mode (0=Trigger, 1=Gate, 2=Toggle, 3=Repeat)
        """
        result = self._client.query(
            "/live/clip/get/launch_mode", track_index, clip_index
        )
        return int(result[2]) if len(result) > 2 else 0

    def set_launch_mode(
        self, track_index: int, clip_index: int, mode: int
    ) -> None:
        """Set the launch mode of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            mode: Launch mode (0=Trigger, 1=Gate, 2=Toggle, 3=Repeat)
        """
        self._client.send(
            "/live/clip/set/launch_mode", track_index, clip_index, int(mode)
        )

    # Launch quantization

    def get_launch_quantization(self, track_index: int, clip_index: int) -> int:
        """Get the launch quantization of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Launch quantization value
        """
        result = self._client.query(
            "/live/clip/get/launch_quantization", track_index, clip_index
        )
        return int(result[2]) if len(result) > 2 else 0

    def set_launch_quantization(
        self, track_index: int, clip_index: int, quantization: int
    ) -> None:
        """Set the launch quantization of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            quantization: Launch quantization value
        """
        self._client.send(
            "/live/clip/set/launch_quantization", track_index, clip_index, int(quantization)
        )

    # File path (audio clips)

    def get_file_path(self, track_index: int, clip_index: int) -> str:
        """Get the file path of an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            File path string, or empty string for MIDI clips
        """
        result = self._client.query(
            "/live/clip/get/file_path", track_index, clip_index
        )
        return str(result[2]) if len(result) > 2 else ""

    # Velocity amount (MIDI clips)

    def get_velocity_amount(self, track_index: int, clip_index: int) -> float:
        """Get the velocity amount scaling for a MIDI clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Velocity amount (0.0-1.0)
        """
        result = self._client.query(
            "/live/clip/get/velocity_amount", track_index, clip_index
        )
        return float(result[2]) if len(result) > 2 else 1.0

    def set_velocity_amount(
        self, track_index: int, clip_index: int, amount: float
    ) -> None:
        """Set the velocity amount scaling for a MIDI clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            amount: Velocity amount (0.0-1.0)
        """
        self._client.send(
            "/live/clip/set/velocity_amount", track_index, clip_index, float(amount)
        )

    # Legato (MIDI clips)

    def get_legato(self, track_index: int, clip_index: int) -> bool:
        """Check if legato mode is enabled for a MIDI clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if legato is enabled
        """
        result = self._client.query(
            "/live/clip/get/legato", track_index, clip_index
        )
        return bool(result[2]) if len(result) > 2 else False

    def set_legato(
        self, track_index: int, clip_index: int, enabled: bool
    ) -> None:
        """Enable or disable legato mode for a MIDI clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            enabled: True to enable legato
        """
        self._client.send(
            "/live/clip/set/legato", track_index, clip_index, int(enabled)
        )

    # Position

    def get_position(self, track_index: int, clip_index: int) -> float:
        """Get the loop position of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            Position in beats
        """
        result = self._client.query(
            "/live/clip/get/position", track_index, clip_index
        )
        return float(result[2]) if len(result) > 2 else 0.0

    def set_position(
        self, track_index: int, clip_index: int, position: float
    ) -> None:
        """Set the loop position of a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            position: Position in beats
        """
        self._client.send(
            "/live/clip/set/position", track_index, clip_index, float(position)
        )

    # RAM mode (audio clips)

    def get_ram_mode(self, track_index: int, clip_index: int) -> bool:
        """Check if RAM mode is enabled for an audio clip.

        When RAM mode is enabled, the entire clip is loaded into RAM.
        When disabled, it streams from disk.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if RAM mode is enabled
        """
        result = self._client.query(
            "/live/clip/get/ram_mode", track_index, clip_index
        )
        return bool(result[2]) if len(result) > 2 else False

    def set_ram_mode(
        self, track_index: int, clip_index: int, enabled: bool
    ) -> None:
        """Enable or disable RAM mode for an audio clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            enabled: True to load clip into RAM
        """
        self._client.send(
            "/live/clip/set/ram_mode", track_index, clip_index, int(enabled)
        )

    # Has groove

    def get_has_groove(self, track_index: int, clip_index: int) -> bool:
        """Check if clip has a groove applied.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)

        Returns:
            True if clip has a groove
        """
        result = self._client.query(
            "/live/clip/get/has_groove", track_index, clip_index
        )
        return bool(result[2]) if len(result) > 2 else False

    # Listener infrastructure

    def _make_dispatcher(self, prop: str, converter: Callable) -> Callable:
        """Create a dispatcher that routes callbacks by (track_index, clip_index).

        Args:
            prop: Property name (e.g., "playing_position")
            converter: Function to convert the value (e.g., float, bool)

        Returns:
            Dispatcher function for the OSC callback
        """

        def dispatcher(addr, *args):
            # Response format: (track_index, clip_index, value)
            track_index = int(args[0])
            clip_index = int(args[1])
            value = converter(args[2])
            key = (track_index, clip_index)
            if prop in self._clip_callbacks:
                if key in self._clip_callbacks[prop]:
                    self._clip_callbacks[prop][key](track_index, clip_index, value)

        return dispatcher

    def _start_clip_listener(
        self,
        track_index: int,
        clip_index: int,
        prop: str,
        callback: Callable,
        converter: Callable,
    ) -> None:
        """Start a listener for a clip property.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            prop: Property name (e.g., "playing_position")
            callback: Function(track_index, clip_index, value) to call on change
            converter: Function to convert the value
        """
        # Initialize callback dict for this property if needed
        if prop not in self._clip_callbacks:
            self._clip_callbacks[prop] = {}

        # Register callback for this clip
        key = (track_index, clip_index)
        self._clip_callbacks[prop][key] = callback

        # Register dispatcher if not already done for this property
        if prop not in self._dispatcher_registered:
            response_addr = f"/live/clip/get/{prop}"
            self._client.start_listener(
                response_addr, self._make_dispatcher(prop, converter)
            )
            self._dispatcher_registered.add(prop)

        # Tell AbletonOSC to start sending updates for this clip
        self._client.send(f"/live/clip/start_listen/{prop}", track_index, clip_index)

    def _stop_clip_listener(
        self, track_index: int, clip_index: int, prop: str
    ) -> None:
        """Stop a listener for a clip property.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            prop: Property name
        """
        # Tell AbletonOSC to stop sending updates for this clip
        self._client.send(f"/live/clip/stop_listen/{prop}", track_index, clip_index)

        # Remove callback
        key = (track_index, clip_index)
        if prop in self._clip_callbacks:
            self._clip_callbacks[prop].pop(key, None)

            # If no more callbacks for this property, unregister dispatcher
            if not self._clip_callbacks[prop]:
                response_addr = f"/live/clip/get/{prop}"
                self._client.stop_listener(response_addr)
                self._dispatcher_registered.discard(prop)

    # Playing position listener

    def on_playing_position_change(
        self,
        track_index: int,
        clip_index: int,
        callback: Callable[[int, int, float], None],
    ) -> None:
        """Register a callback for clip playing position changes.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
            callback: Function(track_index, clip_index, position) called on change
        """
        self._start_clip_listener(
            track_index, clip_index, "playing_position", callback, float
        )

    def stop_playing_position_listener(
        self, track_index: int, clip_index: int
    ) -> None:
        """Stop listening for playing position changes on a clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
        """
        self._stop_clip_listener(track_index, clip_index, "playing_position")
