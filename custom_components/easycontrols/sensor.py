from .const import (
    CONTROLLER,
    DOMAIN,
    VARIABLE_EXTRACT_AIR_FAN_STAGE,
    VARIABLE_SUPPLY_AIR_FAN_STAGE,
    VARIABLE_TEMPERATURE_OUTSIDE_AIR,
    VARIABLE_TEMPERATURE_SUPPLY_AIR,
    VARIABLE_TEMPERATURE_EXTRACT_AIR,
    VARIABLE_TEMPERATURE_OUTGOING_AIR,
    VARIABLE_SUPPLY_AIR_RPM,
    VARIABLE_EXTRACT_AIR_RPM,
    VARIABLE_HUMIDITY_EXTRACT_AIR,
    VARIABLE_ERRORS,
    VARIABLE_WARNINGS,
    VARIABLE_INFOS,
    ERRORS,
    WARNINGS,
    INFOS,
    VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
    VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
    VARIABLE_OPERATION_HOURS_AFTERHEATER,
    VARIABLE_OPERATION_HOURS_PREHEATER,
    VARIABLE_PERCENTAGE_AFTERHEATER,
    VARIABLE_PERCENTAGE_PREHEATER,
    VARIABLE_PERCENTAGE_FAN_SPEED,
    VARIABLE_FAN_STAGE,
    VARIABLE_PREHEATER_STATUS,
    VARIABLE_AFTERHEATER_STATUS
)

from .threadsafe_controller import (ThreadSafeController)
from homeassistant.const import (CONF_HOST, CONF_NAME)
from homeassistant.helpers.entity import (Entity)
from homeassistant.helpers import device_registry as dr

import logging

_LOGGER = logging.getLogger(__name__)


class EasyControlAirFlowRateSensor(Entity):
    def __init__(self, controller: ThreadSafeController, device_name: str):
        self._controller = controller
        self._name = f"{device_name} airflow rate"
        self._device_name = device_name
        self._state = "unavailable"

    async def async_update(self):
        percentage_fan_speed = float(
            self._controller.get_variable(
                VARIABLE_PERCENTAGE_FAN_SPEED, 8, float)
        )

        self._state = "unavailable" if percentage_fan_speed is None else self._controller.maximum_air_flow * \
            percentage_fan_speed / 100.0

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
        return "mdi:air-filter"

    @property
    def unit_of_measurement(self):
        return "m³/h"

class EasyControlEfficiencySensor(Entity):
    # https://www.engineeringtoolbox.com/heat-recovery-efficiency-d_201.html
    def __init__(self, controller: ThreadSafeController, device_name: str):
        self._controller = controller
        self._name = f"{device_name} heat recovery efficiency"
        self._device_name = device_name
        self._state = "unavailable"

    async def async_update(self):
        outside_air_temperature = float(
            self._controller.get_variable(
                VARIABLE_TEMPERATURE_OUTSIDE_AIR, 8, float)
        )
        supply_air_temperature = float(
            self._controller.get_variable(
                VARIABLE_TEMPERATURE_SUPPLY_AIR, 8, float)
        )
        extract_air_temperature = float(
            self._controller.get_variable(
                VARIABLE_TEMPERATURE_EXTRACT_AIR, 8, float)
        )

        if (extract_air_temperature is None or outside_air_temperature is None or supply_air_temperature is None):
            self._state = "unavailable"
            return

        if abs(extract_air_temperature - outside_air_temperature) > 0.5:
            self._state = abs(
                round(
                    (supply_air_temperature - outside_air_temperature)
                    / (extract_air_temperature - outside_air_temperature)
                    * 100,
                    2,
                )
            )
        else:
            self._state = 0

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
        return "mdi:percent"

    @property
    def unit_of_measurement(self):
        return "%"

# class EasyControlExchangedHeatSensor(Entity):
#     def __init__(self, controller: ThreadSafeController, device_name: str):
#         self._controller = controller
#         self._name = f"{device_name} exchanged heat"
#         self._device_name = device_name
#         self._state = "unavailable"

#     async def async_update(self):
#         percentage_fan_speed = float(
#             self._controller.get_variable(
#                 VARIABLE_PERCENTAGE_FAN_SPEED, 8, float)
#         )

#         if (percentage_fan_speed is None):
#             self._state = "unavailable"
#             return

#         airflow_rate = self._controller.maximum_air_flow * percentage_fan_speed / 100.0


#     @property
#     def unique_id(self):
#         return self._controller.mac + self._name

#     @property
#     def device_info(self):
#         return {
#             "connections": {(dr.CONNECTION_NETWORK_MAC, self._controller.mac)},
#             "identifiers": {(DOMAIN, self._controller.serial_number)},
#             "name": self._device_name,
#             "manufacturer": "Helios",
#             "model": self._controller.model,
#             "sw_version": self._controller.version
#         }

#     @property
#     def should_poll(self):
#         return True

#     @property
#     def name(self):
#         """Return the name of the sensor."""
#         return self._name

#     @property
#     def state(self):
#         """Return the state of the sensor."""
#         return self._state

#     @property
#     def icon(self):
#         """Return the icon of the sensor."""
#         return "mdi:air-filter"

#     @property
#     def unit_of_measurement(self):
#         return "m³/h"

class EasyControlFlagSensor(Entity):
    def __init__(self, controller: ThreadSafeController, variable: str, size: int, converter, flags, name: str, device_name: str, icon: str):
        self._controller = controller
        self._variable = variable
        self._converter = converter
        self._size = size
        self._name = name
        self._device_name = device_name
        self._icon = icon
        self._state = "unavailable"
        self._flags = flags

    async def async_update(self):
        value = self._controller.get_variable(
            self._variable, self._size, self._converter)
        self._state = "unavailable" if value is None else self._get_string(
            value)

    def _get_string(self, value: int):
        string = ""
        if (value != 0):
            for item in self._flags.items():
                has_flag = (item[0] & value) == item[0]
                if (has_flag):
                    if (string != ""):
                        string += "\n"
                    string += item[1]
        return string

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


class EasyControlSensor(Entity):
    def __init__(self, controller: ThreadSafeController, variable: str, size: int, converter, name: str, device_name: str, icon: str, unit_of_measurement: str = None):
        self._controller = controller
        self._variable = variable
        self._converter = converter
        self._size = size
        self._name = name
        self._device_name = device_name
        self._icon = icon
        self._unit_of_measurement = unit_of_measurement
        self._state = "unavailable"

    async def async_update(self):
        self._state = self._controller.get_variable(
            self._variable, self._size, self._converter)

    @property
    def unique_id(self):
        return self._controller.mac + self._name

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

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
    _LOGGER.info("Setting up Helios EasyControls sensors.")

    name = entry.data[CONF_NAME]
    controller = hass.data[DOMAIN][CONTROLLER][entry.data[CONF_HOST]]

    async_add_entities([
        EasyControlSensor(
            controller, VARIABLE_PERCENTAGE_FAN_SPEED, 8, float, f"{name} fan speed percentage", name, "mdi:air-conditioner"
        ),
        EasyControlSensor(
            controller, VARIABLE_FAN_STAGE, 1, int, f"{name} fan stage", name, "mdi:air-conditioner"
        ),
        EasyControlSensor(
            controller, VARIABLE_EXTRACT_AIR_FAN_STAGE, 1, int, f"{name} extract air fan stage", name, "mdi:air-conditioner"
        ),
        EasyControlSensor(
            controller, VARIABLE_SUPPLY_AIR_FAN_STAGE, 1, int, f"{name} supply air fan stage", name, "mdi:air-conditioner"
        ),
        EasyControlSensor(
            controller, VARIABLE_TEMPERATURE_OUTSIDE_AIR, 8, float, f"{name} outside air temperature", name,  "mdi:thermometer", "°C"
        ),
        EasyControlSensor(
            controller, VARIABLE_TEMPERATURE_SUPPLY_AIR, 8, float, f"{name} supply air temperature", name, "mdi:thermometer", "°C"
        ),
        EasyControlSensor(
            controller, VARIABLE_TEMPERATURE_EXTRACT_AIR, 8, float, f"{name} extract air temperature", name, "mdi:thermometer", "°C"
        ),
        EasyControlSensor(
            controller, VARIABLE_TEMPERATURE_OUTGOING_AIR, 8, float, f"{name} outgoing air temperature", name, "mdi:thermometer", "°C"
        ),
        EasyControlSensor(
            controller, VARIABLE_EXTRACT_AIR_RPM, 8, int, f"{name} extract air rpm", name, "mdi:rotate-3d-variant", "rpm"
        ),
        EasyControlSensor(
            controller, VARIABLE_SUPPLY_AIR_RPM, 8, int, f"{name} supply air rpm", name, "mdi:rotate-3d-variant", "rpm"
        ),
        EasyControlSensor(
            controller, VARIABLE_HUMIDITY_EXTRACT_AIR, 8, int, f"{name} extract air relative humidity", name, "mdi:water-percent", "%"
        ),
        EasyControlSensor(
            controller, VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN, 10, lambda x: round(float(
                x) / 60.0, 2), f"{name} supply air fan operation hours", name, "mdi:history", "h"
        ),
        EasyControlSensor(
            controller, VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN, 10, lambda x: round(float(
                x) / 60.0, 2), f"{name} extract air fan operation hours", name, "mdi:history", "h"
        ),
        EasyControlFlagSensor(
            controller, VARIABLE_ERRORS, 32, int, ERRORS, f"{name} errors", name, "mdi:alert-circle"
        ),
        EasyControlFlagSensor(
            controller, VARIABLE_WARNINGS, 32, int, WARNINGS, f"{name} warnings", name, "mdi:alert-circle-outline"
        ),
        EasyControlFlagSensor(
            controller, VARIABLE_INFOS, 32, int, INFOS, f"{name} information", name, "mdi:information-outline"
        ),
        EasyControlAirFlowRateSensor(
            controller, name
        ),
        EasyControlEfficiencySensor(
            controller, name
        )
    ])

    if (int(controller.get_variable(VARIABLE_PREHEATER_STATUS, 1, int))):
        async_add_entities([
            EasyControlSensor(
                controller, VARIABLE_OPERATION_HOURS_PREHEATER, 10, lambda x: round(float(
                    x) / 60.0, 2), f"{name} preheater operation hours", name, "mdi:history", "h"
            ),
            EasyControlSensor(
                controller, VARIABLE_PERCENTAGE_PREHEATER, 4, float, f"{name} preheater percentage", name, "mdi:thermometer-lines", "%"
            )
        ])
        
    if (int(controller.get_variable(VARIABLE_AFTERHEATER_STATUS, 1, int))):
        async_add_entities([
            EasyControlSensor(
                controller, VARIABLE_OPERATION_HOURS_AFTERHEATER, 10, lambda x: round(float(
                    x) / 60.0, 2), f"{name} afterheater operation hours", name, "mdi:history", "h"
            ),
            EasyControlSensor(
                controller, VARIABLE_PERCENTAGE_AFTERHEATER, 4, float, f"{name} afterheater percentage", name, "mdi:thermometer-lines", "%"
            )            
        ])

    _LOGGER.info("Setting up Helios EasyControls sensors completed.")
