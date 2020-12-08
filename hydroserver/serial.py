import enum
import glob
import logging
import threading
import time

import termios
from serial import Serial, SerialException
from hydroserver import app


log = logging.getLogger(__name__)
# CONSTANTS
baud_rate = 19200
serial_prefix = app.config["SERIAL_PREFIX"]


# todo: move to config, or auto scan
# SERIAL_PORTS = ['/dev/ttyUSB0', '/dev/ttyUSB1']


class SerialCommand(enum.Enum):
    PING = "ping"
    INFO = "info"
    STATUS = "status"


class DeviceType(enum.Enum):
    ARDUINO_UNO = "Arduino UNO"


class MyArduino:

    device_type = DeviceType.ARDUINO_UNO
    TIMEOUT = 5
    WAIT_FOR_RESPONSE = 0.1

    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        self.lock = threading.Lock()
        self.uuid = None
        self.serial = None

        self.serial = self.__init_serial()

    def __init_serial(self):
        log.info("Initializing {}...".format(self))
        try:
            serial = Serial(self.port, self.baud, timeout=self.TIMEOUT)
            time.sleep(2)  # fixme: serial takes time to be ready to receive

            device_info = self.__parse_dict(
                self.__send(serial, SerialCommand.INFO.value))
            if device_info:
                if "uuid" in device_info.keys():
                    self.uuid = device_info['uuid']
                    return serial
                else:
                    log.warning("Device info received, but without UUID field")
            else:
                log.warning("Device info not received.")
        except (FileNotFoundError, SerialException) as e:
            log.error("Failed to open serial connection: {}".format(e))
        return None

    # [!] one and only send method
    def __send(self, serial, command, wait_for_response=WAIT_FOR_RESPONSE):
        with self.lock:
            try:
                log.debug("{}: sending '{}'".format(self, command))
                # serial.flushInput()
                serial.flush()
                to_write = "{}\n".format(command).encode("utf-8")
                serial.write(to_write)
                time.sleep(wait_for_response)
                response = serial.readline().decode("utf-8").rstrip()
                if not response:
                    self.uuid = None
                    log.warning(
                        "{}: response for '{}' not received..".format(self, command))
                log.debug("{}: received '{}'".format(self, response))
                return response
            except SerialException as e:
                log.warning(e.strerror)
                self.uuid = None
            except termios.error as e:
                log.fatal("{}: device got probably disconnected".format(e))
                self.uuid = None
                self.serial = None

    @staticmethod
    def __parse_dict(response_string):
        data = {}
        if response_string:
            for item in response_string.split(","):
                if len(item.split(":")) < 2:
                    continue
                key, value = item.split(":")
                data[key] = value
        return data

    def reset_serial(self):
        self.serial = None

    def send_command(self, command):
        if not self.is_connected:
            log.warning("'{}' is not connected".format(self))
            serial = self.__init_serial()
            if not serial:
                return
            else:
                self.serial = serial
        return self.__send(self.serial, command)

    def read_status(self):
        data = self.__parse_dict(self.send_command(SerialCommand.STATUS.value))
        # omit uuid in the response, only data is what we care for..
        if data and data.get("uuid"):
            del data["uuid"]
        return data

    @property
    def is_responding(self):
        return self.uuid is not None

    @property
    def is_connected(self):
        return self.serial is not None

    def __str__(self):
        return "{} ({} @ {})".format(self.device_type.value, self.port, self.baud)

    def __repr__(self):
        return self.__str__()


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
            device = MyArduino(port, baud_rate)
        except SerialException as e:
            log.warning(e)
            continue
        if device.is_responding:
            found_devices.append(device)
        else:
            log.warning("{} not responding.".format(device))
    log.info("Scan complete, found devices: {}".format(found_devices))
    return found_devices

