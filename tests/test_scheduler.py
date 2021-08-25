import time

import pytest

from app import db
from app.cache import CACHE
from app.main.device_mapper import DeviceMapper
from app.models import Task
from app.scheduler import Scheduler
from app.scheduler.tasks import TaskType


@pytest.fixture()
def status_task(mocked_device_and_db):
    t = Task(device=mocked_device_and_db, type=TaskType.STATUS.value)
    db.session.add(t)
    db.session.commit()
    return Task.query.filter_by(id=t.id).first()


@pytest.mark.parametrize("task_num", [5, 10, 50])
def test_get_tasks_from_db(mocked_device, mocked_device_and_db, task_num):
    CACHE.add_active_device(mocked_device)
    for i in range(task_num):
        task = Task(device=DeviceMapper.from_physical(mocked_device_and_db).model)
        task.type = TaskType.STATUS.value
        db.session.commit()
    scheduler = Scheduler(mocked_device, None, None)
    assert len(scheduler.get_tasks_from_db()) == task_num


def test_terminate(test_config, mocked_device, mocked_device_and_db):
    scheduler = Scheduler(mocked_device, None, None)
    scheduler.start()
    assert scheduler.is_running
    scheduler.terminate()
    time.sleep(test_config.IDLE_INTERVAL_SECONDS + 0.2)
    assert not scheduler.is_running
