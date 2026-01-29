"""Device operations for AbletonOSC.

Covers /live/device/* endpoints for device and parameter control.
"""

from typing import Callable, NamedTuple

from abletonosc_client.client import AbletonOSCClient


class Parameter(NamedTuple):
    """Represents a device parameter.

    Attributes:
        index: Parameter index within the device
        name: Parameter name
        value: Current value
        min: Minimum value
        max: Maximum value
    """

    index: int
    name: str
    value: float
    min: float
    max: float


class Device:
    """Device operations like getting/setting parameters."""

    def __init__(self, client: AbletonOSCClient):
        self._client = client
        # Listener callbacks: {(track_idx, device_idx, param_idx): callback}
        self._param_callbacks: dict[tuple[int, int, int], Callable] = {}
        self._dispatcher_registered: bool = False

    def get_name(self, track_index: int, device_index: int) -> str:
        """Get the device name.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Device name
        """
        result = self._client.query(
            "/live/device/get/name", track_index, device_index
        )
        # Response format: (track_index, device_index, name)
        return str(result[2]) if len(result) > 2 else ""

    def get_class_name(self, track_index: int, device_index: int) -> str:
        """Get the device class name (type).

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Device class name (e.g., "Compressor", "Reverb")
        """
        result = self._client.query(
            "/live/device/get/class_name", track_index, device_index
        )
        # Response format: (track_index, device_index, class_name)
        return str(result[2]) if len(result) > 2 else ""

    def get_is_active(self, track_index: int, device_index: int) -> bool:
        """Check if the device is active (enabled).

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            True if device is active
        """
        result = self._client.query(
            "/live/device/get/is_active", track_index, device_index
        )
        # Response format: (track_index, device_index, is_active)
        return bool(result[2])

    def set_is_active(
        self, track_index: int, device_index: int, active: bool
    ) -> None:
        """Enable or disable a device.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            active: True to enable, False to bypass
        """
        self._client.send(
            "/live/device/set/is_active", track_index, device_index, int(active)
        )

    def get_num_parameters(self, track_index: int, device_index: int) -> int:
        """Get the number of parameters on a device.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Number of parameters
        """
        result = self._client.query(
            "/live/device/get/num_parameters", track_index, device_index
        )
        # Response format: (track_index, device_index, num_parameters)
        return int(result[2])

    def get_parameter_value(
        self, track_index: int, device_index: int, parameter_index: int
    ) -> float:
        """Get a parameter value.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index (0-based)

        Returns:
            Current parameter value
        """
        result = self._client.query(
            "/live/device/get/parameter/value",
            track_index,
            device_index,
            parameter_index,
        )
        # Response format: (track_index, device_index, parameter_index, value)
        return float(result[3])

    def set_parameter_value(
        self,
        track_index: int,
        device_index: int,
        parameter_index: int,
        value: float,
    ) -> None:
        """Set a parameter value.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index (0-based)
            value: New parameter value
        """
        self._client.send(
            "/live/device/set/parameter/value",
            track_index,
            device_index,
            parameter_index,
            float(value),
        )

    def get_parameter_name(
        self, track_index: int, device_index: int, parameter_index: int
    ) -> str:
        """Get a parameter name.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index (0-based)

        Returns:
            Parameter name
        """
        result = self._client.query(
            "/live/device/get/parameter/name",
            track_index,
            device_index,
            parameter_index,
        )
        # Response format: (track_index, device_index, parameter_index, name)
        return str(result[3]) if len(result) > 3 else ""

    def get_parameter_min(
        self, track_index: int, device_index: int, parameter_index: int
    ) -> float:
        """Get a parameter's minimum value.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index (0-based)

        Returns:
            Minimum parameter value
        """
        result = self._client.query(
            "/live/device/get/parameter/min",
            track_index,
            device_index,
            parameter_index,
        )
        # Response format: (track_index, device_index, parameter_index, min)
        return float(result[3])

    def get_parameter_max(
        self, track_index: int, device_index: int, parameter_index: int
    ) -> float:
        """Get a parameter's maximum value.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index (0-based)

        Returns:
            Maximum parameter value
        """
        result = self._client.query(
            "/live/device/get/parameter/max",
            track_index,
            device_index,
            parameter_index,
        )
        # Response format: (track_index, device_index, parameter_index, max)
        return float(result[3])

    def get_parameters(
        self, track_index: int, device_index: int
    ) -> list[Parameter]:
        """Get all parameters for a device.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            List of Parameter objects
        """
        num_params = self.get_num_parameters(track_index, device_index)
        parameters = []

        for i in range(num_params):
            name = self.get_parameter_name(track_index, device_index, i)
            value = self.get_parameter_value(track_index, device_index, i)
            min_val = self.get_parameter_min(track_index, device_index, i)
            max_val = self.get_parameter_max(track_index, device_index, i)
            parameters.append(
                Parameter(index=i, name=name, value=value, min=min_val, max=max_val)
            )

        return parameters

    # Device type

    def get_type(self, track_index: int, device_index: int) -> int:
        """Get the device type.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Device type (0=audio_effect, 1=instrument, 2=midi_effect)
        """
        result = self._client.query(
            "/live/device/get/type", track_index, device_index
        )
        return int(result[2]) if len(result) > 2 else 0

    # Bulk parameter operations

    def get_parameters_names(self, track_index: int, device_index: int) -> tuple:
        """Get all parameter names for a device in a single query.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Tuple of parameter names
        """
        result = self._client.query(
            "/live/device/get/parameters/name", track_index, device_index
        )
        # Response format: (track_index, device_index, name1, name2, ...)
        return result[2:] if len(result) > 2 else ()

    def get_parameters_values(self, track_index: int, device_index: int) -> tuple:
        """Get all parameter values for a device in a single query.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Tuple of parameter values
        """
        result = self._client.query(
            "/live/device/get/parameters/value", track_index, device_index
        )
        return result[2:] if len(result) > 2 else ()

    def set_parameters_values(
        self, track_index: int, device_index: int, values: list[float]
    ) -> None:
        """Set all parameter values for a device in a single call.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            values: List of parameter values (one per parameter)
        """
        self._client.send(
            "/live/device/set/parameters/value",
            track_index,
            device_index,
            *[float(v) for v in values],
        )

    def get_parameters_mins(self, track_index: int, device_index: int) -> tuple:
        """Get all parameter minimum values for a device.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Tuple of minimum values
        """
        result = self._client.query(
            "/live/device/get/parameters/min", track_index, device_index
        )
        return result[2:] if len(result) > 2 else ()

    def get_parameters_maxs(self, track_index: int, device_index: int) -> tuple:
        """Get all parameter maximum values for a device.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Tuple of maximum values
        """
        result = self._client.query(
            "/live/device/get/parameters/max", track_index, device_index
        )
        return result[2:] if len(result) > 2 else ()

    def get_parameters_is_quantized(
        self, track_index: int, device_index: int
    ) -> tuple:
        """Get which parameters are quantized (stepped) for a device.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)

        Returns:
            Tuple of booleans indicating if each parameter is quantized
        """
        result = self._client.query(
            "/live/device/get/parameters/is_quantized", track_index, device_index
        )
        return tuple(bool(v) for v in result[2:]) if len(result) > 2 else ()

    # Parameter value string

    def get_parameter_value_string(
        self, track_index: int, device_index: int, parameter_index: int
    ) -> str:
        """Get a parameter's display string (formatted value with units).

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index (0-based)

        Returns:
            Formatted parameter value string (e.g., "440 Hz", "-12 dB")
        """
        result = self._client.query(
            "/live/device/get/parameter/value_string",
            track_index,
            device_index,
            parameter_index,
        )
        return str(result[3]) if len(result) > 3 else ""

    # Parameter listener

    def _param_dispatcher(self, addr, *args):
        """Dispatch parameter value updates to registered callbacks."""
        # Response format: (track_index, device_index, param_index, value)
        if len(args) >= 4:
            key = (int(args[0]), int(args[1]), int(args[2]))
            value = float(args[3])
            if key in self._param_callbacks:
                callback = self._param_callbacks[key]
                callback(key[0], key[1], key[2], value)

    def on_parameter_value_change(
        self,
        track_index: int,
        device_index: int,
        parameter_index: int,
        callback: Callable[[int, int, int, float], None],
    ) -> None:
        """Register a callback for parameter value changes.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index (0-based)
            callback: Function(track_index, device_index, param_index, value)
        """
        key = (track_index, device_index, parameter_index)
        self._param_callbacks[key] = callback

        # Register dispatcher if not already done
        if not self._dispatcher_registered:
            self._client.start_listener(
                "/live/device/get/parameter/value", self._param_dispatcher
            )
            self._dispatcher_registered = True

        # Tell AbletonOSC to start sending updates
        self._client.send(
            "/live/device/start_listen/parameter/value",
            track_index,
            device_index,
            parameter_index,
        )

    def stop_parameter_value_listener(
        self, track_index: int, device_index: int, parameter_index: int
    ) -> None:
        """Stop listening for parameter value changes.

        Args:
            track_index: Track index (0-based)
            device_index: Device index on track (0-based)
            parameter_index: Parameter index (0-based)
        """
        # Tell AbletonOSC to stop sending updates
        self._client.send(
            "/live/device/stop_listen/parameter/value",
            track_index,
            device_index,
            parameter_index,
        )

        # Remove callback
        key = (track_index, device_index, parameter_index)
        self._param_callbacks.pop(key, None)

        # If no more callbacks, unregister dispatcher
        if not self._param_callbacks and self._dispatcher_registered:
            self._client.stop_listener("/live/device/get/parameter/value")
            self._dispatcher_registered = False
