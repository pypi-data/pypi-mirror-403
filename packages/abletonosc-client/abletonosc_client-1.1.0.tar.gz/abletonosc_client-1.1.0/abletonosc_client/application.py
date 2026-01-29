"""Application-level operations for AbletonOSC.

Covers /live/application/* and /live/api/* endpoints.
"""

from abletonosc_client.client import AbletonOSCClient


class Application:
    """Application-level operations like version info and connection testing."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client

    def test(self, timeout: float = 2.0) -> bool:
        """Test the connection to AbletonOSC.

        Args:
            timeout: How long to wait for response

        Returns:
            True if connection is working

        Raises:
            TimeoutError: If Ableton/AbletonOSC not responding
        """
        self._client.query("/live/test", timeout=timeout)
        return True

    def get_version(self) -> str:
        """Get the Ableton Live version string.

        Returns:
            Version string (e.g., "12.0.1")
        """
        result = self._client.query("/live/application/get/version")
        return str(result[0]) if result else ""

    def get_api_version(self) -> int:
        """Get the AbletonOSC API version.

        Returns:
            API version number
        """
        result = self._client.query("/live/api/get/version")
        return int(result[0]) if result else 0

    # API Utilities

    def reload(self) -> None:
        """Reload the AbletonOSC MIDI Remote Script.

        Useful for development when editing the script without restarting Ableton.
        """
        self._client.send("/live/api/reload")

    def get_log_level(self) -> str:
        """Get the AbletonOSC log level.

        Returns:
            Log level: "debug", "info", "warning", "error", or "critical"
        """
        result = self._client.query("/live/api/get/log_level")
        return str(result[0]) if result else "info"

    def set_log_level(self, level: str) -> None:
        """Set the AbletonOSC log level.

        Args:
            level: Log level ("debug", "info", "warning", "error", "critical")

        Raises:
            ValueError: If level is not valid
        """
        valid_levels = {"debug", "info", "warning", "error", "critical"}
        if level.lower() not in valid_levels:
            raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")
        self._client.send("/live/api/set/log_level", level.lower())

    def show_message(self, message: str) -> None:
        """Display a message in Ableton's status bar.

        Args:
            message: Message to display
        """
        self._client.send("/live/api/show_message", message)
