"""The binary sensor module for Helios Easy Controls integration."""

import logging
from typing import Self

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.easycontrols import get_coordinator
from custom_components.easycontrols.const import (
    VARIABLE_BYPASS,
    VARIABLE_INFO_FILTER_CHANGE,
)
from custom_components.easycontrols.coordinator import EasyControlsDataUpdateCoordinator
from custom_components.easycontrols.modbus_variable import BoolModbusVariable

_LOGGER = logging.getLogger(__name__)


class EasyControlBinarySensor(BinarySensorEntity):
    """Represents a ModBus variable as a binary sensor."""

    def __init__(
        self: Self,
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
            variable: BoolModbusVariable,  # noqa: ARG001
            value: bool,
        ) -> None:
            self._value_updated(value)

        self._update_listener = update_listener

    async def async_added_to_hass(self: Self) -> None:
        """
        Called when an entity is added to Home Assistant.

        Add the update listener to the coordinator.
        """
        self._coordinator.add_listener(self._variable, self._update_listener)
        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        """
        Called when an entity is about to be removed from Home Assistant.

        Remove the update listener from the coordinator.
        """
        self._coordinator.remove_listener(self._variable, self._update_listener)
        return await super().async_will_remove_from_hass()

    def _value_updated(self: Self, value: bool) -> None:
        self._attr_is_on = value
        self._attr_available = self._attr_is_on is not None
        self.schedule_update_ha_state(False)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
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
