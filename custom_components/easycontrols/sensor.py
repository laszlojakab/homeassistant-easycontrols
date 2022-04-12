''' The sensor module for Helios Easy Controls integration. '''
import logging
from typing import Dict

from homeassistant.components.sensor import (STATE_CLASS_MEASUREMENT,
                                             STATE_CLASS_TOTAL_INCREASING,
                                             SensorEntity,
                                             SensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_MAC, DEVICE_CLASS_HUMIDITY,
                                 DEVICE_CLASS_TEMPERATURE)
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
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
from .modbus_variable import IntModbusVariable, ModbusVariable
from .controller import Controller

_LOGGER = logging.getLogger(__name__)


class EasyControlsAirFlowRateSensor(SensorEntity):
    '''
    Represents a sensor which provides current airflow rate.
    '''

    def __init__(self, controller: Controller):
        '''
        Initialize a new instance of EasyControlsAirFlowRateSensor class.

        Parameters
        ----------
        controller: Controller
            The thread safe Helios Easy Controls controller instance.
        '''
        self.entity_description = SensorEntityDescription(
            key='air_flow_rate',
            name=f'{controller.device_name} airflow rate',
            state_class=STATE_CLASS_MEASUREMENT,
            icon='mdi:air-filter',
            native_unit_of_measurement='m³/h',
            entity_category=EntityCategory.DIAGNOSTIC
        )
        self._controller = controller
        self._attr_unique_id = self._controller.mac + self.name

    async def async_update(self) -> None:
        '''
        Updates the sensor value.
        '''
        percentage_fan_speed = await self._controller.get_variable(VARIABLE_PERCENTAGE_FAN_SPEED)

        if percentage_fan_speed is None:
            self._attr_native_value = None
        else:
            self._attr_native_value = self._controller.maximum_air_flow * \
                percentage_fan_speed / 100.0

        self._attr_available = self._attr_native_value is not None

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)


class EasyControlsEfficiencySensor(SensorEntity):
    '''
    Represents a sensor which provides heat recover efficiency rate.
    For more details: https://www.engineeringtoolbox.com/heat-recovery-efficiency-d_201.html
    '''

    def __init__(self, controller: Controller):
        '''
        Initialize a new instance of EasyControlsEfficiencySensor class.

        Parameters
        ----------
        controller: Controller
            The thread safe Helios Easy Controls controller.
        '''
        self.entity_description = SensorEntityDescription(
            key='heat_recover_efficiency',
            name=f'{controller.device_name} heat recovery efficiency',
            state_class=STATE_CLASS_MEASUREMENT,
            icon='mdi:percent',
            native_unit_of_measurement='%',
            entity_category=EntityCategory.DIAGNOSTIC
        )
        self._controller = controller
        self._attr_unique_id = self._controller.mac + self.name

    async def async_update(self) -> None:
        '''
        Updates the sensor value.
        '''
        outside_air_temperature = await self._controller.get_variable(
            VARIABLE_TEMPERATURE_OUTSIDE_AIR
        )
        supply_air_temperature = await self._controller.get_variable(
            VARIABLE_TEMPERATURE_SUPPLY_AIR
        )
        extract_air_temperature = await self._controller.get_variable(
            VARIABLE_TEMPERATURE_EXTRACT_AIR
        )

        if extract_air_temperature is None or \
           outside_air_temperature is None or \
           supply_air_temperature is None:
            self._attr_native_value = None
        else:
            if abs(extract_air_temperature - outside_air_temperature) > 0.5:
                self._attr_native_value = abs(
                    round(
                        (supply_air_temperature - outside_air_temperature)
                        / (extract_air_temperature - outside_air_temperature)
                        * 100,
                        2,
                    )
                )
            else:
                self._attr_native_value = 0

        self._attr_available = self._attr_native_value is not None

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)


class EasyControlFlagSensor(SensorEntity):
    '''
    Represents a sensor which provides a text value
    for a variable which is a flag based representation
    of multiple binary states.
    '''

    def __init__(
        self,
        controller: Controller,
        variable: IntModbusVariable,
        flags: Dict[int, str],
        description: SensorEntityDescription
    ):
        '''
        Initialize a new instance of EasyControlsFlagSensor class.

        Parameters
        controller: Controller
            The thread safe Helios Easy Controls controller.
        variable: IntModbusVariable
            The Modbus flag variable.
        flags: Dict[int, str]
            The dictionary which holds the flag value as the key
            and the related text as the value.
        description: homeassistant.components.sensor.SensorEntityDescription
            The sensor description.
        '''
        self.entity_description = description
        self._controller = controller
        self._variable = variable
        self._flags = flags
        self._attr_unique_id = self._controller.mac + self.name

    async def async_update(self) -> None:
        '''
        Updates the sensor value.
        '''
        self._attr_native_value = self._get_string(
            await self._controller.get_variable(self._variable)
        )
        self._attr_available = self._attr_native_value is not None

    def _get_string(self, value: int) -> str:
        '''
        Converts the specified integer to its
        text representation
        '''
        if value is None:
            return None
        string: str = ''
        if value != 0:
            for item in self._flags.items():
                has_flag = (item[0] & value) == item[0]
                if has_flag:
                    if string != '':
                        string += '\n'
                    string += item[1]
        else:
            string = '-'

        return string

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)


class EasyControlsSensor(SensorEntity):
    '''
    Represents a sensor which provides
    a ModBus variable value.
    '''

    def __init__(
        self,
        controller: Controller,
        variable: ModbusVariable,
        description: SensorEntityDescription
    ):
        '''
        Initialize a new instance of EasyControlSensor class.

        Parameters
        ----------
        controller: Controller
            The thread safe Helios Easy Controls controller.
        variable: ModbusVariable
            The Modbus variable.
        description: homeassistant.components.sensor.SensorEntityDescription
            The sensor description.
        '''
        self.entity_description = description
        self._controller = controller
        self._variable = variable
        self._attr_unique_id = self._controller.mac + self.name

    async def async_update(self):
        '''
        Updates the sensor value.
        '''
        self._attr_native_value = await self._controller.get_variable(self._variable)
        self._attr_available = self._attr_native_value is not None

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)


class EasyControlsVersionSensor(SensorEntity):
    '''
    Provides the software version of Helios device as a sensor.
    '''

    def __init__(
        self,
        controller: Controller,
        name: str
    ):
        '''
        Initialize a new instance of EasyControlVersionSensor class.

        Parameters
        ----------
        controller: Controller
            The thread safe Helios Easy Controls controller
        name: str
            The name of the sensor.
        '''
        self.entity_description = SensorEntityDescription(
            key='version',
            name=name,
            icon='mdi:new-box',
            entity_category=EntityCategory.DIAGNOSTIC
        )

        self._controller = controller
        self._attr_unique_id = self._controller.mac + self.name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return get_device_info(self._controller)

    async def async_update(self):
        '''
        Updates the sensor value.
        '''
        self._attr_native_value = self._controller.version
        self._attr_available = self._attr_native_value is not None


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
            SensorEntityDescription(
                key='fan_speed',
                name=f'{controller.device_name} fan speed percentage',
                icon='mdi:air-conditioner',
                native_unit_of_measurement='%',
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_FAN_STAGE,
            SensorEntityDescription(
                key='fan_stage',
                name=f'{controller.device_name} fan stage',
                icon='mdi:air-conditioner',
                native_unit_of_measurement=' ',
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_EXTRACT_AIR_FAN_STAGE,
            SensorEntityDescription(
                key='extract_air_fan_stage',
                name=f'{controller.device_name} extract air fan stage',
                icon='mdi:air-conditioner',
                native_unit_of_measurement=' ',
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_SUPPLY_AIR_FAN_STAGE,
            SensorEntityDescription(
                key='supply_air_fan_stage',
                name=f'{controller.device_name} supply air fan stage',
                icon='mdi:air-conditioner',
                native_unit_of_measurement=' ',
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_OUTSIDE_AIR,
            SensorEntityDescription(
                key='outside_air_temperature',
                name=f'{controller.device_name} outside air temperature',
                icon='mdi:thermometer',
                native_unit_of_measurement='°C',
                device_class=DEVICE_CLASS_TEMPERATURE,
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_SUPPLY_AIR,
            SensorEntityDescription(
                key='supply_air_temperature',
                name=f'{controller.device_name} supply air temperature',
                icon='mdi:thermometer',
                native_unit_of_measurement='°C',
                device_class=DEVICE_CLASS_TEMPERATURE,
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_EXTRACT_AIR,
            SensorEntityDescription(
                key='extract_air_temperature',
                name=f'{controller.device_name} extract air temperature',
                icon='mdi:thermometer',
                native_unit_of_measurement='°C',
                device_class=DEVICE_CLASS_TEMPERATURE,
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_OUTGOING_AIR,
            SensorEntityDescription(
                key='outgoing_air_temperature',
                name=f'{controller.device_name} outgoing air temperature',
                icon='mdi:thermometer',
                native_unit_of_measurement='°C',
                device_class=DEVICE_CLASS_TEMPERATURE,
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_EXTRACT_AIR_RPM,
            SensorEntityDescription(
                key='extract_air_rpm',
                name=f'{controller.device_name} extract air rpm',
                icon='mdi:rotate-3d-variant',
                native_unit_of_measurement='rpm',
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_SUPPLY_AIR_RPM,
            SensorEntityDescription(
                key='supply_air_rpm',
                name=f'{controller.device_name} supply air rpm',
                icon='mdi:rotate-3d-variant',
                native_unit_of_measurement='rpm',
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_HUMIDITY_EXTRACT_AIR,
            SensorEntityDescription(
                key='extract_air_relative_humidity',
                name=f'{controller.device_name} extract air relative humidity',
                icon='mdi:water-percent',
                native_unit_of_measurement='%',
                device_class=DEVICE_CLASS_HUMIDITY,
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PARTY_MODE_REMAINING_TIME,
            SensorEntityDescription(
                key='party_mode_remaining_time',
                name=f'{controller.device_name} party mode remaining time',
                icon='mdi:clock',
                native_unit_of_measurement='min',
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
            SensorEntityDescription(
                key='supply_air_fan_operation_hours',
                name=f'{controller.device_name} supply air fan operation hours',
                icon='mdi:history',
                native_unit_of_measurement='h',
                state_class=STATE_CLASS_TOTAL_INCREASING,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
            SensorEntityDescription(
                key='extract_air_fan_operation_hours',
                name=f'{controller.device_name} extract air fan operation hours',
                icon='mdi:history',
                native_unit_of_measurement='h',
                state_class=STATE_CLASS_TOTAL_INCREASING,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_PREHEATER,
            SensorEntityDescription(
                key='preheater_operation_hours',
                name=f'{controller.device_name} preheater operation hours',
                icon='mdi:history',
                native_unit_of_measurement='h',
                state_class=STATE_CLASS_TOTAL_INCREASING,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PERCENTAGE_PREHEATER,
            SensorEntityDescription(
                key='preheater_percentage',
                name=f'{controller.device_name} preheater percentage',
                icon='mdi:thermometer-lines',
                native_unit_of_measurement='%',
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_AFTERHEATER,
            SensorEntityDescription(
                key='after_heater_operation_hours',
                name=f'{controller.device_name} afterheater operation hours',
                icon='mdi:history',
                native_unit_of_measurement='h',
                state_class=STATE_CLASS_TOTAL_INCREASING,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PERCENTAGE_AFTERHEATER,
            SensorEntityDescription(
                key='afterheater_percentage',
                name=f'{controller.device_name} afterheater percentage',
                icon='mdi:thermometer-lines',
                native_unit_of_measurement='%',
                state_class=STATE_CLASS_MEASUREMENT,
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_ERRORS,
            ERRORS,
            SensorEntityDescription(
                key='ERRORS',
                name=f'{controller.device_name} errors',
                icon='mdi:alert-circle',
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_WARNINGS,
            WARNINGS,
            SensorEntityDescription(
                key='WARNINGS',
                name=f'{controller.device_name} warnings',
                icon='mdi:alert-circle-outline',
                entity_category=EntityCategory.DIAGNOSTIC
            )
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_INFOS,
            INFOS,
            SensorEntityDescription(
                key='INFORMATION',
                name=f'{controller.device_name} information',
                icon='mdi:information-outline',
                entity_category=EntityCategory.DIAGNOSTIC
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
