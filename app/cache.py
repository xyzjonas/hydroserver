import threading


class Cache:

    def __init__(self):
        self.__active_devices = dict()
        self.__active_schedulers = dict()
        self.lock = threading.Lock()

    def get_all_active_devices(self):
        return list(self.__active_devices.values())

    def get_active_device(self, uuid):
        return self.__active_devices[uuid]

    def add_active_device(self, device):
        with self.lock:
            # todo: null
            self.__active_devices[device.uuid] = device

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
