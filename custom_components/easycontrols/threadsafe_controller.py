import eazyctrl
import threading
import re

import logging

from .const import (
    VARIABLE_ARTICLE_DESCRIPTION,
    VARIABLE_SOFTWARE_VERSION,
    VARIABLE_MAC_ADDRESS,
    VARIABLE_SERIAL_NUMBER
)

_LOGGER = logging.getLogger(__name__)


class ThreadSafeController:
    def __init__(self, host: str, mac: str):
        self._host = host
        self._eazyctrl = eazyctrl.EazyController(host)
        self._lock = threading.Lock()
        self._mac = mac
        self._model = None
        self._version = None
        self._serial_number = None
        self._maximum_air_flow = None

    @property
    def maximum_air_flow(self):
        if (self._maximum_air_flow is None):
            if (self.model is None):
                return None

            self._maximum_air_flow = float(re.findall(r"\d+", self.model)[0])
        return self._maximum_air_flow

    @property
    def host(self):
        return self._host

    @property
    def mac(self):
        return self._mac

    @property
    def model(self):
        if (self._model is None):
            try:
                self._model = self.get_variable(VARIABLE_ARTICLE_DESCRIPTION, 128, str)
            except Exception as e:
                _LOGGER.error(e)
        return self._model

    @property
    def version(self):
        if (self._version is None):
            try:
                self._version = self.get_variable(VARIABLE_SOFTWARE_VERSION, 128, str)
            except Exception as e:
                _LOGGER.error(e)

        return self._version

    @property
    def serial_number(self):
        if (self._serial_number is None):
            try:
                self._serial_number = self.get_variable(VARIABLE_SERIAL_NUMBER, 16, str)
            except Exception as e:
                _LOGGER.error(e)

        return self._serial_number

    def get_variable(self, variable_name, variable_length, conversion=None):
        with self._lock:
            _LOGGER.debug(f"Getting {variable_name}.")
            value = self._eazyctrl.get_variable(
                variable_name,
                variable_length,
                conversion
            )
            _LOGGER.debug(f"{variable_name} value: {value}")
            return value

    def set_variable(self, variable_name, value, conversion=None):
        with self._lock:
            _LOGGER.debug(f"Setting {variable_name} to {value}")            
            return self._eazyctrl.set_variable(variable_name, value, conversion)
