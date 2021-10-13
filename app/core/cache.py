import threading


class Cache:

    @staticmethod
    def __sanitize(device):
        return device

    def __init__(self):
        self.__active_devices = dict()
        self.__active_schedulers = dict()
        self.lock = threading.Lock()

    def get_all_active_devices(self):
        return list(self.__active_devices.values())

    def get_active_device(self, device, strict=False):
        return self.get_active_device_by_uuid(self.__sanitize(device).uuid, strict=strict)

    def get_active_device_by_uuid(self, uuid, strict=False):
        dev = self.__active_devices.get(uuid)
        if not dev and strict:
            raise KeyError(f'No such active device cached: {uuid}')
        return dev

    def add_active_device(self, device):
        with self.lock:
            self.__active_devices[device.uuid] = self.__sanitize(device)

    def remove_active_device(self, device):
        with self.lock:
            del self.__active_devices[device.uuid]

    def clear_devices(self):
        with self.lock:
            self.__active_devices.clear()

    def has_active_scheduler(self, uuid):
        return self.__active_schedulers.get(uuid) is not None \
               and self.__active_schedulers.get(uuid).is_running

    def get_active_scheduler(self, uuid):
        if self.has_active_scheduler(uuid):
            return self.__active_schedulers[uuid]

    def add_scheduler(self, uuid, scheduler):
        if self.has_active_scheduler(uuid):
            return  # not allowed more than 1
        with self.lock:
            self.__active_schedulers[uuid] = scheduler

    def remove_scheduler(self, uuid):
        if self.has_active_scheduler(uuid):
            with self.lock:
                del self.__active_schedulers[uuid]


CACHE = Cache()
