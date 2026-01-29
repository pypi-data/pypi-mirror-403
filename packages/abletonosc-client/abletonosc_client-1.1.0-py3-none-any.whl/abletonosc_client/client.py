"""Core OSC transport layer for AbletonOSC communication."""

import threading
from typing import Any, Callable

from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer


class AbletonOSCClient:
    """OSC client for communicating with AbletonOSC.

    Handles sending messages and receiving responses via UDP.
    Default ports: send to 11000, receive on 11001.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        send_port: int = 11000,
        receive_port: int = 11001,
    ):
        self.host = host
        self.send_port = send_port
        self.receive_port = receive_port

        # Outbound client
        self._client = udp_client.SimpleUDPClient(host, send_port)

        # Response handling
        self._pending_responses: dict[str, tuple[threading.Event, list]] = {}
        self._listeners: dict[str, Callable] = {}

        # Set up dispatcher and server for receiving
        self._dispatcher = Dispatcher()
        self._dispatcher.set_default_handler(self._handle_response)

        self._server = ThreadingOSCUDPServer(
            (host, receive_port),
            self._dispatcher,
        )
        self._server_thread = threading.Thread(target=self._server.serve_forever)
        self._server_thread.daemon = True
        self._server_thread.start()

    def _handle_response(self, address: str, *args: Any) -> None:
        """Handle incoming OSC messages.

        Routes to pending query responses or registered listeners.
        """
        # Check if this is a response to a pending query
        if address in self._pending_responses:
            event, result = self._pending_responses[address]
            result.extend(args)
            event.set()

        # Check if there's a listener registered
        if address in self._listeners:
            self._listeners[address](address, *args)

    def send(self, address: str, *args: Any) -> None:
        """Send an OSC message (fire-and-forget).

        Args:
            address: OSC address pattern (e.g., "/live/song/set/tempo")
            *args: Arguments to send with the message
        """
        self._client.send_message(address, list(args) if args else [])

    def query(self, address: str, *args: Any, timeout: float = 2.0) -> tuple:
        """Send an OSC message and wait for response.

        Args:
            address: OSC address pattern (e.g., "/live/song/get/tempo")
            *args: Arguments to send with the message
            timeout: How long to wait for response in seconds

        Returns:
            Tuple of response arguments

        Raises:
            TimeoutError: If no response received within timeout
        """
        event = threading.Event()
        result: list = []

        # Register for response
        self._pending_responses[address] = (event, result)

        try:
            # Send the query
            self._client.send_message(address, list(args) if args else [])

            # Wait for response
            if not event.wait(timeout):
                raise TimeoutError(f"No response for {address} within {timeout}s")

            return tuple(result)
        finally:
            # Cleanup
            self._pending_responses.pop(address, None)

    def start_listener(self, address: str, callback: Callable) -> None:
        """Register a callback for messages at an address.

        Args:
            address: OSC address to listen for
            callback: Function(address, *args) to call on message
        """
        self._listeners[address] = callback

    def stop_listener(self, address: str) -> None:
        """Unregister a callback for an address.

        Args:
            address: OSC address to stop listening for
        """
        self._listeners.pop(address, None)

    def close(self) -> None:
        """Cleanup resources and stop the server."""
        self._server.shutdown()
        self._server_thread.join(timeout=1.0)
