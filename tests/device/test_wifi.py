import pytest

from app.core.device.http import HttpDevice
from app.core.device import StatusResponse


@pytest.mark.parametrize("invalid_url", [
    None, 12352345234, "",
    "jliajliadjilad"
])
def test_init_invalid_url(invalid_url):
    dev = HttpDevice(url=invalid_url)
    assert dev
    assert not dev.is_connected
    assert not dev.is_responding


def test_init(actual_wifi_device):
    assert actual_wifi_device.is_connected
    assert actual_wifi_device.is_responding


def test_read_status(actual_wifi_device):
    status = actual_wifi_device.read_status()
    assert status.is_success
    assert type(status) is StatusResponse
    assert type(status.data) is dict
    assert status.data
    assert status.data['uuid']
    assert status.controls
    assert status.sensors
