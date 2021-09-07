import json
import logging
import math
from datetime import datetime

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import or_, and_

from app import db
from app.core.cache import CACHE
from app.core.device import Device as PhysicalDevice
from app.core.device import StatusResponse

log = logging.getLogger(__name__)
NOT_APPLICABLE = 'N/A'


class UnexpectedModelException(Exception):
    pass


class Base(db.Model):
    __items__ = ['id']  # use to specify REST available items

    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)

    def _to_dict(self):
        result = {}
        available_items = self.__items__ or self.__dict__

        for attribute in available_items:
            if attribute.startswith("_"):
                continue
            value = self.__getattribute__(attribute)
            if type(value) in [dict, list, bool] or value is None:
                result[attribute] = value
            else:
                result[attribute] = str(value)
        return result

    @staticmethod
    def parse_bool(value):
        if type(value) is bool:
            return value
        if type(value) is str:
            if value in ["True", "true"]:
                return True
            elif value in ["False", "false"]:
                return False
        raise TypeError(f'\'bool\' cast failed for value {value}')

    @staticmethod
    def parse_int(value):
        if type(value) is int:
            return value
        if type(value) is str:
            try:
                return int(value)
            except (TypeError, ValueError) as e:
                pass
        raise TypeError(f'\'int\' cast failed for value {value}')

    @staticmethod
    def parse_float(value):
        if type(value) in [int, float]:
            return round(float(value), 2)
        if type(value) is str:
            try:
                return round(float(value), 2)
            except (TypeError, ValueError) as e:
                pass
        raise TypeError(f'\'float\' cast failed for value {value}')


class Sensor(Base):
    """
    A Read only sensor on the device (e.g. a temperature sensor)
    """
    __items__ = Base.__items__.extend(['id', 'name', 'description', 'unit'])

    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)
    _value = db.Column(db.String(80), default='-1')
    unit = db.Column(db.String(80), nullable=True)

    # Careful with this, could slow things down significantly.
    # history (=backref) - list of historic values

    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    device = db.relationship('Device',
                             backref=db.backref(
                                 'sensors', lazy=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<Sensor (name={self.name}, value={self.last_value} {self.unit}," \
               f"device={self.device_id})>"

    @property
    def last_value(self):
        """return typed value, bool"""
        try:
            return self.parse_bool(self._value)
        except TypeError:
            pass

        try:
            return self.parse_float(self._value)
        except TypeError:
            pass

        return self._value

    @last_value.setter
    def last_value(self, value):
        """Tries to parse and store float and bool, otherwise raises TypeError."""
        try:
            value = self.parse_bool(value)
        except TypeError:
            pass

        try:
            value = self.parse_float(value)
        except TypeError:
            pass

        if type(value) not in [bool, int, float]:
            raise TypeError(f"Cannot store '{type(value)}' as sensor value.")
        self._value = str(value)

    def get_last_values(self, since=None, count=None):
        """Return a desired number of history items as DICT since a specific timestamp"""
        def reduce_history_item(item):
            try:
                return {'timestamp': item.timestamp, 'value': item.value}
            except (KeyError, AttributeError):
                return None

        if since:
            history = db.session.query(HistoryItem) \
                .filter(
                    HistoryItem.sensor == self,
                    HistoryItem.timestamp >= since
                ).all()
            history = [reduce_history_item(it) for it in history]
        else:
            history = [reduce_history_item(it) for it in self.history]
        history.sort(key=lambda i: i['timestamp'])
        if not history:
            return []

        if count and count < len(history):
            def takespread(sequence, num):
                """Get n-th value generator"""
                length = float(len(sequence))
                for i in range(num):
                    yield sequence[int(math.ceil(i * length / num))]
            gen = takespread(history, count)
            history = [next(gen) for _ in range(count)]
        return history

    @property
    def value_type(self):
        return type(self.last_value).__name__

    @property
    def dictionary(self):
        d = self._to_dict()
        d['last_value'] = self.last_value
        d['type'] = self.value_type
        return d


class Control(Base):
    """
    A controllable entity on the device (e.g. a switch)
    """
    __items__ = None

    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)
    _state = db.Column(db.Boolean, default=False)  # deprecated
    value = db.Column(db.String(80), default=NOT_APPLICABLE)
    input = db.Column(db.String(80), nullable=True)

    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    device = db.relationship('Device',
                             backref=db.backref('controls', lazy=False))

    def __repr__(self):
        return f"<Control (name={self.name}, device={self.device_id})>"

    @property
    def state(self):
        return self._state

    @property
    def parsed_value(self):
        return self.parse_value(self.value)

    def parse_value(self, value):
        """Return appropriate type of the value, based on 'input' attribute."""
        if self.input == 'bool':
            return self.parse_bool(value)
        elif self.input == 'int':
            return self.parse_int(value)
        elif self.input == 'float':
            return self.parse_float(value)
        else:
            return self.value

    @property
    def dictionary(self):
        d = self._to_dict()
        d['value'] = self.parsed_value
        return d


class Task(Base):
    """
    A schedule-able action to be performed on the device
    """
    __items__ = None

    name = db.Column(db.String(80), default="Unnamed task")
    cron = db.Column(db.String(80), default="* * * * *")  # cron signature or 'status' keyword
    type = db.Column(db.String(80), nullable=True)

    locked = db.Column(db.Boolean(), default=False)
    paused = db.Column(db.Boolean(), default=False)

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
    device = db.relationship(
        'Device', backref=db.backref('tasks', lazy=False, cascade='all, delete-orphan'))

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
        t = db.session.query(Task).filter_by(id=task_id).first()
        if t:
            t.last_run = datetime.utcnow()
            t.last_run_success = True
            t.last_run_error = None
            db.session.commit()

    @staticmethod
    def set_failed(task_id, exception):
        t = db.session.query(Task).filter_by(id=task_id).first()
        if t:
            t.last_run = datetime.utcnow()
            t.last_run_success = False
            t.last_run_error = str(exception)
            db.session.commit()


class Device(Base):
    """
    Device
    """
    __items__ = None

    time_modified = db.Column(db.DateTime, nullable=True)
    last_seen_online = db.Column(db.DateTime, nullable=True)

    # Unique for device: e.g. hard-coded in the Arduino sketch or MAC from ESP32
    uuid = db.Column(db.String(80), unique=True, nullable=True)
    # Human readable, user can change it to his liking
    name = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(80), nullable=True)
    type = db.Column(db.String(80), nullable=True)

    is_online = db.Column(db.Boolean(), default=False)
    scheduler_error = db.Column(db.String(80), nullable=True)
    # sensors (=backref)
    # controls (=backref)
    # tasks (=backref)

    # store any unrecognized device attributes (for later manual triage)
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
        d['sensors'] = sorted([s.dictionary for s in self.sensors], key=lambda t: t['id'])
        d['controls'] = sorted([c.dictionary for c in self.controls], key=lambda t: t['id'])
        d['tasks'] = sorted([t.dictionary for t in self.tasks], key=lambda t: t['id'])
        d['scheduler_running'] = CACHE.has_active_scheduler(self.uuid)
        d['unrecognized'] = self.unknown_commands
        return d

    def __repr__(self):
        return f"<Device (uuid={self.uuid}, name={self.name})>"

    def update_commands(self, data: dict):
        """Update sensor/control values according to a status dict"""

        # todo: legacy remove!
        controls_keys = [c.name for c in self.controls]
        sensors_keys = [s.name for s in self.sensors]
        for key, value in data.items():
            # new style (JSON) of controls/sensors
            if type(value) is dict and value.get('type') == 'control':
                control = db.session.query(Control).filter_by(name=key, device=self).first()
                if not control:
                    control = Control(name=key, description=key, device=self)
                control.value = str(value.get('value')) or NOT_APPLICABLE
                control.input = str(value.get('input'))

            elif type(value) is dict and value.get('type') == 'sensor':
                sensor = db.session.query(Sensor).filter_by(name=key, device=self).first()
                if not sensor:
                    sensor = Sensor(
                        name=key,
                        description=key,
                        device=self,
                        unit=value.get("unit", NOT_APPLICABLE)
                    )
                sensor.last_value = value.get('value')

            # todo: legacy remove!
            elif key in controls_keys:
                control = db.session.query(Control).filter_by(name=key, device=self).first()
                if not controls_keys:  # todo: necessary?
                    raise UnexpectedModelException("Key was in controls, db.session.query(but) failed.")
                control.value = str(value)
            # todo: legacy remove!
            elif key in sensors_keys:
                sensor = db.session.query(Sensor).filter_by(name=key, device=self).first()
                if not sensor:  # todo: necessary?
                    raise UnexpectedModelException("Key was in controls, db.session.query(but) failed.")
                sensor.last_value = value

            else:
                self.put_unknown_command(key, value)

    @classmethod
    def from_status_response(cls, device: PhysicalDevice, status: StatusResponse, create=True):
        d = db.session.query(Device).filter_by(uuid=device.uuid).first()
        if not d and create:
            d = Device(uuid=device.uuid,
                       name=str(device),
                       type=device.device_type.value,
                       url=device.url)
            db.session.add(d)
            db.session.commit()  # commit the new device to create its ID
        if d:
            d.update_commands(status.controls)
            d.update_commands(status.sensors)
            d.is_online = True
            d.last_seen_online = datetime.utcnow()
        return d


class HistoryItem(Base):
    """Stored sensor's history data."""
    __items__ = None

    timestamp = db.Column(db.DateTime, nullable=True)
    _value = db.Column(db.String(80), default='-1')

    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'), nullable=False)
    sensor = db.relationship(
        'Sensor', backref=db.backref('history', lazy=True, cascade='all, delete-orphan'))

    @property
    def dictionary(self):
        d = self._to_dict()
        d['value'] = self.value
        return d

    @property
    def value(self):
        """return typed value or string"""
        try:
            return self.parse_bool(self._value)
        except TypeError:
            pass
        try:
            return self.parse_float(self._value)
        except TypeError:
            pass
        return self._value


@event.listens_for(Device, "before_insert")
@event.listens_for(Device, "before_update")
def my_before_insert_listener(mapper, connection, target):
    target.time_modified = datetime.utcnow()
