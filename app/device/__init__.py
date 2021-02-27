import logging
from enum import Enum

from app import Config


log = logging.getLogger(__name__)


class Command(Enum):
    """Available device communication commands"""
    PING = Config.PRECONFIGURED_COMMAND["ping"]
    STATUS = Config.PRECONFIGURED_COMMAND["status"]
    CONTROL = Config.PRECONFIGURED_COMMAND["control_prefix"]
    SENSOR = Config.PRECONFIGURED_COMMAND["sensor_prefix"]


class DeviceType(Enum):
    SERIAL = "serial"
    WIFI = "wifi"
    ZIGBEE = "zigbee"
    BLUETOOTH = "bluetooth"
    GENERIC = "generic"
    # ...


class Status(Enum):
    OK = Config.STATUS_OK
    FAIL = Config.STATUS_FAIL
    NO_DATA = "NO_DATA"

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
            status = Status.from_string(data.pop("status"))
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
    """
    To implement:

    * _send_raw (I/O)
    * unique id getter
    * initialization routine
    * is_connected/is_responding behaviour
    * device_type
    """

    device_type = DeviceType.GENERIC

    def __init__(self):
        self._init()

    def __repr__(self):
        return f"<{self.__class__.__name__} (type={self.device_type.value})>"

    # to be overridden
    def _send_raw(self, string):
        """
        Per device type send/receive implementation.
        (!) responsible for changing device state in case of connection issues.

        :param str string: raw string to be sent
        :return: raw string (decoded) response
        :rtype: str
        """
        pass

    # to be overridden
    def _get_uuid(self):
        """UUID getter"""
        pass

    # to be overridden
    def _init(self):
        """Initialization method -> fetch status and make device responding"""
        pass

    # to be overridden
    def _is_connected(self):
        """Device is sending/receiving'"""
        pass

    # to be overridden
    def _is_responding(self):
        """Device is sending/receiving according to 'protocol'"""
        pass

    @property
    def is_responding(self):
        return self._is_responding() and self._is_connected()

    @property
    def is_connected(self):
        return self._is_connected()

    @property
    def uuid(self):
        return self._get_uuid()

    def ensure_connectivity(self):
        """If device is not responding, try to initialize it."""
        if not self.is_responding:
            log.warning(f"{self} is not connected")
            self._parse_response(self._send_raw(Command.STATUS.value))
            if not self.is_responding:
                log.error(f"{self}: reconnect failed: "
                          f"connected={self.is_connected}, responding={self.is_responding}")
                return False
        return True

    def send_command(self, command, retries=2):
        """
        SEND a generic string command
        :rtype: dict
        """
        cmd = str(command)
        log.debug(f"{self}: sending command '{cmd}'")
        data = self._parse_response(self._send_raw(cmd))

        # retry
        if not data:
            for i in range(retries):
                if self.ensure_connectivity():
                    data = self._parse_response(self._send_raw(cmd))
                    if data:
                        break

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
        cmd = "_".join([Command.SENSOR.value, sensor])
        response = DeviceResponse.from_response_data(
            self.send_command(cmd), extract_field=sensor)

        if not response.is_success and strict:
            raise DeviceException(
                f"{self}: '{sensor}' sensor read failed '{response}'")

        try:
            # fixme: response TYPES!
            response.data = float(response.data)
        except (TypeError, ValueError):
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

        if response.data is None and strict:
            raise DeviceException(f"{self}: no response value '{response}'")
        return response

    def health_check(self):
        if self.is_responding:
            return True
        log.info(f"{self} is offline, checking if something changed...")

        try:
            self.read_status()
        except DeviceException as e:
            log.error(f"Status failed: {e}")
            return False

        if self.is_responding:
            return True
        return False

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


from app.device.serial import scan as serial_scan
from app.device.mock import scan as mock_scan


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
