import logging

from app import db
from app.cache import CACHE
from app.device import DeviceType, DeviceException, scan
from app.device.wifi import WifiDevice
from app.device.serial import SerialDevice

from app.models import Device, Control
from app.scheduler import Scheduler

log = logging.getLogger(__name__)


class ControllerError(Exception):
    pass


def device_action(device: Device, control: Control):
    physical_device = CACHE.get_active_device_by_uuid(device.uuid)
    if not device:
        return f"{device.name} not connected", 503

    try:
        response = physical_device.send_control(control.name)
        if not response.is_success:
            raise ControllerError(f"{device}: '{control.name}' ERROR - {response}")

        control.state = response.data
        db.session.add(control)
        db.session.commit()
        # return f"{device}: '{control.name}' cmd sent successfully: {response}", 200
    except DeviceException as e:
        raise ControllerError(e)


def device_register(url):
    device = WifiDevice(url=url)

    if not device.is_site_online():
        raise ControllerError(f"Device '{url}' is not responding.")
    try:
        status = device.read_status()
        d = Device.from_status_response(device, status.data, create=True)

        db.session.add(d)
        db.session.commit()
    except Exception as e:
        raise ControllerError(e)
    CACHE.add_active_device(device)


def init_device(dev):
    status = dev.read_status()
    if status.is_success:
        d = Device.from_status_response(dev, status.data)
        db.session.add(d)
        db.session.commit()
        CACHE.add_active_device(dev)
        return True
    return False


def device_scan():
    CACHE.clear_devices()
    found_devices = scan()
    for device in found_devices:
        if init_device(device):
            CACHE.add_active_device(device)
    return found_devices


def init_devices():
    """Init (reconnect & cache) all devices found in the db."""
    devices = Device.query.all()
    log.info(f'Initializing devices ({len(devices)} found in the db).')
    for device in devices:
        log.info(f'Initializing {device}')
        if CACHE.get_active_device_by_uuid(device.uuid):
            log.debug(f'Already cached, skipping...')
            continue
        try:
            type_ = DeviceType(device.type)
        except ValueError:
            log.error(f'Unrecognized device type: {device.type}')
            continue

        if type_ == DeviceType.SERIAL:
            port, baud = SerialDevice.port_baud(device.url)
            physical_device = SerialDevice(port=port, baud=baud)
        elif type_ == DeviceType.WIFI:
            physical_device = WifiDevice(device.url)
        else:
            log.error(f'Unsupported device type: {type_}')
            continue
        status = physical_device.read_status()
        if not status.is_success:
            log.error(f'Unreachable device: {physical_device}')
            continue
        CACHE.add_active_device(physical_device)


def run_scheduler(device: Device):
    if CACHE.has_active_scheduler(device.uuid):
        return
    physical_device = CACHE.get_active_device_by_uuid(device.uuid)
    scheduler = Scheduler(physical_device)
    CACHE.add_scheduler(device.uuid, scheduler)
    scheduler.start()

