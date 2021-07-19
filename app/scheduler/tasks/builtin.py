from app import db
from app.device import Device as PhysicalDevice
from app.models import Task, Device
from app.scheduler.tasks import TaskRunnable, TaskType, TaskNotCreatedException, TaskException


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
        task = Task.query.filter_by(id=task_id).first()
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
        sensor = Task.query.filter_by(id=self.task_id).first().sensor
        control = Task.query.filter_by(id=self.task_id).first().control

        response = device.read_sensor(sensor.name)
        if not response.is_success:
            raise TaskException(f"{device}: invalid response '{response}'")
        value = response.data

        def toggle(dev, c):
            r = dev.send_control(c.name)
            c.state = r.data
            db.session.commit()
            self.log.info(f"{dev}: {c} toggled.")

        if value < self.interval[0] and not control.state:
            self.log.info(f"{device}: {value} < {self.interval[0]}, switching on.")
            toggle(device, control)

        if value > self.interval[1] and control.state:
            self.log.info(f"{device}: {value} > {self.interval[1]}, switching off.")
            toggle(device, control)
        return True


class Status(TaskRunnable):
    type = TaskType.STATUS

    @TaskRunnable.update_task_status()
    def run(self, device: PhysicalDevice):
        response = device.read_status()

        d = Device.from_status_response(device, response.data)
        db.session.add(d)
        db.session.commit()
        return True


class Toggle(TaskRunnable):
    type = TaskType.TOGGLE

    def __init__(self, task_id: int):
        super().__init__(task_id)
        task = Task.query.filter_by(id=task_id).first()
        if not task.control:
            raise TaskNotCreatedException(f"Control needed for '{self.type}' task.")

    @TaskRunnable.update_task_status()
    def run(self, device: PhysicalDevice):
        control = Task.query.filter_by(id=self.task_id).first().control
        response = device.send_control(control.name)
        control.state = response.data
        db.session.add(control)
        db.session.commit()
        return response.is_success
