'''Helios Easy Controls integration.'''
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import CONF_MAC_ADDRESS, DATA_CONTROLLER, DOMAIN
from .threadsafe_controller import ThreadSafeController


# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    '''
    Set up the Helios Easy Controls component.

    Parameters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    config: homeassistant.helpers.typing.ConfigType
        The configuration.

    Returns
    -------
    bool
        The value indicates whether the setup succeeded.
    '''
    hass.data[DOMAIN] = {DATA_CONTROLLER: {}}
    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    '''
    Initialize the sensors and the fan based on the config entry represents a Helios device.

    Parameters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    config_entry: homeassistant.config_entries.ConfigEntry
        The config entry which contains information gathered by the config flow.

    Returns
    -------
    bool
        The value indicates whether the setup succeeded.
    '''
    if config_entry.data[CONF_HOST] not in hass.data[DOMAIN][DATA_CONTROLLER]:
        hass.data[DOMAIN][DATA_CONTROLLER][
            config_entry.data[CONF_HOST]
        ] = ThreadSafeController(config_entry.data[CONF_HOST], config_entry.data[CONF_MAC_ADDRESS])

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, 'fan')
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, 'sensor')
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, 'binary_sensor')
    )
    return True
