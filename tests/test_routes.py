import time

import pytest

from app.cache import CACHE
from app.scheduler.tasks import TaskType


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


def test_post_task(app_setup, mocked_device, mocked_device_and_db):
    url = f"/devices/{mocked_device_and_db.id}/tasks"
    data = {"type": TaskType.STATUS.value}
    assert not CACHE.has_active_scheduler(mocked_device.uuid)
    with app_setup.test_client() as client:
        r = client.post(url, json=data)
        assert r.status_code == 201
    time.sleep(0.2)
    assert CACHE.has_active_scheduler(mocked_device.uuid)


def test_post_run_scheduler(app_setup, mocked_device, mocked_device_and_db):
    url = f"/devices/{mocked_device_and_db.id}/scheduler"
    assert not CACHE.has_active_scheduler(mocked_device.uuid)
    with app_setup.test_client() as client:
        r = client.post(url)
        assert r.status_code == 200
    assert CACHE.has_active_scheduler(mocked_device.uuid)
