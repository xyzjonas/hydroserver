import pytest

from app import db
from app.models import Control

@pytest.mark.parametrize("url", [
    "http://obviously_a_fake_url/and/some/path",
    "not_an_url_at_all",
    "@&TGJ!KAUYDI@A@Y"
])
def test_register_invalid_url(app_setup, url):
    with app_setup.test_client() as client:
        r = client.post("/devices/register", json={"url": url})
        assert r.status_code == 400


@pytest.mark.parametrize("data", [None, {}, {"url": None}, {"other_param": 12}])
def test_register_no_data(app_setup, data):
    with app_setup.test_client() as client:
        r = client.post("/devices/register", json=data)
        assert r.status_code == 400


def test_send_command_invalid_command(app_setup, actual_serial_device):
    with app_setup.test_client() as client:
        url = f"/devices/{actual_serial_device.id}/action"
        r = client.post(url, json={"control": "no_such"})
        assert r.status_code == 400


def test_send_command(app_setup, actual_serial_device, control):
    url = f"/devices/{actual_serial_device.id}/action"
    with app_setup.test_client() as client:
        r = client.post(url, json={"control": control.name})
        assert r.status_code == 200
