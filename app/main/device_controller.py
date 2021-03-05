import logging

from app import init_device, db
from app.cache import CACHE
from app.device import DeviceException, scan
from app.device.wifi import WifiDevice
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


def device_scan():
    CACHE.clear_devices()
    found_devices = scan()
    for device in found_devices:
        if init_device(device):
            CACHE.add_active_device(device)
    return found_devices


def run_scheduler(device: Device):
    if CACHE.has_active_scheduler(device.uuid):
        return
    physical_device = CACHE.get_active_device_by_uuid(device.uuid)
    scheduler = Scheduler(physical_device)
    CACHE.add_scheduler(device.uuid, scheduler)
    scheduler.start()

