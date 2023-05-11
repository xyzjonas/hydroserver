import os

import pytest
import shutil

from app.core.plugins import plugin_manager
from app.core.tasks import TaskRunnable, TaskType
from app.models import Task


@pytest.mark.parametrize('task_type', ['status', 'toggle', 'interval', 'history'])
def test_builtin_from_database_task(mocked_device, mocked_device_with_sensor_and_control,
                                    task_factory, task_type):
    from app.core.plugins import plugin_manager
    assert task_type in plugin_manager.available_tasks
    dev, s, c = mocked_device_with_sensor_and_control
    t = task_factory(dev, task_type, control=c, sensor=s, meta={'interval': '10-20'})
    runnable = TaskRunnable.from_database_task(t)
    assert runnable.type == task_type


@pytest.fixture()
def task_type():
    return "test_task"


@pytest.fixture()
def set_plugin_dir(task_type):
    dir_path = '/tmp/test-plugins'
    filename = 'plugins.py'

    os.mkdir(dir_path)
    content = f"""
from app.core.tasks import TaskRunnable

class TestTask(TaskRunnable):
    type = '{task_type}'

    def _run(self, device):
        x = 2 + 1
        return True
"""
    with open("/".join([dir_path, filename]), 'x') as file:
        file.write(content)
    yield dir_path
    shutil.rmtree(dir_path)


def test_custom_task(mocked_device, mocked_device_and_db, set_plugin_dir, task_factory, task_type):
    task = task_factory(mocked_device_and_db, task_type)

    plugin_manager.initialize(plugin_paths=[set_plugin_dir])
    assert 'test_task' in plugin_manager.available_tasks

    runnable = TaskRunnable.from_database_task(task)
    assert runnable.type == task_type
    assert not Task.query.filter_by(id=runnable.task_id).first().last_run_success
    runnable.run(mocked_device)
    assert Task.query.filter_by(id=runnable.task_id).first().last_run_success


def test_multiple_init(mocked_device_with_sensor_and_control, task_factory):
    dev, s, c = mocked_device_with_sensor_and_control
    task = task_factory(dev, TaskType.TOGGLE.value, control=c)

    plugin_manager.initialize()
    assert TaskRunnable.from_database_task(task)

    plugin_manager.initialize(plugin_paths='/tmp')
    assert TaskRunnable.from_database_task(task)
