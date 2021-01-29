import logging
from enum import Enum

from hydroserver import Config


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
    # ...


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
    def from_response_data(cls, data, extract_field=None):
        if data.get("status"):
            status = Status.from_string(data.get("status"))
            del data["status"]
        else:
            raise DeviceException(
                f"Response '{data or None}' does not contain 'status' field.")

        if extract_field:
            if not data.get(extract_field):
                raise DeviceException(
                    f"Response does not contain '{extract_field}' field.")
            data = data.get(extract_field)

        return DeviceResponse(status, data)


class Device:

    device_type = DeviceType.GENERIC

    def __repr__(self):
        return f"<{self.__class__.__name__} (type={self.device_type.value})>"

    # to be overridden
    def _send_raw(self, string):
        """
        Per device type implementation
        :param string: raw string to be sent
        :rtype: str
        """
        pass

    def _get_uuid(self):
        pass

    @property
    def is_connected(self):
        return False

    @property
    def is_responding(self):
        return self.uuid is not None
    # END

    @property
    def uuid(self):
        return self._get_uuid()

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

    def read_status(self, strict=True):
        """
        READ full device status (expecting dev info + sensors/controls values
        :rtype: DeviceResponse
        """
        response = DeviceResponse.from_response_data(
            self.send_command(Command.STATUS.value))

        if not response.is_success and strict:
            raise DeviceException(
                f"{self}: status read failed '{response}'")

        return response

    def read_sensor(self, sensor: str, strict=True):
        """
        READ a sensor value and return number
        :rtype: DeviceResponse
        """
        response = DeviceResponse.from_response_data(
            self.send_command(Command.SENSOR.value, sensor), extract_field=sensor)

        if not response.is_success and strict:
            raise DeviceException(
                f"{self}: '{sensor}' sensor read failed '{response}'")

        try:
            response.data = float(response.data)
        except TypeError:
            if strict:
                raise DeviceException(
                    f"{self}: received value '{response.data}' is not a number")

        return response

    def send_control(self, control: str, strict=True):
        """
        SEND a control command
        :rtype: DeviceResponse
        """
        response = DeviceResponse.from_response_data(
            self.send_command(Command.CONTROL.value, control), extract_field=control)

        if not response.is_success and strict:
            raise DeviceException(
                f"{self}: '{control}' control failed '{response}'")

        if not response.data and strict:
            raise DeviceException(
                f"{self}: no response value '{response}'")

        response.data = float(response.data)
        if Config.INVERT_BOOLEAN:
            response.data = not float(response.data)
        return response

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


from hydroserver.device.serial import scan as serial_scan
from hydroserver.device.mock import scan as mock_scan


def scan():
    import os
    try:
        mocked_devices = os.getenv("MOCK_DEV", "0")
        mocked_devices = int(mocked_devices)
    except Exception:
        mocked_devices = 0
    scans = serial_scan() or []
    scans.extend(mock_scan(num=mocked_devices))
    return scans
