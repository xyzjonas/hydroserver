import pytest

from app.main.device_controller import init_devices
from app.cache import CACHE
from app.device import DeviceException
from app.device.serial import SerialDevice


@pytest.mark.parametrize("url_expected", [
    ("serial://USB_01:9600", ('USB_01', 9600)),
    ("serial://11111:9600", ('11111', 9600)),
    ("serial:///dev/ttyS0:9600", ('/dev/ttyS0', 9600)),
    ("serial://1-2:9600", ('1-2', 9600)),
    ("serial://1_2:9600", ('1_2', 9600)),
])
def test_parse_url(url_expected):
    url, expected = url_expected
    assert expected == SerialDevice.port_baud(url)


@pytest.mark.parametrize("url", [
    None, 12352345234, "", "/dev/ttyUSB123", 'serial://USB:1a', 'serial://12345'
])
def test_parse_url_negative(url):
    assert SerialDevice.port_baud(url) is None


@pytest.mark.parametrize("port", [None, 12352345234, "", "/dev/ttyUSB123"])
@pytest.mark.parametrize("baud", [None, 12352345234, -5, ""])
def test_init_negative(port, baud):
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


def test_init_from_db(actual_serial_device_and_db):
    device = actual_serial_device_and_db
    CACHE.clear_devices()
    assert not CACHE.get_active_device_by_uuid(device.uuid)
    init_devices()
    assert CACHE.get_active_device_by_uuid(device.uuid)


# FUNCTION TESTS - ROUTES
def test_send_command_invalid_command(app_setup, actual_serial_device_and_db):
    with app_setup.test_client() as client:
        url = f"/devices/{actual_serial_device_and_db.id}/action"
        r = client.post(url, json={"control": "no_such"})
        assert r.status_code == 404


def test_send_command(app_setup, actual_serial_device_and_db, control):
    url = f"/devices/{actual_serial_device_and_db.id}/action"
    with app_setup.test_client() as client:
        r = client.post(url, json={"control": control.name})
        assert r.status_code == 200

