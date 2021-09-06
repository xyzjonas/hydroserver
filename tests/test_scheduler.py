import time

import pytest

from app import db
from app.core.cache import CACHE
from app.system.device_mapper import DeviceMapper
from app.models import Task
from app.core.scheduler import Scheduler
from app.core.tasks import TaskType


@pytest.fixture()
def status_task(mocked_device_and_db):
    t = Task(device=mocked_device_and_db, type=TaskType.STATUS.value)
    db.session.add(t)
    db.session.commit()
    return db.session.query(Task).filter_by(id=t.id).first()


@pytest.mark.parametrize("task_num", [5, 10, 50])
def test_get_tasks_from_db(mocked_device, mocked_device_and_db, task_num):
    CACHE.add_active_device(mocked_device)
    for i in range(task_num):
        task = Task(device=DeviceMapper.from_physical(mocked_device_and_db).model)
        task.type = TaskType.STATUS.value
        db.session.commit()
    scheduler = Scheduler(mocked_device)
    assert len(scheduler.get_tasks_from_db()) == task_num


def test_get_tasks_from_db_and_edit(mocked_device, mocked_device_with_sensor_and_control):
    CACHE.add_active_device(mocked_device)
    device, s, c = mocked_device_with_sensor_and_control
    name = 'test task 12345'
    type_ = TaskType.STATUS.value
    cron = '1 2 3 * *'

    task = Task(name=name, device=device, type=type_, cron=cron)
    db.session.add(task)
    db.session.commit()

    scheduler = Scheduler(mocked_device)
    tasks_1 = scheduler.get_tasks_from_db()

    task = db.session.query(Task).filter_by(name=name).first()
    assert task
    task.name = "Another name"
    task.cron = "* * * * *"
    db.session.commit()

    tasks_2 = scheduler.get_tasks_from_db()
    # todo


def test_terminate(test_config, mocked_device, mocked_device_and_db):
    CACHE.add_active_device(mocked_device)
    scheduler = Scheduler(mocked_device)
    scheduler.start()
    assert scheduler.is_running
    scheduler.terminate()
    time.sleep(test_config.IDLE_INTERVAL_SECONDS + 0.2)
    assert not scheduler.is_running
