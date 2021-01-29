import json
import logging

from datetime import datetime
from hydroserver import db, CACHE
from hydroserver.config import Config
from hydroserver.device import Device as PhysicalDevice
from sqlalchemy import event
from sqlalchemy.orm import relationship

log = logging.getLogger(__name__)
NOT_APPLICABLE = 'N/A'


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
    last_value = db.Column(db.Float, default=-1)
    unit = db.Column(db.String(80), nullable=True)

    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    device = db.relationship('Device', backref=db.backref('sensors', lazy=False))

    def __repr__(self):
        return f"<Sensor (name={self.name}, value={self.last_value} {self.unit}," \
               f"device={self.device_id})>"

    @property
    def dictionary(self):
        return self._to_dict()


class Control(Base):
    """
    A controllable entity on the device (e.g. a switch)
    """
    # possible_controls = ["light", "heat", "fan", "air_stone", "pump", ]
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)
    state = db.Column(db.Boolean, default=False)

    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    device = db.relationship('Device', backref=db.backref('controls', lazy=False))

    def __repr__(self):
        return f"<Control (name={self.name}, device={self.device_id})>"

    @property
    def dictionary(self):
        return self._to_dict()


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
        return json.loads(self._task_meta)

    @task_metadata.setter
    def task_metadata(self, md: dict):
        self._task_meta = json.dumps(md)

    @task_metadata.deleter
    def task_metadata(self):
        self._task_meta = None

    @property
    def dictionary(self):
        d = self._to_dict()
        d["meta"] = self.task_metadata
        return d


class Device(Base):
    """
    Device
    """
    time_modified = db.Column(db.DateTime, nullable=True)
    last_seen_online = db.Column(db.DateTime, nullable=True)

    # Unique for device: hard-coded in the Arduino sketch
    uuid = db.Column(db.String(80), unique=True, nullable=True)
    # Human readable, user can change it to his liking
    name = db.Column(db.String(80), nullable=False)

    is_online = db.Column(db.Boolean(), default=False)
    # sensors (=backref)
    # controls (=backref)
    # tasks (=backref)

    @property
    def dictionary(self):
        d = self._to_dict()
        d['sensors'] = [s.dictionary for s in self.sensors]
        d['controls'] = [c.dictionary for c in self.controls]
        d['tasks'] = [t.dictionary for t in self.tasks]
        d['scheduler_running'] = CACHE.has_active_scheduler(self.uuid)
        return d

    def __repr__(self):
        return f"<Device (uuid={self.uuid}, name={self.name})>"

    def update_sensors(self, data: dict):
        configured = Config.PRECONFIGURED_MAPPINGS["sensors"]
        for key, value in data.items():
            if key in configured:
                if key not in [s.name for s in self.sensors]:
                    Sensor(name=key, device=self, last_value=value,
                           description=configured[key]['description'],
                           unit=configured[key]['unit'])
                else:
                    Sensor.query.filter_by(name=key, device=self).first() \
                        .last_value = value

    # todo: Take controls from self -> move init to create only
    def update_controls(self, data: dict):
        configured = Config.PRECONFIGURED_MAPPINGS["controls"]
        for key, value in data.items():
            if key in configured:
                c = Control.query.filter_by(name=key, device=self).first()
                if not c:
                    c = Control(name=key, device=self,
                                description=configured[key].get('description'))
                    try:
                        x = int(value)
                    except Exception:
                        x = 1
                    c.state = not bool(x) if Config.INVERT_BOOLEAN else bool()

    @classmethod
    def query_by_serial_device(cls, device: PhysicalDevice):
        return Device.query.filter_by(uuid=device.uuid).first()

    @classmethod
    def from_status_response(cls,
                             device: PhysicalDevice, status: dict, create=True):
        d = Device.query_by_serial_device(device)
        if not d and create:
            d = Device(uuid=device.uuid, name=str(device))
            db.session.add(d)
            db.session.commit()
        if d:
            d.update_sensors(status)
            d.update_controls(status)
            d.is_online = True
            d.last_seen_online = datetime.utcnow()
        return d


@event.listens_for(Device, "before_insert")
@event.listens_for(Device, "before_update")
def my_before_insert_listener(mapper, connection, target):
    target.time_modified = datetime.utcnow()
