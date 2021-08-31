import pytest
from app import db, CACHE
from app.main.device_controller import *
from app.models import Device, Task


@pytest.fixture
def device(mocked_device):
    CACHE.add_active_device(mocked_device)
    return mocked_device


def test_device_status(device, mocked_device_and_db):
    """Test that read status marks device as online"""
    controller = Controller(device)
    assert not db.session.query(Device).get(mocked_device_and_db.id).is_online
    controller.read_status()
    assert db.session.query(Device).get(mocked_device_and_db.id).is_online


@pytest.mark.parametrize(
    "return_data", [None, {}, {"status": "error"}, 123],
    ids=["none", "empty", "error", "int"]
)
def test_device_status_negative(device, mocked_device_and_db, return_data):
    """Test that read status marks device as offline"""
    def invalid_return_data(request_dict):
        return return_data
    CACHE.add_active_device(device)

    controller = Controller(mocked_device_and_db)
    controller.read_status()
    assert db.session.query(Device).get(mocked_device_and_db.id).is_online

    device._send_raw = invalid_return_data

    controller.read_status()
    assert not db.session.query(Device).get(mocked_device_and_db.id).is_online


@pytest.mark.parametrize("return_data", [
    {"status": "ok", "value": True},
    {"status": "ok", "value": 123},
    {"status": "ok", "value": 12.25},
], ids=["bool", "int", "float"])
def test_device_action(return_data, device, mocked_device_with_sensor_and_control):
    model, sensor, control = mocked_device_with_sensor_and_control

    def invalid_return_data(request_dict):
        return return_data

    assert not db.session.query(Device).get(model.id).is_online
    controller = Controller(device)

    device._send_raw = invalid_return_data

    controller.action(control=control)
    assert not db.session.query(Device).get(model.id).is_online
    control.input = type(return_data["value"]).__name__
    assert db.session.query(Control).get(control.id).parsed_value == return_data["value"]


@pytest.mark.parametrize("return_data", [
    None,
    {},
    123,
    {"status": "error"},
    {"status": "ok", "not_value_key": 12}
], ids=["none", "empty", "int", "error", "ok"]
)
def test_device_action_negative(device, mocked_device_with_sensor_and_control, return_data):
    model, sensor, control = mocked_device_with_sensor_and_control

    def invalid_return_data(request_dict):
        return return_data

    controller = Controller(device)
    controller.read_status()
    assert db.session.query(Device).get(model.id).is_online

    device._send_raw = invalid_return_data

    controller.action(control=control)
    assert not db.session.query(Device).get(model.id).is_online


def device_register():
    assert False


def test_refresh_devices(mocked_device_and_db):
    assert not CACHE.get_active_device(mocked_device_and_db)
    refresh_devices(devices=[mocked_device_and_db])
    assert CACHE.get_active_device(mocked_device_and_db)


def test_init_device(db_setup, mocked_device):
    init_device(mocked_device)
    device = db.session.query(Device).filter_by(uuid=mocked_device.uuid).first()
    assert device
    status_tasks = db.session.query(Task).filter_by(device=device, name='status').all()
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
