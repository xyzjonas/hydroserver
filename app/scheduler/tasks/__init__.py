import logging
import math
import traceback
from contextlib import wraps
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
        return f"<{__name__} (id={self.task_id}, time={self.scheduled_time})>"

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


class TaskRunnable:

    log = logging.getLogger(__name__)

    def __init__(self, task_id: int):
        if not db.session.query(Task).filter_by(id=task_id).first():
            raise TaskNotCreatedException(f"No such task '{task_id}'.")
        self.task_id = task_id

    def run(self, device):
        """Return 'True' if all went well"""
        raise NotImplemented

    def _get_description(self):
        raise NotImplemented

    @property
    def description(self):
        """information"""
        return self._get_description()

    @classmethod
    def from_database_task(cls, task: Task):
        from app.scheduler.tasks.builtin import Toggle, Status, Interval, HistoryLogger

        typ = TaskType.from_string(task.type)
        if typ == TaskType.STATUS:
            return Status(task.id)
        if typ == TaskType.HISTORY:
            return HistoryLogger(task.id)
        elif typ == TaskType.TOGGLE:
            return Toggle(task.id)
        elif typ == TaskType.INTERVAL:
            return Interval(task.id)
        else:
            # todo: instantiate generic (user-added) task by name
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
                    TaskRunnable.log.debug(f"{args[1]}: running {args[0].type}")
                    result = func(*args, **kwargs)
                    if result:
                        Task.set_success(task_id)
                    else:
                        Task.set_failed(task_id, "No errors, wrapped function returned 'False'")
                except Exception as e:
                    traceback.print_exc()
                    if task_id:
                        Task.set_failed(task_id, e)
                    else:
                        TaskRunnable.log.error("Decorated function is missing 'self' parameter.")
                finally:
                    db.session.close()
            return wrapper
        return decorate
