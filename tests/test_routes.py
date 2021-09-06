import random
import time

from app.system.device_controller import *
from app.core.cache import CACHE
from app.core.tasks import TaskType
from app.models import Task, HistoryItem


def test_get_devices(db_setup, app_setup, mocked_device):
    init_device(mocked_device)
    url = "/devices"
    with app_setup.test_client() as client:
        r = client.get(url)
        assert r.status_code == 200


def test_post_task(app_setup, mocked_device, mocked_device_and_db):
    """Test that posting a new task starts up the scheduler."""
    CACHE.add_active_device(mocked_device)
    url = f"/devices/{mocked_device_and_db.id}/tasks"
    data = {"type": TaskType.STATUS.value}

    assert not CACHE.has_active_scheduler(mocked_device.uuid)
    with app_setup.test_client() as client:
        r = client.post(url, json=data)
        assert r.status_code == 201
    time.sleep(0.2)
    assert CACHE.has_active_scheduler(mocked_device.uuid)


def test_post_run_scheduler(app_setup, mocked_device, mocked_device_and_db):
    CACHE.add_active_device(mocked_device)
    url = f"/devices/{mocked_device_and_db.id}/scheduler"
    assert not CACHE.has_active_scheduler(mocked_device.uuid)
    with app_setup.test_client() as client:
        r = client.post(url)
        assert r.status_code == 200
    assert CACHE.has_active_scheduler(mocked_device.uuid)


def test_delete_locked_task(app_setup, mocked_device_and_db, task_factory):
    task = task_factory(mocked_device_and_db, 'status', locked=True)
    url = f"/devices/{mocked_device_and_db.id}/tasks/{task.id}"
    with app_setup.test_client() as client:
        r = client.delete(url)
        assert r.status_code == 400
        assert 'is locked' in r.data.decode()


def test_pause_task(app_setup, mocked_device_and_db, task_factory):
    task = task_factory(mocked_device_and_db, 'status')
    assert not task.paused
    url = f"/devices/{mocked_device_and_db.id}/tasks/{task.id}/pause"
    with app_setup.test_client() as client:
        r = client.post(url)
        assert r.status_code == 200
    assert db.session.query(Task).filter_by(id=task.id).first().paused


def test_resume_task(app_setup, mocked_device_and_db, task_factory):
    task = task_factory(mocked_device_and_db, 'status', paused=True)
    assert task.paused
    url = f"/devices/{mocked_device_and_db.id}/tasks/{task.id}/resume"
    with app_setup.test_client() as client:
        r = client.post(url)
        assert r.status_code == 200
    assert not db.session.query(Task).filter_by(id=task.id).first().paused


def test_get_sensor_history(app_setup, mocked_device_with_sensor_and_control):
    device, sensor, control = mocked_device_with_sensor_and_control
    for _ in range(100):
        val = random.randint(0, 100)
        db.session.add(
            HistoryItem(sensor=sensor, _value=val, timestamp=datetime.datetime.utcnow()))
    db.session.commit()

    url = f"/devices/{device.id}/sensors/{sensor.id}/history"
    with app_setup.test_client() as client:
        response = client.get(url)
    assert response.status_code == 200
    assert type(response.json) is list
    assert len(response.json) == 100
