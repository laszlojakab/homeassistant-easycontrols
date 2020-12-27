from .const import (
    CONTROLLER,
    DOMAIN,
    VARIABLE_BYPASS,
    VARIABLE_INFOS,
    INFO_FILTER_CHANGE_FLAG
)

from .threadsafe_controller import (ThreadSafeController)
from homeassistant.const import (CONF_HOST, CONF_NAME)
from homeassistant.helpers.entity import (Entity)
from homeassistant.helpers import device_registry as dr

import logging

_LOGGER = logging.getLogger(__name__)

class EasyControlBinarySensor(Entity):
    def __init__(self, controller: ThreadSafeController, variable: str, size: int, converter, name: str, device_name: str, icon: str, device_class:str):
        self._controller = controller
        self._variable = variable
        self._converter = converter
        self._size = size
        self._name = name
        self._device_name = device_name
        self._icon = icon
        self._device_class = device_class
        self._state = "unavailable"

    async def async_update(self):
        value = self._controller.get_variable(
            self._variable, self._size, self._converter)
        self._state = "unavailable" if value is None else value

    @property
    def device_class(self):
        return self._device_class

    @property
    def unique_id(self):
        return self._controller.mac + self._name

    @property
    def device_info(self):
        return {
            "connections": {(dr.CONNECTION_NETWORK_MAC, self._controller.mac)},
            "identifiers": {(DOMAIN, self._controller.serial_number)},
            "name": self._device_name,
            "manufacturer": "Helios",
            "model": self._controller.model,
            "sw_version": self._controller.version
        }

    @property
    def should_poll(self):
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.info("Setting up Helios EasyControls binary sensors.")

    name = entry.data[CONF_NAME]
    controller = hass.data[DOMAIN][CONTROLLER][entry.data[CONF_HOST]]

    async_add_entities([
        EasyControlBinarySensor(
            controller, VARIABLE_BYPASS, 8, lambda x : "on" if int(x) == 1 else "off", f"{name} bypass", name, "mdi:delta", "opening"
        ),
        EasyControlBinarySensor(
            controller, VARIABLE_INFOS, 32, lambda x : "on" if (int(x) & INFO_FILTER_CHANGE_FLAG) == INFO_FILTER_CHANGE_FLAG else "off", f"{name} filter change", name, "mdi:air-filter", None
        )
    ])

    _LOGGER.info("Setting up Helios EasyControls binary sensors completed.")
