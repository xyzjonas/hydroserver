import pytest
from hydroserver.models import Device
from hydroserver import db


@pytest.fixture()
def setup():
    db.drop_all()
    db.create_all()
    yield
    db.drop_all()


def test_by_device(setup):
    pass