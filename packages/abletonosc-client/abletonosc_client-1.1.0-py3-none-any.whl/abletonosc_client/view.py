"""View operations for AbletonOSC.

Covers /live/view/* endpoints for navigation and selection.
"""

from typing import Callable

from abletonosc_client.client import AbletonOSCClient


class View:
    """View operations like track/scene selection and navigation."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client

    def get_selected_track(self) -> int:
        """Get the currently selected track index.

        Returns:
            Selected track index (0-based)
        """
        result = self._client.query("/live/view/get/selected_track")
        return int(result[0])

    def set_selected_track(self, track_index: int) -> None:
        """Set the selected track.

        Args:
            track_index: Track index to select (0-based)
        """
        self._client.send("/live/view/set/selected_track", track_index)

    def get_selected_scene(self) -> int:
        """Get the currently selected scene index.

        Returns:
            Selected scene index (0-based)
        """
        result = self._client.query("/live/view/get/selected_scene")
        return int(result[0])

    def set_selected_scene(self, scene_index: int) -> None:
        """Set the selected scene.

        Args:
            scene_index: Scene index to select (0-based)
        """
        self._client.send("/live/view/set/selected_scene", scene_index)

    def get_detail_clip(self) -> tuple[int, int]:
        """Get the track and clip index of the clip shown in detail view.

        Returns:
            Tuple of (track_index, clip_index)
        """
        result = self._client.query("/live/view/get/detail_clip")
        return (int(result[0]), int(result[1])) if len(result) >= 2 else (-1, -1)

    def set_detail_clip(self, track_index: int, clip_index: int) -> None:
        """Set which clip is shown in detail view.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
        """
        self._client.send("/live/view/set/detail_clip", track_index, clip_index)

    def get_is_view_visible(self, view_name: str) -> bool:
        """Check if a view is visible.

        Args:
            view_name: View name (e.g., "Session", "Arranger", "Detail", "Browser")

        Returns:
            True if visible
        """
        result = self._client.query("/live/view/get/is_view_visible", view_name)
        return bool(result[0])

    def focus_view(self, view_name: str) -> None:
        """Focus a specific view.

        Args:
            view_name: View name (e.g., "Session", "Arranger", "Detail", "Browser")
        """
        self._client.send("/live/view/focus_view", view_name)

    # Clip selection

    def get_selected_clip(self) -> tuple[int, int]:
        """Get the currently selected clip.

        Returns:
            Tuple of (track_index, clip_index), or (-1, -1) if none selected
        """
        result = self._client.query("/live/view/get/selected_clip")
        return (int(result[0]), int(result[1])) if len(result) >= 2 else (-1, -1)

    def set_selected_clip(self, track_index: int, clip_index: int) -> None:
        """Set the selected clip.

        Args:
            track_index: Track index (0-based)
            clip_index: Clip/scene index (0-based)
        """
        self._client.send("/live/view/set/selected_clip", track_index, clip_index)

    # Device selection

    def get_selected_device(self) -> tuple[int, int]:
        """Get the currently selected device.

        Returns:
            Tuple of (track_index, device_index), or (-1, -1) if none selected
        """
        result = self._client.query("/live/view/get/selected_device")
        return (int(result[0]), int(result[1])) if len(result) >= 2 else (-1, -1)

    def set_selected_device(self, track_index: int, device_index: int) -> None:
        """Set the selected device.

        Args:
            track_index: Track index (0-based)
            device_index: Device index (0-based)
        """
        self._client.send("/live/view/set/selected_device", track_index, device_index)

    # Listeners

    def on_selected_track_change(self, callback: Callable[[int], None]) -> None:
        """Register a callback for track selection changes.

        Args:
            callback: Function(track_index) called when selection changes
        """
        self._client.send("/live/view/start_listen/selected_track")
        self._client.start_listener(
            "/live/view/get/selected_track",
            lambda addr, *args: callback(int(args[0])),
        )

    def stop_selected_track_listener(self) -> None:
        """Stop listening for track selection changes."""
        self._client.send("/live/view/stop_listen/selected_track")
        self._client.stop_listener("/live/view/get/selected_track")

    def on_selected_scene_change(self, callback: Callable[[int], None]) -> None:
        """Register a callback for scene selection changes.

        Args:
            callback: Function(scene_index) called when selection changes
        """
        self._client.send("/live/view/start_listen/selected_scene")
        self._client.start_listener(
            "/live/view/get/selected_scene",
            lambda addr, *args: callback(int(args[0])),
        )

    def stop_selected_scene_listener(self) -> None:
        """Stop listening for scene selection changes."""
        self._client.send("/live/view/stop_listen/selected_scene")
        self._client.stop_listener("/live/view/get/selected_scene")
