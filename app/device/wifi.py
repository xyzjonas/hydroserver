import logging
import threading
import requests

from app.device import Device, DeviceType


log = logging.getLogger(__name__)


class WifiDevice(Device):

    device_type = DeviceType.WIFI

    def __init__(self, url):
        self.url = url
        self.lock = threading.Lock()
        self.__uuid = None
        super().__init__()

    def _get_uuid(self):
        return self.__uuid

    def _init(self):
        if not self.is_site_online():
            self.__uuid = None
            return
        response = self.send_command('status')
        if not response:
            self.__uuid = None
            return
        uuid = response.get('uuid')
        if not uuid:
            log.warning(f"{self}: device response doesn't contain a uuid.")
            self.__uuid = None
            return
        self.__uuid = uuid

    def is_site_online(self):
        """A basic Wifi device is realized as a HTTP server accepting GET on '/'"""
        return not requests.get(self.url).status_code >= 300

    # [!] one and only send method
    def _send_raw(self, string):
        data = {
            'request': string
        }
        response = requests.post(self.url, json=data)
        # todo: error state (better)
        if response.status_code >= 300:
            self.__uuid = None

        return ",".join([f"{k}:{v}"
                         for k, v in response.json().items()])

    def _is_connected(self):
        return self.is_site_online()

    def _is_responding(self):
        return self.__uuid is not None

    @classmethod
    def from_url(cls, url):
        """Create a device from URL - by fetching its status"""
        device = WifiDevice(url=url)
        response = device.read_status()
        if response.is_success:
            if response.data.get('uuid'):
                device.__uuid = response.data.get('uuid')
                return device

