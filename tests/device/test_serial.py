import pytest
from app.device import DeviceException
from app.device.serial import SerialDevice


@pytest.mark.parametrize("port", [None, 12352345234, "", "/dev/ttyUSB123"])
@pytest.mark.parametrize("baud", [None, 12352345234, -5, ""])
def test_init(port, baud):
    dev = SerialDevice(port=port, baud=baud)
    assert dev
    assert not dev.is_connected
    assert not dev.is_responding


@pytest.mark.parametrize("invalid_control", [None, 12, "c"])
def test_send_control_negative(actual_serial_device, invalid_control):
    with pytest.raises(DeviceException):
        actual_serial_device.send_control(invalid_control)


def test_send_control(actual_serial_device, control):
    actual_serial_device.send_control(control.name)


# FUNCTION TESTS - ROUTES
def test_send_command_invalid_command(app_setup, actual_serial_device_and_db):
    with app_setup.test_client() as client:
        url = f"/devices/{actual_serial_device_and_db.id}/action"
        r = client.post(url, json={"control": "no_such"})
        assert r.status_code == 400


def test_send_command(app_setup, actual_serial_device_and_db, control):
    url = f"/devices/{actual_serial_device_and_db.id}/action"
    with app_setup.test_client() as client:
        r = client.post(url, json={"control": control.name})
        assert r.status_code == 200

