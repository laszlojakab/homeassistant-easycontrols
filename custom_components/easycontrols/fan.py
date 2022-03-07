'''
Fan entity support for Helios Easy Controls device.
'''
import logging
from typing import Any, List, Optional

from homeassistant.components.fan import (SUPPORT_PRESET_MODE,
                                          SUPPORT_SET_SPEED, FanEntity,
                                          FanEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.core import ServiceCall
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util.percentage import (ordered_list_item_to_percentage,
                                           percentage_to_ordered_list_item)

from . import get_controller, get_device_info
from .const import (DOMAIN, OPERATING_MODE_AUTO, OPERATING_MODE_MANUAL,
                    PRESET_AUTO, PRESET_PARTY, PRESET_STANDBY,
                    SERVICE_START_PARTY_MODE, SERVICE_STOP_PARTY_MODE,
                    VARIABLE_EXTRACT_AIR_RPM, VARIABLE_FAN_STAGE,
                    VARIABLE_OPERATING_MODE, VARIABLE_PARTY_MODE,
                    VARIABLE_PARTY_MODE_DURATION,
                    VARIABLE_PARTY_MODE_FAN_STAGE, VARIABLE_STANDBY_MODE,
                    VARIABLE_SUPPLY_AIR_RPM)
from .controller import Controller

SPEED_BASIC_VENTILATION = 'basic'
SPEED_RATED_VENTILATION = 'rated'
SPEED_INTENSIVE_VENTILATION = 'intensive'
SPEED_MAXIMUM_FAN_SPEED = 'maximum'

ORDERED_NAMED_FAN_SPEEDS = [
    SPEED_BASIC_VENTILATION,
    SPEED_RATED_VENTILATION,
    SPEED_INTENSIVE_VENTILATION,
    SPEED_MAXIMUM_FAN_SPEED
]

_LOGGER = logging.getLogger(__name__)

# pylint: disable=abstract-method


class EasyControlsFanDevice(FanEntity):
    '''
    Represents a fan entity which controls the Helios device.
    '''

    def __init__(self, controller: Controller):
        self.entity_description = FanEntityDescription(
            key='fan',
            name=controller.device_name
        )
        self._controller = controller
        self._speed = None
        self._supply_air_rpm = None
        self._extract_air_rpm = None
        self._preset_mode = None
        self._attr_extra_state_attributes = {}

    @property
    def available(self) -> bool:
        '''
        Gets the value indicates wether the fan is available.
        '''
        return self._speed is not None

    @property
    def unique_id(self):
        '''
        Gets the unique ID of the fan.
        '''
        return self._controller.mac

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)

    @property
    def supported_features(self) -> int:
        '''
        Gets the supported features flag.
        '''
        return SUPPORT_SET_SPEED | SUPPORT_PRESET_MODE

    @property
    def preset_modes(self) -> List[str]:
        return [
            PRESET_AUTO,
            PRESET_PARTY,
            PRESET_STANDBY
        ]

    @property
    def preset_mode(self) -> str:
        return self._preset_mode

    @property
    def speed_count(self) -> int:
        '''Return the number of speeds the fan supports.'''
        return len(ORDERED_NAMED_FAN_SPEEDS)

    @property
    def percentage(self) -> Optional[int]:
        '''Return the current speed percentage.'''
        if self._speed is None or self._speed == 0:
            return 0
        else:
            return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, self._speed)

    @property
    def is_on(self):
        '''
        Gets the value indicates whether the fan is on.
        '''
        return ((not self._supply_air_rpm is None and self._supply_air_rpm > 0) or
                (not self._extract_air_rpm is None and self._extract_air_rpm > 0))

    async def async_set_percentage(self, percentage: int) -> None:
        '''
        Sets the speed percentage of the fan.

        Parameters
        ----------
        percentage: int
            The speed percentage.
        '''
        if percentage == 0:
            await self.async_turn_off()
        else:
            speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)

            await self._controller.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_MANUAL)
            await self._controller.set_variable(VARIABLE_FAN_STAGE, self.speed_to_fan_stage(speed))

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        if preset_mode == PRESET_AUTO:
            await self._controller.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_AUTO)
        elif preset_mode == PRESET_PARTY:
            await self._controller.set_variable(VARIABLE_PARTY_MODE, True)
        elif preset_mode == PRESET_STANDBY:
            await self._controller.set_variable(VARIABLE_STANDBY_MODE, True)
        else:
            await self._controller.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_MANUAL)

    async def async_turn_on(
        self,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any
    ):
        '''
        Turns on the fan at the specific speed.
        '''
        if percentage is None and preset_mode is None:
            percentage = 50

        if percentage is not None:
            await self._controller.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_MANUAL)
            speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
            await self._controller.set_variable(VARIABLE_FAN_STAGE, self.speed_to_fan_stage(speed))
        else:
            await self.async_set_preset_mode(preset_mode)

    async def async_turn_off(self, **kwargs: Any):
        '''
        Turns off the fan.
        '''
        await self._controller.set_variable(VARIABLE_OPERATING_MODE, OPERATING_MODE_MANUAL)
        await self._controller.set_variable(VARIABLE_FAN_STAGE, 0)

    async def start_party_mode(self, speed: str, duration: int):
        '''
        Starts the party mode.

        speed: str
            The speed of the party mode.
            Set to None to keep the previously set value.
        duration: int
            The duration of the party mode.
            Set to None to keep the previously set value.
        '''
        if speed is not None:
            await self._controller.set_variable(VARIABLE_PARTY_MODE_FAN_STAGE,
                                          self.speed_to_fan_stage(speed))
        if duration is not None:
            await self._controller.set_variable(VARIABLE_PARTY_MODE_DURATION, duration)

        await self._controller.set_variable(VARIABLE_PARTY_MODE, True)

    async def stop_party_mode(self):
        '''
        Stops the party mode.
        '''
        await self._controller.set_variable(VARIABLE_PARTY_MODE, False)

    async def async_update(self) -> None:
        '''
        Updates the fan device.
        '''
        self._supply_air_rpm = await self._controller.get_variable(VARIABLE_SUPPLY_AIR_RPM)
        self._extract_air_rpm = await self._controller.get_variable(VARIABLE_EXTRACT_AIR_RPM)
        fan_stage = await self._controller.get_variable(VARIABLE_FAN_STAGE)
        if fan_stage == 0:
            self._speed = 0
        else:
            self._speed = self.fan_stage_to_speed(
                await self._controller.get_variable(VARIABLE_FAN_STAGE)
            )

        operating_mode = await self._controller.get_variable(VARIABLE_OPERATING_MODE)
        party_mode = await self._controller.get_variable(VARIABLE_PARTY_MODE)
        standby_mode = await self._controller.get_variable(VARIABLE_STANDBY_MODE)

        if party_mode:
            self._preset_mode = PRESET_PARTY
        elif standby_mode:
            self._preset_mode = PRESET_STANDBY
        elif operating_mode == OPERATING_MODE_AUTO:
            self._preset_mode = PRESET_AUTO
        else:
            self._preset_mode = None

    def speed_to_fan_stage(self, speed: str) -> int:
        '''
        Converts named fan speed to fan stage.

        Parameters
        ----------
        speed: str
            The named fan speed to convert.

        Returns
        -------
        int
            The fan stage belongs to speed.
        '''
        return ORDERED_NAMED_FAN_SPEEDS.index(speed) + 1

    def fan_stage_to_speed(self, fan_stage: int) -> str:
        '''
        Converts fan stage to named speed.

        Parameters
        ----------
        fan_stage: int
            The fan stage to convert.

        Returns
        -------
        int
            The named fan speed belongs to the fan stage.
        '''
        return ORDERED_NAMED_FAN_SPEEDS[fan_stage - 1]


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    '''
    Setup of Helios Easy Controls fan for the specified config_entry.

    Parameters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    config_entry: homeassistant.helpers.typing.ConfigEntry
        The config entry which is used to create sensors.
    async_add_entities: homeassistant.helpers.entity_platform.AddEntitiesCallback
        The callback which can be used to add new entities to Home Assistant.

    Returns
    -------
    bool
        The value indicates whether the setup succeeded.
    '''
    _LOGGER.info('Setting up Helios EasyControls fan device.')

    controller = get_controller(hass, config_entry.data[CONF_MAC])
    fan = EasyControlsFanDevice(controller)

    async_add_entities([fan])

    async def handle_party_mode(call: ServiceCall):
        _LOGGER.warning(
            'party_mode service is deprecated. '
            'Use start_party_mode and stop_party_mode service instead!'
        )
        duration = call.data.get('duration', 60)
        speed = call.data.get('speed', 'high')
        if speed == 0:
            await fan.stop_party_mode()
        else:
            await fan.start_party_mode(speed, duration)

    hass.services.async_register(DOMAIN, 'party_mode', handle_party_mode)

    async def handle_start_party_mode(call: ServiceCall):
        duration = call.data.get('duration', None)
        speed = call.data.get('speed', None)
        await fan.start_party_mode(speed, duration)

    # pylint: disable=unused-argument
    async def handle_stop_party_mode(call: ServiceCall):
        await fan.stop_party_mode()

    hass.services.async_register(DOMAIN, SERVICE_START_PARTY_MODE, handle_start_party_mode)
    hass.services.async_register(DOMAIN, SERVICE_STOP_PARTY_MODE, handle_stop_party_mode)

    _LOGGER.info('Setting up Helios EasyControls fan device completed.')
