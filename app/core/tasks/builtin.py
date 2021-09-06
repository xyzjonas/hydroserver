from app import db
from app.core.device import Device as PhysicalDevice
from app.system.device_controller import Controller
from app.models import Task
from app.core.tasks import TaskRunnable, TaskType, TaskNotCreatedException, TaskException


class Interval(TaskRunnable):
    """Toggles the control based on a sensors value (tries to keep it inside the interval)."""
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
        task = db.session.query(Task).filter_by(id=task_id).first()
        if not task.sensor:
            raise TaskNotCreatedException(f"Sensor needed for '{self.type}' task.")
        if not task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

        if not task.task_metadata.get("interval"):
            raise TaskNotCreatedException(f"'interval' field needed for '{self.type}' task.")
        self.interval = Interval.__parse_interval(task.task_metadata["interval"])

    @TaskRunnable.update_task_status()
    def run(self, device: PhysicalDevice):
        self.log.info(f"{device}: running {self.type}")
        sensor = db.session.query(Task).filter_by(id=self.task_id).first().sensor
        control = db.session.query(Task).filter_by(id=self.task_id).first().control

        response = device.read_sensor(sensor.name)
        if not response.is_success:
            raise TaskException(f"{device}: failed to read sensor {sensor.name}: {response}")
        value = response.value

        controller = Controller(device)

        if value < self.interval[0] and not control.state:
            self.log.info(f"{device}: {value} < {self.interval[0]}, switching on.")
            controller.action(control)

        if value > self.interval[1] and control.state:
            self.log.info(f"{device}: {value} > {self.interval[1]}, switching off.")
            controller.action(control)
        return True


class Status(TaskRunnable):
    """Just read the status & update."""
    type = TaskType.STATUS

    @TaskRunnable.update_task_status()
    def run(self, device: PhysicalDevice):
        Controller(device=device).read_status()
        return True


class HistoryLogger(TaskRunnable):
    """Log sensor values."""
    type = TaskType.HISTORY

    @TaskRunnable.update_task_status()
    def run(self, device: PhysicalDevice):
        controller = Controller(device=device)
        controller.log_sensors()
        return True


class Toggle(TaskRunnable):
    """Toggle a switch."""
    type = TaskType.TOGGLE

    def __init__(self, task_id: int):
        super().__init__(task_id)
        self.task = db.session.query(Task).filter_by(id=task_id).first()
        if not self.task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

    @TaskRunnable.update_task_status()
    def run(self, device: PhysicalDevice):
        control = self.task.control
        Controller(device=device).action(control)
        return True
