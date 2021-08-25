import json
import logging
import threading

import requests

from app.device import Device, DeviceType, Command, DeviceCommunicationException

log = logging.getLogger(__name__)


class WifiDevice(Device):

    device_type = DeviceType.WIFI

    def __init__(self, url):
        self.__url = url
        self.lock = threading.Lock()
        self.__uuid = None
        super(WifiDevice, self).__init__()

    def _get_uuid(self):
        return self.__uuid

    def _get_url(self):
        return self.__url

    def _init(self):
        # 1) network issues - unreachable
        if not self.is_site_online():
            self.__uuid = None
            return

        # 2) online, but communication issues
        try:
            response_dict = self._send_raw(self._simple_request(Command.STATUS))
        except DeviceCommunicationException:
            self.__uuid = None
            return

        # 3) malformed data received
        if not response_dict:
            self.__uuid = None
            return
        uuid = response_dict.get('uuid')
        if not uuid:
            log.warning(f"{self}: device response doesn't contain a uuid.")
            self.__uuid = None
            return
        self.__uuid = uuid

    def is_site_online(self):
        """A basic Wifi device is realized as a HTTP server accepting GET on '/'"""
        try:
            return not requests.get(self.url).status_code >= 300
        except requests.RequestException:
            return False

    # [!] one and only send method
    def _send_raw(self, request_dict):
        try:
            response = requests.post(self.url, json=request_dict)
        except requests.RequestException as e:
            self.__uuid = None
            raise DeviceCommunicationException(e)
        if response.status_code >= 300:
            self.__uuid = None
            raise DeviceCommunicationException(f"{self}: server response > 300.")

        # item values can be further dicts encoded as string...
        response_dict = response.json()
        for k, v in response_dict.items():
            try:
                response_dict[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                pass

        return response_dict

    def _is_connected(self):
        return self.is_site_online()

    def _is_responding(self):
        return self.__uuid is not None


