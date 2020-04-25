# https://community.home-assistant.io/t/using-native-modbus-component-for-helios-kwl/107461
"""
Fan support for EasyControls Helios KWL Ventillation unit.
"""
import logging
import re
from datetime import timedelta

from homeassistant.components.fan import FanEntity
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import (CONTROLLER, DOMAIN, MODE_AUTO, MODE_MANUAL,
                    PRESET_HOLIDAY_CONSTANT, PRESET_HOLIDAY_INTERVAL,
                    PRESET_NOT_SET, PRESET_PARTY, PRESET_STANDBY,
                    VARIABLE_ARTICLE_DESCRIPTION, VARIABLE_ERRORS,
                    VARIABLE_EXTRACT_AIR_FAN_STAGE, VARIABLE_EXTRACT_AIR_RPM,
                    VARIABLE_FAN_STAGE, VARIABLE_FILTER_CHANGE,
                    VARIABLE_HOLIDAY_MODE, VARIABLE_HUMIDITY_EXTRACT_AIR,
                    VARIABLE_INFOS, VARIABLE_OPERATING_MODE,
                    VARIABLE_OPERATION_HOURS_AFTERHEATER,
                    VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
                    VARIABLE_OPERATION_HOURS_PREHEATER,
                    VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
                    VARIABLE_PARTY_MODE, VARIABLE_PERCENTAGE_AFTERHEATER,
                    VARIABLE_PERCENTAGE_FAN_STAGE,
                    VARIABLE_PERCENTAGE_PREHEATER, VARIABLE_PREHEATER_STATUS,
                    VARIABLE_SOFTWARE_VERSION, VARIABLE_STANDBY_MODE,
                    VARIABLE_SUPPLY_AIR_FAN_STAGE, VARIABLE_SUPPLY_AIR_RPM,
                    VARIABLE_TEMPERATURE_EXTRACT_AIR,
                    VARIABLE_TEMPERATURE_OUTGOING_AIR,
                    VARIABLE_TEMPERATURE_OUTSIDE_AIR,
                    VARIABLE_TEMPERATURE_SUPPLY_AIR, VARIABLE_WARNINGS)

SUPPORT_SET_SPEED = 1

SPEED_BASIC_VENTILATION = "basic"
SPEED_RATED_VENTILATION = "rated"
SPEED_INTENSIVE_VENTILATION = "intensive"
SPEED_MAXIMUM_FAN_SPEED = "maximum"

_LOGGER = logging.getLogger(__name__)


class EasyControlFanDevice(FanEntity):
    def __init__(self, controller, name):
        self._controller = controller
        self._name = name
        self._model = controller.get_variable(VARIABLE_ARTICLE_DESCRIPTION, 128, str)
        self._version = controller.get_variable(VARIABLE_SOFTWARE_VERSION, 128, str)
        self._maximum_air_flow = float(re.findall(r"\d+", self._model)[0])
        self._attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def device_state_attributes(self):
        return self._attributes

    @property
    def unique_id(self):
        return self._name

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self._name,
            "manufacturer": "Helios",
            "model": self._model,
            "sw_version": self._version,
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
        fan_stage = self._attributes.get("fan_stage")
        if fan_stage is None or fan_stage == 0:
            return None
        return self.speed_list[fan_stage - 1]

    @property
    def is_on(self):
        percentage_fan_speed = self._attributes.get("percentage_fan_speed")
        return not percentage_fan_speed is None and percentage_fan_speed > 0

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
            VARIABLE_FAN_STAGE, self.speed_list.index(speed), "{:d}"
        )

    async def async_turn_off(self, **kwargs):
        self._controller.set_variable(
            VARIABLE_OPERATING_MODE, 1, "{:d}"
        )  # operation mode = manual
        self._controller.set_variable(VARIABLE_FAN_STAGE, 0, "{:d}")

    async def async_update(self):
        percentage_fan_speed = float(
            self._controller.get_variable(VARIABLE_PERCENTAGE_FAN_STAGE, 8, float)
        )
        outside_air_temperature = float(
            self._controller.get_variable(VARIABLE_TEMPERATURE_OUTSIDE_AIR, 8, float)
        )
        supply_air_temperature = float(
            self._controller.get_variable(VARIABLE_TEMPERATURE_SUPPLY_AIR, 8, float)
        )
        outgoing_air_temperature = float(
            self._controller.get_variable(VARIABLE_TEMPERATURE_OUTGOING_AIR, 8, float)
        )
        extract_air_temperature = float(
            self._controller.get_variable(VARIABLE_TEMPERATURE_EXTRACT_AIR, 8, float)
        )
        operation_mode = int(
            self._controller.get_variable(VARIABLE_OPERATING_MODE, 1, int)
        )
        fan_stage = int(self._controller.get_variable(VARIABLE_FAN_STAGE, 1, int))
        supply_air_rpm = int(
            self._controller.get_variable(VARIABLE_SUPPLY_AIR_RPM, 4, int)
        )
        extract_air_rpm = int(
            self._controller.get_variable(VARIABLE_EXTRACT_AIR_RPM, 4, int)
        )
        filter_change = int(
            self._controller.get_variable(VARIABLE_FILTER_CHANGE, 1, int)
        )
        supply_air_fan_stage = int(
            self._controller.get_variable(VARIABLE_SUPPLY_AIR_FAN_STAGE, 1, int)
        )
        extract_air_fan_stage = int(
            self._controller.get_variable(VARIABLE_EXTRACT_AIR_FAN_STAGE, 1, int)
        )
        software_version = self._controller.get_variable(VARIABLE_SOFTWARE_VERSION, 5)
        operation_hours_supply_air_fan = (
            float(
                self._controller.get_variable(
                    VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN, 10, float
                )
            )
            / 60
        )
        operation_hours_extract_air_fan = (
            float(
                self._controller.get_variable(
                    VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN, 10, float
                )
            )
            / 60
        )
        operation_hours_preheater = (
            float(
                self._controller.get_variable(
                    VARIABLE_OPERATION_HOURS_PREHEATER, 10, float
                )
            )
            / 60
        )
        operation_hours_afterheater = (
            float(
                self._controller.get_variable(
                    VARIABLE_OPERATION_HOURS_AFTERHEATER, 10, float
                )
            )
            / 60
        )
        preheater_status = int(
            self._controller.get_variable(VARIABLE_PREHEATER_STATUS, 1, int)
        )
        preheater_percentage = float(
            self._controller.get_variable(VARIABLE_PERCENTAGE_PREHEATER, 4, float)
        )
        afterheater_percentage = float(
            self._controller.get_variable(VARIABLE_PERCENTAGE_AFTERHEATER, 4, float)
        )
        errors = self._controller.get_variable(VARIABLE_ERRORS, 32)
        warnings = self._controller.get_variable(VARIABLE_WARNINGS, 32)
        infos = self._controller.get_variable(VARIABLE_INFOS, 32)
        extract_humidity = int(
            self._controller.get_variable(VARIABLE_HUMIDITY_EXTRACT_AIR, 3, int)
        )

        party_mode = self._controller.get_variable(VARIABLE_PARTY_MODE, 1, int)
        standby_mode = self._controller.get_variable(VARIABLE_STANDBY_MODE, 1, int)
        holiday_mode = self._controller.get_variable(VARIABLE_HOLIDAY_MODE, 1, int)

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

        air_flow_rate = self._maximum_air_flow * percentage_fan_speed / 100.0
        heat_exchanged = round(
            air_flow_rate
            / 3600
            * 1.2
            * (supply_air_temperature - outside_air_temperature),
            2,
        )

        if abs(extract_air_temperature - outside_air_temperature) > 0.5:
            heat_exchanger_efficiency = abs(
                round(
                    (supply_air_temperature - outside_air_temperature)
                    / (extract_air_temperature - outside_air_temperature)
                    * 100,
                    2,
                )
            )
        else:
            heat_exchanger_efficiency = 0

        self._attributes = {
            "outside_air_temperature": outside_air_temperature,
            "supply_air_temperature": supply_air_temperature,
            "outgoing_air_temperature": outgoing_air_temperature,
            "extract_air_temperature": extract_air_temperature,
            "fan_stage": fan_stage,
            "preset_mode": preset_mode,
            "percentage_fan_speed": percentage_fan_speed,
            "operation_mode": operation_mode,
            "supply_air_rpm": supply_air_rpm,
            "extract_air_rpm": extract_air_rpm,
            "filter_change": filter_change,
            "supply_air_fan_stage": supply_air_fan_stage,
            "extract_air_fan_stage": extract_air_fan_stage,
            "extract_humidity": extract_humidity,
            "software_version": software_version,
            "operation_hours_supply_air_fan": operation_hours_supply_air_fan,
            "operation_hours_extract_air_fan": operation_hours_extract_air_fan,
            "operation_hours_preheater": operation_hours_preheater,
            "operation_hours_afterheater": operation_hours_afterheater,
            "preheater_status": preheater_status,
            "preheater_percentage": preheater_percentage,
            "afterheater_percentage": afterheater_percentage,
            "maximum_air_flow": self._maximum_air_flow,
            "heat_exchanged": heat_exchanged,
            "heat_exchanger_efficiency": heat_exchanger_efficiency,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
        }


async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.info("Setting up Helios EasyControls fan device.")

    name = entry.data[CONF_NAME]
    controller = hass.data[DOMAIN][CONTROLLER][entry.data[CONF_HOST]]

    async_add_entities([EasyControlFanDevice(controller, name)])

    _LOGGER.info("Setting up Helios EasyControls fan device completed.")
