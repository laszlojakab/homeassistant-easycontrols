"""
The binary sensor module for Helios Easy Controls integration.
"""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType
from typing_extensions import Self

from custom_components.easycontrols import get_coordinator
from custom_components.easycontrols.const import (
    VARIABLE_BYPASS,
    VARIABLE_INFO_FILTER_CHANGE,
)
from custom_components.easycontrols.coordinator import EasyControlsDataUpdateCoordinator
from custom_components.easycontrols.modbus_variable import BoolModbusVariable

_LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class EasyControlBinarySensor(BinarySensorEntity):
    """
    Represents a ModBus variable as a binary sensor.
    """

    def __init__(
        self,
        coordinator: EasyControlsDataUpdateCoordinator,
        variable: BoolModbusVariable,
        description: BinarySensorEntityDescription,
    ):
        """
        Initialize a new instance of `EasyControlsBinarySensor` class.

        Args:
            coordinator:
                The coordinator instance.
            variable:
                The Modbus variable.
            description:
                The binary sensor description.
        """
        self.entity_description = description
        self._coordinator = coordinator
        self._variable = variable
        self._attr_unique_id = self._coordinator.mac + self.name
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._coordinator.mac)}
        )

        def update_listener(
            # pylint: disable=unused-argument
            variable: BoolModbusVariable,
            value: bool,
        ):
            self._value_updated(value)

        self._update_listener = update_listener

    async def async_added_to_hass(self: Self) -> None:
        self._coordinator.add_listener(self._variable, self._update_listener)
        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.remove_listener(self._variable, self._update_listener)
        return await super().async_will_remove_from_hass()

    def _value_updated(self: Self, value: bool):
        self._attr_is_on = value
        self._attr_available = self._attr_is_on is not None
        self.schedule_update_ha_state(False)


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """
    Setup of Helios Easy Controls sensors for the specified config_entry.

    Args:
        hass:
            The Home Assistant instance.
        config_entry:
            The config entry which is used to create sensors.
        async_add_entities:
            The callback which can be used to add new entities to Home Assistant.

    Returns:
        The value indicates whether the setup succeeded.
    """
    _LOGGER.info("Setting up Helios EasyControls binary sensors.")

    coordinator = get_coordinator(hass, config_entry.data[CONF_MAC])

    async_add_entities(
        [
            EasyControlBinarySensor(
                coordinator,
                VARIABLE_BYPASS,
                BinarySensorEntityDescription(
                    key="bypass",
                    name=f"{coordinator.device_name} bypass",
                    icon="mdi:delta",
                    device_class=BinarySensorDeviceClass.OPENING,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlBinarySensor(
                coordinator,
                VARIABLE_INFO_FILTER_CHANGE,
                BinarySensorEntityDescription(
                    key="filter_change",
                    name=f"{coordinator.device_name} filter change",
                    icon="mdi:air-filter",
                    device_class=BinarySensorDeviceClass.PROBLEM,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
        ]
    )

    _LOGGER.info("Setting up Helios EasyControls binary sensors completed.")
