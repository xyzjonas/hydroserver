import glob
import logging
import termios
import threading
import time

from serial import Serial, SerialException

from app.device import Device, DeviceType, DeviceException, Command
from app import Config


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

    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        self.lock = threading.Lock()
        self.serial = None
        self.__uuid = None
        super().__init__()

    def _get_uuid(self):
        return self.__uuid

    # @Override
    def _init(self):
        log.info("Initializing {}...".format(self))
        try:
            self.serial = Serial(self.port, self.baud, timeout=self.TIMEOUT)
            time.sleep(2)  # fixme: serial takes time to be ready to receive

            device_info = self._parse_response(
                self._send_raw(Command.STATUS.value))
            if device_info:
                if "uuid" in device_info:
                    self.__uuid = device_info['uuid']
                else:
                    log.warning("Device info received, but without UUID field")
            else:
                log.warning("Device info not received.")
        except (FileNotFoundError, SerialException, ValueError) as e:
            log.error("Failed to open serial connection: {}".format(e))
            self.serial = None

    # [!] one and only send method
    def _send_raw(self, command):
        if not self.serial:
            return
        with self.lock:
            try:
                self.serial.flush()
                to_write = "{}\n".format(command).encode("utf-8")
                self.serial.write(to_write)
                time.sleep(self.WAIT_FOR_RESPONSE)
                response = self.serial.readline().decode("utf-8").rstrip()
                if not response:
                    self.__uuid = None
                    log.warning(
                        "{}: response for '{}' not received..".format(self, command))
                return response
            except SerialException as e:
                log.warning(e)
                self.__uuid = None
                self.serial = None
            except termios.error as e:
                log.fatal("{}: device got probably disconnected".format(e))
                self.__uuid = None
                self.serial = None

    def reset_serial(self):
        self.serial = None

    def _is_connected(self):
        return self.serial is not None

    def _is_responding(self):
        return self.__uuid is not None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{super().__repr__()[:-2]}, port={self.port}, baud={self.baud}"


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

