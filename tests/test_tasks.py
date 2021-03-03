import pytest

from app import db
from app.models import Task, Device, Sensor, Control
from app.scheduler.tasks import ScheduledTask, TaskType, \
    Toggle, Interval, Status, \
    TaskNotCreatedException, TaskRunnable


@pytest.fixture()
def task():
    def _task(device, task_type, sensor=None, control=None, meta=None):
        t = Task(device=device, type=task_type, sensor=sensor,
                 control=control, task_metadata=meta)
        db.session.add(t)
        db.session.commit()
        return t

    return _task


def test_from_db_object_status(mocked_device_and_db, task):
    t = task(mocked_device_and_db, TaskType.STATUS.value)
    sch = ScheduledTask.from_db_object(t)
    assert sch


def test_from_db_object_toggle(mocked_device_and_db):
    db_device = mocked_device_and_db
    task = Task(device=db_device)
    task.type = TaskType.TOGGLE.value
    task.cron = "* * * * *"
    task.control = Control(name="control", device=db_device)
    db.session.commit()

    sch = ScheduledTask.from_db_object(task)
    assert sch


def test_from_db_object_interval(mocked_device_and_db):
    db_device = mocked_device_and_db
    task = Task(device=db_device)
    task.type = TaskType.INTERVAL.value
    task.cron = "* * * * *"
    task.sensor = Sensor(name="sensor", device=db_device)
    task.control = Control(name="control", device=db_device)
    task.task_metadata = {"interval": "10-20"}
    db.session.commit()

    sch = ScheduledTask.from_db_object(task)
    assert sch


@pytest.mark.parametrize("task_type", [None, "", 123, -10, "asjdsa"])
def test_runnable_from_database_task_negative(mocked_device_and_db, task, task_type):
    t = task(mocked_device_and_db, task_type)
    with pytest.raises(TaskNotCreatedException, match="Unknown task type"):
        TaskRunnable.from_database_task(t)

def test_toggle(mocked_device, mocked_device_with_sensor_and_control, task):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task(device, TaskType.TOGGLE.value, control=control)

    toggle_task = Toggle(t.id)
    toggle_task.run(mocked_device)
    task_db = Task.query.filter_by(id=t.id).first()
    assert task_db.last_run
    assert task_db.last_run_success
    assert not task_db.last_run_error


def test_toggle_no_control(mocked_device, mocked_device_with_sensor_and_control, task):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task(device, TaskType.TOGGLE.value)

    with pytest.raises(TaskNotCreatedException):
        Toggle(t.id)


def test_toggle_from_database_task(mocked_device_with_sensor_and_control, task):
    device, s, c = mocked_device_with_sensor_and_control
    t = task(device, TaskType.TOGGLE.value, control=c)
    assert type(TaskRunnable.from_database_task(t)) is Toggle


@pytest.mark.parametrize("task_id", [None, "", "adasd", -10])
def test_toggle_no_task(db_setup, task_id):
    with pytest.raises(TaskNotCreatedException):
        Toggle(task_id)


def test_interval_from_database_task(mocked_device_with_sensor_and_control, task):
    device, s, c = mocked_device_with_sensor_and_control
    t = task(device, TaskType.INTERVAL.value, control=c, sensor=s)
    t.task_metadata = {"interval": "10-20"}
    db.session.commit()
    assert type(TaskRunnable.from_database_task(t)) is Interval


def test_interval(mocked_device, mocked_device_with_sensor_and_control, task):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task(device, TaskType.TOGGLE.value, control=control, sensor=sensor)
    t.task_metadata = {"interval": "10-20"}
    db.session.commit()

    interval_task = Interval(t.id)
    interval_task.run(mocked_device)
    task_db = Task.query.filter_by(id=t.id).first()
    assert task_db.last_run
    assert task_db.last_run_success
    assert not task_db.last_run_error


@pytest.mark.parametrize("task_id", [None, "", "adasd", -10])
def test_inerval_no_task(db_setup, task_id):
    with pytest.raises(TaskNotCreatedException):
        Interval(task_id)


def test_interval_no_meta(mocked_device_with_sensor_and_control, task):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task(device, TaskType.INTERVAL.value, control=control, sensor=sensor)
    with pytest.raises(TaskNotCreatedException, match="'interval' field needed"):
        Interval(t.id)


def test_interval_no_control(mocked_device_with_sensor_and_control, task):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task(device, TaskType.INTERVAL.value, sensor=sensor)
    t.task_metadata = {"interval": "10-20"}
    with pytest.raises(TaskNotCreatedException, match="Control needed for"):
        Interval(t.id)


def test_interval_no_sensor(mocked_device, mocked_device_with_sensor_and_control, task):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task(device, TaskType.INTERVAL.value, control=control)
    t.task_metadata = {"interval": "10-20"}
    with pytest.raises(TaskNotCreatedException, match="Sensor needed for"):
        Interval(t.id)


def test_status_from_database_task(mocked_device_and_db, task):
    t = task(mocked_device_and_db, TaskType.STATUS.value)
    assert type(TaskRunnable.from_database_task(t)) is Status


@pytest.mark.parametrize("task_id", [None, "", "adasd", -10])
def test_status_no_task(mocked_device_and_db, task_id):
    with pytest.raises(TaskNotCreatedException):
        Status(task_id)


def test_status(mocked_device, mocked_device_and_db, task):
    t = task(mocked_device_and_db, TaskType.STATUS.value)

    status_task = Status(t.id)
    status_task.run(mocked_device)
    task_db = Task.query.filter_by(id=t.id).first()
    assert task_db.last_run
    assert task_db.last_run_success
    assert not task_db.last_run_error
