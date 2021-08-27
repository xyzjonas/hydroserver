import logging
import os
from enum import Enum

from app import Config

log = logging.getLogger(__name__)


class Command(Enum):
    """Available device communication commands"""
    PING = Config.PRECONFIGURED_COMMAND["ping"]
    STATUS = Config.PRECONFIGURED_COMMAND["status"]
    CONTROL = Config.PRECONFIGURED_COMMAND["control_prefix"]
    SENSOR = Config.PRECONFIGURED_COMMAND["sensor_prefix"]

    def __str__(self):
        return self.value


class DeviceType(Enum):
    SERIAL = "serial"
    WIFI = "wifi"
    ZIGBEE = "zigbee"
    BLUETOOTH = "bluetooth"
    GENERIC = "generic"
    MOCK = "mock"
    # ...


class Status(Enum):
    OK = Config.STATUS_OK  # response contains status and is 'ok'
    FAIL = Config.STATUS_FAIL  # response contains status and is not 'ok'
    NO_DATA = "NO_DATA"  # empty response
    MALFORMED = "MALFORMED"  # response does not contain 'status'

    @classmethod
    def from_string(cls, string):
        try:
            return Status(string)
        except ValueError:
            return Status.MALFORMED


class DeviceException(Exception):
    """Generic device exception"""
    pass


class DeviceCommunicationException(DeviceException):
    """Raise when there is something wrong with the device,
    e.g. malformed data, filed connection, ..."""
    pass


class DeviceResponse:
    """Generic response object. Pops-out status item, everything else is dict."""
    def __init__(self, status, data=None, reason=None):
        self.status = status
        self.data = data
        self.reason = reason

    def __repr__(self):
        return f"<DeviceResponse (status={self.status}, data={self.data})>"

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    @property
    def is_success(self):
        return self.status == Status.OK

    @classmethod
    def from_response_data(cls, data):
        if type(data) is not dict:
            return cls(Status.MALFORMED, data=data, reason="Response is not a dict.")
        if not data:
            return cls(Status.NO_DATA, data=data, reason="Response is an empty dict.")
        if "status" not in data:
            return cls(Status.MALFORMED, data=data, reason="Does not contain status.")
        status = Status.from_string(data.pop("status", None))
        return cls(status, data)


class SensorResponse(DeviceResponse):
    """Sensor/Control 'get' object. Data should contain 'value' key."""
    def __init__(self, status, data=None, reason=None):
        super(SensorResponse, self).__init__(status, data, reason)
        if not data or type(data) is not dict or "value" not in data:
            raise DeviceCommunicationException(f"Received response '{data}' is missing 'value'.")

    @property
    def value(self):
        return self.data['value']


class StatusResponse(DeviceResponse):
    """Status response object.
    Should contain everything, informational as well as sensors, controls."""

    # non-control/sensor fields
    # todo: configurable?
    info_fields = ['status', 'uuid']

    def __init__(self, status, data=None, reason=None):
        super(StatusResponse, self).__init__(status, data, reason)
        self._controls = None
        self._sensors = None

    @staticmethod
    def __is_control(item):
        try:
            x = item.get("type") == "control"
            return x
        except (AttributeError, KeyError):
            return False

    @staticmethod
    def __is_sensor(item):
        try:
            return item.get("type") == "sensor"
        except (AttributeError, KeyError):
            return False

    @property
    def controls(self):
        if not self._controls:
            controls = {k: v for k, v in self.data.items() if k not in self.info_fields}
            controls = {k: v for k, v in controls.items() if self.__is_control(v)}
            self._controls = controls
        return self._controls

    @property
    def sensors(self):
        if not self._sensors:
            sensors = {k: v for k, v in self.data.items() if k not in self.info_fields}
            sensors = {k: v for k, v in sensors.items() if self.__is_sensor(v)}
            self._sensors = sensors
        return self._sensors


class Device(object):
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
    def _send_raw(self, data):
        """
        Per device type send/receive implementation.
        (!) responsible for changing device state in case of connection issues.

        :param dict data: request data
        :return: response dictionary
        :rtype: dict
        """
        pass

    # to be overridden
    def _get_uuid(self):
        """UUID getter"""
        pass

    # to be overridden
    def _get_url(self):
        """URL getter"""
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

    @property
    def url(self):
        return self._get_url()

    def ensure_connectivity(self):
        """If device is not responding, try to initialize it."""
        try:
            log.debug(f"Ensuring connectivity: {self}")
            self._send_raw(self._simple_request(Command.STATUS))
            return True
        except DeviceException:
            return False

    def send_command(self, request_data, retries=2):
        """
        public wrapper for _send_raw() with retry mechanism.

        :param request_data: data to be sent
        :param in retries: number of retries
        :rtype: dict
        """
        # fallback to string-only requests
        if type(request_data) is not dict:
            request_data = self._simple_request(str(request_data))

        try:
            return self._send_raw(request_data)
        except DeviceCommunicationException:
            for i in range(retries):
                if self.ensure_connectivity():
                    try:
                        response_dict = self._send_raw(request_data)
                        if response_dict:
                            return response_dict
                    except DeviceException:
                        pass
            raise

    def read_status(self, strict=True):
        """
        READ full device status (expecting dev info + sensors/controls values
        :rtype: StatusResponse
        """
        received = self.send_command(Command.STATUS.value)
        try:
            return StatusResponse.from_response_data(received)
        except DeviceCommunicationException as e:
            raise DeviceException("Unexpected error while reading status.", e)

    def read_sensor(self, sensor: str, strict=True):
        """
        READ a sensor value and return number
        :rtype: DeviceResponse
        """
        # raise NotImplementedError("Read sensor not implemented yet, sorry.")
        cmd = f"{Command.SENSOR.value}{sensor}"
        response = DeviceResponse.from_response_data(self.send_command(cmd))

        if not response.is_success and strict:
            raise DeviceException(
                f"{self}: '{sensor}' sensor read failed '{response}'")

        try:
            # fixme: response TYPES!
            response.data = response.data.get("value")
        except (TypeError, ValueError):
            if strict:
                raise DeviceException(
                    f"{self}: received value '{response.data}' is not a number")
        return response

    def send_control(self, control: str, value=None, strict=True):
        """
        SEND a control command
        :rtype: SensorResponse
        """
        command_name = f"{Command.CONTROL.value}{control}"
        request = {
            'request': command_name,
        }
        if value:
            request['value'] = value

        try:
            return SensorResponse.from_response_data(self.send_command(request))
        except DeviceException as e:
            raise DeviceException("Unexpected error while sending control cmd.", e)

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
    def _simple_request(string_requst):
        return {'request': str(string_requst)}


from app.device.serial import scan as serial_scan
from app.device.mock import scan as mock_scan


def scan():
    try:
        mocked_devices = os.getenv("MOCK_DEV", "0")
        mocked_devices = int(mocked_devices)
    except Exception:
        mocked_devices = 0
    scans = serial_scan() or []
    scans.extend(mock_scan(num=mocked_devices))
    return scans
