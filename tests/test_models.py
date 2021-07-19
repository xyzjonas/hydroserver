import datetime

import pytest

from app import db
from app.models import Device, Task, Sensor, Control


@pytest.fixture()
def task(db_setup):
    device = Device(name="test_device")
    task = Task(device=device)
    db.session.add(task)
    db.session.commit()
    yield task
    db.session.delete(task)
    db.session.commit()


def test_empty_db(db_setup):
    assert not Device.query.all()


def test_task_metadata(task):
    meta = {"interval": "10-20"}
    task.task_metadata = meta
    assert task.task_metadata == meta
    del task.task_metadata
    assert not task.task_metadata


@pytest.mark.parametrize("meta", [None, "", {123, 123}])
def test_task_metadata_negative(task, meta):
    task.task_metadata = meta
    assert task.task_metadata == {}


def test_dictionary(task):
    """
        @property
    def dictionary(self):
        d = self._to_dict()
        d["meta"] = self.task_metadata
        d["sensor"] = self.sensor.dictionary if self.sensor else None
        d["control"] = self.control.dictionary if self.control else None
        return d
    """
    c = Control(name="control", device=task.device)
    s = Sensor(name="sensor", device=task.device)
    meta = {"interval": "10-20"}
    name = "name"
    date = datetime.datetime.utcnow()

    task.control = c
    task.sensor = s
    task.task_metadata = meta
    task.name = name
    task.last_run = date

    dictionary = task.dictionary
    assert dictionary.get("control") == c.dictionary
    assert dictionary.get("sensor") == s.dictionary
    assert dictionary.get("meta") == meta
    assert dictionary.get("name") == name
    assert dictionary.get("last_run") == str(date)
