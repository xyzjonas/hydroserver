import pytest

from app.models import Device
from app import db


def test_get(mocked_device_with_sensor_and_control):
    pass


def test_delete(mocked_device_with_sensor_and_control, app_setup):
    device, _, _ = mocked_device_with_sensor_and_control
    url = f'/devices/{device.id}'
    with app_setup.test_client() as client:
        r = client.delete(url)
        assert r.status_code == 200
    assert not db.session.query(Device).filter_by(id=device.id).first()


@pytest.mark.parametrize("url", [
    "http://obviously_a_fake_url/and/some/path",
    "not_an_url_at_all",
    "@&TGJ!KAUYDI@A@Y"
])
def test_register_invalid_url(app_setup, url):
    with app_setup.test_client() as client:
        r = client.post("/devices/register", json={"url": url})
        assert r.status_code == 500  # device registration fails


@pytest.mark.parametrize("data", [None, {}, {"url": None}, {"other_param": 12}])
def test_register_no_data(app_setup, data):
    with app_setup.test_client() as client:
        r = client.post("/devices/register", json=data)
        assert r.status_code == 400


def test_register(app_setup, actual_wifi_device, actual_serial_device_and_db):
    with app_setup.test_client() as client:
        r = client.post("/devices/register", json={"url": actual_wifi_device.url})
        assert r.status_code == 201


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
