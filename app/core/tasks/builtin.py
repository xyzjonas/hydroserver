from app import db
from app.core.device import Device as PhysicalDevice
from app.system.device_controller import Controller
from app.models import Task
from app.core.tasks import TaskRunnable, TaskType, TaskNotCreatedException, TaskException


class Interval(TaskRunnable):
    """Toggles the control based on a sensors value (tries to keep it inside the interval)."""
    type = TaskType.INTERVAL.value

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
        task = db.session.query(Task).filter_by(id=task_id).first()
        if not task.sensor:
            raise TaskNotCreatedException(f"Sensor needed for '{self.type}' task.")
        if not task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

        if not task.task_metadata.get("interval"):
            raise TaskNotCreatedException(f"'interval' field needed for '{self.type}' task.")
        self.interval = Interval.__parse_interval(task.task_metadata["interval"])

    def _run(self, device: PhysicalDevice):
        """
        Use interval (e.g. 10-20) to either turn on/off or adjust control
        (depending on control type). In case of 'numeric' control, optional 'step'
        metadata is used for the adjustment.
        """
        self.log.info(f"{device}: running {self.type}")
        task_db = db.session.query(Task).filter_by(id=self.task_id).first()
        sensor = task_db.sensor
        control = task_db.control
        controller = Controller(device)

        value = sensor.get_recent_average()

        def __parse_step_as_float():
            try:
                return float(task_db.task_metadata.get("step", 0.1))
            except (TypeError, ValueError):
                raise TaskException(
                    f"Step value '{task_db.task_metadata.get('step', 0.1)}' is not a number.")

        def __action(up=True):
            if control.input == "bool":
                if (up and not control.parsed_value) or (not up and control.parsed_value):
                    controller.action(control)
            elif control.input == "float":
                new_value = control.parsed_value + __parse_step_as_float() if up \
                    else control.parsed_value - __parse_step_as_float()
                if new_value < 0 or new_value > 1:
                    raise TaskException(f"Value out of bounds: {new_value}")
                controller.action(control, value=new_value)
            else:
                raise TaskException(f"Cannot handle control type '{control.input}'.")

        left, right = self.interval
        if value < left:
            self.log.info(f"{device}: {value} < {left}, going up.")
            __action(up=True)

        if value > right:
            self.log.info(f"{device}: {value} > {right}, going down.")
            __action(up=False)
        return True


class Status(TaskRunnable):
    """Just read the status & update."""
    type = TaskType.STATUS.value

    def _run(self, device: PhysicalDevice):
        Controller(device=device).read_status()
        return True


class HistoryLogger(TaskRunnable):
    """Log sensor values."""
    type = TaskType.HISTORY.value

    def _run(self, device: PhysicalDevice):
        controller = Controller(device=device)
        controller.log_sensors()
        return True


class Toggle(TaskRunnable):
    """Toggle a switch."""
    type = TaskType.TOGGLE.value

    def __init__(self, task_id: int):
        super(Toggle, self).__init__(task_id)
        self.task = db.session.query(Task).filter_by(id=task_id).first()
        if not self.task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

    def _run(self, device: PhysicalDevice):
        control = self.task.control
        Controller(device=device).action(control)
        return True
