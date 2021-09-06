import uuid

from app.core.device import Device, DeviceType, Command


class MockedDevice(Device):

    device_type = DeviceType.MOCK

    def __init__(self, uid=None):
        if uid:
            self.__uuid = uid
        else:
            self.__uuid = str(uuid.uuid1())
        self.toggle = False

        super().__init__()

    @classmethod
    def from_model(cls, device_model):
        return cls(uid=device_model.uuid)

    def _get_uuid(self):
        return self.__uuid

    def _send_raw(self, data):
        if data.get('request') and data.get("request").startswith(Command.SENSOR.value):
            return {
                'status': 'ok',
                'value': 23.1
            }

        if data.get('request') and data.get("request").startswith(Command.CONTROL.value):
            return {
                'status': 'ok',
                'value': self.toggle
            }

        return {
            "status": "ok",
            "uuid": self._get_uuid(),
            "temp": {
                "type": "sensor",
                "unit": "°C",
                "value": 23.1,
            },
            "hum": {
                "type": "sensor",
                "unit": "%",
                "value": 50.1,
            },
            "switch_01":  {
                "type": "control",
                "input": "bool",
                "value": self.toggle
            }
        }

    def _init(self):
        super()._init()

    def _is_connected(self):
        return True

    def _is_responding(self):
        return True

    def _get_url(self):
        return f"mocked://{self.uuid}"

    def send_control(self, control_name: str, value=None, strict=True):
        self.toggle = not self.toggle
        return super().send_control(control_name, strict)

    def __repr__(self):
        return f"{super().__repr__()[:-2]}, random_shit='why_not')>"

    @property
    def is_connected(self):
        return True


def scan(num=1):
    return [MockedDevice() for _ in range(num)]
