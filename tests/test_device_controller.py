import pytest
from app import db, CACHE
from app.main.device_controller import *
from app.models import Device, Task


def device_action():
    assert False


def device_register():
    assert False


def test_refresh_devices(mocked_device_and_db):
    assert not CACHE.get_active_device(mocked_device_and_db)
    refresh_devices(devices=[mocked_device_and_db])
    assert CACHE.get_active_device(mocked_device_and_db)


def test_init_device(db_setup, mocked_device):
    init_device(mocked_device)
    device = Device.query.filter_by(uuid=mocked_device.uuid).first()
    assert device
    status_tasks = Task.query.filter_by(device=device, name='status').all()
    assert len(status_tasks) == 1


def test_device_scan():
    pass  # not trivial, not needed so far...


def test_run_scheduler(mocked_device, mocked_device_and_db):
    CACHE.add_active_device(mocked_device)
    run_scheduler(mocked_device_and_db.uuid)
    assert CACHE.has_active_scheduler(mocked_device.uuid)


@pytest.mark.parametrize('device', [
    Device(name='test-dev', uuid='jlaiwdjdilawjdljali2jli'),
    Device(name='test-dev', uuid=None)
], ids=['name+uuid', 'null-uuid'])
def test_run_scheduler_no_device_cached(db_setup, device):
    db.session.add(device)
    db.session.commit()

    with pytest.raises(ControllerError):
        run_scheduler(device.uuid)

    assert not CACHE.has_active_scheduler(device.uuid)
