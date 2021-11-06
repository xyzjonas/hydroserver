import pytest

from app import db, CACHE
from app.models import Task
from app.core.tasks import ScheduledTask, TaskType, TaskNotCreatedException, TaskRunnable
from app.core.tasks.builtin import Status, Toggle, Interval


def test_from_db_object_status(mocked_device_and_db, task_factory):
    t = task_factory(mocked_device_and_db, TaskType.STATUS.value)
    sch = ScheduledTask.from_db_object(t)
    assert sch


def test_from_db_object_status_cron(mocked_device_and_db, task_factory):
    t = task_factory(mocked_device_and_db, TaskType.STATUS.value)
    t.cron = 'status'
    sch = ScheduledTask.from_db_object(t)
    assert sch


@pytest.mark.parametrize("task_type", [None, "", 123, -10, "asjdsa"])
def test_runnable_from_database_task_negative(mocked_device_and_db, task_factory, task_type):
    t = task_factory(mocked_device_and_db, task_type)
    with pytest.raises(TaskNotCreatedException, match="Unknown task type"):
        TaskRunnable.from_database_task(t)


def test_toggle(mocked_device, mocked_device_with_sensor_and_control, task_factory):
    CACHE.add_active_device(mocked_device)
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task_factory(device, TaskType.TOGGLE.value, control=control)
    task_id = t.id

    toggle_task = Toggle(task_id)
    toggle_task.run(mocked_device)
    task_db = db.session.query(Task).filter_by(id=task_id).first()
    assert task_db.last_run
    assert task_db.last_run_success
    assert not task_db.last_run_error


def test_toggle_no_control(mocked_device, mocked_device_with_sensor_and_control,
                           task_factory):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task_factory(device, TaskType.TOGGLE.value)

    with pytest.raises(TaskNotCreatedException):
        Toggle(t.id)


@pytest.mark.parametrize("task_id", [None, "", "adasd", -10])
def test_toggle_no_task(db_setup, task_id):
    with pytest.raises(TaskNotCreatedException):
        Toggle(task_id)


@pytest.mark.parametrize('task_type', [type_.value for type_ in TaskType])
def test_scheduler_task_from_db_object(mocked_device_with_sensor_and_control,
                                       task_factory, task_type):
    device, s, c = mocked_device_with_sensor_and_control
    task = task_factory(device,
                        task_type,
                        control=c,
                        sensor=s,
                        meta={"interval": "10-20"})
    assert task.id
    sch = ScheduledTask.from_db_object(task)
    assert sch


@pytest.mark.parametrize('task_type', [type_.value for type_ in TaskType])
def test_builtin_from_database_task(mocked_device_with_sensor_and_control,
                                    task_factory, task_type):
    device, s, c = mocked_device_with_sensor_and_control
    t = task_factory(device,
                     task_type,
                     control=c,
                     sensor=s,
                     meta={"interval": "10-20"})
    assert t.id
    runnable = TaskRunnable.from_database_task(t)
    assert runnable
    assert runnable.type == task_type


@pytest.mark.parametrize('input_type,value', [('bool', 'True'), ('float', '0.33')])
def test_interval(mocked_device,
                  mocked_device_with_sensor_and_control,
                  task_factory, input_type, value
                  ):
    device, sensor, control = mocked_device_with_sensor_and_control
    control.input = input_type
    control.value = value
    t = task_factory(device, TaskType.TOGGLE.value, control=control, sensor=sensor)
    t.task_metadata = {"interval": "10-20"}
    db.session.commit()
    task_id = t.id

    interval_task = Interval(t.id)
    interval_task.run(mocked_device)
    task_db = db.session.query(Task).filter_by(id=task_id).first()
    assert task_db.last_run
    assert task_db.last_run_success
    assert not task_db.last_run_error


@pytest.mark.parametrize("task_id", [None, "", "adasd", -10])
def test_inerval_no_task(db_setup, task_id):
    with pytest.raises(TaskNotCreatedException):
        Interval(task_id)


def test_interval_no_meta(mocked_device_with_sensor_and_control, task_factory):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task_factory(device, TaskType.INTERVAL.value, control=control, sensor=sensor)
    with pytest.raises(TaskNotCreatedException, match="'interval' field needed"):
        Interval(t.id)


def test_interval_no_control(mocked_device_with_sensor_and_control, task_factory):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task_factory(device, TaskType.INTERVAL.value, sensor=sensor)
    t.task_metadata = {"interval": "10-20"}
    with pytest.raises(TaskNotCreatedException, match="Control needed for"):
        Interval(t.id)


def test_interval_no_sensor(mocked_device, mocked_device_with_sensor_and_control,
                            task_factory):
    device, sensor, control = mocked_device_with_sensor_and_control
    t = task_factory(device, TaskType.INTERVAL.value, control=control)
    t.task_metadata = {"interval": "10-20"}
    with pytest.raises(TaskNotCreatedException, match="Sensor needed for"):
        Interval(t.id)


@pytest.mark.parametrize("task_id", [None, "", "adasd", -10])
def test_status_no_task(mocked_device_and_db, task_id):
    with pytest.raises(TaskNotCreatedException):
        Status(task_id)


def test_status(mocked_device, mocked_device_and_db, task_factory):
    CACHE.add_active_device(mocked_device)
    t = task_factory(mocked_device_and_db, TaskType.STATUS.value)
    task_id = t.id

    status_task = Status(task_id)
    status_task.run(mocked_device)
    task_db = db.session.query(Task).filter_by(id=task_id).first()
    assert task_db.last_run
    assert task_db.last_run_success
    assert not task_db.last_run_error
