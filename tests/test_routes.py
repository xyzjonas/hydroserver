import time

from app.cache import CACHE
from app.scheduler.tasks import TaskType
from app.models import Task


def test_post_task(app_setup, mocked_device, mocked_device_and_db):
    url = f"/devices/{mocked_device_and_db.id}/tasks"
    data = {"type": TaskType.STATUS.value}
    assert not CACHE.has_active_scheduler(mocked_device.uuid)
    with app_setup.test_client() as client:
        r = client.post(url, json=data)
        assert r.status_code == 201
    time.sleep(0.2)
    assert CACHE.has_active_scheduler(mocked_device.uuid)


def test_post_run_scheduler(app_setup, mocked_device, mocked_device_and_db):
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
    assert Task.query.filter_by(id=task.id).first().paused


def test_resume_task(app_setup, mocked_device_and_db, task_factory):
    task = task_factory(mocked_device_and_db, 'status', paused=True)
    assert task.paused
    url = f"/devices/{mocked_device_and_db.id}/tasks/{task.id}/resume"
    with app_setup.test_client() as client:
        r = client.post(url)
        assert r.status_code == 200
    assert not Task.query.filter_by(id=task.id).first().paused