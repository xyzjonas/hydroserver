import uuid
from hydroserver.device import Device


class MockedDevice(Device):

    def __init__(self):
        self.__uuid = str(uuid.uuid1())
        self.toggle = False

    def _get_uuid(self):
        return self.__uuid

    def _send_raw(self, string):
        return f"status:ok,temp:23.1, hum:50,switch_01:{'1' if self.toggle else '0'}"

    def send_control(self, control: str, strict=True):
        self.toggle = not self.toggle
        return super().send_control(control, strict)

    def __repr__(self):
        return f"{super().__repr__()[:-2]}, random_shit='why_not'"

    @property
    def is_connected(self):
        return True


def scan(num=1):
    return [MockedDevice() for i in range(num)]

