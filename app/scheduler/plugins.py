import logging
import traceback
import os
from inspect import isclass
from pluginbase import PluginBase

from app.scheduler import tasks


log = logging.getLogger(__name__)


class PluginManager:

    def __init__(self, init=False):
        self.__available_tasks = {}
        self.__plugin_paths = [  # always include built-in task types
            os.path.dirname(os.path.abspath(tasks.__file__))]
        if init:
            self.initialize()

    def initialize(self, plugin_paths=None):
        if plugin_paths is None:
            plugin_paths = []

        log.info("Loading plugins...")
        # todo: duplicate paths - multiple init?
        self.__plugin_paths.extend(plugin_paths)

        for path in self.__plugin_paths:
            if not os.path.isdir(path):
                log.error(f"Error during plugin loading: '{path}': is not a directory.")
                continue
            self.__collect_task_types(path)
            log.info(f"Plugins loaded: {self.available_tasks}")

    def __collect_task_types(self, path):
        plugin_base = PluginBase(package='app.plugins')
        self._plugin_source = plugin_base.make_plugin_source(searchpath=[path])

        tree = os.listdir(path)
        for module_file in tree:
            module_name = module_file.replace(".py", "")

            with self.plugin_source:
                try:
                    module = self.plugin_source.load_plugin(module_name)
                except Exception:
                    log.error(f"Failed to load plugin '{module_name}' "
                              f"located in {path}/{module_file}")
                    traceback.print_exc()
                    continue

            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if attribute is tasks.TaskRunnable:
                    continue
                if isclass(attribute) and issubclass(attribute, tasks.TaskRunnable):
                    self.__available_tasks[attribute_name.lower()] = attribute

    def get_class(self, class_name):
        return self.__available_tasks.get(class_name)

    @property
    def available_tasks(self):
        return set(self.__available_tasks.keys())

    @property
    def plugin_source(self):
        return self._plugin_source


PLUGIN_MANAGER = PluginManager()
