# pylint: disable=bad-continuation
'''
The binary sensor module for Helios Easy Controls integration.
'''
import logging
from typing import Callable

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_OPENING, DEVICE_CLASS_PROBLEM, BinarySensorEntity,
    BinarySensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType

from .const import (DATA_CONTROLLER, DOMAIN, INFO_FILTER_CHANGE_FLAG,
                    VARIABLE_BYPASS, VARIABLE_INFOS)
from .threadsafe_controller import ThreadSafeController

_LOGGER = logging.getLogger(__name__)


class EasyControlBinarySensor(BinarySensorEntity):
    '''
    Represents a ModBus variable as a binary sensor.
    '''

    def __init__(
        self,
        controller: ThreadSafeController,
        variable_name: str,
        variable_size: int,
        converter: Callable[[str], str],
        device_name: str,
        description: BinarySensorEntityDescription
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
        device_name: str
            The device name.
        description: homeassistant.components.binary_sensor.BinarySensorEntityDescription
            The binary sensor description.
        '''
        self.entity_description = description
        self._controller = controller
        self._variable = variable_name
        self._converter = converter
        self._size = variable_size
        self._device_name = device_name
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
    def unique_id(self):
        '''
        Gets the unique ID of the sensor.
        '''
        return self._controller.mac + self.name

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
    def state(self):
        '''
        Gets the state of the sensor.
        '''
        return self._state


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

    device_name = config_entry.data[CONF_NAME]
    controller = hass.data[DOMAIN][DATA_CONTROLLER][config_entry.data[CONF_HOST]]

    async_add_entities([
        EasyControlBinarySensor(
            controller,
            VARIABLE_BYPASS,
            8,
            lambda x: 'on' if int(x) == 1 else 'off',
            device_name,
            BinarySensorEntityDescription(
                key="bypass",
                name=f'{device_name} bypass',
                icon='mdi:delta',
                device_class=DEVICE_CLASS_OPENING
            ),
        ),
        EasyControlBinarySensor(
            controller,
            VARIABLE_INFOS,
            32,
            lambda x: 'on' if (
                int(x) & INFO_FILTER_CHANGE_FLAG) == INFO_FILTER_CHANGE_FLAG else 'off',
            device_name,
            BinarySensorEntityDescription(
                key="filter_change",
                name=f'{device_name} filter change',
                icon='mdi:air-filter',
                device_class=DEVICE_CLASS_PROBLEM
            )
        )
    ])

    _LOGGER.info('Setting up Helios EasyControls binary sensors completed.')
