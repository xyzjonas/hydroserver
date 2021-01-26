import threading


class Cache:

    def __init__(self):
        self.__active_devices = dict()
        self.lock = threading.Lock()

    def get_active_devices_keys(self):
        return self.__active_devices.keys()

    def get_active_device(self, uuid):
        return self.__active_devices[uuid]

    def add_active_device(self, device):
        with self.lock:
            self.__active_devices[device.uuid] = device

    def remove_active_device(self, device):
        with self.lock:
            del self.__active_devices[device.uuid]

    def clear(self):
        with self.lock:
            self.__active_devices.clear()

    @property
    def active_devices(self):
        return list(self.__active_devices.values())

    @property
    def items(self):
        return {uuid: device for uuid, device in self.__active_devices.items()}
