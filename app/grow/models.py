import json
import logging
import math
from datetime import datetime

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import or_, and_

from app import db
from app.models import Base, Sensor, Control
from app.core.cache import CACHE
from app.core.device import Device as PhysicalDevice
from app.core.device import StatusResponse

log = logging.getLogger(__name__)
NOT_APPLICABLE = 'N/A'


class GrowSystem(Base):
    __items__ = ['name', 'description']

    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)


class GrowSystemInstance(Base):
    grow_system_id = db.Column(db.Integer, db.ForeignKey('grow_system.id'), nullable=False)
    grow_system = db.relationship(GrowSystem, backref=db.backref('instances', lazy=True))


class GrowProperty(Base):
    """Predefined and user added property 'types': EC, pH, air temp, etc..."""
    __items__ = ['name', 'description']

    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)


class GrowPropertyInstance(Base):
    """Actual property instances bound to the real device sensors/controls."""
    __items__ = Base.__items__.extend(['name', 'description'])

    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'))
    sensor = db.relationship(Sensor,
                             backref=db.backref('grow_properties', lazy=False))

    control_id = db.Column(db.Integer, db.ForeignKey('control.id'))
    control = db.relationship(Control,
                              backref=db.backref('grow_properties', lazy=False))

    property_id = db.Column(db.Integer, db.ForeignKey('grow_property.id'), nullable=False)
    grow_property = db.relationship(GrowProperty,
                                    backref=db.backref(
                                        'instances', lazy=False, cascade='all, delete-orphan'))

    grow_system_id = db.Column(db.Integer, db.ForeignKey('grow_system_instance.id'), nullable=True)
    grow_system = db.relationship(GrowSystemInstance,
                                  backref=db.backref(
                                      'grow_properties', lazy=False, cascade='all, delete-orphan'))
