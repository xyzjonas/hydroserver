import pytest
from app import db, CACHE
from app.main.device_controller import *
from app.models import Device


def device_action():
    assert False


def device_register():
    assert False


def test_init_device():
    assert False


def test_device_scan():
    assert False


def test_init_devices():
    assert False


def test_run_scheduler(mocked_device, mocked_device_and_db):
    run_scheduler(mocked_device_and_db)
    assert CACHE.has_active_scheduler(mocked_device.uuid)


@pytest.mark.parametrize('device', [
    Device(name='test-dev', uuid='jlaiwdjdilawjdljali2jli'),
    Device(name='test-dev', uuid=None)
], ids=['name+uuid', 'null-uuid'])
def test_run_scheduler_no_device_cached(db_setup, device):
    db.session.add(device)
    db.session.commit()

    with pytest.raises(ControllerError):
        run_scheduler(device)

    assert not CACHE.has_active_scheduler(device.uuid)
