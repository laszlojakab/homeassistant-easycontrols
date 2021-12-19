# pylint: disable=bad-continuation
'''
Fan entity support for Helios Easy Controls device.
'''
import logging

from homeassistant.components.fan import FanEntity, FanEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType

from . import get_controller, get_device_info
from .const import (DOMAIN, MODE_AUTO, MODE_MANUAL, PRESET_HOLIDAY_CONSTANT,
                    PRESET_HOLIDAY_INTERVAL, PRESET_NOT_SET, PRESET_PARTY,
                    PRESET_STANDBY, VARIABLE_EXTRACT_AIR_RPM,
                    VARIABLE_FAN_STAGE, VARIABLE_HOLIDAY_MODE,
                    VARIABLE_OPERATING_MODE, VARIABLE_PARTY_MODE,
                    VARIABLE_PARTY_MODE_DURATION,
                    VARIABLE_PARTY_MODE_FAN_STAGE, VARIABLE_STANDBY_MODE,
                    VARIABLE_SUPPLY_AIR_RPM)
from .threadsafe_controller import ThreadSafeController

SUPPORT_SET_SPEED = 1

SPEED_BASIC_VENTILATION = 'basic'
SPEED_RATED_VENTILATION = 'rated'
SPEED_INTENSIVE_VENTILATION = 'intensive'
SPEED_MAXIMUM_FAN_SPEED = 'maximum'

_LOGGER = logging.getLogger(__name__)


class EasyControlsFanDevice(FanEntity):
    '''
    Represents a fan entity which controls the Helios device.
    '''

    def __init__(self, controller: ThreadSafeController):
        self.entity_description = FanEntityDescription(
            key="fan",
            name=controller.device_name
        )
        self._controller = controller
        self._fan_stage = None
        self._supply_air_rpm = None
        self._extract_air_rpm = None
        self._attributes = {}


    @property
    def device_state_attributes(self):
        '''
        Get the attributes of the fan.
        '''
        return self._attributes

    @property
    def unique_id(self):
        '''
        Get the unique ID of the fan.
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
        return SUPPORT_SET_SPEED

    @property
    def speed_list(self):
        '''
        Gets the supported speed list.
        '''
        return [
            SPEED_BASIC_VENTILATION,
            SPEED_RATED_VENTILATION,
            SPEED_INTENSIVE_VENTILATION,
            SPEED_MAXIMUM_FAN_SPEED,
        ]

    @property
    def speed(self):
        '''
        Gets the current speed.
        '''
        if self._fan_stage is None or self._fan_stage == 0:
            return None
        return self.speed_list[self._fan_stage - 1]

    @property
    def is_on(self):
        '''
        Gets the value indicates whether the fan is on.
        '''
        return ((not self._supply_air_rpm is None and self._supply_air_rpm > 0) or
                (not self._extract_air_rpm is None and self._extract_air_rpm > 0))

    async def async_set_speed(self, speed: str):
        '''
        Sets the speed of the fan

        Parameter
        ---------
        speed: str
            The speed of the fan.
        '''
        self._controller.set_variable(
            VARIABLE_OPERATING_MODE, 1, '{:d}'
        )  # operation mode = manual
        self._controller.set_variable(
            VARIABLE_FAN_STAGE, self.speed_list.index(speed) + 1, '{:d}'
        )

    async def async_turn_on(self, speed=None, **kwargs):
        '''
        Turns on the fan at the specific speed.
        '''
        self._controller.set_variable(
            VARIABLE_OPERATING_MODE, 1, '{:d}'
        )  # operation mode = manual
        if speed is None:
            speed = SPEED_RATED_VENTILATION

        self._controller.set_variable(
            VARIABLE_FAN_STAGE, self.speed_list.index(speed) + 1, '{:d}'
        )

    async def async_turn_off(self, **kwargs):
        '''
        Turns off the fan.
        '''
        self._controller.set_variable(
            VARIABLE_OPERATING_MODE, 1, '{:d}'
        )  # operation mode = manual
        self._controller.set_variable(VARIABLE_FAN_STAGE, 0, '{:d}')

    def start_party_mode(self, speed: str, duration: int):
        '''
        Starts the party mode of the fan. Set duration to 0
        to stop current party mode.

        speed: str
            The speed of the party mode.
        duration: int
            The duration of the party mode.
        '''
        if duration == 0:
            # stop current party mode
            self._controller.set_variable(
                VARIABLE_PARTY_MODE, 0, '{:d}'
            )
            return

        self._controller.set_variable(
            VARIABLE_PARTY_MODE_FAN_STAGE, self.speed_list.index(
                speed) + 1, '{:d}'
        )
        self._controller.set_variable(
            VARIABLE_PARTY_MODE_DURATION, duration, '{:d}'
        )
        self._controller.set_variable(
            VARIABLE_PARTY_MODE, 1, '{:d}'
        )

    async def async_update(self) -> None:
        '''
        Updates the fan device.
        '''
        self._supply_air_rpm = self._controller.get_variable(VARIABLE_SUPPLY_AIR_RPM, 8, float)
        self._extract_air_rpm = self._controller.get_variable(VARIABLE_EXTRACT_AIR_RPM, 8, float)
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

        self._attributes = {
            'preset_mode': preset_mode,
            'operation_mode': operation_mode
        }


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

    def handle_party_mode(call):
        duration = call.data.get('duration', 60)
        speed = call.data.get('speed', 'high')
        fan.start_party_mode(speed, duration)

    hass.services.async_register(DOMAIN, 'party_mode', handle_party_mode)

    _LOGGER.info('Setting up Helios EasyControls fan device completed.')
