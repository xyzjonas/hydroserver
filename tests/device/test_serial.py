import pytest
from app import CACHE
from app.device import DeviceException


@pytest.fixture()
def serial_device(actual_serial_device):
    serial = CACHE.get_active_device(actual_serial_device.uuid)
    assert serial
    return serial


@pytest.mark.parametrize("invalid_control", [None, 12, "c"])
def test_send_control_negative(serial_device, invalid_control):
    with pytest.raises(DeviceException):
        serial_device.send_control(invalid_control)


def test_send_control(serial_device, control):
    serial_device.send_control(control.name)
