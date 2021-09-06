import glob
import json
import logging
import re
import termios
import threading
import time

from serial import Serial, SerialException

from app import Config
from app.core.device import Device, DeviceType, DeviceException, DeviceCommunicationException,  Command

log = logging.getLogger(__name__)

# CONSTANTS
baud_rate = Config.BAUD_RATE
serial_prefix = Config.SERIAL_PREFIX


class DeviceSerialException(DeviceException):
    """Something wrong with serial connection"""
    pass


class DeviceNotFoundException(DeviceSerialException):
    """File not found - not connected"""
    pass


class DeviceNotRespondingException(DeviceException):
    """Serial works, but we're not receiving expected data"""
    pass


class SerialDevice(Device):

    device_type = DeviceType.SERIAL
    TIMEOUT = 5
    WAIT_FOR_RESPONSE = 0.1

    __url_pattern = re.compile('^serial://(?P<port>[\w/-]+):(?P<baud>\d+)$')

    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        self.lock = threading.Lock()
        self.serial = None
        self.__uuid = None
        try:
            super(SerialDevice, self).__init__()
        except DeviceCommunicationException:
            # do nothing, _send_raw 'marked' this object as unresponsive already.
            pass

    def _get_uuid(self):
        return self.__uuid

    @staticmethod
    def port_baud(url: str):
        """Return connection details from url string: serial://<port>:<baud>"""
        match = re.match(SerialDevice.__url_pattern, str(url))
        if not match:
            return None
        return match.groupdict()['port'], int(match.groupdict()['baud'])

    def _get_url(self):
        return f"serial://{self.port}:{self.baud}"

    # @Override
    def _init(self):
        log.debug("Initializing {}".format(self))
        try:
            self.serial = Serial(self.port, self.baud, timeout=self.TIMEOUT)
            time.sleep(2)  # serial takes time to be ready to receive

            device_info = self._send_raw(self._simple_request(Command.STATUS))
            if device_info:
                if "uuid" in device_info:
                    self.__uuid = device_info['uuid']
                else:
                    raise DeviceCommunicationException(
                        "Device info received, but without UUID field")
            else:
                raise DeviceCommunicationException("Device info not received.")

        except (FileNotFoundError, SerialException, ValueError) as e:
            log.error("Failed to open serial connection: {}".format(e))
            self.serial = None
            raise DeviceCommunicationException("Failed to open serial connection.", e)

    # [!] one and only send method
    def _send_raw(self, request_dict):
        if not self.serial:
            raise DeviceCommunicationException("Serial is None. Connection wasn't initialized"
                                               "or was broken.")
        with self.lock:
            try:
                self.serial.flush()
                to_write = json.dumps(request_dict).encode('utf-8')
                self.serial.write(to_write)
                time.sleep(self.WAIT_FOR_RESPONSE)
                response = self.serial.readline().decode("utf-8").rstrip()
                if not response:
                    self.__uuid = None
                    raise DeviceCommunicationException(
                        "{}: response for '{}' not received..".format(self, request_dict))

                return json.loads(response)
            except SerialException as e:
                log.warning(e)
                self.__uuid = None
                self.serial = None
                raise DeviceCommunicationException(e)
            except termios.error as e:
                log.fatal("{}: device got probably disconnected".format(e))
                self.__uuid = None
                self.serial = None
                raise DeviceCommunicationException("Device got probably disconnected.", e)

    def reset_serial(self):
        self.serial = None

    def _is_connected(self):
        return self.serial is not None

    def _is_responding(self):
        return self.__uuid is not None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{super().__repr__()[:-2]}, port={self.port}, baud={self.baud})>"


def get_connected_devices():
    devices = glob.glob("/dev/{}*".format(serial_prefix))
    log.info("Connected devices (prefix '{}'): {}".format(serial_prefix, devices))
    return devices


def scan(exclude=None):
    """
    Run scan for all configured serial ports
    """
    if not exclude:
        exclude = []
    log.info("Scanning for serial devices...")
    found_devices = []
    for port in get_connected_devices():
        if port in exclude:
            log.info("{}: skipping...".format(port))
            continue
        try:
            device = SerialDevice(port, baud_rate)
        except SerialException as e:
            log.warning(e)
            continue
        if device.is_responding:
            found_devices.append(device)
        else:
            log.warning("{} not responding.".format(device))
    log.info("Scan complete, found devices: {}".format(found_devices))
    return found_devices

