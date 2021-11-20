import functools
import logging
import math
import traceback
from datetime import datetime
from enum import Enum

from croniter import croniter, CroniterNotAlphaError

from app.models import Task
from app import db

AVAILABLE_TASKS = {}


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
    HISTORY = "history"

    @classmethod
    def from_string(cls, string):
        try:
            return TaskType(string)
        except ValueError:
            return None


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
        return f"<{self.runnable.type or 'N/A'} (id={self.task_id}, time={self.scheduled_time})>"

    @classmethod
    def from_db_object(cls, task_db: Task):
        """Create the object and calculate next scheduled time."""
        if task_db.paused:
            return None
        try:
            # if cron is set to 'status', run each 10s todo: configurable
            if task_db.cron == 'status':
                time = datetime.utcnow()
                next_ten_seconds = math.ceil(time.second / 10) * 10
                next_minute = time.minute
                if next_ten_seconds > 50:
                    next_ten_seconds = 0
                    next_minute = next_minute + 1 if next_minute < 59 else 0
                time = time.replace(second=next_ten_seconds, minute=next_minute, microsecond=0)
            else:
                time = croniter(task_db.cron).get_next(datetime)
            runnable = TaskRunnable.from_database_task(task_db)
            return ScheduledTask(task_db.id, time, runnable)
        except CroniterNotAlphaError:
            raise TaskException(f"{task_db}: invalid cron definition '{task_db.cron}'")


class TaskRunnable(object):
    """
    Represents the actual operation to be executed. String 'type' is required.
    """

    log = logging.getLogger(__name__)
    type = "abstract"

    def __init__(self, task_id: int):
        if not db.session.query(Task).filter_by(id=task_id).first():
            raise TaskNotCreatedException(f"No such task '{task_id}'.")
        self.task_id = task_id

    def _run(self, device):
        raise NotImplemented

    def run(self, device):
        """Intercept and store unexpected errors"""
        try:
            self.log.debug(f"{device}: running {self.type}")
            result = self._run(device)
            if result:
                Task.set_success(self.task_id)
            else:
                Task.set_failed(self.task_id, "Task returned 'False'")
        except Exception as e:
            self.log.error(f"Task Runnable failed: {e}")
            traceback.print_exc()
            Task.set_failed(self.task_id, e)
        finally:
            db.session.close()

    def _get_description(self):
        raise NotImplemented

    @property
    def description(self):
        """information"""
        return self._get_description()

    @classmethod
    def from_database_task(cls, task: Task):
        from app.core.plugins import plugin_manager
        type_ = task.type
        if type_ not in plugin_manager.available_tasks:
            raise TaskNotCreatedException(f"Unknown task type '{type_}'")
        assert task.id
        instance = plugin_manager.get_class(type_)(task.id)
        return instance
