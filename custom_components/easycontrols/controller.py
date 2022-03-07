'''
The module of Helios Easy Controls thread safe controller.
'''
import logging
import re
from asyncio import Lock
from typing import Any

from eazyctrl import AsyncEazyController

from .const import (VARIABLE_ARTICLE_DESCRIPTION, VARIABLE_SERIAL_NUMBER,
                    VARIABLE_SOFTWARE_VERSION)
from .modbus_variable import ModbusVariable

_LOGGER = logging.getLogger(__name__)


class Controller:
    '''
    Represents a Helios Easy Controls controller.
    '''

    def __init__(self, device_name: str, host: str, mac: str):
        '''
        Initialize a new instance of Controller class.

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
        self._eazyctrl = AsyncEazyController(host)
        self._lock = Lock()
        self._mac = mac
        self._model = None
        self._version = None
        self._serial_number = None
        self._maximum_air_flow = None

    async def init(self):
        '''
        Initialize device specific properties:
        - model
        - version
        - serial_number
        - maximum_air_flow
        '''
        self._model = await self.get_variable(VARIABLE_ARTICLE_DESCRIPTION)
        self._version = await self.get_variable(VARIABLE_SOFTWARE_VERSION)
        self._serial_number = await self.get_variable(VARIABLE_SERIAL_NUMBER)
        self._maximum_air_flow = float(re.findall(r'\d+', self._model)[0])

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
        return self._model

    @property
    def version(self) -> str:
        '''
        Gets the software version of Helios device.
        '''
        return self._version

    @property
    def serial_number(self) -> str:
        '''
        Gets the serial number of Helios device.
        '''
        return self._serial_number

    async def get_variable(
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
        async with self._lock:
            _LOGGER.debug('Getting %s.', variable.name)
            value = await self._eazyctrl.get_variable(
                variable.name,
                variable.size,
                variable.get_converter
            )
            _LOGGER.debug('%s value: %s', variable.name, value)
            return value

    async def set_variable(
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
        -------
        bool
            True if setting of variable succeeded otherwise False.
        '''
        async with self._lock:
            _LOGGER.debug('Setting %s to %s.', variable.name, value)
            return await self._eazyctrl.set_variable(variable.name, value, variable.set_converter)
