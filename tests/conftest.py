import pytest

from app import create_app, db, init_device
from app.config import TestConfig
from app.device import serial, mock
from app.models import Device, Control


@pytest.fixture(scope="session", autouse=True)
def app_setup():
    application = create_app(TestConfig)
    db.drop_all()
    return application


@pytest.fixture()
def db_setup():
    db.create_all()
    yield
    db.drop_all()
    db.session.remove()


@pytest.fixture()
def mocked_device(db_setup):
    d = mock.MockedDevice()
    init_device(d)
    return d


@pytest.fixture()
def actual_serial_device(db_setup):
    serial_devs = serial.scan()
    if not serial_devs:
        pytest.skip("An actual connected serial device is needed for this test.")
    serial_dev = serial_devs[0]
    init_device(serial_dev)
    device = Device.from_status_response(
        serial_dev, serial_dev.read_status().data, create=True)
    db.session.add(device)
    db.session.commit()
    return device


@pytest.fixture()
def control(actual_serial_device):
    expected_control = "led_g"
    assert expected_control in actual_serial_device.unknown_commands

    control = Control(device=actual_serial_device, name=expected_control)
    db.session.add(control)
    db.session.commit()
    yield control
    db.session.delete(control)
    db.session.commit()
