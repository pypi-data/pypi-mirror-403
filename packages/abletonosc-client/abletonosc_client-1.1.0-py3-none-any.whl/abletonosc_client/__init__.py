"""OSC client wrapper for AbletonOSC.

Provides a Pythonic interface to control Ableton Live via OSC.
"""

from abletonosc_client.application import Application
from abletonosc_client.browser import Browser
from abletonosc_client.client import AbletonOSCClient
from abletonosc_client.clip import Clip
from abletonosc_client.clip_slot import ClipSlot
from abletonosc_client.device import Device
from abletonosc_client.midimap import MidiMap
from abletonosc_client.scene import Scene
from abletonosc_client.song import Song
from abletonosc_client.track import Track
from abletonosc_client.view import View
from abletonosc_client import scales
from abletonosc_client import chords

__all__ = [
    "AbletonOSCClient",
    "Application",
    "Browser",
    "Clip",
    "ClipSlot",
    "Device",
    "MidiMap",
    "Scene",
    "Song",
    "Track",
    "View",
    "connect",
    "scales",
    "chords",
]


def connect(
    host: str = "127.0.0.1",
    send_port: int = 11000,
    receive_port: int = 11001,
) -> AbletonOSCClient:
    """Create and return an AbletonOSC client.

    Convenience function to create a client with default settings.

    Args:
        host: Ableton host address (default: localhost)
        send_port: Port to send OSC messages (default: 11000)
        receive_port: Port to receive OSC responses (default: 11001)

    Returns:
        Connected AbletonOSCClient instance
    """
    return AbletonOSCClient(host, send_port, receive_port)
