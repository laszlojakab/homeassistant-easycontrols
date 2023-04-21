"""Helios Easy Controls integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from custom_components.easycontrols.const import DATA_COORDINATOR, DOMAIN
from custom_components.easycontrols.coordinator import (
    EasyControlsDataUpdateCoordinator,
    create_coordinator,
)

_LOGGER = logging.getLogger(__name__)

# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    """
    Set up the Helios Easy Controls component.

    Args:
        hass: The Home Assistant instance.
        config: The configuration.

    Returns:
        The value indicates whether the setup succeeded.
    """
    hass.data[DOMAIN] = {DATA_COORDINATOR: {}}
    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    """
    Initialize the sensors and the fan based on the config entry represents a Helios device.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry which contains information gathered by the config flow.

    Returns:
        The value indicates whether the setup succeeded.
    """

    if not is_coordinator_exists(hass, config_entry.data[CONF_MAC]):
        try:
            coordinator = await create_coordinator(
                hass,
                config_entry.data[CONF_NAME],
                config_entry.data[CONF_HOST],
            )
        except Exception as exception:
            _LOGGER.error(exception)
            raise ConfigEntryNotReady("Error during initialization") from exception

        set_coordinator(hass, coordinator)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "fan")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )
    return True


async def async_unload_entry(
    hass: HomeAssistantType, config_entry: ConfigEntry
) -> bool:
    """
    Executed when a config entry unloaded by Home Assistant.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry being unloaded.

    Returns:
        The value indicates whether the unloading succeeded.
    """
    if is_coordinator_exists(hass, config_entry.data[CONF_MAC]):
        coordinator = get_coordinator(hass, config_entry.data[CONF_MAC])
        coordinator.unload()

    await hass.config_entries.async_forward_entry_unload(config_entry, "fan")
    await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")

    return True


def is_coordinator_exists(hass: HomeAssistantType, mac_address: str) -> bool:
    """
    Gets the value indicates whether a coordinator already registered
    in hass.data for the given MAC address

    Args:
        hass: The Home Assistant instance.
        mac_address: The MAC address of the Helios device.

    Returns:
        The value indicates whether a coordinator already registered
        in hass.data for the given MAC address.
    """
    return mac_address in hass.data[DOMAIN][DATA_COORDINATOR]


def set_coordinator(
    hass: HomeAssistantType, coordinator: EasyControlsDataUpdateCoordinator
) -> None:
    """
    Stores the specified controller in hass.data by its MAC address.

    Args:
        hass: The Home Assistant instance.
        controller: The coordinator instance to store.
    """
    hass.data[DOMAIN][DATA_COORDINATOR][coordinator.mac] = coordinator


def get_coordinator(
    hass: HomeAssistantType, mac_address: str
) -> EasyControlsDataUpdateCoordinator:
    """
    Gets the coordinator for the given MAC address.

    Args:
        hass: The Home Assistant instance.
        mac_address: The MAC address of the Helios device.

    Returns:
        The thread safe Helios Easy Controls controller.
    """
    return hass.data[DOMAIN][DATA_COORDINATOR][mac_address]
