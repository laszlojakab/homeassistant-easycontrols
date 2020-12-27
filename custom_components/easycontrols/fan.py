# https://community.home-assistant.io/t/using-native-modbus-component-for-helios-kwl/107461
"""
Fan support for EasyControls Helios KWL Ventillation unit.
"""
import logging
from datetime import timedelta

from homeassistant.components.fan import (FanEntity)
from homeassistant.const import (CONF_HOST, CONF_NAME)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import (
    async_track_state_change
)

from .threadsafe_controller import (ThreadSafeController)
from .const import (
    CONTROLLER, DOMAIN, MODE_AUTO, MODE_MANUAL,
    PRESET_HOLIDAY_CONSTANT, PRESET_HOLIDAY_INTERVAL,
    PRESET_NOT_SET, PRESET_PARTY, PRESET_STANDBY,
    VARIABLE_FAN_STAGE,
    VARIABLE_HOLIDAY_MODE,
    VARIABLE_OPERATING_MODE,
    VARIABLE_PARTY_MODE,
    VARIABLE_PERCENTAGE_FAN_SPEED,
    VARIABLE_STANDBY_MODE
)

SUPPORT_SET_SPEED = 1

SPEED_BASIC_VENTILATION = "basic"
SPEED_RATED_VENTILATION = "rated"
SPEED_INTENSIVE_VENTILATION = "intensive"
SPEED_MAXIMUM_FAN_SPEED = "maximum"

_LOGGER = logging.getLogger(__name__)


class EasyControlFanDevice(FanEntity):
    def __init__(self, hass, controller: ThreadSafeController, name: str):
        self._controller = controller
        self._name = name
        self._fan_stage = None
        self._percentage_fan_speed = None
        self._attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def device_state_attributes(self):
        return self._attributes

    @property
    def unique_id(self):
        return self._controller.mac

    @property
    def device_info(self):
        return {
            "connections": {(dr.CONNECTION_NETWORK_MAC, self._controller.mac)},
            "identifiers": {(DOMAIN, self._controller.serial_number)},
            "name": self._name,
            "manufacturer": "Helios",
            "model": self._controller.model,
            "sw_version": self._controller.version
        }

    @property
    def supported_features(self):
        return SUPPORT_SET_SPEED

    @property
    def speed_list(self):
        return [
            SPEED_BASIC_VENTILATION,
            SPEED_RATED_VENTILATION,
            SPEED_INTENSIVE_VENTILATION,
            SPEED_MAXIMUM_FAN_SPEED,
        ]

    @property
    def speed(self):
        if self._fan_stage is None or self._fan_stage == 0:
            return None
        return self.speed_list[self._fan_stage - 1]

    @property
    def is_on(self):
        return not self._percentage_fan_speed is None and self._percentage_fan_speed > 0

    async def async_set_speed(self, speed: str):
        self._controller.set_variable(
            VARIABLE_OPERATING_MODE, 1, "{:d}"
        )  # operation mode = manual
        self._controller.set_variable(
            VARIABLE_FAN_STAGE, self.speed_list.index(speed) + 1, "{:d}"
        )

    async def async_turn_on(self, speed=None, **kwargs):
        self._controller.set_variable(
            VARIABLE_OPERATING_MODE, 1, "{:d}"
        )  # operation mode = manual
        if speed is None:
            speed = SPEED_RATED_VENTILATION

        self._controller.set_variable(
            VARIABLE_FAN_STAGE, self.speed_list.index(speed) + 1, "{:d}"
        )

    async def async_turn_off(self, **kwargs):
        self._controller.set_variable(
            VARIABLE_OPERATING_MODE, 1, "{:d}"
        )  # operation mode = manual
        self._controller.set_variable(VARIABLE_FAN_STAGE, 0, "{:d}")

    async def async_update(self):
        self._percentage_fan_speed = float(
            self._controller.get_variable(
                VARIABLE_PERCENTAGE_FAN_SPEED, 8, float)
        )
        self._fan_stage = int(
            self._controller.get_variable(VARIABLE_FAN_STAGE, 1, int))

        operation_mode = int(
            self._controller.get_variable(VARIABLE_OPERATING_MODE, 1, int)
        )
        party_mode = self._controller.get_variable(VARIABLE_PARTY_MODE, 1, int)
        standby_mode = self._controller.get_variable(
            VARIABLE_STANDBY_MODE, 1, int)
        holiday_mode = self._controller.get_variable(
            VARIABLE_HOLIDAY_MODE, 1, int)

        if party_mode == 1:
            preset_mode = PRESET_PARTY
        else:
            if standby_mode == 1:
                preset_mode = PRESET_STANDBY
            else:
                if holiday_mode == 1:
                    preset_mode = PRESET_HOLIDAY_INTERVAL
                else:
                    if holiday_mode == 2:
                        preset_mode = PRESET_HOLIDAY_CONSTANT
                    else:
                        preset_mode = PRESET_NOT_SET

        operation_mode = MODE_AUTO if operation_mode == 0 else MODE_MANUAL

        # air_flow_rate = self._controller.maximum_air_flow * \
        #     self._percentage_fan_speed / 100.0

        # # https://www.engineeringtoolbox.com/heater-coolers-ventilation-systems-d_200.html
        # heat_exchanged = round(
        #     air_flow_rate
        #     / 3600
        #     * 1.2
        #     * (supply_air_temperature - outside_air_temperature),
        #     2,
        # )

        self._attributes = {
            "preset_mode": preset_mode,
            "operation_mode": operation_mode
        }

async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.info("Setting up Helios EasyControls fan device.")

    name = entry.data[CONF_NAME]
    controller = hass.data[DOMAIN][CONTROLLER][entry.data[CONF_HOST]]

    async_add_entities([EasyControlFanDevice(hass, controller, name)])

    _LOGGER.info("Setting up Helios EasyControls fan device completed.")
