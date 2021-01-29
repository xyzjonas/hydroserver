import logging
import time


from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from hydroserver import db, CACHE, Config
from hydroserver.device import DeviceException
from hydroserver.device import Device as PhysicalDevice
from hydroserver.models import Device, Task
from hydroserver.scheduler.tasks import ScheduledTask, \
    TaskException, TaskNotCreatedException

log = logging.getLogger(__name__)
MAX_WORKERS = Config.MAX_WORKERS
SAFE_INTERVAL = Config.SAFE_INTERVAL
RECONNECT_ATTEMPTS = Config.RECONNECT_ATTEMPTS
IDLE_INTERVAL_SECONDS = Config.IDLE_INTERVAL_SECONDS


class Scheduler:
    """
    1 scheduler per serial device, own thread pool...
    Creates schedule based on set up tasks and their crons.
    """

    def __init__(self, device: PhysicalDevice):
        self.device = device
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.device_uuid = self.device.uuid
        self.__running = False

    def __repr__(self):
        return f"<Scheduler (device={self.device}, running={self.__running})>"

    def run(self):
        self.__loop()

    @property
    def is_running(self):
        return self.__running

    def __loop(self):
        """
        * grabs device tasks from DB
        * sorts by which is to be scheduled the earliest
        * wait until at least '< safe interval'
        * execute
        """
        attempts = 0
        no_task_limit = 0
        last_executed = set()
        self.__running = True
        while True:
            # 1) Healthcheck
            if not self.__device_health_check(self.device):
                self.__set_is_offline(self.device_uuid)
                attempts += 1
                if attempts > RECONNECT_ATTEMPTS:
                    log.warning(f"{self}: device offline, stopping scheduling...")
                    self.executor.shutdown(wait=True)
                    self.__running = False
                    CACHE.remove_scheduler(self.device_uuid)
                    return
                to_be_scheduled = set()
                log.warning(f"{self}: device offline, schedule cleared "
                            f"(attempts={attempts}/{RECONNECT_ATTEMPTS}).")
            else:
                attempts = 0
                to_be_scheduled = {
                    self.__sanitize_task_input(t)
                    for t in self.__load_tasks_from_db(self.device)
                }.difference(last_executed)
                to_be_scheduled = {t for t in to_be_scheduled if t}

            # 2) handle tasks
            active_tasks = sorted(to_be_scheduled, key=lambda t: t.scheduled_time)
            log.debug(f"{self}: {len(active_tasks)} active tasks: {active_tasks}")
            if active_tasks:
                no_task_limit = 0
                up_next = active_tasks[0]

                # figure out the execution time and delta
                scheduled_time = up_next.scheduled_time
                time_to_next = scheduled_time - datetime.utcnow()

                log.debug(f"{self}: up next: id={up_next.task_id}, "
                          f"at {scheduled_time} (i.e. in {time_to_next})")
                # if inside the 'safe interval' execute right away and don't wait
                if time_to_next <= timedelta(seconds=SAFE_INTERVAL):
                    try:
                        up_next.runnable.run(self.device)
                        self.__set_task_success(up_next.task_id)
                    except (DeviceException, TaskException) as e:
                        self.__set_task_failed(up_next.task_id, e)
                    last_executed.add(up_next)
                    time_to_next = timedelta(milliseconds=1)
            else:
                time_to_next = timedelta(seconds=IDLE_INTERVAL_SECONDS)
                no_task_limit += 1
                if no_task_limit > RECONNECT_ATTEMPTS:
                    log.warning(f"{self}: no tasks received for quite some "
                                "time, stopping scheduling...")
                    self.executor.shutdown(wait=True)
                    self.__running = False
                    CACHE.remove_scheduler(self.device_uuid)
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
            log.debug(f"{self}: sleeping for {time_to_next.total_seconds()}")
            time.sleep(time_to_next.total_seconds())

    @staticmethod
    def __device_health_check(device):
        if device.is_responding:
            return True
        log.info(f"{device} is offline, checking if something changed...")

        try:
            device.read_status()
        except DeviceException as e:
            log.error(f"Status failed: {e}")
            return False

        if device.is_responding:
            return True
        return False

    @staticmethod
    def __sanitize_task_input(task):
        try:
            return ScheduledTask.from_db_object(task)
        except TaskNotCreatedException as e:
            task.last_run = datetime.utcnow()
            task.last_run_success = False
            task.last_run_error = str(e)
            db.session.commit()

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
