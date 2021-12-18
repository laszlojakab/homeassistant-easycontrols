# pylint: disable=bad-continuation
"""
The module of Helios Easy Controls thread safe controller.
"""
import logging
import re
import threading
from typing import Any, Callable

import eazyctrl

from .const import (VARIABLE_ARTICLE_DESCRIPTION, VARIABLE_SERIAL_NUMBER,
                    VARIABLE_SOFTWARE_VERSION)

_LOGGER = logging.getLogger(__name__)


class ThreadSafeController:
    """
    Represents a Helios Easy Controls controller.
    The get_variable and set_variables methods are thread safe.
    For more information please visit:
    https://github.com/baradi09/eazyctrl#notes-on-concurrent-access-conflicts
    """

    def __init__(self, host: str, mac: str):
        """
        Initialize a new instance of ThreadSafeController class.

        Parameters
        ----------
        host: str
            The host name or the IP address of the Helios device.
        mac: str
            The MAC address of the Helios device.
        """
        self._host = host
        self._eazyctrl = eazyctrl.EazyController(host)
        self._lock = threading.Lock()
        self._mac = mac
        self._model = None
        self._version = None
        self._serial_number = None
        self._maximum_air_flow = None

    @property
    def maximum_air_flow(self) -> float:
        """
        Gets the maximum airflow rate of the Helios device.
        The value is extracted from the model name.
        """
        if self._maximum_air_flow is None:
            if self.model is None:
                return None

            self._maximum_air_flow = float(re.findall(r"\d+", self.model)[0])
        return self._maximum_air_flow

    @property
    def host(self) -> str:
        """
        Gets the host name or the IP address of the Helios device.
        """
        return self._host

    @property
    def mac(self) -> str:
        """
        Gets the MAC address of the Helios device.
        """
        return self._mac

    @property
    def model(self) -> str:
        """
        Gets the model of Helios device.
        """
        if self._model is None:
            try:
                self._model = self.get_variable(VARIABLE_ARTICLE_DESCRIPTION, 128, str)
            # pylint: disable=broad-except
            except Exception as error:
                _LOGGER.error("Failed to get the model of Helios device: %s", error)
        return self._model

    @property
    def version(self) -> str:
        """
        Gets the software version of Helios device.
        """
        if self._version is None:
            try:
                self._version = self.get_variable(VARIABLE_SOFTWARE_VERSION, 128, str)
            # pylint: disable=broad-except
            except Exception as error:
                _LOGGER.error("Failed to get the software version of Helios device: %s", error)

        return self._version

    @property
    def serial_number(self) -> str:
        """
        Gets the serial number of Helios device.
        """
        if self._serial_number is None:
            try:
                self._serial_number = self.get_variable(VARIABLE_SERIAL_NUMBER, 16, str)
            # pylint: disable=broad-except
            except Exception as error:
                _LOGGER.error("Failed to get the serial number of Helios device: %s", error)

        return self._serial_number

    def get_variable(
        self,
        variable_name: str,
        variable_length: int,
        conversion: Callable[[str], Any] = None
    ) -> Any:
        """
        Gets the specified variable value from the Helios device.

        Parameters
        ----------
        variable_name: str
            The variable to query from Helios device.
        variable_length: int
            The length of the variable.
        conversion: Callable[[str], Any]
            The conversion function to apply to
            the result returned by the Helios device.
        """
        with self._lock:
            _LOGGER.debug("Getting %s.", variable_name)
            value = self._eazyctrl.get_variable(
                variable_name,
                variable_length,
                conversion
            )
            _LOGGER.debug("%s value: %s", variable_name, value)
            return value

    def set_variable(
        self,
        variable_name: str,
        value: Any,
        conversion: Callable[[Any], str] = None
    ):
        """
        Sets the specified variable value on the Helios device.

        Parameters
        ----------
        variable_name: str
            The variable to set on Helios device.
        value: Any
            The value to set on Helios device.
        conversion: Callable[[Any], str]
            The conversion function to apply to value before
            sending to Helios device.

        Returns
        bool
            True if setting of variable suceeded otherwise False.
        """
        with self._lock:
            _LOGGER.debug("Setting %s to %s.", variable_name, value)
            return self._eazyctrl.set_variable(variable_name, value, conversion)
