import pytest
import time

from app import db
from app.models import Task, Device
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
    for i in range(task_num):
        task = Task(device=Device.query_by_serial_device(mocked_device_and_db))
        task.type = TaskType.STATUS.value
        db.session.commit()
    scheduler = Scheduler(mocked_device)
    assert len(scheduler.get_tasks_from_db()) == task_num


def test_terminate(test_config, mocked_device, mocked_device_and_db):
    scheduler = Scheduler(device=mocked_device)
    scheduler.start()
    assert scheduler.is_running
    scheduler.terminate()
    time.sleep(test_config.IDLE_INTERVAL_SECONDS + 0.2)
    assert not scheduler.is_running


# @pytest.mark.xfail("Not implemented properly yet.")
# def test_loop(test_config, mocked_device, mocked_device_and_db, status_tasks):
#     tasks = status_tasks(num_of_tasks=30)
#     scheduler = Scheduler(device=mocked_device)
#     for task_id in tasks:
#         task = Task.query.filter_by(id=task_id).first()
#         assert not task.last_run
#
#     scheduler.start()
#     time.sleep(60 + 0.2)
#     scheduler.terminate()
#
#     for task_id in tasks:
#         task = Task.query.filter_by(id=task_id).first()
#         assert task.last_run
#         assert task.last_run_success
