# pylint: disable=bad-continuation
''' The sensor module for Helios Easy Controls integration. '''
import logging
from typing import Any, Callable, Dict

from homeassistant.components.sensor import (STATE_CLASS_MEASUREMENT,
                                             STATE_CLASS_TOTAL_INCREASING,
                                             SensorEntity)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (CONF_HOST, CONF_NAME, DEVICE_CLASS_HUMIDITY,
                                 DEVICE_CLASS_TEMPERATURE)
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType

from .const import (DATA_CONTROLLER, DOMAIN, ERRORS, INFOS, VARIABLE_ERRORS,
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

    def __init__(self, controller: ThreadSafeController, device_name: str):
        '''
        Initialize a new instance of EasyControlsAirFlowRateSensor class.

        Parameters
        ----------
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller instance.
        '''
        self._controller = controller
        self._name = f'{device_name} airflow rate'
        self._device_name = device_name
        self._state = 'unavailable'
        self._attr_state_class = STATE_CLASS_MEASUREMENT

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
        return self._controller.mac + self._name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return {
            'connections': {(device_registry.CONNECTION_NETWORK_MAC, self._controller.mac)},
            'identifiers': {(DOMAIN, self._controller.serial_number)},
            'name': self._device_name,
            'manufacturer': 'Helios',
            'model': self._controller.model,
            'sw_version': self._controller.version
        }

    @property
    def should_poll(self) -> bool:
        '''
        Gets the value indicates whether the sensor value should be polled.
        '''
        return True

    @property
    def name(self) -> str:
        '''
        Gets the name of the sensor.
        '''
        return self._name

    @property
    def state(self) -> float:
        '''
        Gets the state of the sensor.
        '''
        return self._state

    @property
    def icon(self) -> str:
        '''
        Gets the icon of the sensor.
        '''
        return 'mdi:air-filter'

    @property
    def unit_of_measurement(self) -> str:
        '''
        Gets the unit of measurement of the sensor.
        '''
        return 'm³/h'


class EasyControlsEfficiencySensor(SensorEntity):
    '''
    Represents a sensor which provides heat recover efficiency rate.
    For more details: https://www.engineeringtoolbox.com/heat-recovery-efficiency-d_201.html
    '''

    def __init__(self, controller: ThreadSafeController, device_name: str):
        '''
        Initialize a new instance of EasyControlsEfficiencySensor class.

        Parameters
        ----------
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller.
        name: str
            The name of the device.
        '''
        self._controller = controller
        self._name = f'{device_name} heat recovery efficiency'
        self._device_name = device_name
        self._state = 'unavailable'
        self._attr_state_class = STATE_CLASS_MEASUREMENT

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
        return self._controller.mac + self._name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return {
            'connections': {(device_registry.CONNECTION_NETWORK_MAC, self._controller.mac)},
            'identifiers': {(DOMAIN, self._controller.serial_number)},
            'name': self._device_name,
            'manufacturer': 'Helios',
            'model': self._controller.model,
            'sw_version': self._controller.version
        }

    @property
    def should_poll(self) -> bool:
        '''
        Gets the value indicates whether the sensor value should be polled.
        '''
        return True

    @property
    def name(self) -> str:
        '''
        Gets the name of the sensor.
        '''
        return self._name

    @property
    def state(self) -> int:
        '''
        Gets the state of the sensor.
        '''
        return self._state

    @property
    def icon(self) -> str:
        '''
        Gets the icon of the sensor.
        '''
        return 'mdi:percent'

    @property
    def unit_of_measurement(self):
        '''
        Gets the unit of measurement of the sensor.
        '''
        return '%'


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
        name: str,
        device_name: str,
        icon: str
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
        name: str
            The name of the sensor.
        device_name: str
            The Helios device name.
        icon: str
            The icon of the sensor.
        '''
        self._controller = controller
        self._variable = variable_name
        self._name = name
        self._device_name = device_name
        self._icon = icon
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
        return self._controller.mac + self._name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return {
            'connections': {(device_registry.CONNECTION_NETWORK_MAC, self._controller.mac)},
            'identifiers': {(DOMAIN, self._controller.serial_number)},
            'name': self._device_name,
            'manufacturer': 'Helios',
            'model': self._controller.model,
            'sw_version': self._controller.version
        }

    @property
    def should_poll(self) -> bool:
        '''
        Gets the value indicates whether the sensor value should be polled.
        '''
        return True

    @property
    def name(self) -> str:
        '''
        Gets the name of the sensor.
        '''
        return self._name

    @property
    def state(self) -> str:
        '''
        Gets the state of the sensor.
        '''
        return self._state

    @property
    def icon(self) -> str:
        '''
        Gets the icon of the sensor.
        '''
        return self._icon


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
        name: str,
        device_name: str,
        icon: str,
        device_class: str = None,
        unit_of_measurement: str = None,
        state_class: str = None
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
        name: str
            The name of the sensor
        device_name: str
            The name of the device.
        icon: str
            The icon of the sensor.
        device_class: str
            The device class of the sensor.
        unit_of_measurement: str
            The unit of measurement of the sensor value.
        state_class: str
            The state class.
        '''
        self._controller = controller
        self._variable_name = variable_name
        self._converter = converter
        self._variable_size = variable_size
        self._name = name
        self._device_name = device_name
        self._icon = icon
        self._unit_of_measurement = unit_of_measurement
        self._state_class = state_class
        self._state = 'unavailable'
        self._attr_state_class = state_class
        self._device_class = device_class

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
        return self._controller.mac + self._name

    @property
    def unit_of_measurement(self) -> str:
        '''
        Gets the unit of measurement of the sensor.
        '''
        return self._unit_of_measurement

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return {
            'connections': {(device_registry.CONNECTION_NETWORK_MAC, self._controller.mac)},
            'identifiers': {(DOMAIN, self._controller.serial_number)},
            'name': self._device_name,
            'manufacturer': 'Helios',
            'model': self._controller.model,
            'sw_version': self._controller.version
        }

    @property
    def should_poll(self) -> bool:
        '''
        Gets the value indicates whether the sensor value should be polled.
        '''
        return True

    @property
    def name(self) -> str:
        '''
        Gets the name of the sensor.
        '''
        return self._name

    @property
    def state(self) -> Any:
        '''
        Gets the state of the sensor.
        '''
        return self._state

    @property
    def icon(self) -> str:
        '''
        Gets the icon of the sensor.
        '''
        return self._icon

    @property
    def device_class(self) -> str:
        '''
        Gets the device class of the sensor.
        '''
        return self._device_class


class EasyControlsVersionSensor(SensorEntity):
    '''
    Provides the software version of Helios device as a sensor.
    '''

    def __init__(
        self,
        controller: ThreadSafeController,
        name: str,
        device_name: str
    ):
        '''
        Initialize a new instance of EasyControlVersionSensor class.

        Parameters
        ----------
        controller: ThreadSafeController
            The thread safe Helios Easy Controls controller
        name: str
            The name of the sensor.
        device_name: str
            The name of the device.
        '''
        self._controller = controller
        self._name = name
        self._device_name = device_name

    @property
    def unique_id(self) -> str:
        '''
        Gets the unique ID of the sensor.
        '''
        return self._controller.mac + self._name

    @property
    def device_info(self) -> DeviceInfo:
        '''
        Gets the device information.
        '''
        return {
            'connections': {(device_registry.CONNECTION_NETWORK_MAC, self._controller.mac)},
            'identifiers': {(DOMAIN, self._controller.serial_number)},
            'name': self._device_name,
            'manufacturer': 'Helios',
            'model': self._controller.model,
            'sw_version': self._controller.version
        }

    @property
    def should_poll(self) -> bool:
        '''
        Gets the value indicates whether the sensor value should be polled.
        '''
        return True

    @property
    def name(self) -> str:
        '''
        Gets the name of the sensor.
        '''
        return self._name

    @property
    def state(self) -> str:
        '''
        Gets the state of the sensor.
        '''
        return self._controller.version or 'unavailable'

    @property
    def icon(self) -> str:
        '''
        Gets the icon of the sensor.
        '''
        return 'mdi:new-box'


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

    name = config_entry.data[CONF_NAME]
    controller = hass.data[DOMAIN][DATA_CONTROLLER][config_entry.data[CONF_HOST]]

    async_add_entities([
        EasyControlsVersionSensor(
            controller,
            f'{name} software version',
            name
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PERCENTAGE_FAN_SPEED,
            8,
            float,
            f'{name} fan speed percentage',
            name,
            'mdi:air-conditioner',
            None,
            '%'
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_FAN_STAGE,
            1,
            int,
            f'{name} fan stage',
            name,
            'mdi:air-conditioner',
            None,
            ' '
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_EXTRACT_AIR_FAN_STAGE,
            1,
            int,
            f'{name} extract air fan stage',
            name,
            'mdi:air-conditioner',
            None,
            ' '
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_SUPPLY_AIR_FAN_STAGE,
            1,
            int,
            f'{name} supply air fan stage',
            name,
            'mdi:air-conditioner',
            None,
            ' '
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_OUTSIDE_AIR,
            8,
            float,
            f'{name} outside air temperature',
            name,
            'mdi:thermometer',
            DEVICE_CLASS_TEMPERATURE,
            '°C',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_SUPPLY_AIR,
            8,
            float,
            f'{name} supply air temperature',
            name,
            'mdi:thermometer',
            DEVICE_CLASS_TEMPERATURE,
            '°C',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_EXTRACT_AIR,
            8,
            float,
            f'{name} extract air temperature',
            name,
            'mdi:thermometer',
            DEVICE_CLASS_TEMPERATURE,
            '°C',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_TEMPERATURE_OUTGOING_AIR,
            8,
            float,
            f'{name} outgoing air temperature',
            name,
            'mdi:thermometer',
            DEVICE_CLASS_TEMPERATURE,
            '°C',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_EXTRACT_AIR_RPM,
            8,
            int,
            f'{name} extract air rpm',
            name,
            'mdi:rotate-3d-variant',
            None,
            'rpm',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_SUPPLY_AIR_RPM,
            8,
            int,
            f'{name} supply air rpm',
            name,
            'mdi:rotate-3d-variant',
            None,
            'rpm',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_HUMIDITY_EXTRACT_AIR,
            8,
            int,
            f'{name} extract air relative humidity',
            name,
            'mdi:water-percent',
            DEVICE_CLASS_HUMIDITY,
            '%',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PARTY_MODE_REMAINING_TIME,
            8,
            int,
            f'{name} party mode remaining time',
            name,
            'mdi:clock',
            None,
            'min'
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
            10,
            lambda x: round(float(x) / 60.0, 2),
            f'{name} supply air fan operation hours',
            name,
            'mdi:history',
            None,
            'h'
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
            10,
            lambda x: round(float(x) / 60.0, 2),
            f'{name} extract air fan operation hours',
            name,
            'mdi:history',
            None,
            'h'
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_PREHEATER,
            10,
            lambda x: round(float(x) / 60.0, 2),
            f'{name} preheater operation hours',
            name,
            'mdi:history',
            None,
            'h',
            STATE_CLASS_TOTAL_INCREASING
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PERCENTAGE_PREHEATER,
            4,
            float,
            f'{name} preheater percentage',
            name,
            'mdi:thermometer-lines',
            None,
            '%',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_OPERATION_HOURS_AFTERHEATER,
            10,
            lambda x: round(float(x) / 60.0, 2),
            f'{name} afterheater operation hours',
            name,
            'mdi:history',
            None,
            'h',
            STATE_CLASS_TOTAL_INCREASING
        ),
        EasyControlsSensor(
            controller,
            VARIABLE_PERCENTAGE_AFTERHEATER,
            4,
            float,
            f'{name} afterheater percentage',
            name,
            'mdi:thermometer-lines',
            None,
            '%',
            STATE_CLASS_MEASUREMENT
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_ERRORS,
            ERRORS,
            f'{name} errors',
            name,
            'mdi:alert-circle'
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_WARNINGS,
            WARNINGS,
            f'{name} warnings',
            name,
            'mdi:alert-circle-outline'
        ),
        EasyControlFlagSensor(
            controller,
            VARIABLE_INFOS,
            INFOS,
            f'{name} information',
            name,
            'mdi:information-outline'
        ),
        EasyControlsAirFlowRateSensor(
            controller,
            name
        ),
        EasyControlsEfficiencySensor(
            controller,
            name
        )
    ])

    _LOGGER.info('Setting up Helios EasyControls sensors completed.')
    return True
