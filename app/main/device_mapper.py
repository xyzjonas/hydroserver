from app import CACHE, db
from app.device import Device
from app.models import Device
from app.device import Device as PhysicalDevice


class DeviceMapper(object):

    def __init__(self, db_device: Device, physical_device):
        self._physical_device = physical_device
        self._db_device = db_device

    @property
    def model(self):
        return self._db_device

    @property
    def physical(self):
        return self._physical_device

    @classmethod
    def from_anything(cls, identifier):
        if type(identifier) is str:
            return cls.from_uuid(identifier)
        if type(identifier) is Device:
            return cls.from_model(identifier)
        if issubclass(identifier.__class__, PhysicalDevice):
            return cls.from_physical(identifier)
        else:
            raise TypeError(f"unknown type: {type(identifier)} for object {identifier}")

    @classmethod
    def from_uuid(cls, uuid: str):
        physical_device = CACHE.get_active_device_by_uuid(uuid)
        if not physical_device:
            raise KeyError(f'No such device in cache: {uuid}')
        return DeviceMapper.from_physical(physical_device)

    @classmethod
    def from_model(cls, db_device: Device):
        physical_device = CACHE.get_active_device(db_device)
        if not physical_device:
            raise KeyError(f'No such device in cache: {db_device}')
        return cls(db_device, physical_device)

    @classmethod
    def from_physical(cls, physical_device):
        db_device = db.session.query(Device).filter_by(uuid=physical_device.uuid).first()
        if not db_device:
            raise KeyError(f'No such device in database: {physical_device}')
        return cls(db_device, physical_device)