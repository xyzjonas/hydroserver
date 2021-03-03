import pytest

from app.device.wifi import WifiDevice


@pytest.mark.parametrize("invalid_url", [
    None, 12352345234, "",
    "jliajliadjilad"
])
def test_init_invalid_url(invalid_url):
    dev = WifiDevice(url=invalid_url)
    assert dev
    assert not dev.is_connected
    assert not dev.is_responding


def test_init(actual_wifi_device):
    assert actual_wifi_device.is_connected
    assert actual_wifi_device.is_responding


def test_read_status(actual_wifi_device):
    r = actual_wifi_device.read_status(strict=False)
    assert r.is_success
    assert type(r.data) is dict
    assert r.data
