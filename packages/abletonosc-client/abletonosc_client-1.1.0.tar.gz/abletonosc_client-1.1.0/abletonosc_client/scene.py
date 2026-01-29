"""Scene operations for AbletonOSC.

Covers /live/scene/* endpoints for scene control.
"""

from abletonosc_client.client import AbletonOSCClient


class Scene:
    """Scene operations like firing scenes and getting/setting names."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client

    def get_name(self, scene_index: int) -> str:
        """Get the scene name.

        Args:
            scene_index: Scene index (0-based)

        Returns:
            Scene name
        """
        result = self._client.query("/live/scene/get/name", scene_index)
        # Response format: (scene_index, name)
        return str(result[1]) if len(result) > 1 else ""

    def set_name(self, scene_index: int, name: str) -> None:
        """Set the scene name.

        Args:
            scene_index: Scene index (0-based)
            name: New scene name
        """
        self._client.send("/live/scene/set/name", scene_index, name)

    def fire(self, scene_index: int) -> None:
        """Fire (launch) a scene.

        This launches all clips in the scene row.

        Args:
            scene_index: Scene index (0-based)
        """
        self._client.send("/live/scene/fire", scene_index)

    def get_color(self, scene_index: int) -> int:
        """Get the scene color.

        Args:
            scene_index: Scene index (0-based)

        Returns:
            Color as integer
        """
        result = self._client.query("/live/scene/get/color", scene_index)
        # Response format: (scene_index, color)
        return int(result[1])

    def set_color(self, scene_index: int, color: int) -> None:
        """Set the scene color.

        Args:
            scene_index: Scene index (0-based)
            color: Color as integer
        """
        self._client.send("/live/scene/set/color", scene_index, color)

    def get_tempo(self, scene_index: int) -> float:
        """Get the scene tempo (if set).

        Args:
            scene_index: Scene index (0-based)

        Returns:
            Scene tempo in BPM, or 0 if not set
        """
        result = self._client.query("/live/scene/get/tempo", scene_index)
        # Response format: (scene_index, tempo)
        return float(result[1]) if len(result) > 1 else 0.0

    def set_tempo(self, scene_index: int, tempo: float) -> None:
        """Set the scene tempo.

        Args:
            scene_index: Scene index (0-based)
            tempo: Tempo in BPM
        """
        self._client.send("/live/scene/set/tempo", scene_index, float(tempo))

    def get_is_triggered(self, scene_index: int) -> bool:
        """Check if the scene is triggered (about to play).

        Args:
            scene_index: Scene index (0-based)

        Returns:
            True if triggered
        """
        result = self._client.query("/live/scene/get/is_triggered", scene_index)
        # Response format: (scene_index, is_triggered)
        return bool(result[1])

    # Additional fire methods

    def fire_as_selected(self, scene_index: int) -> None:
        """Fire a scene and make it the selected scene.

        Args:
            scene_index: Scene index (0-based)
        """
        self._client.send("/live/scene/fire_as_selected", scene_index)

    def fire_selected(self) -> None:
        """Fire the currently selected scene.

        This fires whichever scene is currently selected in the UI.
        """
        self._client.send("/live/scene/fire_selected")

    # Color index

    def get_color_index(self, scene_index: int) -> int:
        """Get the color index of a scene.

        Args:
            scene_index: Scene index (0-based)

        Returns:
            Color index (0-69)
        """
        result = self._client.query("/live/scene/get/color_index", scene_index)
        return int(result[1]) if len(result) > 1 else 0

    def set_color_index(self, scene_index: int, color_index: int) -> None:
        """Set the color index of a scene.

        Args:
            scene_index: Scene index (0-based)
            color_index: Color index (0-69)
        """
        self._client.send("/live/scene/set/color_index", scene_index, int(color_index))

    # Is empty

    def get_is_empty(self, scene_index: int) -> bool:
        """Check if a scene is empty (has no clips).

        Args:
            scene_index: Scene index (0-based)

        Returns:
            True if scene has no clips
        """
        result = self._client.query("/live/scene/get/is_empty", scene_index)
        return bool(result[1]) if len(result) > 1 else True

    # Tempo enabled

    def get_tempo_enabled(self, scene_index: int) -> bool:
        """Check if scene tempo is enabled.

        When enabled, launching this scene will change the song tempo
        to the scene's tempo value.

        Args:
            scene_index: Scene index (0-based)

        Returns:
            True if scene tempo is enabled
        """
        result = self._client.query("/live/scene/get/tempo_enabled", scene_index)
        return bool(result[1]) if len(result) > 1 else False

    def set_tempo_enabled(self, scene_index: int, enabled: bool) -> None:
        """Enable or disable scene tempo.

        Args:
            scene_index: Scene index (0-based)
            enabled: True to enable scene tempo
        """
        self._client.send("/live/scene/set/tempo_enabled", scene_index, int(enabled))

    # Time signature

    def get_time_signature_numerator(self, scene_index: int) -> int:
        """Get the time signature numerator for a scene.

        Args:
            scene_index: Scene index (0-based)

        Returns:
            Time signature numerator (e.g., 4 for 4/4)
        """
        result = self._client.query(
            "/live/scene/get/time_signature_numerator", scene_index
        )
        return int(result[1]) if len(result) > 1 else 4

    def set_time_signature_numerator(
        self, scene_index: int, numerator: int
    ) -> None:
        """Set the time signature numerator for a scene.

        Args:
            scene_index: Scene index (0-based)
            numerator: Time signature numerator
        """
        self._client.send(
            "/live/scene/set/time_signature_numerator", scene_index, int(numerator)
        )

    def get_time_signature_denominator(self, scene_index: int) -> int:
        """Get the time signature denominator for a scene.

        Args:
            scene_index: Scene index (0-based)

        Returns:
            Time signature denominator (e.g., 4 for 4/4)
        """
        result = self._client.query(
            "/live/scene/get/time_signature_denominator", scene_index
        )
        return int(result[1]) if len(result) > 1 else 4

    def set_time_signature_denominator(
        self, scene_index: int, denominator: int
    ) -> None:
        """Set the time signature denominator for a scene.

        Args:
            scene_index: Scene index (0-based)
            denominator: Time signature denominator
        """
        self._client.send(
            "/live/scene/set/time_signature_denominator", scene_index, int(denominator)
        )

    def get_time_signature_enabled(self, scene_index: int) -> bool:
        """Check if scene time signature is enabled.

        When enabled, launching this scene will change the song time signature
        to the scene's time signature value.

        Args:
            scene_index: Scene index (0-based)

        Returns:
            True if scene time signature is enabled
        """
        result = self._client.query(
            "/live/scene/get/time_signature_enabled", scene_index
        )
        return bool(result[1]) if len(result) > 1 else False

    def set_time_signature_enabled(self, scene_index: int, enabled: bool) -> None:
        """Enable or disable scene time signature.

        Args:
            scene_index: Scene index (0-based)
            enabled: True to enable scene time signature
        """
        self._client.send(
            "/live/scene/set/time_signature_enabled", scene_index, int(enabled)
        )
