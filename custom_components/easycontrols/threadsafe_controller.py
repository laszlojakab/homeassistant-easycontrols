# pylint: disable=bad-continuation
'''
The module of Helios Easy Controls thread safe controller.
'''
import logging
import re
import threading
from typing import Any

import eazyctrl
from custom_components.easycontrols.modbus_variable import ModbusVariable

from .const import (VARIABLE_ARTICLE_DESCRIPTION, VARIABLE_SERIAL_NUMBER,
                    VARIABLE_SOFTWARE_VERSION)

_LOGGER = logging.getLogger(__name__)


class ThreadSafeController:
    '''
    Represents a Helios Easy Controls controller.
    The get_variable and set_variables methods are thread safe.
    For more information please visit:
    https://github.com/baradi09/eazyctrl#notes-on-concurrent-access-conflicts
    '''

    def __init__(self, device_name: str, host: str, mac: str):
        '''
        Initialize a new instance of ThreadSafeController class.

        Parameters
        ----------
        device_name: str
            The name of the device.
        host: str
            The host name or the IP address of the Helios device.
        mac: str
            The MAC address of the Helios device.
        '''
        self._host = host
        self._device_name = device_name
        self._eazyctrl = eazyctrl.EazyController(host)
        self._lock = threading.Lock()
        self._mac = mac
        self._model = None
        self._version = None
        self._serial_number = None
        self._maximum_air_flow = None

    @property
    def device_name(self) -> str:
        '''
        Gets the name of the Helios device.
        '''
        return self._device_name

    @property
    def maximum_air_flow(self) -> float:
        '''
        Gets the maximum airflow rate of the Helios device.
        The value is extracted from the model name.
        '''
        if self._maximum_air_flow is None:
            if self.model is None:
                return None

            self._maximum_air_flow = float(re.findall(r'\d+', self.model)[0])
        return self._maximum_air_flow

    @property
    def host(self) -> str:
        '''
        Gets the host name or the IP address of the Helios device.
        '''
        return self._host

    @property
    def mac(self) -> str:
        '''
        Gets the MAC address of the Helios device.
        '''
        return self._mac

    @property
    def model(self) -> str:
        '''
        Gets the model of Helios device.
        '''
        if self._model is None:
            try:
                self._model = self.get_variable(VARIABLE_ARTICLE_DESCRIPTION)
            # pylint: disable=broad-except
            except Exception as error:
                _LOGGER.error('Failed to get the model of Helios device: %s', error)
        return self._model

    @property
    def version(self) -> str:
        '''
        Gets the software version of Helios device.
        '''
        if self._version is None:
            try:
                self._version = self.get_variable(VARIABLE_SOFTWARE_VERSION)
            # pylint: disable=broad-except
            except Exception as error:
                _LOGGER.error('Failed to get the software version of Helios device: %s', error)

        return self._version

    @property
    def serial_number(self) -> str:
        '''
        Gets the serial number of Helios device.
        '''
        if self._serial_number is None:
            try:
                self._serial_number = self.get_variable(VARIABLE_SERIAL_NUMBER)
            # pylint: disable=broad-except
            except Exception as error:
                _LOGGER.error('Failed to get the serial number of Helios device: %s', error)

        return self._serial_number

    def get_variable(
        self,
        variable: ModbusVariable,
    ) -> Any:
        '''
        Gets the specified variable value from the Helios device.

        Parameters
        ----------
        variable: ModbusVariable
            The variable to get.
        '''
        with self._lock:
            _LOGGER.debug('Getting %s.', variable.name)
            value = self._eazyctrl.get_variable(
                variable.name,
                variable.size,
                variable.get_converter
            )
            _LOGGER.debug('%s value: %s', variable.name, value)
            return value

    def set_variable(
        self,
        variable: ModbusVariable,
        value: Any
    ):
        '''
        Sets the specified variable value on the Helios device.

        Parameters
        ----------
        variable: ModbusVariable
            The variable to set on Helios device.
        value: Any
            The value to set on Helios device.

        Returns
        bool
            True if setting of variable succeeded otherwise False.
        '''
        with self._lock:
            _LOGGER.debug('Setting %s to %s.', variable.name, value)
            return self._eazyctrl.set_variable(variable.name, value, variable.set_converter)
