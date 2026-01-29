"""Track operations for AbletonOSC.

Covers /live/track/* endpoints for individual track control.
"""

from typing import Callable

from abletonosc_client.client import AbletonOSCClient


class Track:
    """Track operations like volume, pan, mute, solo."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client
        # Track listener callbacks: {"property": {track_index: callback}}
        self._track_callbacks: dict[str, dict[int, Callable]] = {}
        # Set of properties with dispatchers registered
        self._dispatcher_registered: set[str] = set()

    # Name

    def get_name(self, track_index: int) -> str:
        """Get the track name.

        Args:
            track_index: Track index (0-based)

        Returns:
            Track name
        """
        result = self._client.query("/live/track/get/name", track_index)
        # Response format: (track_index, name)
        return str(result[1]) if len(result) > 1 else ""

    def set_name(self, track_index: int, name: str) -> None:
        """Set the track name.

        Args:
            track_index: Track index (0-based)
            name: New track name
        """
        self._client.send("/live/track/set/name", track_index, name)

    # Volume

    def get_volume(self, track_index: int) -> float:
        """Get the track volume.

        Args:
            track_index: Track index (0-based)

        Returns:
            Volume level (0.0-1.0, where 0.85 is 0dB)
        """
        result = self._client.query("/live/track/get/volume", track_index)
        # Response format: (track_index, volume)
        return float(result[1])

    def set_volume(self, track_index: int, volume: float) -> None:
        """Set the track volume.

        Args:
            track_index: Track index (0-based)
            volume: Volume level (0.0-1.0, where 0.85 is 0dB)
        """
        self._client.send("/live/track/set/volume", track_index, float(volume))

    # Pan

    def get_panning(self, track_index: int) -> float:
        """Get the track pan position.

        Args:
            track_index: Track index (0-based)

        Returns:
            Pan position (-1.0 left to 1.0 right, 0.0 center)
        """
        result = self._client.query("/live/track/get/panning", track_index)
        # Response format: (track_index, panning)
        return float(result[1])

    def set_panning(self, track_index: int, pan: float) -> None:
        """Set the track pan position.

        Args:
            track_index: Track index (0-based)
            pan: Pan position (-1.0 left to 1.0 right, 0.0 center)
        """
        self._client.send("/live/track/set/panning", track_index, float(pan))

    # Mute

    def get_mute(self, track_index: int) -> bool:
        """Check if track is muted.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if muted
        """
        result = self._client.query("/live/track/get/mute", track_index)
        # Response format: (track_index, mute)
        return bool(result[1])

    def set_mute(self, track_index: int, muted: bool) -> None:
        """Mute or unmute a track.

        Args:
            track_index: Track index (0-based)
            muted: True to mute
        """
        self._client.send("/live/track/set/mute", track_index, int(muted))

    # Solo

    def get_solo(self, track_index: int) -> bool:
        """Check if track is soloed.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if soloed
        """
        result = self._client.query("/live/track/get/solo", track_index)
        # Response format: (track_index, solo)
        return bool(result[1])

    def set_solo(self, track_index: int, soloed: bool) -> None:
        """Solo or unsolo a track.

        Args:
            track_index: Track index (0-based)
            soloed: True to solo
        """
        self._client.send("/live/track/set/solo", track_index, int(soloed))

    # Arm

    def get_arm(self, track_index: int) -> bool:
        """Check if track is armed for recording.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if armed
        """
        result = self._client.query("/live/track/get/arm", track_index)
        # Response format: (track_index, arm)
        return bool(result[1])

    def set_arm(self, track_index: int, armed: bool) -> None:
        """Arm or disarm a track for recording.

        Args:
            track_index: Track index (0-based)
            armed: True to arm
        """
        self._client.send("/live/track/set/arm", track_index, int(armed))

    # Track info

    def get_color(self, track_index: int) -> int:
        """Get the track color.

        Args:
            track_index: Track index (0-based)

        Returns:
            Color as integer
        """
        result = self._client.query("/live/track/get/color", track_index)
        # Response format: (track_index, color)
        return int(result[1])

    def set_color(self, track_index: int, color: int) -> None:
        """Set the track color.

        Args:
            track_index: Track index (0-based)
            color: Color as integer
        """
        self._client.send("/live/track/set/color", track_index, color)

    def get_is_foldable(self, track_index: int) -> bool:
        """Check if track is a group track (foldable).

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track is a group
        """
        result = self._client.query("/live/track/get/is_foldable", track_index)
        # Response format: (track_index, is_foldable)
        return bool(result[1])

    def get_is_grouped(self, track_index: int) -> bool:
        """Check if track is inside a group.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track is in a group
        """
        result = self._client.query("/live/track/get/is_grouped", track_index)
        # Response format: (track_index, is_grouped)
        return bool(result[1])

    # Devices

    def get_num_devices(self, track_index: int) -> int:
        """Get the number of devices on a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Number of devices
        """
        result = self._client.query("/live/track/get/num_devices", track_index)
        # Response format: (track_index, num_devices)
        return int(result[1])

    # Sends

    def get_send(self, track_index: int, send_index: int) -> float:
        """Get the send level for a track.

        Args:
            track_index: Track index (0-based)
            send_index: Send index (0-based, corresponds to return track order)

        Returns:
            Send level (0.0-1.0)
        """
        result = self._client.query(
            "/live/track/get/send", track_index, send_index
        )
        # Response format: (track_index, send_index, level)
        return float(result[2])

    def set_send(self, track_index: int, send_index: int, level: float) -> None:
        """Set the send level for a track.

        Args:
            track_index: Track index (0-based)
            send_index: Send index (0-based, corresponds to return track order)
            level: Send level (0.0-1.0)
        """
        self._client.send(
            "/live/track/set/send", track_index, send_index, float(level)
        )

    # Clip control

    def stop_all_clips(self, track_index: int) -> None:
        """Stop all playing clips on this track.

        Args:
            track_index: Track index (0-based)
        """
        self._client.send("/live/track/stop_all_clips", track_index)

    # Device insertion

    def insert_device(
        self, track_index: int, device_name: str, device_index: int = -1
    ) -> int:
        """Insert a device onto a track by name.

        Searches instruments, audio effects, midi effects, drums, and sounds
        for a matching device name and loads it onto the track.

        Args:
            track_index: Track index (0-based)
            device_name: Name of the device to load (e.g., "Wavetable", "Reverb")
            device_index: Position to insert device (-1 = end of chain)

        Returns:
            Index of newly inserted device, or -1 if device not found
        """
        result = self._client.query(
            "/live/track/insert_device", track_index, device_name, device_index
        )
        # Response format: (track_index, device_index)
        return int(result[1]) if len(result) > 1 else -1

    def get_device_names(self, track_index: int) -> tuple:
        """Get names of all devices on a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of device names
        """
        result = self._client.query("/live/track/get/devices/name", track_index)
        # Response format: (track_index, name1, name2, ...)
        return result[1:] if len(result) > 1 else ()

    def get_device_types(self, track_index: int) -> tuple:
        """Get types of all devices on a track.

        Device types: 0 = audio_effect, 1 = instrument, 2 = midi_effect

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of device types (integers)
        """
        result = self._client.query("/live/track/get/devices/type", track_index)
        # Response format: (track_index, type1, type2, ...)
        return result[1:] if len(result) > 1 else ()

    def delete_device(self, track_index: int, device_index: int) -> None:
        """Delete a device from a track.

        Args:
            track_index: Track index (0-based)
            device_index: Device index to delete (0-based)
        """
        self._client.send("/live/track/delete_device", track_index, device_index)

    # Input routing

    def get_input_routing_type(self, track_index: int) -> str:
        """Get the input routing type for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Input routing type name (e.g., "Ext. In", "No Input")
        """
        result = self._client.query(
            "/live/track/get/input_routing_type", track_index
        )
        return str(result[1]) if len(result) > 1 else ""

    def set_input_routing_type(self, track_index: int, routing_type: str) -> None:
        """Set the input routing type for a track.

        Args:
            track_index: Track index (0-based)
            routing_type: Input routing type name
        """
        self._client.send(
            "/live/track/set/input_routing_type", track_index, routing_type
        )

    def get_input_routing_channel(self, track_index: int) -> str:
        """Get the input routing channel for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Input routing channel name
        """
        result = self._client.query(
            "/live/track/get/input_routing_channel", track_index
        )
        return str(result[1]) if len(result) > 1 else ""

    def set_input_routing_channel(self, track_index: int, channel: str) -> None:
        """Set the input routing channel for a track.

        Args:
            track_index: Track index (0-based)
            channel: Input routing channel name
        """
        self._client.send(
            "/live/track/set/input_routing_channel", track_index, channel
        )

    # Output routing

    def get_output_routing_type(self, track_index: int) -> str:
        """Get the output routing type for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Output routing type name (e.g., "Master", "Sends Only")
        """
        result = self._client.query(
            "/live/track/get/output_routing_type", track_index
        )
        return str(result[1]) if len(result) > 1 else ""

    def set_output_routing_type(self, track_index: int, routing_type: str) -> None:
        """Set the output routing type for a track.

        Args:
            track_index: Track index (0-based)
            routing_type: Output routing type name
        """
        self._client.send(
            "/live/track/set/output_routing_type", track_index, routing_type
        )

    def get_output_routing_channel(self, track_index: int) -> str:
        """Get the output routing channel for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Output routing channel name
        """
        result = self._client.query(
            "/live/track/get/output_routing_channel", track_index
        )
        return str(result[1]) if len(result) > 1 else ""

    def set_output_routing_channel(self, track_index: int, channel: str) -> None:
        """Set the output routing channel for a track.

        Args:
            track_index: Track index (0-based)
            channel: Output routing channel name
        """
        self._client.send(
            "/live/track/set/output_routing_channel", track_index, channel
        )

    # Available routing options

    def get_available_input_routing_types(self, track_index: int) -> tuple:
        """Get available input routing types for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of available input routing type names
        """
        result = self._client.query(
            "/live/track/get/available_input_routing_types", track_index
        )
        return result[1:] if len(result) > 1 else ()

    def get_available_output_routing_types(self, track_index: int) -> tuple:
        """Get available output routing types for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of available output routing type names
        """
        result = self._client.query(
            "/live/track/get/available_output_routing_types", track_index
        )
        return result[1:] if len(result) > 1 else ()

    def get_available_input_routing_channels(self, track_index: int) -> tuple:
        """Get available input routing channels for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of available input routing channel names
        """
        result = self._client.query(
            "/live/track/get/available_input_routing_channels", track_index
        )
        return result[1:] if len(result) > 1 else ()

    def get_available_output_routing_channels(self, track_index: int) -> tuple:
        """Get available output routing channels for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of available output routing channel names
        """
        result = self._client.query(
            "/live/track/get/available_output_routing_channels", track_index
        )
        return result[1:] if len(result) > 1 else ()

    # Bulk clip queries

    def get_clips_names(self, track_index: int) -> tuple:
        """Get names of all clips on a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of clip names (empty string for empty slots)
        """
        result = self._client.query("/live/track/get/clips/name", track_index)
        return result[1:] if len(result) > 1 else ()

    def get_clips_lengths(self, track_index: int) -> tuple:
        """Get lengths of all clips on a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of clip lengths in beats (0 for empty slots)
        """
        result = self._client.query("/live/track/get/clips/length", track_index)
        return result[1:] if len(result) > 1 else ()

    def get_clips_colors(self, track_index: int) -> tuple:
        """Get colors of all clips on a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of clip colors as integers
        """
        result = self._client.query("/live/track/get/clips/color", track_index)
        return result[1:] if len(result) > 1 else ()

    # Bulk device queries

    def get_devices_class_names(self, track_index: int) -> tuple:
        """Get class names (types) of all devices on a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Tuple of device class names (e.g., "Compressor", "Reverb")
        """
        result = self._client.query("/live/track/get/devices/class_name", track_index)
        return result[1:] if len(result) > 1 else ()

    # Monitoring

    def get_current_monitoring_state(self, track_index: int) -> int:
        """Get the current monitoring state for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Monitoring state (0=In, 1=Auto, 2=Off)
        """
        result = self._client.query(
            "/live/track/get/current_monitoring_state", track_index
        )
        return int(result[1])

    def set_current_monitoring_state(self, track_index: int, state: int) -> None:
        """Set the current monitoring state for a track.

        Args:
            track_index: Track index (0-based)
            state: Monitoring state (0=In, 1=Auto, 2=Off)
        """
        self._client.send(
            "/live/track/set/current_monitoring_state", track_index, int(state)
        )

    # Track capabilities

    def get_can_be_armed(self, track_index: int) -> bool:
        """Check if a track can be armed for recording.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track can be armed
        """
        result = self._client.query(
            "/live/track/get/can_be_armed", track_index
        )
        return bool(result[1])

    def get_has_midi_input(self, track_index: int) -> bool:
        """Check if a track has MIDI input.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track has MIDI input
        """
        result = self._client.query(
            "/live/track/get/has_midi_input", track_index
        )
        return bool(result[1])

    def get_has_midi_output(self, track_index: int) -> bool:
        """Check if a track has MIDI output.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track has MIDI output
        """
        result = self._client.query(
            "/live/track/get/has_midi_output", track_index
        )
        return bool(result[1])

    def get_has_audio_input(self, track_index: int) -> bool:
        """Check if a track has audio input.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track has audio input
        """
        result = self._client.query(
            "/live/track/get/has_audio_input", track_index
        )
        return bool(result[1])

    def get_has_audio_output(self, track_index: int) -> bool:
        """Check if a track has audio output.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track has audio output
        """
        result = self._client.query(
            "/live/track/get/has_audio_output", track_index
        )
        return bool(result[1])

    # Track state

    def get_fired_slot_index(self, track_index: int) -> int:
        """Get the index of the clip slot that was fired (triggered).

        Args:
            track_index: Track index (0-based)

        Returns:
            Fired slot index, or -1 if none
        """
        result = self._client.query(
            "/live/track/get/fired_slot_index", track_index
        )
        return int(result[1])

    def get_playing_slot_index(self, track_index: int) -> int:
        """Get the index of the currently playing clip slot.

        Args:
            track_index: Track index (0-based)

        Returns:
            Playing slot index, or -1 if none
        """
        result = self._client.query(
            "/live/track/get/playing_slot_index", track_index
        )
        return int(result[1])

    def get_color_index(self, track_index: int) -> int:
        """Get the color index of a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Color index (0-69)
        """
        result = self._client.query(
            "/live/track/get/color_index", track_index
        )
        return int(result[1])

    def set_color_index(self, track_index: int, color_index: int) -> None:
        """Set the color index of a track.

        Args:
            track_index: Track index (0-based)
            color_index: Color index (0-69)
        """
        self._client.send(
            "/live/track/set/color_index", track_index, int(color_index)
        )

    # Group tracks

    def get_fold_state(self, track_index: int) -> bool:
        """Get the fold state of a group track.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track is folded (collapsed)
        """
        result = self._client.query(
            "/live/track/get/fold_state", track_index
        )
        return bool(result[1])

    def set_fold_state(self, track_index: int, folded: bool) -> None:
        """Set the fold state of a group track.

        Args:
            track_index: Track index (0-based)
            folded: True to fold (collapse) the group
        """
        self._client.send(
            "/live/track/set/fold_state", track_index, int(folded)
        )

    def get_is_visible(self, track_index: int) -> bool:
        """Check if a track is visible.

        Args:
            track_index: Track index (0-based)

        Returns:
            True if track is visible
        """
        result = self._client.query(
            "/live/track/get/is_visible", track_index
        )
        return bool(result[1])

    # Meters

    def get_output_meter_level(self, track_index: int) -> float:
        """Get the output meter level for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Output meter level (0.0-1.0)
        """
        result = self._client.query(
            "/live/track/get/output_meter_level", track_index
        )
        return float(result[1])

    def get_output_meter_left(self, track_index: int) -> float:
        """Get the left channel output meter level for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Left channel meter level (0.0-1.0)
        """
        result = self._client.query(
            "/live/track/get/output_meter_left", track_index
        )
        return float(result[1]) if len(result) > 1 and result[1] is not None else 0.0

    def get_output_meter_right(self, track_index: int) -> float:
        """Get the right channel output meter level for a track.

        Args:
            track_index: Track index (0-based)

        Returns:
            Right channel meter level (0.0-1.0)
        """
        result = self._client.query(
            "/live/track/get/output_meter_right", track_index
        )
        return float(result[1]) if len(result) > 1 and result[1] is not None else 0.0

    # Listener infrastructure

    def _make_dispatcher(self, prop: str, converter: Callable) -> Callable:
        """Create a dispatcher that routes callbacks by track index.

        Args:
            prop: Property name (e.g., "volume")
            converter: Function to convert the value (e.g., float, bool)

        Returns:
            Dispatcher function for the OSC callback
        """

        def dispatcher(addr, *args):
            # Response format: (track_index, value)
            track_index = int(args[0])
            value = converter(args[1])
            if prop in self._track_callbacks:
                if track_index in self._track_callbacks[prop]:
                    self._track_callbacks[prop][track_index](track_index, value)

        return dispatcher

    def _start_track_listener(
        self, track_index: int, prop: str, callback: Callable, converter: Callable
    ) -> None:
        """Start a listener for a track property.

        Args:
            track_index: Track index (0-based)
            prop: Property name (e.g., "volume")
            callback: Function(track_index, value) to call on change
            converter: Function to convert the value
        """
        # Initialize callback dict for this property if needed
        if prop not in self._track_callbacks:
            self._track_callbacks[prop] = {}

        # Register callback for this track
        self._track_callbacks[prop][track_index] = callback

        # Register dispatcher if not already done for this property
        if prop not in self._dispatcher_registered:
            response_addr = f"/live/track/get/{prop}"
            self._client.start_listener(
                response_addr, self._make_dispatcher(prop, converter)
            )
            self._dispatcher_registered.add(prop)

        # Tell AbletonOSC to start sending updates for this track
        self._client.send(f"/live/track/start_listen/{prop}", track_index)

    def _stop_track_listener(self, track_index: int, prop: str) -> None:
        """Stop a listener for a track property.

        Args:
            track_index: Track index (0-based)
            prop: Property name
        """
        # Tell AbletonOSC to stop sending updates for this track
        self._client.send(f"/live/track/stop_listen/{prop}", track_index)

        # Remove callback
        if prop in self._track_callbacks:
            self._track_callbacks[prop].pop(track_index, None)

            # If no more callbacks for this property, unregister dispatcher
            if not self._track_callbacks[prop]:
                response_addr = f"/live/track/get/{prop}"
                self._client.stop_listener(response_addr)
                self._dispatcher_registered.discard(prop)

    # Track Listeners

    def on_volume_change(
        self, track_index: int, callback: Callable[[int, float], None]
    ) -> None:
        """Register a callback for track volume changes.

        Args:
            track_index: Track index (0-based)
            callback: Function(track_index, volume) called on change
        """
        self._start_track_listener(track_index, "volume", callback, float)

    def stop_volume_listener(self, track_index: int) -> None:
        """Stop listening for volume changes on a track.

        Args:
            track_index: Track index (0-based)
        """
        self._stop_track_listener(track_index, "volume")

    def on_mute_change(
        self, track_index: int, callback: Callable[[int, bool], None]
    ) -> None:
        """Register a callback for track mute changes.

        Args:
            track_index: Track index (0-based)
            callback: Function(track_index, muted) called on change
        """
        self._start_track_listener(track_index, "mute", callback, bool)

    def stop_mute_listener(self, track_index: int) -> None:
        """Stop listening for mute changes on a track.

        Args:
            track_index: Track index (0-based)
        """
        self._stop_track_listener(track_index, "mute")

    def on_solo_change(
        self, track_index: int, callback: Callable[[int, bool], None]
    ) -> None:
        """Register a callback for track solo changes.

        Args:
            track_index: Track index (0-based)
            callback: Function(track_index, soloed) called on change
        """
        self._start_track_listener(track_index, "solo", callback, bool)

    def stop_solo_listener(self, track_index: int) -> None:
        """Stop listening for solo changes on a track.

        Args:
            track_index: Track index (0-based)
        """
        self._stop_track_listener(track_index, "solo")

    def on_arm_change(
        self, track_index: int, callback: Callable[[int, bool], None]
    ) -> None:
        """Register a callback for track arm changes.

        Args:
            track_index: Track index (0-based)
            callback: Function(track_index, armed) called on change
        """
        self._start_track_listener(track_index, "arm", callback, bool)

    def stop_arm_listener(self, track_index: int) -> None:
        """Stop listening for arm changes on a track.

        Args:
            track_index: Track index (0-based)
        """
        self._stop_track_listener(track_index, "arm")

    def on_panning_change(
        self, track_index: int, callback: Callable[[int, float], None]
    ) -> None:
        """Register a callback for track panning changes.

        Args:
            track_index: Track index (0-based)
            callback: Function(track_index, pan) called on change
        """
        self._start_track_listener(track_index, "panning", callback, float)

    def stop_panning_listener(self, track_index: int) -> None:
        """Stop listening for panning changes on a track.

        Args:
            track_index: Track index (0-based)
        """
        self._stop_track_listener(track_index, "panning")

    def on_name_change(
        self, track_index: int, callback: Callable[[int, str], None]
    ) -> None:
        """Register a callback for track name changes.

        Args:
            track_index: Track index (0-based)
            callback: Function(track_index, name) called on change
        """
        self._start_track_listener(track_index, "name", callback, str)

    def stop_name_listener(self, track_index: int) -> None:
        """Stop listening for name changes on a track.

        Args:
            track_index: Track index (0-based)
        """
        self._stop_track_listener(track_index, "name")
