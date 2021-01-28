import uuid
from hydroserver.device import Device


class MockedDevice(Device):

    def __init__(self):
        self.__uuid = str(uuid.uuid1())

    def _get_uuid(self):
        return self.__uuid

    def _send_raw(self, string):
        return "status:ok,temp:23.1, hum:50"


def scan(num=1):
    return [MockedDevice() for i in range(num)]

