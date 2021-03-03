import json
import logging

from datetime import datetime
from app import CACHE, db
from app.config import Config
from app.device import Device as PhysicalDevice
from sqlalchemy import event
from sqlalchemy.orm import relationship

log = logging.getLogger(__name__)
NOT_APPLICABLE = 'N/A'


class UnexpectedModelException(Exception):
    pass


class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)

    def _to_dict(self):
        result = {}
        for attribute in self.__dict__:
            if attribute.startswith("_"):
                continue
            value = self.__getattribute__(attribute)
            if type(value) in [dict, list, bool] or value is None:
                result[attribute] = value
            else:
                result[attribute] = str(value)
        return result


class Sensor(Base):
    """
    A Read only sensor on the device (e.g. a temperature sensor)
    """
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)
    _last_value = db.Column(db.Float, default=-1)
    unit = db.Column(db.String(80), nullable=True)

    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    device = db.relationship('Device', backref=db.backref('sensors', lazy=False))

    def __repr__(self):
        return f"<Sensor (name={self.name}, value={self.last_value} {self.unit}," \
               f"device={self.device_id})>"

    @property
    def last_value(self):
        return self._last_value

    @last_value.setter
    def last_value(self, value):
        try:
            self._last_value = float(value)
        except Exception as e:
            log.error(f"{self}: failed to parse number '{value}': {e}")
            self._last_value = -1

    @property
    def dictionary(self):
        d = self._to_dict()
        d['last_value'] = self.last_value
        return d


class Control(Base):
    """
    A controllable entity on the device (e.g. a switch)
    """
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)
    _state = db.Column(db.Boolean, default=False)

    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    device = db.relationship('Device', backref=db.backref('controls', lazy=False))

    def __repr__(self):
        return f"<Control (name={self.name}, device={self.device_id})>"

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if type(value) is bool:
            self._state = value
            return
        if type(value) is str:
            if value in ["True", "true"]:
                self._state = True
                return
            elif value in ["False", "false"]:
                self._state = False
                return
        try:
            x = int(value)
        except Exception as e:
            log.error(f"{self}: failed to parse bool '{value}': {e}")
            self._state = False
            return
        self._state = not bool(x) if Config.INVERT_BOOLEAN else bool(x)

    @property
    def dictionary(self):
        d = self._to_dict()
        d["state"] = self.state
        return d


class Task(Base):
    """
    A schedule-able action to be performed on the device
    """
    name = db.Column(db.String(80), default="Unnamed task")
    cron = db.Column(db.String(80), default="* * * * *")
    type = db.Column(db.String(80), nullable=True)

    # store any task specifics
    _task_meta = db.Column(db.String(200), nullable=True)

    last_run = db.Column(db.DateTime, nullable=True)
    last_run_success = db.Column(db.Boolean(), default=False)
    last_run_error = db.Column(db.String(80), nullable=True)

    control_id = db.Column(db.Integer, db.ForeignKey(Control.id))
    control = relationship(Control, uselist=False)

    sensor_id = db.Column(db.Integer, db.ForeignKey(Sensor.id))
    sensor = relationship(Sensor, uselist=False)

    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    device = db.relationship('Device', backref=db.backref('tasks', lazy=False))

    def __repr__(self):
        s = self.sensor.name if self.sensor else "NaN"
        c = self.control.name if self.control else "NaN"
        return f"<Task (id={self.id}, name={self.name}, device={self.device_id}, " \
               f"cron={self.cron}, sensor={s}, control={c})>"

    @property
    def task_metadata(self):
        if not self._task_meta:
            return {}
        try:
            return json.loads(self._task_meta) or {}
        except (TypeError, json.JSONDecodeError) as e:
            log.error(f"Failed to decode JSON '{self._task_meta}': {e}")
            return {}

    @task_metadata.setter
    def task_metadata(self, md: dict):
        try:
            self._task_meta = json.dumps(md)
        except TypeError as e:
            log.error(f"Failed to encode JSON: '{md}': {e}")

    @task_metadata.deleter
    def task_metadata(self):
        self._task_meta = None

    @property
    def dictionary(self):
        d = self._to_dict()
        d["meta"] = self.task_metadata
        d["sensor"] = self.sensor.dictionary if self.sensor else None
        d["control"] = self.control.dictionary if self.control else None
        return d

    @staticmethod
    def set_success(task_id):
        t = Task.query.filter_by(id=task_id).first()
        if t:
            t.last_run = datetime.utcnow()
            t.last_run_success = True
            t.last_run_error = None
            db.session.commit()

    @staticmethod
    def set_failed(task_id, exception):
        t = Task.query.filter_by(id=task_id).first()
        if t:
            t.last_run = datetime.utcnow()
            t.last_run_success = False
            t.last_run_error = str(exception)
            db.session.commit()


class Device(Base):
    """
    Device
    """
    time_modified = db.Column(db.DateTime, nullable=True)
    last_seen_online = db.Column(db.DateTime, nullable=True)

    # Unique for device: e.g. hard-coded in the Arduino sketch or MAC from ESP32
    uuid = db.Column(db.String(80), unique=True, nullable=True)
    # Human readable, user can change it to his liking
    name = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(80), nullable=True)
    type = db.Column(db.String(80), nullable=True)

    is_online = db.Column(db.Boolean(), default=False)
    # sensors (=backref)
    # controls (=backref)
    # tasks (=backref)

    # store any unreckognized device attributes (for later triage)
    _unknown_commands = db.Column(db.String(500), nullable=True)

    @property
    def unknown_commands(self):
        if not self._unknown_commands:
            return {}
        return json.loads(self._unknown_commands)

    @unknown_commands.setter
    def unknown_commands(self, data: dict):
        self._unknown_commands = json.dumps(data)

    def put_unknown_command(self, command, value):
        # todo: thread safe?
        if not self._unknown_commands:
            data = {}
        else:
            data = json.loads(self._unknown_commands)
        data[command] = value
        self._unknown_commands = json.dumps(data)

    @property
    def dictionary(self):
        d = self._to_dict()
        d['sensors'] = sorted(
            [s.dictionary for s in self.sensors], key=lambda t: t['id'])
        d['controls'] = sorted(
            [c.dictionary for c in self.controls], key=lambda t: t['id'])
        d['tasks'] = sorted(
            [t.dictionary for t in self.tasks], key=lambda t: t['id'])
        d['scheduler_running'] = CACHE.has_active_scheduler(self.uuid)
        d['unrecognized'] = self.unknown_commands
        return d

    def __repr__(self):
        return f"<Device (uuid={self.uuid}, name={self.name})>"

    def update_commands(self, data: dict):
        """Update sensor/control values according to a status dict"""
        controls = [c.name for c in self.controls]
        sensors = [s.name for s in self.sensors]
        for key, value in data.items():
            if key in controls:
                control = Control.query.filter_by(name=key, device=self).first()
                if not controls:  # todo: necessary?
                    raise UnexpectedModelException("Key was in controls, but query failed.")
                control.state = value
            elif key in sensors:
                sensor = Sensor.query.filter_by(name=key, device=self).first()
                if not sensor:  # todo: necessary?
                    raise UnexpectedModelException("Key was in controls, but query failed.")
                sensor.last_value = value

            elif getattr(self, key, None):
                # skip received device attributes
                continue
            else:
                self.put_unknown_command(key, value)

    @classmethod
    def query_by_serial_device(cls, device: PhysicalDevice):
        return Device.query.filter_by(uuid=device.uuid).first()

    @classmethod
    def from_status_response(cls,
                             device: PhysicalDevice, status: dict, create=True):
        d = Device.query_by_serial_device(device)
        if not d and create:
            d = Device(uuid=device.uuid, name=str(device),
                       type=device.device_type.value, url=device.url)
            db.session.add(d)
            db.session.commit()
        if d:
            d.update_commands(status)
            d.is_online = True
            d.last_seen_online = datetime.utcnow()
        return d


@event.listens_for(Device, "before_insert")
@event.listens_for(Device, "before_update")
def my_before_insert_listener(mapper, connection, target):
    target.time_modified = datetime.utcnow()
