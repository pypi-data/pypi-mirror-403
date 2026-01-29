"""Tests for MidiMap operations.

Note: MidiMap.map_cc is a fire-and-forget operation that creates a MIDI mapping.
Testing is limited as we can't easily verify the mapping was created.
"""

import pytest

from abletonosc_client.midimap import MidiMap


def test_midimap_init(client):
    """Test MidiMap initialization."""
    midimap = MidiMap(client)
    assert midimap is not None


@pytest.mark.skip(reason="map_cc requires device on track 0 and cannot be easily verified")
def test_map_cc(midimap, device, track):
    """Test mapping a CC to a device parameter."""
    # Ensure we have a device on track 0
    num_devices = track.get_num_devices(0)
    if num_devices == 0:
        pytest.skip("No devices on track 0")

    # Map CC 1 on channel 0 to parameter 0 of device 0 on track 0
    # This is a fire-and-forget operation, so we just verify no error
    midimap.map_cc(0, 0, 0, 0, 1)
