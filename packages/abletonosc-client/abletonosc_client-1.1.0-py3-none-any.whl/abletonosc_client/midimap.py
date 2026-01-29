"""MIDI mapping operations for AbletonOSC.

Covers /live/midimap/* endpoints for MIDI controller mapping.
"""

from abletonosc_client.client import AbletonOSCClient


class MidiMap:
    """MIDI mapping operations for controlling Live parameters via MIDI CC."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client

    def map_cc(
        self,
        track_index: int,
        device_index: int,
        parameter_index: int,
        midi_channel: int,
        cc_number: int,
    ) -> None:
        """Map a MIDI CC to a device parameter.

        Creates a MIDI mapping so that sending CC messages will control
        the specified device parameter.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index within device (0-based)
            midi_channel: MIDI channel (0-15)
            cc_number: MIDI CC number (0-127)
        """
        self._client.send(
            "/live/midimap/map_cc",
            track_index,
            device_index,
            parameter_index,
            midi_channel,
            cc_number,
        )
