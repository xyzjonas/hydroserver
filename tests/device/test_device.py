import mock
import pytest

from app.main.device_controller import init_device
from app.device import DeviceException, DeviceCommunicationException, DeviceResponse
from app.device import mock, Status
from app.device.serial import SerialDevice
from app.device.wifi import WifiDevice
from app.main.device_mapper import DeviceMapper


DEVICES = [
    WifiDevice(url="http://invalid-url/and/some/path"),
    SerialDevice(port="/dev/ttyUSB999", baud=19200)
]
DEVICES_IDS = [
    "wifi",
    "serial"
]


def test_init_device(db_setup):
    d = mock.MockedDevice()
    assert init_device(d)
    device_db = DeviceMapper.from_physical(d).model
    assert device_db
    assert len(device_db.tasks) == 1
    assert device_db.tasks[0].cron == 'status'
    assert device_db.tasks[0].type == 'status'


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
    """Whatever gets sent, exception is raised"""
    with pytest.raises(DeviceCommunicationException):
        device.send_command(command)


@pytest.mark.xfail
def test_reconnect(mocked_device):
    assert mocked_device.read_status()

    with mock.patch.object(mocked_device, "send_command", return_value={}):
        assert mocked_device.send_command("cmd") == {}
        with pytest.raises(DeviceException):
            mocked_device.read_status()
        assert not mocked_device.is_responding

    assert mocked_device.read_status()
    assert mocked_device.is_responding


@pytest.mark.parametrize(
    "data",
    [None, "", 123, {'status': None}, {'status': 'invalid'}],
    ids=['none', 'empty_str', 'integer', 'status_none', 'invalid_status']
)
def test_parse_device_response_malformed(data):
    response = DeviceResponse.from_response_data(data=data)
    assert response.status == Status.MALFORMED


def test_parse_device_response_empty():
    response = DeviceResponse.from_response_data(data={})
    assert response.status == Status.NO_DATA


@pytest.mark.parametrize("data", [
    {"status": ""},
    {"status": None},
    {"status": 123},
    {"status": "error"},
])
def test_parse_device_response_nok(data):
    res = DeviceResponse.from_response_data(data=data)
    assert not res.is_success


def test_parse_device_response_ok():
    res = DeviceResponse.from_response_data(data={"status": "ok"})
    assert res.is_success
