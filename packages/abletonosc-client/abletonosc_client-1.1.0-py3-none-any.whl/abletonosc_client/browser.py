"""Browser operations for AbletonOSC.

Provides access to Ableton's browser for exploring packs and loading devices.
Covers /live/browser/* endpoints.
"""

from typing import List, Tuple, Optional

from abletonosc_client.client import AbletonOSCClient


class Browser:
    """Browser operations for exploring packs and loading devices."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client

    # =============================================================================
    # Pack Exploration
    # =============================================================================

    def list_packs(self) -> List[str]:
        """List all installed pack names.

        Returns:
            List of pack names
        """
        result = self._client.query("/live/browser/list_packs")
        return list(result) if result else []

    def list_pack_contents(
        self, pack_name: str, max_depth: int = 10
    ) -> List[str]:
        """List all loadable items in a pack.

        Returns paths to all loadable items (presets, instruments, etc.)
        within the specified pack.

        Args:
            pack_name: Name of the pack to explore (can be partial match)
            max_depth: Maximum folder depth to search (default: 10)

        Returns:
            List of item paths (e.g., "Pack/Folder/Preset.adv")
        """
        result = self._client.query(
            "/live/browser/list_pack_contents", pack_name, max_depth
        )
        return list(result) if result else []

    # =============================================================================
    # Search
    # =============================================================================

    def search(
        self, query: str, max_results: int = 50, max_depth: int = 10
    ) -> List[Tuple[str, str, str]]:
        """Search all packs for items matching a query.

        Performs a recursive search through all installed packs to find
        items (presets, instruments, effects) matching the query string.

        Args:
            query: Search string (case-insensitive partial match)
            max_results: Maximum number of results to return (default: 50)
            max_depth: Maximum folder depth to search (default: 10)

        Returns:
            List of tuples: (item_name, pack_name, full_path)
        """
        result = self._client.query(
            "/live/browser/search", query, max_results, max_depth
        )
        if not result:
            return []

        # Parse results: each is "item_name|pack_name|path"
        parsed = []
        for item in result:
            parts = str(item).split("|")
            if len(parts) == 3:
                parsed.append((parts[0], parts[1], parts[2]))
        return parsed

    def search_and_load(self, query: str) -> str:
        """Search for an item and load the first match.

        Searches all packs and standard browser locations for an item
        matching the query. If found, loads it into the currently
        selected track.

        Args:
            query: Search string (case-insensitive partial match)

        Returns:
            Name of the loaded item, or empty string if not found
        """
        result = self._client.query("/live/browser/search_and_load", query)
        return str(result[0]) if result and result[0] else ""

    # =============================================================================
    # Loading Items
    # =============================================================================

    def load_item(self, full_path: str) -> bool:
        """Load a browser item by its full path.

        The path should be in the format returned by list_pack_contents
        or search, e.g., "Pack Name/Folder/Subfolder/Item Name"

        Args:
            full_path: Full path to the item

        Returns:
            True if successfully loaded, False otherwise
        """
        result = self._client.query("/live/browser/load_item", full_path)
        return result[0] == 1 if result else False

    # =============================================================================
    # Standard Browser Locations
    # =============================================================================

    def list_instruments(self) -> List[str]:
        """List top-level items in the instruments browser.

        Returns:
            List of instrument names/folder names
        """
        result = self._client.query("/live/browser/list_instruments")
        return list(result) if result else []

    def list_audio_effects(self) -> List[str]:
        """List top-level items in the audio effects browser.

        Returns:
            List of audio effect names/folder names
        """
        result = self._client.query("/live/browser/list_audio_effects")
        return list(result) if result else []

    def list_midi_effects(self) -> List[str]:
        """List top-level items in the MIDI effects browser.

        Returns:
            List of MIDI effect names/folder names
        """
        result = self._client.query("/live/browser/list_midi_effects")
        return list(result) if result else []

    def list_drums(self) -> List[str]:
        """List top-level items in the drums browser.

        Returns:
            List of drum kit names/folder names
        """
        result = self._client.query("/live/browser/list_drums")
        return list(result) if result else []

    def list_sounds(self) -> List[str]:
        """List top-level items in the sounds browser.

        Returns:
            List of sound names/folder names
        """
        result = self._client.query("/live/browser/list_sounds")
        return list(result) if result else []
