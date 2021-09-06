from app.core.plugins import PLUGIN_MANAGER


def test_load():
    assert PLUGIN_MANAGER
    assert PLUGIN_MANAGER.available_tasks == {"status", "toggle", "interval", "historylogger"}


def test_instantiate(mocked_device, mocked_device_and_db, task_factory):
    pm = PLUGIN_MANAGER
    task = task_factory(device=mocked_device_and_db, task_type='status')
    Status = pm.get_class('status')
    assert Status
    status = Status(task.id)
    assert type(status) is Status

    r = status.run(mocked_device)
