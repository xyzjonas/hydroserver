import logging
import pprint
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from app import CACHE, Config
from app.device import Device as PhysicalDevice
from app.device import DeviceException
from app.models import db, Device, Task
from app.scheduler.tasks import ScheduledTask, \
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
        self.__should_be_running = False

        self.__last_executed = set()

    def __repr__(self):
        return f"<Scheduler (device={self.device}, running={self.__running})>"

    def start(self):
        if self.is_running:
            return
        self.__should_be_running = True

        def try_run():
            try:
                self.__loop()
            except Exception as e:
                log.fatal(f"{self}: [!!!] scheduler FAILED: \n{e}")
                self.__running = False
                self.__should_be_running = False

        t = threading.Thread(target=try_run)
        t.daemon = True
        t.start()

    def terminate(self):
        self.__should_be_running = False

    @property
    def is_running(self):
        return self.__running

    def get_tasks_from_db(self):
        return self.__load_tasks_from_db(self.device)

    def __execute(self, task):
        """execute function to be spawned in the thread executor"""
        self.__last_executed.add(task)
        try:
            log.debug(f"Executing {task} on '{self.device}'")
            task.runnable.run(self.device)
            self.__set_task_success(task.task_id)
            log.debug(f"{task} SUCCESS")
        except (DeviceException, TaskException) as e:
            log.debug(f"{task} FAILED")
            self.__set_task_failed(task.task_id, e)

    def __loop(self):
        """
        * grabs device tasks from DB
        * sorts by which is to be scheduled the earliest
        * wait until at least '< safe interval'
        * execute
        """
        attempts = 0
        no_task_retry_limit = 0
        self.__running = True
        while self.__should_be_running:
            # 1) Health-check
            if not self.device.health_check():
                self.__set_is_offline(self.device_uuid)
                attempts += 1
                if attempts > RECONNECT_ATTEMPTS:
                    log.warning(f"{self}: device offline, stopping scheduling...")
                    self.executor.shutdown(wait=True)
                    self.__running = False
                    self.__should_be_running = False
                    CACHE.remove_scheduler(self.device_uuid)
                    return
                to_be_scheduled = set()
                log.warning(f"{self}: device offline, schedule cleared "
                            f"(attempts={attempts}/{RECONNECT_ATTEMPTS}).")
            else:
                attempts = 0
                to_be_scheduled = self.__load_tasks_from_db(self.device) \
                    .difference(self.__last_executed)

            # 2) handle tasks
            active_tasks = sorted(to_be_scheduled, key=lambda t: t.scheduled_time)
            log.debug(f"{self}: {len(active_tasks)} active tasks: \n"
                      f"{pprint.pformat(active_tasks)}")
            for task in active_tasks:
                time_to_next = task.scheduled_time - datetime.utcnow()
                # if inside the 'safe interval' execute right away and don't wait
                if time_to_next <= timedelta(seconds=SAFE_INTERVAL):
                    self.executor.submit(self.__execute, task)

            active_tasks = to_be_scheduled.difference(self.__last_executed)
            active_tasks = sorted(active_tasks, key=lambda t: t.scheduled_time)

            if active_tasks:
                up_next = active_tasks[0]
                time_to_next = up_next.scheduled_time - datetime.utcnow()
                log.debug(f"Up-next: {up_next}, i.e. in {up_next.scheduled_time - datetime.utcnow()}")
            else:
                # 3) auto-stop in case of no tasks
                # fixme: necessary?
                time_to_next = timedelta(seconds=IDLE_INTERVAL_SECONDS)
                no_task_retry_limit += 1
                if no_task_retry_limit > RECONNECT_ATTEMPTS:
                    log.warning(f"{self}: no tasks received for quite some "
                                "time, stopping scheduling...")
                    self.executor.shutdown(wait=True)
                    self.__running = False
                    CACHE.remove_scheduler(self.device_uuid)
                    return

            # 3) Time delta shenanigans
            if not time_to_next or time_to_next.seconds >= IDLE_INTERVAL_SECONDS:
                time_to_next = timedelta(seconds=IDLE_INTERVAL_SECONDS)
                self.__last_executed.clear()  # CLEANUP - prevent memory leak

            # 4) Obligatory sleep
            log.debug(f"{self}: sleeping for {time_to_next.total_seconds()}")
            sleep_secs = time_to_next.total_seconds() - SAFE_INTERVAL
            time.sleep(sleep_secs if sleep_secs > 0 else 0.01)

        # end WHILE
        log.info(f"{self} exiting...")
        self.__running = False

    @staticmethod
    def __load_tasks_from_db(serial_device):
        def __sanitize(task):
            try:
                return ScheduledTask.from_db_object(task)
            except TaskNotCreatedException as e:
                task.last_run = datetime.utcnow()
                task.last_run_success = False
                task.last_run_error = str(e)
                db.session.commit()

        device = Device.query_by_serial_device(serial_device)
        return {task for task in [__sanitize(t) for t in device.tasks] if task}

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