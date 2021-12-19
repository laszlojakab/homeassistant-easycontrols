# pylint: disable=bad-continuation
''' The sensor module for Helios Easy Controls integration. '''
import logging
from typing import Any, Callable, Dict

from homeassistant.components.sensor import (STATE_CLASS_MEASUREMENT,
                                             STATE_CLASS_TOTAL_INCREASING,
                                             SensorEntity,
                                             SensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_MAC, DEVICE_CLASS_HUMIDITY,
                                 DEVICE_CLASS_TEMPERATURE)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType

from . import get_controller, get_device_info
from .const import (ERRORS, INFOS, VARIABLE_ERRORS,
                    VARIABLE_EXTRACT_AIR_FAN_STAGE, VARIABLE_EXTRACT_AIR_RPM,
                    VARIABLE_FAN_STAGE, VARIABLE_HUMIDITY_EXTRACT_AIR,
                    VARIABLE_INFOS, VARIABLE_OPERATION_HOURS_AFTERHEATER,
                    VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
                    VARIABLE_OPERATION_HOURS_PREHEATER,
                    VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
                    VARIABLE_PARTY_MODE_REMAINING_TIME,
                    VARIABLE_PERCENTAGE_AFTERHEATER,
                    VARIABLE_PERCENTAGE_FAN_SPEED,
                    VARIABLE_PERCENTAGE_PREHEATER,
                    VARIABLE_SUPPLY_AIR_FAN_STAGE, VARIABLE_SUPPLY_AIR_RPM,
                    VARIABLE_TEMPERATURE_EXTRACT_AIR,
                    VARIABLE_TEMPERATURE_OUTGOING_AIR,
                    VARIABLE_TEMPERATURE_OUTSIDE_AIR,
                    VARIABLE_TEMPERATURE_SUPPLY_AIR, VARIABLE_WARNINGS,
                    WARNINGS)
from .threadsafe_controller import ThreadSafeController

_LOGGER = logging.getLogger(__name__)


class EasyControlsAirFlowRateSensor(SensorEntity):
    '''
    Represents a sensor which provides current airflow rate.
    '''

    def __init__(self, controller: ThreadSafeController):
        '''
        Initialize a new instance of EasyControlsAirFlowRateSensor class.

        Parameters
        ----------
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller instance.
        '''
        self.entity_description = SensorEntityDescription(
            key='air_flow_rate',
            name=f'{controller.device_name} airflow rate',
            state_class=STATE_CLASS_MEASUREMENT,
            icon='mdi:air-filter',
            native_unit_of_measurement='m³/h'
        )
        self._controller = controller
        self._state = 'unavailable'

    async def async_update(self) -> None:
        '''
        Updates the sensor value.
        '''
        percentage_fan_speed = self._controller.get_variable(
            VARIABLE_PERCENTAGE_FAN_SPEED, 8, float
        )

        if percentage_fan_speed is None:
            self._state = 'unavailable'
        else:
            self._state = self._controller.maximum_air_flow * percentage_fan_speed / 100.0

    @property
    def unique_id(self) -> str:
        '''
        Gets the unique ID of the sensor.
        '''
        return self._controller.mac + self.name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)

    @property
    def state(self) -> float:
        '''
        Gets the state of the sensor.
        '''
        return self._state


class EasyControlsEfficiencySensor(SensorEntity):
    '''
    Represents a sensor which provides heat recover efficiency rate.
    For more details: https://www.engineeringtoolbox.com/heat-recovery-efficiency-d_201.html
    '''

    def __init__(self, controller: ThreadSafeController):
        '''
        Initialize a new instance of EasyControlsEfficiencySensor class.

        Parameters
        ----------
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller.
        '''
        self.entity_description = SensorEntityDescription(
            key='heat_recover_efficiency',
            name=f'{controller.device_name} heat recovery efficiency',
            state_class=STATE_CLASS_MEASUREMENT,
            icon='mdi:percent',
            native_unit_of_measurement='%'
        )
        self._controller = controller
        self._state = 'unavailable'

    async def async_update(self) -> None:
        '''
        Updates the sensor value.
        '''
        outside_air_temperature = self._controller.get_variable(
            VARIABLE_TEMPERATURE_OUTSIDE_AIR, 8, float
        )
        supply_air_temperature = self._controller.get_variable(
            VARIABLE_TEMPERATURE_SUPPLY_AIR, 8, float
        )
        extract_air_temperature = self._controller.get_variable(
            VARIABLE_TEMPERATURE_EXTRACT_AIR, 8, float
        )

        if extract_air_temperature is None or \
           outside_air_temperature is None or \
           supply_air_temperature is None:
            self._state = 'unavailable'
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
    def unique_id(self) -> str:
        '''
        Gets the unique ID of the sensor.
        '''
        return self._controller.mac + self.name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)

    @property
    def state(self) -> int:
        '''
        Gets the state of the sensor.
        '''
        return self._state


class EasyControlFlagSensor(SensorEntity):
    '''
    Represents a sensor which provides a text value
    for a variable which is a flag based representation
    of multiple binary states.
    '''

    def __init__(
        self,
        controller: ThreadSafeController,
        variable_name: str,
        flags: Dict[int, str],
        description: SensorEntityDescription
    ):
        '''
        Initialize a new instance of EasyControlsFlagSensor class.

        Parameters
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller.
        variable_name: str
            The ModBus flag variable name.
        flags: Dict[int, str]
            The dictionary which holds the flag value as the key
            and the related text as the value.
        description: homeassistant.components.sensor.SensorEntityDescription
            The sensor description.
        '''
        self.entity_description = description
        self._controller = controller
        self._variable = variable_name
        self._state = 'unavailable'
        self._flags = flags

    async def async_update(self) -> None:
        '''
        Updates the sensor value.
        '''
        value = self._controller.get_variable(
            self._variable, 32, int
        )
        self._state = 'unavailable' if value is None else self._get_string(
            value
        )

    def _get_string(self, value: int) -> str:
        '''
        Converts the specified integer to its
        text representation
        '''
        string = ''
        if value != 0:
            for item in self._flags.items():
                has_flag = (item[0] & value) == item[0]
                if has_flag:
                    if string != '':
                        string += '\n'
                    string += item[1]
        return string

    @property
    def unique_id(self) -> str:
        '''
        Gets the unique ID of the sensor.
        '''
        return self._controller.mac + self.name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)

    @property
    def state(self) -> str:
        '''
        Gets the state of the sensor.
        '''
        return self._state


class EasyControlsSensor(SensorEntity):
    '''
    Represents a sensor which provides
    a ModBus variable value.
    '''

    def __init__(
        self,
        controller: ThreadSafeController,
        variable_name: str,
        variable_size: int,
        converter: Callable[[str], Any],
        description: SensorEntityDescription
    ):
        '''
        Initialize a new instance of EasyControlSensor class.

        Parameters
        ----------
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller.
        variable_name: str
            The ModBus variable name.
        variable_size: int
            The ModBus variable value size.
        converter: Callable[[str], Any]
            The converter function which converts the string value
            received from ModBus to sensor value.
        description: homeassistant.components.sensor.SensorEntityDescription
            The sensor description.
        '''
        self.entity_description = description
        self._controller = controller
        self._variable_name = variable_name
        self._converter = converter
        self._variable_size = variable_size
        self._state = 'unavailable'

    async def async_update(self):
        '''
        Updates the sensor value.
        '''
        self._state = self._controller.get_variable(
            self._variable_name,
            self._variable_size,
            self._converter
        )

    @property
    def unique_id(self) -> str:
        '''
        Gets the unique ID of the sensor.
        '''
        return self._controller.mac + self.name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)

    @property
    def state(self) -> Any:
        '''
        Gets the state of the sensor.
        '''
        return self._state


class EasyControlsVersionSensor(SensorEntity):
    '''
    Provides the software version of Helios device as a sensor.
    '''

    def __init__(
        self,
        controller: ThreadSafeController,
        name: str
    ):
        '''
        Initialize a new instance of EasyControlVersionSensor class.

        Parameters
        ----------
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller
        name: str
            The name of the sensor.
        '''
        self.entity_description = SensorEntityDescription(
            key='version',
            name=name,
            icon='mdi:new-box'
        )

        self._controller = controller

    @property
    def unique_id(self) -> str:
        '''
        Gets the unique ID of the sensor.
        '''
        return self._controller.mac + self.name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)

    @property
    def state(self) -> str:
        '''
        Gets the state of the sensor.
        '''
        return self._controller.version or 'unavailable'


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> bool:
    '''
    Setup of Helios Easy Controls sensors for the specified config_entry.

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
    _LOGGER.info('Setting up Helios EasyControls sensors.')

    controller = get_controller(hass, config_entry.data[CONF_MAC])

    async_add_entities([
        EasyControlsVersionSensor(
            controller,
            f'{controller.device_name} software version'
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PERCENTAGE_FAN_SPEED,
            8,
            float,
            SensorEntityDescription(
                key='fan_speed',
                name=f'{controller.device_name} fan speed percentage',
                icon='mdi:air-conditioner',
                native_unit_of_measurement='%',
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_FAN_STAGE,
            1,
            int,
            SensorEntityDescription(
                key='fan_stage',
                name=f'{controller.device_name} fan stage',
                icon='mdi:air-conditioner',
                native_unit_of_measurement=' ',
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_EXTRACT_AIR_FAN_STAGE,
            1,
            int,
            SensorEntityDescription(
                key='extract_air_fan_stage',
                name=f'{controller.device_name} extract air fan stage',
                icon='mdi:air-conditioner',
                native_unit_of_measurement=' ',
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_SUPPLY_AIR_FAN_STAGE,
            1,
            int,
            SensorEntityDescription(
                key='supply_air_fan_stage',
                name=f'{controller.device_name} supply air fan stage',
                icon='mdi:air-conditioner',
                native_unit_of_measurement=' ',
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_OUTSIDE_AIR,
            8,
            float,
            SensorEntityDescription(
                key='outside_air_temperature',
                name=f'{controller.device_name} outside air temperature',
                icon='mdi:thermometer',
                native_unit_of_measurement='°C',
                device_class=DEVICE_CLASS_TEMPERATURE,
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_SUPPLY_AIR,
            8,
            float,
            SensorEntityDescription(
                key='supply_air_temperature',
                name=f'{controller.device_name} supply air temperature',
                icon='mdi:thermometer',
                native_unit_of_measurement='°C',
                device_class=DEVICE_CLASS_TEMPERATURE,
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_EXTRACT_AIR,
            8,
            float,
            SensorEntityDescription(
                key='extract_air_temperature',
                name=f'{controller.device_name} extract air temperature',
                icon='mdi:thermometer',
                native_unit_of_measurement='°C',
                device_class=DEVICE_CLASS_TEMPERATURE,
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_OUTGOING_AIR,
            8,
            float,
            SensorEntityDescription(
                key='outgoing_air_temperature',
                name=f'{controller.device_name} outgoing air temperature',
                icon='mdi:thermometer',
                native_unit_of_measurement='°C',
                device_class=DEVICE_CLASS_TEMPERATURE,
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_EXTRACT_AIR_RPM,
            8,
            int,
            SensorEntityDescription(
                key='extract_air_rpm',
                name=f'{controller.device_name} extract air rpm',
                icon='mdi:rotate-3d-variant',
                native_unit_of_measurement='rpm',
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_SUPPLY_AIR_RPM,
            8,
            int,
            SensorEntityDescription(
                key='supply_air_rpm',
                name=f'{controller.device_name} supply air rpm',
                icon='mdi:rotate-3d-variant',
                native_unit_of_measurement='rpm',
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_HUMIDITY_EXTRACT_AIR,
            8,
            int,
            SensorEntityDescription(
                key='extract_air_relative_humidity',
                name=f'{controller.device_name} extract air relative humidity',
                icon='mdi:water-percent',
                native_unit_of_measurement='%',
                device_class=DEVICE_CLASS_HUMIDITY,
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PARTY_MODE_REMAINING_TIME,
            8,
            int,
            SensorEntityDescription(
                key='party_mode_remaining_time',
                name=f'{controller.device_name} party mode remaining time',
                icon='mdi:clock',
                native_unit_of_measurement='min'
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
            10,
            lambda x: round(float(x) / 60.0, 2),
            SensorEntityDescription(
                key='supply_air_fan_operation_hours',
                name=f'{controller.device_name} supply air fan operation hours',
                icon='mdi:history',
                native_unit_of_measurement='h',
                state_class=STATE_CLASS_TOTAL_INCREASING
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
            10,
            lambda x: round(float(x) / 60.0, 2),
            SensorEntityDescription(
                key='extract_air_fan_operation_hours',
                name=f'{controller.device_name} extract air fan operation hours',
                icon='mdi:history',
                native_unit_of_measurement='h',
                state_class=STATE_CLASS_TOTAL_INCREASING
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_PREHEATER,
            10,
            lambda x: round(float(x) / 60.0, 2),
            SensorEntityDescription(
                key='preheater_operation_hours',
                name=f'{controller.device_name} preheater operation hours',
                icon='mdi:history',
                native_unit_of_measurement='h',
                state_class=STATE_CLASS_TOTAL_INCREASING
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PERCENTAGE_PREHEATER,
            4,
            float,
            SensorEntityDescription(
                key='preheater_percentage',
                name=f'{controller.device_name} preheater percentage',
                icon='mdi:thermometer-lines',
                native_unit_of_measurement='%',
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_AFTERHEATER,
            10,
            lambda x: round(float(x) / 60.0, 2),
            SensorEntityDescription(
                key='after_heater_operation_hours',
                name=f'{controller.device_name} afterheater operation hours',
                icon='mdi:history',
                native_unit_of_measurement='h',
                state_class=STATE_CLASS_TOTAL_INCREASING
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PERCENTAGE_AFTERHEATER,
            4,
            float,
            SensorEntityDescription(
                key='afterheater_percentage',
                name=f'{controller.device_name} afterheater percentage',
                icon='mdi:thermometer-lines',
                native_unit_of_measurement='%',
                state_class=STATE_CLASS_MEASUREMENT
            )
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_ERRORS,
            ERRORS,
            SensorEntityDescription(
                key='ERRORS',
                name=f'{controller.device_name} errors',
                icon='mdi:alert-circle'
            )
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_WARNINGS,
            WARNINGS,
            SensorEntityDescription(
                key='WARNINGS',
                name=f'{controller.device_name} warnings',
                icon='mdi:alert-circle-outline'
            )
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_INFOS,
            INFOS,
            SensorEntityDescription(
                key='INFORMATION',
                name=f'{controller.device_name} information',
                icon='mdi:information-outline'
            )
        ),
        EasyControlsAirFlowRateSensor(
            controller
        ),
        EasyControlsEfficiencySensor(
            controller
        )
    ])

    _LOGGER.info('Setting up Helios EasyControls sensors completed.')
    return True
