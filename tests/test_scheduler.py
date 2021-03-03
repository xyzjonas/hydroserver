import pytest
import time

from app import db
from app.models import Task, Device
from app.scheduler import Scheduler
from app.scheduler.tasks import TaskType


# @pytest.mark.parametrize("task_num", [1])
# def test_task_executed(task_num, device):
#     dev_db = Device.query_by_serial_device(device)
#
#     tasks = []
#     for i in range(task_num):
#         t = Task(device=dev_db)
#         t.type = TaskType.STATUS.value
#         tasks.append(t)
#         db.session.add(t)
#         # db.session.add(t)
#     db.session.commit()
#     x = db
#
#     assert len(dev_db.tasks) == task_num
#     assert not any([t.last_run_success for t in tasks])
#     sched = Scheduler(device)
#     sched.start()
#
#     time.sleep(70)
#     sched.terminate()
#
#     tasks_db = Task.query.all()
#     assert all([t.last_run_success for t in tasks_db])

#
# def test_is_running(device):
#     sched = Scheduler(device)
#     sched.start()
#     assert sched.is_running
#     sched.terminate()
#
#     time.sleep(15)
#
#     assert not sched.is_running


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
