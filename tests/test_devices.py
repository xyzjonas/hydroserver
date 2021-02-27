import pytest
from mock import patch

from app.device import DeviceException
from app.device.wifi import WifiDevice
from app.device.serial import SerialDevice


DEVICES = [
    WifiDevice(url="http://invalid-url/and/some/path"),
    SerialDevice(port="/dev/ttyUSB999", baud=19200)
]
DEVICES_IDS = ["wifi", "serial"]


@pytest.mark.parametrize("url", [
    None,
    "asdad&@*!HADK@&AHD@*QY",
    "http://invalid_url/but/still/url"
])
def test_wifi_init_invalid_url(url):
    device = WifiDevice(url)
    assert not device.is_site_online()
    assert not device.is_connected
    assert not device.is_responding


@pytest.mark.parametrize("baud", [None, 19200])
@pytest.mark.parametrize("port", [None, "/dev/no_such_dev"])
def test_device_serial_init_invalid_port(port, baud):
    device = SerialDevice(port, baud)
    assert not device.is_connected
    assert not device.is_responding


@pytest.mark.parametrize("device", DEVICES, ids=DEVICES_IDS)
def test_read_status_non_existent_device(device):
    with pytest.raises(DeviceException):
        device.read_status()


@pytest.mark.parametrize("command", [None, 123, 1.0, "", "bollocks"])
@pytest.mark.parametrize("device", DEVICES, ids=DEVICES_IDS)
def test_send_command_negative(device, command):
    """Whatever gets sent, we receive an empty dict"""
    assert device.send_command(command) == {}


@pytest.mark.xfail
def test_reconnect(mocked_device):
    assert mocked_device.read_status()

    with patch.object(mocked_device, "send_command", return_value={}):
        assert mocked_device.send_command("cmd") == {}
        with pytest.raises(DeviceException):
            mocked_device.read_status()
        assert not mocked_device.is_responding

    assert mocked_device.read_status()
    assert mocked_device.is_responding