import datetime
import logging

from app import db
from app.core.cache import CACHE
from app.core.device import DeviceType, DeviceException, scan
from app.core.device.http import HttpDevice
from app.core.device.serial import SerialDevice
from app.core.device.mock import MockedDevice

from app.models import Device, Control, Task, HistoryItem
from app.core.scheduler import Scheduler
from app.core.tasks import TaskType
from app.system.device_mapper import DeviceMapper

log = logging.getLogger(__name__)


class ControllerError(Exception):
    """Errors that controller cannot solve."""
    pass


class Controller(object):
    """Wrapper for device, performs actions and updates models accordingly.
    Catches all device exceptions."""
    def __init__(self, device):
        try:
            self.device = DeviceMapper.from_anything(device)
        except KeyError:
            raise ControllerError(f"Device controller init failed for: {device}")

    def read_status(self):
        """Read status and update db model."""
        device = self.device.model
        try:
            status = self.device.physical.read_status()
            if status and status.is_success:
                device = Device.from_status_response(self.device.model, status, create=False)
            else:
                device.is_online = False
        except DeviceException as e:
            log.error(f"{self.device.physical} read status failed: {e}")
            device.is_online = False
        finally:
            db.session.commit()

    def action(self, control: Control, value=None):
        """Send command action and update db model."""
        device = self.device.model
        try:
            if value:
                try:
                    value = control.parse_value(value)
                except TypeError as e:
                    raise ControllerError(f"Invalid supplied value: {value}", e)
            response = self.device.physical \
                .send_control(control.name, value=value)
            if not response.is_success:
                log.error(f"{device}: '{control.name}' is not success - {response}")
                device.is_online = False
            control.value = str(response.value)
        except DeviceException as e:
            log.error(f"{self.device.physical} action for '{control.name}' failed: {e}")
            device.is_online = False
        finally:
            db.session.commit()

    def log_sensors(self):
        """Create history items for all attached sensors."""
        time = datetime.datetime.utcnow()
        for sensor in self.device.model.sensors:
            item = HistoryItem(timestamp=time, _value=str(sensor.last_value), sensor=sensor)
            db.session.add(item)
        db.session.commit()


def register_device(url):
    device = HttpDevice(url=url)

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


def ensure_system_tasks_are_created(device_db):
    """Create 'system' tasks in case they are not created yet"""
    # 1) Create the locked status task (if not yet present).
    if not db.session.query(Task) \
            .filter_by(device=device_db, name='status', cron='status') \
            .first():
        task = Task(name='status', cron='status', device=device_db,
                    type=TaskType.STATUS.value, locked=True)
        db.session.add(task)

    # 2) Create the locked sensor logger task (if not yet present).
    if not db.session.query(Task) \
            .filter_by(device=device_db, name='history-logger') \
            .first():
        from app import config
        configured_cron = config.get('SENSOR_HISTORY_LOGGING_CRON', None)
        if not configured_cron:
            log.error("SENSOR_HISTORY_LOGGING_CRON not set-up, sensor history disabled.")
        # todo: validate CRON format
        task = Task(name='history-logger', cron=configured_cron, device=device_db,
                    type=TaskType.HISTORY.value, locked=True)
        db.session.add(task)

    # 3) Create history clean-up task
    # todo: implement


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
        device = Device.from_status_response(physical_device, status, create=True)
        ensure_system_tasks_are_created(device)
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

    scheduler = Scheduler(physical_device)
    CACHE.add_scheduler(uuid, scheduler)
    scheduler.start()
    db.session.commit()


def scan_devices():
    """Run scan functions - for each device type."""
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
        devices = db.session.query(Device).all()
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
            physical_device = HttpDevice(device.url)
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

        # 4) Create the locked 'system' tasks (if not yet present).
        ensure_system_tasks_are_created(device)

        device.is_online = True
        db.session.commit()
        CACHE.add_active_device(physical_device)
