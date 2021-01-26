import logging
import time


from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from hydroserver import db
from hydroserver.device import DeviceException
from hydroserver.device.serial import SerialDevice
from hydroserver.models import Device, Task
from hydroserver.scheduler.tasks import ScheduledTask

log = logging.getLogger(__name__)
MAX_WORKERS = 4  # max threads to execute simultaneously
SAFE_INTERVAL = 1.8  # seconds left to ignore and execute right away
RECONNECT_ATTEMPTS = 10
IDLE_INTERVAL_SECONDS = 10


class Scheduler:
    """
    1 scheduler per serial device, own thread pool...
    Creates schedule based on set up tasks and their crons.
    """

    def __init__(self, device: SerialDevice):
        self.device = device
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.device_uuid = self.device.uuid

    def run(self):
        self.__loop()

    def __device_health_check(self, attempts):
        if self.device.is_responding:
            return True
        log.info(f"{self.device} is offline, checking if something changed...")
        self.device.read_status()
        if self.device.is_responding:
            return True
        return False

    def __loop(self):
        """
        1) grabs device tasks from DB
        2) sorts by which is to be scheduled the earliest
        3) wait until at least '< safe interval'
        4) execute
        """
        attempts = 0
        no_task_limit = 0
        last_executed = set()
        while True:
            # 1) Healthcheck
            if not self.__device_health_check(attempts):
                self.__set_is_offline(self.device_uuid)
                attempts += 1
                if attempts > RECONNECT_ATTEMPTS:
                    log.warning(f"{self.device} offline, stopping scheduling...")
                    self.executor.shutdown(wait=True)
                    return
                to_be_scheduled = set()
                log.warning("Device offline, schedule cleared "
                            f"(attempts={attempts}/{RECONNECT_ATTEMPTS}).")
            else:
                attempts = 0
                to_be_scheduled = {
                    ScheduledTask.from_db_object(t)
                    # ScheduledTask(t.id, croniter(t.cron).get_next(datetime))
                    for t in self.__load_tasks_from_db(self.device)
                }.difference(last_executed)

            # 2) handle tasks
            active_tasks = sorted(to_be_scheduled, key=lambda t: t.scheduled_time)
            log.debug(f"{len(active_tasks)} active tasks: {active_tasks}")
            if active_tasks:
                up_next = active_tasks[0]

                # figure out the execution time and delta
                scheduled_time = up_next.scheduled_time
                time_to_next = scheduled_time - datetime.utcnow()

                log.debug(f"Up next: id={up_next.task_id}, at {scheduled_time}"
                          f" (i.e. in {time_to_next})")
                # if inside the 'safe interval' execute right away and don't wait
                if time_to_next <= timedelta(seconds=SAFE_INTERVAL):
                    try:
                        up_next.runnable.run(self.device)
                        self.__set_task_success(up_next.task_id)
                    except DeviceException as e:
                        self.__set_task_failed(up_next.task_id, e)
                    last_executed.add(up_next)
                    time_to_next = timedelta(milliseconds=1)
            else:
                time_to_next = timedelta(seconds=IDLE_INTERVAL_SECONDS)
                no_task_limit += 1
                if no_task_limit > RECONNECT_ATTEMPTS:
                    log.warning(f"{self.device} no tasks received for quite some "
                                "time, stopping scheduling...")
                    self.executor.shutdown(wait=True)
                    return

            # 3) Time delta shenanigans
            if not time_to_next or time_to_next.seconds >= IDLE_INTERVAL_SECONDS:
                time_to_next = timedelta(seconds=IDLE_INTERVAL_SECONDS)
                last_executed.clear()  # CLEANUP - prevent memory leak

            if time_to_next < timedelta(seconds=SAFE_INTERVAL):
                time_to_next = timedelta(milliseconds=10)
            else:
                time_to_next = time_to_next - timedelta(seconds=SAFE_INTERVAL / 2)

            # 4) Obligatory sleep
            log.debug(f"sleeping for {time_to_next.total_seconds()}")
            time.sleep(time_to_next.total_seconds())

    @staticmethod
    def __load_tasks_from_db(serial_device):
        device = Device.query_by_serial_device(serial_device)
        return [t for t in device.tasks]

    @staticmethod
    def __set_is_offline(device_uuid):
        d = Device.query.filter_by(uuid=device_uuid).first()
        if d:
            d.is_online = False
            db.session.commit()

    @staticmethod
    def __set_task_success(task_id):
        t = Task.query.filter_by(id=task_id).first()
        if t:
            t.last_run = datetime.utcnow()
            t.last_run_success = True
            t.last_run_error = None
            db.session.commit()

    @staticmethod
    def __set_task_failed(task_id, exception):
        t = Task.query.filter_by(id=task_id).first()
        if t:
            t.last_run = datetime.utcnow()
            t.last_run_success = False
            t.last_run_error = str(exception)
            db.session.commit()
