"""Helios Easy Controls integration."""
import eazyctrl

from homeassistant.const import (CONF_HOST)
from .const import (CONTROLLER, DOMAIN)
from .threadsafe_controller import (ThreadSafeController)

async def async_setup(hass, config):
    hass.data[DOMAIN] = {CONTROLLER: {}}
    return True

async def async_setup_entry(hass, config_entry):
    if not (config_entry.data[CONF_HOST] in hass.data[DOMAIN][CONTROLLER]):
        hass.data[DOMAIN][CONTROLLER][
            config_entry.data[CONF_HOST]
        ] = ThreadSafeController(config_entry.data[CONF_HOST])

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
