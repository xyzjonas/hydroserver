import pytest

from app import create_app, db
from app.config import TestConfig
from app.device import serial, mock, wifi
from app.main.device_controller import init_device
from app.main.device_mapper import DeviceMapper
from app.models import Control, Sensor, Task, Device
from tests.constants import WIFI_DEVICE


@pytest.fixture()
def test_config():
    return TestConfig


@pytest.fixture(scope="session", autouse=True)
def app_setup():
    application = create_app(TestConfig)
    with application.app_context():
        yield application


@pytest.fixture()
def db_setup():
    db.create_all()
    yield
    db.drop_all()
    db.session.remove()


# MOCKED
@pytest.fixture
def mocked_device():
    return mock.MockedDevice()


@pytest.fixture()
def mocked_device_and_db(mocked_device, db_setup):
    # init_device(mocked_device)
    dev = Device(
        name="mocked-" + mocked_device.uuid,
        uuid=mocked_device.uuid,
        type=mocked_device.device_type.value
    )
    db.session.add(dev)
    db.session.commit()
    dev = db.session.query(Device).get(dev.id)
    return dev


@pytest.fixture()
def mocked_device_with_sensor_and_control(mocked_device_and_db):
    c = Control(device=mocked_device_and_db, name="switch_01")
    s = Sensor(device=mocked_device_and_db, name="temp")
    db.session.add(c)
    db.session.add(s)
    db.session.commit()
    yield mocked_device_and_db, s, c
    db.session.delete(c)
    db.session.delete(s)
    db.session.commit()


# SERIAL
@pytest.fixture(scope='session')
def actual_serial_device():
    serial_devs = serial.scan()
    if not serial_devs:
        pytest.skip("An actual connected serial device is needed for this test.")
    return serial_devs[0]


@pytest.fixture()
def actual_serial_device_and_db(actual_serial_device, db_setup):
    assert init_device(actual_serial_device)
    device = DeviceMapper.from_physical(actual_serial_device).model
    return device


# WIFI
@pytest.fixture()
def actual_wifi_device():
    wifi_device = wifi.WifiDevice(url=WIFI_DEVICE)
    if not wifi_device.is_site_online():
        pytest.skip("An actual connected wifi device is needed for this test.")
    return wifi_device


@pytest.fixture()
def actual_wifi_device_and_db(actual_wifi_device, db_setup):
    init_device(actual_wifi_device)
    device = DeviceMapper.from_physical(actual_wifi_device).model
    return device


@pytest.fixture()
def control(actual_serial_device_and_db):
    device = actual_serial_device_and_db
    expected_control = "switch_01"
    assert expected_control in device.unknown_commands

    control = Control(device=device, name=expected_control)
    db.session.add(control)
    db.session.commit()
    yield control
    db.session.delete(control)
    db.session.commit()


@pytest.fixture()
def task_factory():
    params = ["task"]

    def _task(device, task_type, name=None, sensor=None, control=None, meta=None, locked=False, paused=False):
        t = Task(device=device, name=name, type=task_type, sensor=sensor,
                 control=control, task_metadata=meta, locked=locked, paused=paused)
        db.session.add(t)
        db.session.commit()
        params[0] = t
        return t
    yield _task
    task = params[0]
    db.session.delete(task)
    db.session.commit()


@pytest.fixture()
def status_tasks(mocked_device_and_db, task_factory):
    def _tasks(num_of_tasks):
        tasks = []
        for i in range(num_of_tasks):
            t = Task(device=mocked_device_and_db, type="status")
            db.session.add(t)
            db.session.commit()
            tasks.append(t.id)
        return tasks
    return _tasks
