import pytest
from app import create_app, db, init_device
from app.device.mock import MockedDevice
from app.config import TestConfig


@pytest.fixture(scope="session", autouse=True)
def app_setup():
    application = create_app(TestConfig)
    db.drop_all()
    return application


@pytest.fixture()
def setup():
    db.create_all()
    yield
    db.drop_all()
    db.session.remove()


@pytest.fixture()
def mocked_device(setup):
    d = MockedDevice()
    init_device(d)
    return d
