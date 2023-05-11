import logging
import os
import traceback
from inspect import isclass
from threading import Lock

from pluginbase import PluginBase

log = logging.getLogger(__name__)

# common base class - all tasks should extend this
from app.core.tasks import TaskRunnable

builtin_task_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'tasks')


class PluginManager:

    init_lock = Lock()

    def __init__(self, init=False):
        self.__plugin_base = PluginBase(package='app.plugins')
        self.__available_tasks = {}
        self.__plugin_paths = {builtin_task_path}  # always include built-in task types
        self.__plugin_source = None
        self.__is_initialized = False

        if init:
            self.initialize()

    def is_initialized(self, new_paths):
        return self.__is_initialized and all([path in self.__plugin_paths for path in new_paths])

    def initialize(self, plugin_paths=None):
        with self.init_lock:
            if plugin_paths is None:
                plugin_paths = []

            if self.is_initialized(plugin_paths):
                return

            if type(plugin_paths) not in (list, set, tuple):
                plugin_paths = [plugin_paths]

            for custom_path in plugin_paths:
                if not os.path.isdir(custom_path):
                    log.error(f"Can't load plugin: '{custom_path}': is not a directory.")
                    continue
                self.__plugin_paths.add(custom_path)

            log.info(f"Loading plugins {self.__plugin_paths}")
            self.__plugin_source = self.__plugin_base \
                .make_plugin_source(searchpath=list(self.__plugin_paths))

            for path in self.__plugin_paths:
                self.__collect_task_types(path)
            log.info(f"Plugins loaded: {self.available_tasks}")
            self.__is_initialized = True

    def __collect_task_types(self, path):
        if not os.path.isdir(path):
            log.error(f"Path '{path}' disappeared since last init. Skipping...")
            return
        tree = os.listdir(path)
        for module_file in tree:
            module_name = module_file.replace(".py", "")

            with self.__plugin_source:
                try:
                    module = self.__plugin_source.load_plugin(module_name)
                except Exception as e:
                    log.error(f"{e}: Failed to load plugin '{module_name}' "
                              f"located in {path}/{module_file}")
                    traceback.print_exc()
                    continue

            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if attribute is TaskRunnable:
                    continue
                if isclass(attribute) and issubclass(attribute, TaskRunnable):
                    if not getattr(attribute, 'type'):
                        log.error(f'class {attribute} has no attribute \'type\'')
                        continue
                    self.__available_tasks[attribute.type] = attribute

    def get_class(self, type_):
        return self.__available_tasks.get(type_)

    @property
    def available_tasks(self):
        return set(self.__available_tasks.keys())

    @property
    def plugin_source(self):
        return self.__plugin_source


plugin_manager = PluginManager(init=False)
