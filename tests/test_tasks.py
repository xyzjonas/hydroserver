import pytest

from app import db, init_device
from app.models import Task, Device, Sensor, Control
from app.scheduler.tasks import TaskRunnable, ScheduledTask, TaskType


def test_from_db_object_status(mocked_device):
    task = Task(device=Device.query_by_serial_device(mocked_device))
    task.type = TaskType.STATUS.value
    task.cron = "* * * * *"

    sch = ScheduledTask.from_db_object(task)
    assert sch


def test_from_db_object_toggle(mocked_device):
    db_device = Device.query_by_serial_device(mocked_device)
    task = Task(device=db_device)
    task.type = TaskType.TOGGLE.value
    task.cron = "* * * * *"
    task.control = Control(name="control", device=db_device)
    db.session.commit()

    sch = ScheduledTask.from_db_object(task)
    assert sch


def test_from_db_object_interval(mocked_device):
    db_device = Device.query_by_serial_device(mocked_device)
    task = Task(device=db_device)
    task.type = TaskType.INTERVAL.value
    task.cron = "* * * * *"
    task.sensor = Sensor(name="sensor", device=db_device)
    task.control = Control(name="control", device=db_device)
    task.task_metadata = {"interval": "10-20"}
    db.session.commit()

    sch = ScheduledTask.from_db_object(task)
    assert sch
