import logging
import re

from contextlib import wraps
from datetime import datetime
from enum import Enum
from app.device import Device, DeviceException
from app.models import db, Task as TaskDb
from app.models import Device as DeviceDb

from croniter import croniter, CroniterNotAlphaError


log = logging.getLogger(__name__)


class TaskException(Exception):
    """Generic device exception"""
    pass


class TaskNotCreatedException(TaskException):
    """Generic device exception"""
    pass


class TaskType(Enum):
    TOGGLE = "toggle"
    INTERVAL = "interval"
    STATUS = "status"
    GENERIC = "generic"

    @classmethod
    def from_string(cls, string):
        try:
            return TaskType(string)
        except ValueError:
            return TaskType.GENERIC


class ScheduledTask:
    """
    Unique object defining a single task execution
    """

    def __init__(self, task_id, scheduled_time, runnable):
        self.task_id = task_id
        self.scheduled_time = scheduled_time
        self.runnable = runnable

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self.task_id) ^ hash(self.scheduled_time)

    def __repr__(self):
        return f"<ScheduledTask (id={self.task_id}, time={self.scheduled_time})>"

    @classmethod
    def from_db_object(cls, task_db: TaskDb):
        try:
            time = croniter(task_db.cron).get_next(datetime)
            runnable = TaskRunnable.from_database_task(task_db)
            return ScheduledTask(task_db.id, time, runnable)
        except CroniterNotAlphaError:
            log.error(f"{task_db}: invalid cron definition '{task_db.cron}'")
            return


class TaskRunnable:

    def __init__(self, task_id: int):
        if not TaskDb.query.filter_by(id=task_id).first():
            raise TaskNotCreatedException(f"No such task '{task_id}'.")
        self.task_id = task_id

    def run(self, device):
        """Return 'True' if all went well"""
        raise NotImplemented

    @classmethod
    def from_database_task(cls, task: TaskDb):
        typ = TaskType.from_string(task.type)
        if typ == TaskType.STATUS:
            return Status(task.id)
        elif typ == TaskType.TOGGLE:
            return Toggle(task.id)
        elif typ == TaskType.INTERVAL:
            return Interval(task.id)
        else:
            raise TaskNotCreatedException(f"Unknown task type")

    @staticmethod
    def update_task_status():
        """Decorate run methods to update task state
        and prevent unexpected failures."""
        def decorate(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                task_id = None
                try:
                    task_id = args[0].task_id  # self
                    result = func(*args, **kwargs)
                    if result:
                        TaskDb.set_success(task_id)
                    else:
                        TaskDb.set_failed(
                            task_id, "No errors, wrapped function returned 'False'")
                except Exception as e:
                    if task_id:
                        TaskDb.set_failed(task_id, e)
                    else:
                        log.error("Decorated function is missing 'self' parameter.")
            return wrapper
        return decorate


class Toggle(TaskRunnable):
    type = TaskType.TOGGLE

    def __init__(self, task_id: int):
        super().__init__(task_id)
        task = TaskDb.query.filter_by(id=task_id).first()
        if not task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

    @TaskRunnable.update_task_status()
    def run(self, device: Device):
        control = TaskDb.query.filter_by(id=self.task_id).first().control
        log.debug(f"{device}: running {self.type}")
        response = device.send_control(control.name)
        control.state = response.data
        db.session.add(control)
        db.session.commit()
        return response.is_success


class Interval(TaskRunnable):
    type = TaskType.INTERVAL  # todo: needed?

    @staticmethod
    def __parse_interval(string):
        """Expect xx-yy format"""
        i = string.split("-")

        if len(i) == 2:
            try:
                left = float(i[0])
                right = float(i[1])
                if left > right:
                    raise ValueError
                return [left, right]
            except (ValueError, TypeError):
                pass
        raise TaskException(f"Invalid 'interval' field: '{string}'.")

    def __init__(self, task_id: int):
        super().__init__(task_id)
        task = TaskDb.query.filter_by(id=task_id).first()
        if not task.sensor:
            raise TaskNotCreatedException(f"Sensor needed for '{self.type}' task.")
        if not task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

        if not task.task_metadata.get("interval"):
            raise TaskNotCreatedException(f"'interval' field needed for '{self.type}' task.")
        self.interval = Interval.__parse_interval(task.task_metadata["interval"])

    @TaskRunnable.update_task_status()
    def run(self, device: Device):
        log.info(f"{device}: running {self.type}")
        sensor = TaskDb.query.filter_by(id=self.task_id).first().sensor
        control = TaskDb.query.filter_by(id=self.task_id).first().control

        response = device.read_sensor(sensor.name)
        if not response.is_success:
            raise TaskException(f"{device}: invalid response '{response}'")
        value = response.data

        def toggle(dev, c):
            r = dev.send_control(c.name)
            c.state = r.data
            db.session.commit()
            log.info(f"{dev}: {c} toggled.")

        if value < self.interval[0] and not control.state:
            log.info(f"{device}: {value} < {self.interval[0]}, switching on.")
            toggle(device, control)

        if value > self.interval[1] and control.state:
            log.info(f"{device}: {value} > {self.interval[1]}, switching off.")
            toggle(device, control)
        return True


class Status(TaskRunnable):
    type = TaskType.STATUS

    @TaskRunnable.update_task_status()
    def run(self, device: Device):
        log.info(f"{device}: running {self.type}")
        response = device.read_status()

        d = DeviceDb.from_status_response(device, response.data)
        db.session.add(d)
        db.session.commit()
        return True





