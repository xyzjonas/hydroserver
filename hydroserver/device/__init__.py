import logging
from enum import Enum

from hydroserver import Config, db
# from hydroserver.models import Device as DeviceDb


log = logging.getLogger(__name__)


class Command(Enum):
    """Available device communication commands"""
    PING = Config.PRECONFIGURED_COMMAND["ping"]
    STATUS = Config.PRECONFIGURED_COMMAND["status"]
    CONTROL = Config.PRECONFIGURED_COMMAND["control_prefix"]
    SENSOR = Config.PRECONFIGURED_COMMAND["sensor_prefix"]


class DeviceType(Enum):
    ARDUINO_UNO = "Arduino UNO"
    GENERIC = "Generic device"


class Status(Enum):
    OK = Config.STATUS_OK
    FAIL = Config.STATUS_FAIL

    @classmethod
    def from_string(cls, string):
        try:
            return Status(string)
        except ValueError:
            return Status.FAIL


class DeviceException(Exception):
    """Generic device exception"""
    pass


class DeviceResponse:

    def __init__(self, status, data=None):
        self.status = status
        self.data = data

    def __repr__(self):
        return f"<DeviceResponse (status={self.status}, data={self.data})>"

    @property
    def is_success(self):
        return self.status == Status.OK

    @classmethod
    def from_response_data(cls, data, status=Status.FAIL):
        if data.get("status"):
            status = Status.from_string(data.get("status"))
            del data["status"]
        return DeviceResponse(status, data)


class Device:

    device_type = DeviceType.GENERIC

    def __repr__(self):
        return f"<{self.__name__} (type={self.device_type.value})>"

    @property
    def uuid(self):
        return self._get_uuid()

    def _send_raw(self, string):
        """
        Per device type implementation
        :param string: raw string to be sent
        :rtype: str
        """
        pass

    def _get_uuid(self):
        pass

    def send_command(self, *args, separator=""):
        """
        SEND a generic string command
        :rtype: dict
        """
        cmd = separator.join(args)
        log.debug(f"{self}: sending command '{cmd}'")
        data = self._parse_response(self._send_raw(cmd))
        log.debug(f"{self}: received '{data}'")
        return data

    def read_status(self):
        """
        READ full device status (expecting dev info + sensors/controls values
        :rtype: DeviceResponse
        """
        return DeviceResponse.from_response_data(
            self.send_command(Command.STATUS.value))

    def read_sensor(self, sensor):
        """
        READ a sensor value and return number
        :rtype: DeviceResponse
        """
        if type(sensor) is not str:
            sensor = sensor.name

        response = DeviceResponse.from_response_data(
            self.send_command(Command.SENSOR.value, sensor))
        if response.data.get(sensor):
            val = response.data.get(sensor)
            response.data = float(val)

        return response

    def send_control(self, control):
        """
        SEND a control command
        :rtype: DeviceResponse
        """
        if type(control) is not str:
            control = control.name
        return DeviceResponse.from_response_data(
            self.send_command(Command.CONTROL.value, control))

    @staticmethod
    def _parse_response(response_string):
        """
        parsing method, by default expects colon separated 'x:y' tuples
        :rtype: dict
        """
        data = {}
        if response_string:
            for item in response_string.split(","):
                if len(item.split(":")) != 2:
                    continue
                key, value = item.split(":")
                data[key] = value
        return data
