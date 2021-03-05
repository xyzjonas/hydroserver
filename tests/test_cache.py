import pytest

from app.cache import CACHE


def test_add(mocked_device):
    CACHE.add_active_device(mocked_device)
    assert CACHE.get_active_device_by_uuid(mocked_device.uuid)


def test_add_double(mocked_device):
    CACHE.add_active_device(mocked_device)
    assert CACHE.get_active_device_by_uuid(mocked_device.uuid)
    CACHE.add_active_device(mocked_device)
    assert CACHE.get_active_device_by_uuid(mocked_device.uuid).uuid == mocked_device.uuid


def test_remove(mocked_device):
    CACHE.add_active_device(mocked_device)
    assert CACHE.get_active_device_by_uuid(mocked_device.uuid)
    CACHE.remove_active_device(mocked_device)
    assert not CACHE.get_active_device_by_uuid(mocked_device.uuid)


@pytest.mark.parametrize("uuid", [None, 123, -100, "", "122adas"])
def test_get_negative(uuid):
    assert CACHE.get_active_device_by_uuid(uuid) is None
