import logging
import pprint
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from flask import current_app

from app import db
from app.core.cache import CACHE
from app.core.device import Device as PhysicalDevice
from app.system.device_mapper import DeviceMapper
from app.core.tasks import ScheduledTask, TaskNotCreatedException


# todo: create logger for each scheduler (i.e. each device)
log = logging.getLogger(__name__)


class Scheduler:
    """
    1 scheduler per serial device, own thread pool...
    Creates schedule based on set up tasks and their crons.
    """

    def __init__(self, device: PhysicalDevice):
        self.device = DeviceMapper.from_uuid(device.uuid)
        self.__running = False
        self.__should_be_running = False

        with current_app.app_context():
            self.MAX_WORKERS = current_app.config['MAX_WORKERS']
            self.SAFE_INTERVAL = current_app.config['SAFE_INTERVAL']
            self.RECONNECT_ATTEMPTS = current_app.config['RECONNECT_ATTEMPTS']
            self.IDLE_INTERVAL_SECONDS = current_app.config['IDLE_INTERVAL_SECONDS']

        self.executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS)
        self.__last_executed = set()

    def __repr__(self):
        return f"<Scheduler (device={self.device.model}, running={self.__running})>"

    def start(self):
        if self.is_running:
            return
        self.__should_be_running = True

        self._clear_scheduler_error()

        def try_run():
            try:
                self.__loop()
            except Exception as e:
                log.fatal(f"{self}: [!!!] scheduler FAILED: {e}")
                traceback.print_exc()
                self.__running = False
                self.__should_be_running = False
                self._set_scheduler_error(str(e))

        t = threading.Thread(target=try_run)
        t.daemon = True
        t.start()

    def terminate(self):
        self.__should_be_running = False

    @property
    def is_running(self):
        return self.__running

    def get_tasks_from_db(self):
        """
        :rtype: set
        """
        dev = self.device.model

        def __sanitize(task):
            try:
                return ScheduledTask.from_db_object(task)
            except TaskNotCreatedException as e:
                task.last_run = datetime.utcnow()
                task.last_run_success = False
                task.last_run_error = str(e)
                db.session.commit()

        return {task for task in [__sanitize(t) for t in dev.tasks] if task}

    def _set_device_offline(self):
        dev = self.device.model
        dev.is_online = False
        db.session.commit()

    def _set_scheduler_error(self, cause):
        dev = self.device.model
        dev.scheduler_error = str(cause)
        db.session.commit()

    def _clear_scheduler_error(self):
        dev = self.device.model
        dev.scheduler_error = None
        db.session.commit()

    def _execute(self, task):
        """'execute task' function to be spawned in the thread executor."""
        try:
            log.debug(f"{self.device.model.name}: executing '{task.runnable.type}' "
                      f"task (id={task.task_id})")
            task.runnable.run(self.device.physical)
        except Exception as e:
            log.error(f"Task '{task}' submission failed: {e}")
            traceback.print_exc()

    def _stop_scheduler(self, message=None):
        """Scheduler stops itself from within the run loop."""
        self.executor.shutdown(wait=True)
        self.__running = False
        self.__should_be_running = False
        CACHE.remove_scheduler(self.device.uuid)
        if message:
            self._set_scheduler_error(message)

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
            if not self.device.physical.health_check():
                self._set_device_offline()
                attempts += 1
                if attempts > self.RECONNECT_ATTEMPTS:
                    log.warning(f"{self}: device offline, stopping scheduling...")
                    self._stop_scheduler(message="Device offline.")
                    return
                to_be_scheduled = set()
                log.warning(f"{self}: device offline, schedule cleared "
                            f"(attempts={attempts}/{self.RECONNECT_ATTEMPTS}).")
            else:
                attempts = 0
                to_be_scheduled = self.get_tasks_from_db() \
                    .difference(self.__last_executed)

            # 2) handle tasks
            active_tasks = sorted(to_be_scheduled, key=lambda t: t.scheduled_time)
            log.debug(f"{self}: {len(active_tasks)} active tasks: \n"
                      f"{pprint.pformat(active_tasks)}")
            for task in active_tasks:
                time_to_next = task.scheduled_time - datetime.utcnow()
                # if inside the 'safe interval' execute right away and don't wait
                if time_to_next <= timedelta(seconds=self.SAFE_INTERVAL):
                    self.__last_executed.add(task)
                    self.executor.submit(self._execute, task)

            active_tasks = to_be_scheduled.difference(self.__last_executed)
            active_tasks = sorted(active_tasks, key=lambda t: t.scheduled_time)

            if active_tasks:
                no_task_retry_limit = 0
                up_next = active_tasks[0]
                time_to_next = up_next.scheduled_time - datetime.utcnow()
                log.debug(f"Up-next: {up_next}, i.e. in {time_to_next}")
            else:
                # 3) auto-stop in case of no tasks
                time_to_next = timedelta(seconds=self.IDLE_INTERVAL_SECONDS)
                no_task_retry_limit += 1
                if no_task_retry_limit > self.RECONNECT_ATTEMPTS:
                    log.warning(
                        f"{self}: no tasks received for quite some time, stopping scheduling...")
                    self._stop_scheduler(message="No scheduled tasks.")
                    return

            # 3) Time delta shenanigans
            if not time_to_next or time_to_next.seconds >= self.IDLE_INTERVAL_SECONDS:
                time_to_next = timedelta(seconds=self.IDLE_INTERVAL_SECONDS)
                log.debug('Clearing last-executed')
                self.__last_executed.clear()  # CLEANUP - prevent memory leak

            # 4) Obligatory sleep
            log.debug(f"{self}: sleeping for {time_to_next.total_seconds()}")
            sleep_secs = time_to_next.total_seconds() - self.SAFE_INTERVAL
            time.sleep(sleep_secs if sleep_secs > 0 else 0.01)

        # end WHILE
        log.info(f"{self} exiting...")
        self._stop_scheduler()
