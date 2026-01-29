"""Tests for Device operations.

Note: Many tests require a device on track 0.
Tests will be skipped if no device exists.
"""

import pytest


@pytest.fixture
def device_exists(track, device):
    """Check if a device exists on track 0."""
    num_devices = track.get_num_devices(0)
    if num_devices == 0:
        pytest.skip("No devices on track 0")
    return True


def test_get_name(device, device_exists):
    """Test getting device name."""
    name = device.get_name(0, 0)
    assert isinstance(name, str)


def test_get_class_name(device, device_exists):
    """Test getting device class name."""
    class_name = device.get_class_name(0, 0)
    assert isinstance(class_name, str)


def test_get_is_active(device, device_exists):
    """Test checking if device is active."""
    is_active = device.get_is_active(0, 0)
    assert isinstance(is_active, bool)


def test_set_is_active(device, device_exists):
    """Test enabling/disabling device."""
    original = device.get_is_active(0, 0)
    try:
        device.set_is_active(0, 0, False)
        assert device.get_is_active(0, 0) is False

        device.set_is_active(0, 0, True)
        assert device.get_is_active(0, 0) is True
    finally:
        device.set_is_active(0, 0, original)


def test_get_num_parameters(device, device_exists):
    """Test getting parameter count."""
    num_params = device.get_num_parameters(0, 0)
    assert num_params >= 0


def test_get_parameter_value(device, device_exists):
    """Test getting parameter value."""
    num_params = device.get_num_parameters(0, 0)
    if num_params == 0:
        pytest.skip("Device has no parameters")

    value = device.get_parameter_value(0, 0, 0)
    assert isinstance(value, float)


def test_get_parameter_name(device, device_exists):
    """Test getting parameter name."""
    num_params = device.get_num_parameters(0, 0)
    if num_params == 0:
        pytest.skip("Device has no parameters")

    name = device.get_parameter_name(0, 0, 0)
    assert isinstance(name, str)


def test_get_parameter_min_max(device, device_exists):
    """Test getting parameter min/max."""
    num_params = device.get_num_parameters(0, 0)
    if num_params == 0:
        pytest.skip("Device has no parameters")

    min_val = device.get_parameter_min(0, 0, 0)
    max_val = device.get_parameter_max(0, 0, 0)

    assert isinstance(min_val, float)
    assert isinstance(max_val, float)
    assert min_val <= max_val


# New endpoint tests (Gap Coverage - Batch Operations)


def test_get_type(device, device_exists):
    """Test getting device type."""
    device_type = device.get_type(0, 0)
    assert isinstance(device_type, int)
    # 0=audio_effect, 1=instrument, 2=midi_effect
    assert 0 <= device_type <= 2


def test_get_parameters_names(device, device_exists):
    """Test getting all parameter names in bulk."""
    names = device.get_parameters_names(0, 0)
    assert isinstance(names, tuple)


def test_get_parameters_values(device, device_exists):
    """Test getting all parameter values in bulk."""
    values = device.get_parameters_values(0, 0)
    assert isinstance(values, tuple)


def test_get_parameters_mins(device, device_exists):
    """Test getting all parameter minimums in bulk."""
    mins = device.get_parameters_mins(0, 0)
    assert isinstance(mins, tuple)


def test_get_parameters_maxs(device, device_exists):
    """Test getting all parameter maximums in bulk."""
    maxs = device.get_parameters_maxs(0, 0)
    assert isinstance(maxs, tuple)


def test_get_parameters_is_quantized(device, device_exists):
    """Test getting all parameter quantized states in bulk."""
    quantized = device.get_parameters_is_quantized(0, 0)
    assert isinstance(quantized, tuple)


def test_get_parameter_value_string(device, device_exists):
    """Test getting parameter display string."""
    num_params = device.get_num_parameters(0, 0)
    if num_params == 0:
        pytest.skip("Device has no parameters")

    value_string = device.get_parameter_value_string(0, 0, 0)
    assert isinstance(value_string, str)
