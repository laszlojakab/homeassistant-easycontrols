"""Fan entity support for Helios Easy Controls device."""

import logging
from datetime import datetime, timedelta
from typing import Any, Self

from homeassistant.components.fan import (
    FanEntity,
    FanEntityDescription,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from custom_components.easycontrols import get_coordinator
from custom_components.easycontrols.const import (
    DOMAIN,
    OPERATING_MODE_AUTO,
    OPERATING_MODE_MANUAL,
    PRESET_AUTO,
    PRESET_PARTY,
    PRESET_STANDBY,
    SERVICE_SET_FAN_STAGE,
    SERVICE_START_PARTY_MODE,
    SERVICE_STOP_PARTY_MODE,
    VARIABLE_EXTRACT_AIR_FAN_STAGE,
    VARIABLE_EXTRACT_AIR_RPM,
    VARIABLE_FAN_STAGE,
    VARIABLE_OPERATING_MODE,
    VARIABLE_PARTY_MODE,
    VARIABLE_PARTY_MODE_DURATION,
    VARIABLE_PARTY_MODE_FAN_STAGE,
    VARIABLE_PARTY_MODE_REMAINING_TIME,
    VARIABLE_PERCENTAGE_FAN_SPEED,
    VARIABLE_STANDBY_MODE,
    VARIABLE_STANDBY_MODE_FAN_STAGE,
    VARIABLE_STANDBY_MODE_REMAINING_TIME,
    VARIABLE_SUPPLY_AIR_FAN_STAGE,
    VARIABLE_SUPPLY_AIR_RPM,
)
from custom_components.easycontrols.coordinator import EasyControlsDataUpdateCoordinator
from custom_components.easycontrols.modbus_variable import ModbusVariable

SPEED_BASIC_VENTILATION = "basic"
SPEED_RATED_VENTILATION = "rated"
SPEED_INTENSIVE_VENTILATION = "intensive"
SPEED_MAXIMUM_FAN_SPEED = "maximum"

ORDERED_NAMED_FAN_SPEEDS = [
    SPEED_BASIC_VENTILATION,
    SPEED_RATED_VENTILATION,
    SPEED_INTENSIVE_VENTILATION,
    SPEED_MAXIMUM_FAN_SPEED,
]

_LOGGER = logging.getLogger(__name__)


class EasyControlsFanDevice(FanEntity):
    """Represents a fan entity which controls the Helios device."""

    def __init__(self: Self, coordinator: EasyControlsDataUpdateCoordinator):
        """Initialize a new instance of `EasyControlsFanDevice` class."""
        self.entity_description = FanEntityDescription(key="fan", name=coordinator.device_name)
        self._coordinator = coordinator
        self._speed: str | None = None
        self._fan_stage: int | None = None
        self._operating_mode: int | None = None
        self._party_mode: bool | None = None
        self._party_mode_fan_stage: int | None = None
        self._standby_mode: bool | None = None
        self._standby_mode_fan_stage: int | None = None
        self._attr_extra_state_attributes = {}
        self._attr_preset_mode = None
        self._attr_preset_modes = [PRESET_AUTO, PRESET_PARTY, PRESET_STANDBY]
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._coordinator.mac)},
            identifiers={(DOMAIN, self._coordinator.serial_number)},
            name=self._coordinator.device_name,
            manufacturer="Helios",
            model=self._coordinator.article_description,
            sw_version=self._coordinator.version,
            configuration_url=f"http://{self._coordinator.host}",
        )

        def update_listener[T](variable: ModbusVariable[T], value: T) -> None:
            self._value_updated(variable, value)

        self._update_listener = update_listener

    async def async_added_to_hass(self: Self) -> None:
        """
        Called when the entity is added to Home Assistant.

        It adds the update listener to the coordinator.
        """
        self._coordinator.add_listener(VARIABLE_FAN_STAGE, self._update_listener)
        self._coordinator.add_listener(VARIABLE_OPERATING_MODE, self._update_listener)
        self._coordinator.add_listener(VARIABLE_PARTY_MODE, self._update_listener)
        self._coordinator.add_listener(VARIABLE_STANDBY_MODE, self._update_listener)
        self._coordinator.add_listener(VARIABLE_STANDBY_MODE_FAN_STAGE, self._update_listener)
        self._coordinator.add_listener(VARIABLE_PARTY_MODE_FAN_STAGE, self._update_listener)

        self._schedule_variable_updates()

        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        """
        Called when the entity will be removed from Home Assistant.

        It removes the update listener from the coordinator.
        """
        self._coordinator.remove_listener(VARIABLE_FAN_STAGE, self._update_listener)
        self._coordinator.remove_listener(VARIABLE_OPERATING_MODE, self._update_listener)
        self._coordinator.remove_listener(VARIABLE_PARTY_MODE, self._update_listener)
        self._coordinator.remove_listener(VARIABLE_STANDBY_MODE, self._update_listener)
        self._coordinator.remove_listener(VARIABLE_STANDBY_MODE_FAN_STAGE, self._update_listener)
        self._coordinator.remove_listener(VARIABLE_PARTY_MODE_FAN_STAGE, self._update_listener)
        return await super().async_will_remove_from_hass()

    def _value_updated[T](self: Self, variable: ModbusVariable[T], value: T) -> None:  # noqa: C901
        if variable == VARIABLE_FAN_STAGE:
            self._fan_stage = value
        elif variable == VARIABLE_OPERATING_MODE:
            self._operating_mode = value
        elif variable == VARIABLE_PARTY_MODE:
            self._party_mode = value
        elif variable == VARIABLE_STANDBY_MODE:
            self._standby_mode = value
        elif variable == VARIABLE_STANDBY_MODE_FAN_STAGE:
            self._standby_mode_fan_stage = value
        elif variable == VARIABLE_PARTY_MODE_FAN_STAGE:
            self._party_mode_fan_stage = value

        actual_fan_stage = None
        if self._party_mode:
            self._attr_preset_mode = PRESET_PARTY
            actual_fan_stage = self._party_mode_fan_stage
        elif self._standby_mode:
            self._attr_preset_mode = PRESET_STANDBY
            actual_fan_stage = self._standby_mode_fan_stage
        elif self._operating_mode == OPERATING_MODE_AUTO:
            self._attr_preset_mode = PRESET_AUTO
            actual_fan_stage = self._fan_stage
        else:
            self._attr_preset_mode = None
            actual_fan_stage = self._fan_stage

        if actual_fan_stage == 0 or actual_fan_stage is None:
            self._speed = actual_fan_stage
        else:
            self._speed = self.fan_stage_to_speed(actual_fan_stage)

        self._attr_percentage = (
            0
            if self._speed == 0 or self._speed is None
            else ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, self._speed)
        )
        self._attr_available = self._speed is not None

        self.schedule_update_ha_state(False)

    @property
    def unique_id(self) -> str:
        """Gets the unique ID of the fan."""
        return self._coordinator.mac

    @property
    def supported_features(self) -> int:
        """Gets the supported features flag."""
        return (FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE |
                FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF)

    @property
    def speed_count(self) -> int:
        """Gets the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    async def async_set_percentage(self: Self, percentage: int) -> None:
        """
        Sets the speed percentage of the fan.

        Args:
            percentage: The speed percentage.

        """
        if percentage == 0:
            await self.async_turn_off()
        else:
            speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)

            await self._disable_running_preset()

            await self._coordinator.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_MANUAL)
            await self._coordinator.set_variable(VARIABLE_FAN_STAGE, self.speed_to_fan_stage(speed))

            self._schedule_variable_updates()

    async def async_set_preset_mode(self: Self, preset_mode: str) -> None:
        """
        Sets the preset mode of the fan.

        Args:
            preset_mode: The preset mode to set.

        """
        self._disable_running_preset()

        if preset_mode == PRESET_AUTO:
            await self._coordinator.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_AUTO)
        elif preset_mode == PRESET_PARTY:
            await self._coordinator.set_variable(VARIABLE_PARTY_MODE, True)
        elif preset_mode == PRESET_STANDBY:
            await self._coordinator.set_variable(VARIABLE_STANDBY_MODE, True)
        else:
            await self._coordinator.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_MANUAL)

        self._schedule_variable_updates()

    async def async_turn_on(
        self: Self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs,  # noqa: ARG002
    ) -> None:
        """Turns on the fan at the specific speed or sets the specified preset mode."""
        if percentage is None and preset_mode is None:
            percentage = 50

        if percentage is not None:
            await self._disable_running_preset()

            await self._coordinator.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_MANUAL)
            speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)

            await self._coordinator.set_variable(VARIABLE_FAN_STAGE, self.speed_to_fan_stage(speed))
        else:
            await self.async_set_preset_mode(preset_mode)

        self._schedule_variable_updates()

    async def async_turn_off(self: Self, **kwargs: Any) -> None:  # noqa: ARG002, ANN401
        """Turns off the fan."""
        await self._coordinator.set_variable(VARIABLE_PARTY_MODE, False)
        await self._coordinator.set_variable(VARIABLE_STANDBY_MODE, False)
        await self._coordinator.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_MANUAL)
        await self._coordinator.set_variable(VARIABLE_FAN_STAGE, 0)
        self._schedule_variable_updates()

    async def start_party_mode(self: Self, speed: str, duration: int) -> None:
        """
        Starts the party mode.

        Args:
            speed: str
                The speed of the party mode.
                Set to None to keep the previously set value.
            duration: int
                The duration of the party mode.
                Set to None to keep the previously set value.

        """
        if speed is not None:
            await self._coordinator.set_variable(
                VARIABLE_PARTY_MODE_FAN_STAGE, self.speed_to_fan_stage(speed)
            )
        if duration is not None:
            await self._coordinator.set_variable(VARIABLE_PARTY_MODE_DURATION, duration)

        await self._coordinator.set_variable(VARIABLE_PARTY_MODE, True)
        self._schedule_variable_updates()

    async def stop_party_mode(self) -> None:
        """Stops the party mode."""
        await self._coordinator.set_variable(VARIABLE_PARTY_MODE, False)
        self._schedule_variable_updates()

    async def set_fan_stage(self, fan_stage: int) -> None:
        """
        Sets the fan stage.

        Args:
            fan_stage: The fan stage to set.

        """
        _LOGGER.debug("Set Fan Stage to %s", str(fan_stage))
        if fan_stage is not None:
            await self._coordinator.set_variable(
                VARIABLE_FAN_STAGE, fan_stage
            )
        self._schedule_variable_updates()

    @classmethod
    def speed_to_fan_stage(cls, speed: str) -> int:
        """
        Converts named fan speed to fan stage.

        Args:
            speed: The named fan speed to convert.

        Returns:
            The converted fan stage.

        """
        return ORDERED_NAMED_FAN_SPEEDS.index(speed) + 1

    @classmethod
    def fan_stage_to_speed(cls, fan_stage: int) -> str:
        """
        Converts fan stage to named speed.

        Args:
            fan_stage: The fan stage to convert.

        Returns:
            The speed percentage represented by the fan_stage.

        """
        return ORDERED_NAMED_FAN_SPEEDS[fan_stage - 1]

    def _schedule_variable_updates(self: Self) -> None:
        self._coordinator.schedule_update(VARIABLE_PERCENTAGE_FAN_SPEED)
        self._coordinator.schedule_update(VARIABLE_EXTRACT_AIR_FAN_STAGE)
        self._coordinator.schedule_update(VARIABLE_SUPPLY_AIR_FAN_STAGE)
        self._coordinator.schedule_update(VARIABLE_STANDBY_MODE)
        self._coordinator.schedule_update(VARIABLE_PARTY_MODE)
        self._coordinator.schedule_update(VARIABLE_OPERATING_MODE)
        self._coordinator.schedule_update(VARIABLE_FAN_STAGE)

        @callback
        def schedule_rpm_updates(execution_time: datetime) -> None:  # noqa: ARG001
            self._coordinator.schedule_update(VARIABLE_SUPPLY_AIR_RPM)
            self._coordinator.schedule_update(VARIABLE_EXTRACT_AIR_RPM)

        # blades need time to stop so we update a little later
        async_call_later(self.hass, timedelta(seconds=5), schedule_rpm_updates)

    async def _disable_running_preset(self) -> None:
        await self._coordinator.set_variable(VARIABLE_PARTY_MODE, False)
        await self._coordinator.set_variable(VARIABLE_STANDBY_MODE, False)

        self._schedule_preset_variable_updates()

    def _schedule_preset_variable_updates(self: Self) -> None:
        self._coordinator.schedule_update(VARIABLE_PARTY_MODE_REMAINING_TIME)
        self._coordinator.schedule_update(VARIABLE_STANDBY_MODE_REMAINING_TIME)
        self._coordinator.schedule_update(VARIABLE_PARTY_MODE_REMAINING_TIME)
        self._coordinator.schedule_update(VARIABLE_STANDBY_MODE_REMAINING_TIME)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    Setup of Helios Easy Controls fan for the specified config_entry.

    Args:
        hass: The Home Assistant instance.
        config_entry:  The config entry which is used to create sensors.
        async_add_entities: The callback which can be used to add new entities to Home Assistant.

    Returns:
        The value indicates whether the setup succeeded.

    """
    _LOGGER.info("Setting up Helios EasyControls fan device.")

    coordinator = get_coordinator(hass, config_entry.data[CONF_MAC])
    fan = EasyControlsFanDevice(coordinator)

    async_add_entities([fan])

    async def handle_party_mode(call: ServiceCall) -> None:
        _LOGGER.warning(
            "party_mode service is deprecated. "
            "Use start_party_mode and stop_party_mode service instead!"
        )
        duration = call.data.get("duration", 60)
        speed = call.data.get("speed", "high")
        if speed == 0:
            await fan.stop_party_mode()
        else:
            await fan.start_party_mode(speed, duration)

    hass.services.async_register(DOMAIN, "party_mode", handle_party_mode)

    async def handle_start_party_mode(call: ServiceCall) -> None:
        duration = call.data.get("duration", None)
        speed = call.data.get("speed", None)
        await fan.start_party_mode(speed, duration)

    async def handle_stop_party_mode(call: ServiceCall) -> None:  # noqa: ARG001
        await fan.stop_party_mode()

    async def handle_set_fan_stage(call: ServiceCall) -> None:
        stage = call.data.get("stage", None)
        await fan.set_fan_stage(stage)

    hass.services.async_register(DOMAIN, SERVICE_START_PARTY_MODE, handle_start_party_mode)
    hass.services.async_register(DOMAIN, SERVICE_STOP_PARTY_MODE, handle_stop_party_mode)
    hass.services.async_register(DOMAIN, SERVICE_SET_FAN_STAGE, handle_set_fan_stage)

    _LOGGER.info("Setting up Helios EasyControls fan device completed.")
