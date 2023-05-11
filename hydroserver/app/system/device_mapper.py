from app import CACHE, db
from app.models import Device
from app.core.device import Device as PhysicalDevice


class MappingError(Exception):
    pass


class DeviceMapper(object):
    """
    Helps map (and dynamically retrieve db model) physical devices and db device objects
    by a common attribute: UUID
    """

    def __init__(self, uuid):
        self._uuid = uuid

    @property
    def uuid(self):
        return self._uuid

    @property
    def model(self):
        """re-query on each call"""
        return Device.query.filter_by(uuid=self._uuid).first()

    @property
    def physical(self):
        try:
            return CACHE.get_active_device_by_uuid(self._uuid, strict=True)
        except KeyError as e:
            raise MappingError(e)

    @classmethod
    def from_anything(cls, identifier):
        if type(identifier) is str:
            return cls.from_uuid(identifier)
        if type(identifier) is Device:
            return cls.from_model(identifier)
        if issubclass(identifier.__class__, PhysicalDevice):
            return cls.from_physical(identifier)
        else:
            raise MappingError(f"unknown type: {type(identifier)} for object {identifier}")

    @classmethod
    def from_uuid(cls, uuid: str):
        return DeviceMapper.from_physical(
            CACHE.get_active_device_by_uuid(uuid, strict=True))

    @classmethod
    def from_model(cls, db_device: Device):
        physical_device = CACHE.get_active_device(db_device, strict=True)
        if not physical_device.uuid:
            raise MappingError(f'Device does not have a uuid: {physical_device}')
        return cls(physical_device.uuid)

    @classmethod
    def from_physical(cls, physical_device):
        if not physical_device.uuid:
            raise MappingError(f'Device does not have a uuid: {physical_device}')
        db_device = db.session.query(Device).filter_by(uuid=physical_device.uuid).first()
        if not db_device:
            raise MappingError(f'No such device in database: {physical_device}')
        return cls(physical_device.uuid)