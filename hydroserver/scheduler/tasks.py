import logging
import re

from datetime import datetime
from enum import Enum
from hydroserver import db
from hydroserver.device import Device, DeviceException
from hydroserver.models import Task as TaskDb
from hydroserver.models import Device as DeviceDb

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
            runnable = TaskRunnable.get_by_task(task_db)
            return ScheduledTask(task_db.id, time, runnable)
        except CroniterNotAlphaError:
            log.error(f"{task_db}: invalid cron definition '{task_db.cron}'")
            return


class TaskRunnable:

    def run(self, device):
        raise NotImplemented

    @classmethod
    def get_by_task(cls, task: TaskDb):
        typ = TaskType.from_string(task.type)
        if typ == TaskType.STATUS:
            return Status()
        elif typ == TaskType.TOGGLE:
            return Toggle(task.id)
        elif typ == TaskType.INTERVAL:
            return Interval(task.id)
        else:
            raise TaskNotCreatedException(f"Unknown task type")


class Toggle(TaskRunnable):
    type = TaskType.TOGGLE

    def __init__(self, task_id: int):
        self.task_id = task_id
        task = TaskDb.query.filter_by(id=task_id).first()
        if not task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

    def run(self, device: Device):
        control = TaskDb.query.filter_by(id=self.task_id).first().control
        log.info(f"{device}: running {self.type}")
        response = device.send_control(control.name)
        control.state = response.data
        db.session.commit()


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
        # self.control = task.control
        self.task_id = task_id
        task = TaskDb.query.filter_by(id=task_id).first()
        if not task.sensor:
            raise TaskNotCreatedException(f"Sensor needed for '{self.type}' task.")

        if not task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

        # self.sensor = task.sensor
        if not task.task_metadata.get("interval"):
            raise TaskNotCreatedException(f"'interval' field needed for '{self.type}' task.")
        self.interval = Interval.__parse_interval(task.task_metadata["interval"])

    def run(self, device: Device):
        log.info(f"{device}: running {self.type}")
        sensor = TaskDb.query.filter_by(id=self.task_id).first().sensor
        control = TaskDb.query.filter_by(id=self.task_id).first().control

        response = device.read_sensor(sensor.name)
        value = response.data

        def toggle(dev, c):
            r = dev.send_control(c.name)
            log.info(f"{dev}: {c} toggled.")
            c.state = r.data
            db.session.commit()

        if value < self.interval[0] and not control.state:
            log.info(f"{device}: {value} < {self.interval[0]}, switching on.")
            toggle(device, control)
            return

        if self.interval[0] <= value <= self.interval[1] and control.state:
            log.info(
                f"{device}: {value} inside interval {self.interval}, switching off.")
            toggle(device, control)
            return

        if value > self.interval[1] and control.state:
            log.info(f"{device}: {value} > {self.interval[1]}, switching off.")
            toggle(device, control)
            return


class Status(TaskRunnable):
    type = TaskType.STATUS

    def run(self, device: Device):
        log.info(f"{device}: running {self.type}")
        response = device.read_status()

        try:
            d = DeviceDb.from_status_response(device, response.data)
            db.session.add(d)
            db.session.commit()
        except Exception as e:
            log.error(f"{device}: failed to update database ({e})")





