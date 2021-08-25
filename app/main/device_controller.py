import logging
from datetime import datetime

from app import db
from app.cache import CACHE
from app.device import DeviceType, DeviceException, scan
from app.device.wifi import WifiDevice
from app.device.serial import SerialDevice
from app.device.mock import MockedDevice

from app.models import Device, Control, Task
from app.scheduler import Scheduler
from app.scheduler.tasks import TaskType, ScheduledTask, TaskNotCreatedException
from app.main.device_mapper import DeviceMapper

log = logging.getLogger(__name__)


class ControllerError(Exception):
    pass


class Controller(object):
    """Wrapper for device, performs actions and updates models accordingly."""
    def __init__(self, device):
        self.device = DeviceMapper.from_anything(device)

    def read_status(self):
        # todo: error state, update device?
        status = self.device.physical.read_status()
        if status.is_success:
            device = Device.from_status_response(self.device.model, status, create=False)
            if device:
                db.session.commit()

    def action(self, control: Control, value=None):
        try:
            response = self.device.physical \
                .send_control(control.name, value=control.parse_value(value))
            if not response.is_success:
                raise ControllerError(
                    f"{self.device}: '{control.name}' is not success - {response}")

            control.value = str(response.value)
            db.session.commit()
        except DeviceException as e:
            raise ControllerError(e)


def device_action(device: Device, control: Control, value=None):
    physical_device = CACHE.get_active_device_by_uuid(device.uuid)
    if not device:
        return f"{device.name} not connected", 503

    try:
        response = physical_device.send_control(control.name, value=control.parse_value(value))
        if not response.is_success:
            raise ControllerError(f"{device}: '{control.name}' is not success - {response}")

        control.value = str(response.data)
        db.session.add(control)
        db.session.commit()
        # return f"{device}: '{control.name}' cmd sent successfully: {response}", 200
    except DeviceException as e:
        raise ControllerError(e)


def register_device(url):
    device = WifiDevice(url=url)

    if not device.is_site_online():
        raise ControllerError(f"Device '{url}' is not responding.")
    try:
        status = device.read_status()
        d = Device.from_status_response(device, status, create=True)

        db.session.add(d)
        db.session.commit()
    except Exception as e:
        raise ControllerError(e)
    CACHE.add_active_device(device)


def init_device(physical_device):
    """
    Create DB device object. Runs the first time the device is discovered.
     * Health check.
     * Create DB device model.
     * Create locked status task.
     * ...commit
    """

    status = physical_device.read_status()
    if status.is_success:
        device = Device.from_status_response(physical_device, status)
        # Create the locked status task (if not yet present).
        if not Task.query.filter_by(device=device, name='status', cron='status').first():
            task = Task(name='status', cron='status', device=device,
                        type=TaskType.STATUS.value, locked=True)
            db.session.add(task)
        db.session.commit()
        CACHE.add_active_device(physical_device)
        return True
    return False


def run_scheduler(uuid):
    if CACHE.has_active_scheduler(uuid):
        return
    physical_device = CACHE.get_active_device_by_uuid(uuid)
    if not physical_device:
        raise ControllerError(f"Scheduler couldn't be started, {uuid} not cached.")

    device = DeviceMapper.from_uuid(uuid).model
    device.scheduler_error = None

    def _edit_scheduler_error(cause=None):
        """Scheduler callback"""
        dev = DeviceMapper.from_uuid(uuid).model
        dev.scheduler_error = str(cause)
        db.session.commit()

    def _set_device_error():
        dev = DeviceMapper.from_uuid(uuid).model
        dev.is_online = False
        db.session.commit()

    scheduler = Scheduler(
        physical_device,
        device_offline_callback=_set_device_error,
        scheduler_error_callback=_edit_scheduler_error,
    )
    CACHE.add_scheduler(uuid, scheduler)
    scheduler.start()
    db.session.commit()


def scan_devices():
    CACHE.clear_devices()
    found_devices = scan()
    for device in found_devices:
        if init_device(device):
            CACHE.add_active_device(device)
            run_scheduler(device.uuid)
    return found_devices


def refresh_devices(devices=None, strict=True):
    """Init (reconnect & cache) all devices found in the db."""
    if not devices:
        devices = Device.query.all()
        log.info(f'Initializing {len(devices)} devices found in the db).')

    for device in devices:
        # 1) If cached, stop scheduling and remove.
        log.info(f'Initializing {device}')
        if CACHE.get_active_device_by_uuid(device.uuid):
            log.debug(f'Already cached, removing...')
            if CACHE.has_active_scheduler(device.uuid):
                CACHE.get_active_scheduler(device.uuid).terminate()
                CACHE.remove_scheduler(device.uuid)
            CACHE.remove_active_device(device)

        # 2) Try to create the appropriate physical device object.
        try:
            type_ = DeviceType(device.type)
        except ValueError:
            if strict:
                raise ControllerError(f'Unrecognized device type: {device.type}')
            log.error(f'Unrecognized device type: {device.type}')
            continue

        if type_ == DeviceType.SERIAL:
            port, baud = SerialDevice.port_baud(device.url)
            physical_device = SerialDevice(port=port, baud=baud)
        elif type_ == DeviceType.WIFI:
            physical_device = WifiDevice(device.url)
        elif type_ == DeviceType.MOCK:
            physical_device = MockedDevice.from_model(device)
        else:
            if strict:
                raise ControllerError(f'Unsupported device type: {type_}')
            log.error(f'Unsupported device type: {type_}')
            continue

        # 3) Health-check.
        if not physical_device.health_check():
            device.is_online = False
            if strict:
                raise ControllerError(f'Unreachable device: {physical_device}')
            log.error(f'Unreachable device: {physical_device}')
            continue

        # 4) Create the locked status task (if not yet present).
        if not Task.query.filter_by(device=device, name='status', cron='status').first():
            task = Task(name='status', cron='status', device=device,
                        type=TaskType.STATUS.value, locked=True)
            db.session.add(task)

        device.is_online = True
        db.session.commit()
        CACHE.add_active_device(physical_device)
