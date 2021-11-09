import logging
import traceback

from app import db
from app.models import Base, Sensor, Control, Device

log = logging.getLogger(__name__)
NOT_APPLICABLE = 'N/A'


grow_properties = db.Table(
    'grow_properties',
    db.Column('grow_property_id', db.Integer, db.ForeignKey('grow_property.id'), primary_key=True),
    db.Column('grow_system_id', db.Integer, db.ForeignKey('grow_system.id'), primary_key=True)
)


class GrowSystem(Base):
    __items__ = ['id', 'name', 'description', 'properties']

    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)

    properties = db.relationship('GrowProperty', secondary=grow_properties, lazy='subquery',
                                 backref=db.backref('grow_systems', lazy=True))


class GrowSystemInstance(Base):
    """A grow system instance bound to an actual device, one-to-one."""
    __items__ = Base.__items__ + ['grow_properties']

    grow_system_id = db.Column(db.Integer, db.ForeignKey('grow_system.id'), nullable=False)
    grow_system = db.relationship(GrowSystem, backref=db.backref('instances', lazy=True))

    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    device = db.relationship(Device, backref=db.backref('grow_system', lazy=True), uselist=False)

    @staticmethod
    def create_grow_system_instance(system, device_id):
        instance = GrowSystemInstance(grow_system_id=system.id, device_id=device_id)
        for prop in system.properties:
            db.session.add(GrowPropertyInstance(grow_property=prop, grow_system=instance))
        return instance

    @property
    def dictionary(self):
        d = self._to_dict()
        d['device'] = {
            'name': self.device.name,
            'uuid': self.device.uuid,
            'url': self.device.url
        }
        d['name'] = self.grow_system.name
        d['description'] = self.grow_system.description
        return d


class GrowProperty(Base):
    """Predefined and user added property 'types': EC, pH, air temp, etc..."""
    __items__ = ['name', 'description', 'color']

    # Color coding the properties across the system.
    color = db.Column(db.String(9), nullable=True)

    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(80), nullable=True)


class GrowPropertyInstance(Base):
    """Actual property instances bound to the real device sensors/controls."""
    __items__ = Base.__items__ + ['control', 'sensor']

    sensor_id = db.Column(db.Integer, db.ForeignKey('sensor.id'))
    sensor = db.relationship(Sensor)

    control_id = db.Column(db.Integer, db.ForeignKey('control.id'))
    control = db.relationship(Control)

    property_id = db.Column(db.Integer, db.ForeignKey('grow_property.id'), nullable=False)
    grow_property = db.relationship(GrowProperty,
                                    backref=db.backref(
                                        'instances', lazy=False, cascade='all, delete-orphan'))

    grow_system_id = db.Column(db.Integer, db.ForeignKey('grow_system_instance.id'), nullable=True)
    grow_system = db.relationship(GrowSystemInstance,
                                  backref=db.backref(
                                      'grow_properties', lazy=False, cascade='all, delete-orphan'))

    @property
    def name(self):
        return self.grow_property.name

    @property
    def description(self):
        return self.grow_property.description

    @property
    def color(self):
        return self.grow_property.color

    @property
    def dictionary(self):
        d = self._to_dict()
        d['name'] = self.name
        d['description'] = self.description
        d['color'] = self.color
        return d


def load_from_lists(properties=None, systems=None):
    """Load pre-configured properties/systems."""
    try:
        if properties:
            property_names = [p.name for p in GrowProperty.query.all()]
            for prop in properties:
                if 'name' not in prop:
                    raise ValueError(f"Missing name for {prop}")
                if prop['name'] in property_names:
                    p = GrowProperty.query.filter_by(name=prop['name']).first()
                else:
                    p = GrowProperty(name=prop['name'])
                    db.session.add(p)
                p.description = prop.get('description', None)
                p.color = prop.get('color', '#4d4d4d')  # default to dark grey
        db.session.commit()

        if systems:
            system_names = [p.name for p in GrowSystem.query.all()]
            for system in systems:
                if 'name' not in system:
                    raise ValueError(f"Missing name for {system}")
                if system['name'] in system_names:
                    s = GrowSystem.query.filter_by(name=system['name']).first()
                else:
                    s = GrowSystem(name=system['name'])
                    db.session.add(s)
                s.description = system.get('description', None)

                for required_property in system.get('required_properties', []):
                    if required_property not in [gp.name for gp in s.properties]:
                        gp = GrowProperty.query.filter_by(name=required_property).first()
                        if not gp:
                            raise ValueError(f'Required property \'{required_property}\''
                                             f'for system \'{system["name"]}\' not in db.')
                        s.properties = list(s.properties) + [gp]

        db.session.commit()
    except Exception as e:
        log.error(f"Failed to load grow properties/systems from configuration: {e}")
        traceback.print_exc()
        db.session.rollback()
