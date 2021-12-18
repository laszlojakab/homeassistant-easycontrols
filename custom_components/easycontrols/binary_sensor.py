# pylint: disable=bad-continuation
'''
The binary sensor module for Helios Easy Controls integration.
'''
import logging
from typing import Callable
from homeassistant.config_entries import ConfigEntry

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType

from .const import (DATA_CONTROLLER, DOMAIN, INFO_FILTER_CHANGE_FLAG,
                    VARIABLE_BYPASS, VARIABLE_INFOS)
from .threadsafe_controller import ThreadSafeController

_LOGGER = logging.getLogger(__name__)


class EasyControlBinarySensor(Entity):
    '''
    Represents a ModBus variable as a binary sensor.
    '''

    def __init__(
        self,
        controller: ThreadSafeController,
        variable_name: str,
        variable_size: int,
        converter: Callable[[str], str],
        name: str,
        device_name: str,
        icon: str,
        device_class: str
    ):
        '''
        Initialize a new instance of EasyControlsBinarySensor class.

        Parameters
        ----------
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller.
        variable_name: str
            The ModBus variable name.
        variable_size: int
            The ModBus variable size.
        converter: Callable[[str], Any]
            The converter function which converts the received ModBus
            variable value to on/off state.
        name: str
            The name of the sensor.
        device_name: str
            The device name.
        icon: str
            The icon of the sensor.
        device_class: str
            The device class of the sensor.
        '''
        self._controller = controller
        self._variable = variable_name
        self._converter = converter
        self._size = variable_size
        self._name = name
        self._device_name = device_name
        self._icon = icon
        self._device_class = device_class
        self._state = 'unavailable'

    async def async_update(self):
        '''
        Updates the sensor value.
        '''
        value = self._controller.get_variable(
            self._variable, self._size, self._converter
        )
        self._state = 'unavailable' if value is None else value

    @property
    def device_class(self):
        '''
        Gets the device class of the sensor.
        '''
        return self._device_class

    @property
    def unique_id(self):
        '''
        Gets the unique ID of the sensor.
        '''
        return self._controller.mac + self._name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information
        '''
        return {
            'connections': {(device_registry.CONNECTION_NETWORK_MAC, self._controller.mac)},
            'identifiers': {(DOMAIN, self._controller.serial_number)},
            'name': self._device_name,
            'manufacturer': 'Helios',
            'model': self._controller.model,
            'sw_version': self._controller.version
        }

    @property
    def should_poll(self):
        '''
        Gets the value indicates whether the sensor should be polled.
        '''
        return True

    @property
    def name(self):
        '''
        Gets the name of the sensor.
        '''
        return self._name

    @property
    def state(self):
        '''
        Gets the state of the sensor.
        '''
        return self._state

    @property
    def icon(self):
        '''
        Gets the icon of the sensor.
        '''
        return self._icon


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    '''
    Setup of Helios Easy Controls sensors for the specified config_entry.

    Parameters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    config_entry: homeassistant.helpers.typing.ConfigEntry
        The config entry which is used to create sensors.
    async_add_entities: homeassistant.helpers.entity_platform.AddEntitiesCallback
        The callback which can be used to add new entities to Home Assistant.

    Returns
    -------
    bool
        The value indicates whether the setup succeeded.
    '''
    _LOGGER.info('Setting up Helios EasyControls binary sensors.')

    name = config_entry.data[CONF_NAME]
    controller = hass.data[DOMAIN][DATA_CONTROLLER][config_entry.data[CONF_HOST]]

    async_add_entities([
        EasyControlBinarySensor(
            controller,
            VARIABLE_BYPASS,
            8,
            lambda x: 'on' if int(x) == 1 else 'off',
            f'{name} bypass',
            name,
            'mdi:delta',
            'opening'
        ),
        EasyControlBinarySensor(
            controller,
            VARIABLE_INFOS,
            32,
            lambda x: 'on' if (
                int(x) & INFO_FILTER_CHANGE_FLAG) == INFO_FILTER_CHANGE_FLAG else 'off',
            f'{name} filter change',
            name,
            'mdi:air-filter',
            None
        )
    ])

    _LOGGER.info('Setting up Helios EasyControls binary sensors completed.')
