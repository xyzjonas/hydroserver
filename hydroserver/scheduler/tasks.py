import ast
import logging

from datetime import datetime
from enum import Enum
from hydroserver import db
from hydroserver.device import Device, DeviceException
from hydroserver.models import Task as TaskDb
from hydroserver.models import Device as DeviceDb

from croniter import croniter, CroniterNotAlphaError


log = logging.getLogger(__name__)


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
            return Toggle(task)
        elif typ == TaskType.INTERVAL:
            return Interval(task)
        else:
            raise ValueError(f"Unknown task type")


class Toggle(TaskRunnable):
    type = TaskType.TOGGLE

    def __init__(self, task: TaskDb):
        self.control = task.control

    def run(self, device: Device):
        log.info(f"{device}: running {self.type}")
        response = device.send_control(self.control)
        if not response.is_success:
            log.error(f"{device}: failed to toggle '{self.control}'")


class Interval(TaskRunnable):
    type = TaskType.INTERVAL  # todo: needed?

    @staticmethod
    def __parse_interval(string):
        try:
            interval = ast.literal_eval(string)
            if type(interval) is list:
                if len(interval) != 2:
                    raise ValueError(
                        f"Invalid 'interval' field length (!=2): '{string}'.")
                if interval[0] > interval[1]:
                    raise ValueError(f"Invalid interval '{interval}'.")
                return interval
        except SyntaxError:
            pass
        raise ValueError(f"Invalid 'interval' field: '{string}'.")

    def __init__(self, task: TaskDb):
        self.control = task.control

        if not task.sensor:
            raise ValueError(f"Sensor needed for '{self.type}' task.")
        self.sensor = task.sensor

        if not task.interval:
            raise ValueError(f"'interval' field needed for '{self.type}' task.")
        self.interval = Interval.__parse_interval(task.interval)

    def run(self, device: Device):
        log.info(f"{device}: running {self.type}")
        response = device.read_sensor(self.sensor)
        if not response.is_success:
            raise DeviceException(f"Invalid response: {response}")
        value = response.data
        if self.interval[0] < value < self.interval[1]:
            log.info(f"{device}: {value} inside interval {self.interval}, skipping.")
            return

        response = device.send_control(self.control)
        if response.is_success:
            log.info(f"{device}: {self.control} toggled.")
        else:
            log.error(f"{device}: Failed to toggle {self.control}.")


class Status(TaskRunnable):
    type = TaskType.STATUS

    def run(self, device: Device):
        log.info(f"{device}: running {self.type}")
        response = device.read_status()
        if not response.is_success:
            log.error(f"{device}: failed to read status.")
            return
        try:
            d = DeviceDb.by_status_response(device, response.data)
            db.session.add(d)
            db.session.commit()
        except Exception as e:
            log.error(f"{device}: failed to update database ({e})")





