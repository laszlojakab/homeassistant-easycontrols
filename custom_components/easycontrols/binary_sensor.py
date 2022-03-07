'''
The binary sensor module for Helios Easy Controls integration.
'''
import logging

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_OPENING, DEVICE_CLASS_PROBLEM, BinarySensorEntity,
    BinarySensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, ENTITY_CATEGORY_DIAGNOSTIC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType

from . import get_controller, get_device_info
from .const import VARIABLE_BYPASS, VARIABLE_INFO_FILTER_CHANGE
from .modbus_variable import BoolModbusVariable
from .controller import Controller

_LOGGER = logging.getLogger(__name__)


class EasyControlBinarySensor(BinarySensorEntity):
    '''
    Represents a ModBus variable as a binary sensor.
    '''

    def __init__(
        self,
        controller: Controller,
        variable: BoolModbusVariable,
        description: BinarySensorEntityDescription
    ):
        '''
        Initialize a new instance of EasyControlsBinarySensor class.

        Parameters
        ----------
        controller: Controller
            The thread safe Helios Easy Controls controller.
        variable: BoolModbusVariable
            The Modbus variable.
        description: homeassistant.components.binary_sensor.BinarySensorEntityDescription
            The binary sensor description.
        '''
        self.entity_description = description
        self._controller = controller
        self._variable = variable
        self._attr_unique_id = self._controller.mac + self.name

    async def async_update(self):
        '''
        Updates the sensor value.
        '''
        self._attr_is_on = await self._controller.get_variable(self._variable)
        self._attr_available = self._attr_is_on is not None

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)


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

    controller = get_controller(hass, config_entry.data[CONF_MAC])

    async_add_entities([
        EasyControlBinarySensor(
            controller,
            VARIABLE_BYPASS,
            BinarySensorEntityDescription(
                key="bypass",
                name=f'{controller.device_name} bypass',
                icon='mdi:delta',
                device_class=DEVICE_CLASS_OPENING,
                entity_category=ENTITY_CATEGORY_DIAGNOSTIC
            ),
        ),
        EasyControlBinarySensor(
            controller,
            VARIABLE_INFO_FILTER_CHANGE,
            BinarySensorEntityDescription(
                key="filter_change",
                name=f'{controller.device_name} filter change',
                icon='mdi:air-filter',
                device_class=DEVICE_CLASS_PROBLEM,
                entity_category=ENTITY_CATEGORY_DIAGNOSTIC
            )
        )
    ])

    _LOGGER.info('Setting up Helios EasyControls binary sensors completed.')
