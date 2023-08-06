""" The sensor module for Helios Easy Controls integration. """
import logging
from typing import Any, Generic, TypeVar

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import HomeAssistantType
from typing_extensions import Self

from custom_components.easycontrols import get_coordinator
from custom_components.easycontrols.const import (
    ERRORS,
    INFOS,
    VARIABLE_ERRORS,
    VARIABLE_EXTRACT_AIR_FAN_STAGE,
    VARIABLE_EXTRACT_AIR_RPM,
    VARIABLE_FAN_STAGE,
    VARIABLE_HUMIDITY_EXTRACT_AIR,
    VARIABLE_INFOS,
    VARIABLE_OPERATION_HOURS_AFTERHEATER,
    VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
    VARIABLE_OPERATION_HOURS_PREHEATER,
    VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
    VARIABLE_PARTY_MODE_REMAINING_TIME,
    VARIABLE_PERCENTAGE_AFTERHEATER,
    VARIABLE_PERCENTAGE_FAN_SPEED,
    VARIABLE_PERCENTAGE_PREHEATER,
    VARIABLE_SOFTWARE_VERSION,
    VARIABLE_SUPPLY_AIR_FAN_STAGE,
    VARIABLE_SUPPLY_AIR_RPM,
    VARIABLE_TEMPERATURE_EXTRACT_AIR,
    VARIABLE_TEMPERATURE_OUTGOING_AIR,
    VARIABLE_TEMPERATURE_OUTSIDE_AIR,
    VARIABLE_TEMPERATURE_SUPPLY_AIR,
    VARIABLE_TEMPERATURE_FTF1,
    VARIABLE_TEMPERATURE_FTF2,
    VARIABLE_HUMIDITY_FTF1, 
    VARIABLE_HUMIDITY_FTF2,
    VARIABLE_WARNINGS,
    WARNINGS,
)
from custom_components.easycontrols.coordinator import EasyControlsDataUpdateCoordinator
from custom_components.easycontrols.modbus_variable import (
    IntModbusVariable,
    ModbusVariable,
)

_LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class EasyControlsAirFlowRateSensor(SensorEntity):
    """
    Represents a sensor which provides current airflow rate.
    """

    def __init__(self, coordinator: EasyControlsDataUpdateCoordinator):
        """
        Initialize a new instance of `EasyControlsAirFlowRateSensor` class.

        Args:
            coordinator:
                The coordinator instance.
        """
        self.entity_description = SensorEntityDescription(
            key="air_flow_rate",
            name=f"{coordinator.device_name} airflow rate",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:air-filter",
            native_unit_of_measurement="m³/h",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._coordinator = coordinator
        self._attr_unique_id = self._coordinator.mac + self.name
        self._percentage_fan_speed: int | None = None
        self._attr_device_info = DeviceInfo(
            connections={
                (device_registry.CONNECTION_NETWORK_MAC, self._coordinator.mac)
            }
        )

        def update_listener(variable: ModbusVariable[Any], value: Any):
            self._value_updated(variable, value)

        self._update_listener = update_listener

    async def async_added_to_hass(self: Self) -> None:
        self._coordinator.add_listener(
            VARIABLE_PERCENTAGE_FAN_SPEED, self._update_listener
        )
        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.remove_listener(
            VARIABLE_PERCENTAGE_FAN_SPEED, self._update_listener
        )
        return await super().async_will_remove_from_hass()

    @property
    def should_poll(self: Self) -> bool:
        return False

    def _value_updated(self: Self, variable: ModbusVariable[Any], value: Any):
        if variable == VARIABLE_PERCENTAGE_FAN_SPEED:
            self._percentage_fan_speed = value

        if self._percentage_fan_speed is None:
            self._attr_native_value = None
        else:
            self._attr_native_value = (
                self._coordinator.maximum_air_flow * self._percentage_fan_speed / 100.0
            )

        self._attr_available = self._attr_native_value is not None
        self.schedule_update_ha_state(False)


class EasyControlsEfficiencySensor(SensorEntity):
    """
    Represents a sensor which provides heat recover efficiency rate.
    For more details: https://www.engineeringtoolbox.com/heat-recovery-efficiency-d_201.html
    """

    def __init__(self, coordinator: EasyControlsDataUpdateCoordinator):
        """
        Initialize a new instance of `EasyControlsEfficiencySensor` class.

        Args:
            controller: The thread safe Helios Easy Controls controller.
        """
        self.entity_description = SensorEntityDescription(
            key="heat_recover_efficiency",
            name=f"{coordinator.device_name} heat recovery efficiency",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:percent",
            native_unit_of_measurement="%",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        self._coordinator = coordinator
        self._attr_unique_id = self._coordinator.mac + self.name
        self._outside_air_temperature: float | None = None
        self._supply_air_temperature: float | None = None
        self._extract_air_temperature: float | None = None
        self._attr_device_info = DeviceInfo(
            connections={
                (device_registry.CONNECTION_NETWORK_MAC, self._coordinator.mac)
            }
        )

        def update_listener(variable: ModbusVariable[Any], value: Any):
            self._value_updated(variable, value)

        self._update_listener = update_listener

    async def async_added_to_hass(self: Self) -> None:
        self._coordinator.add_listener(
            VARIABLE_TEMPERATURE_OUTSIDE_AIR, self._update_listener
        )
        self._coordinator.add_listener(
            VARIABLE_TEMPERATURE_SUPPLY_AIR, self._update_listener
        )
        self._coordinator.add_listener(
            VARIABLE_TEMPERATURE_EXTRACT_AIR, self._update_listener
        )
        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.remove_listener(
            VARIABLE_TEMPERATURE_OUTSIDE_AIR, self._update_listener
        )
        self._coordinator.remove_listener(
            VARIABLE_TEMPERATURE_SUPPLY_AIR, self._update_listener
        )
        self._coordinator.remove_listener(
            VARIABLE_TEMPERATURE_EXTRACT_AIR, self._update_listener
        )
        return await super().async_will_remove_from_hass()

    @property
    def should_poll(self: Self) -> bool:
        return False

    def _value_updated(self: Self, variable: ModbusVariable[Any], value: Any):
        if variable == VARIABLE_TEMPERATURE_OUTSIDE_AIR:
            self._outside_air_temperature = value
        elif variable == VARIABLE_TEMPERATURE_SUPPLY_AIR:
            self._supply_air_temperature = value
        elif variable == VARIABLE_TEMPERATURE_EXTRACT_AIR:
            self._extract_air_temperature = value

        if (
            self._outside_air_temperature is None
            or self._supply_air_temperature is None
            or self._extract_air_temperature is None
        ):
            self._attr_native_value = None
        else:
            if abs(self._extract_air_temperature - self._outside_air_temperature) > 0.5:
                self._attr_native_value = abs(
                    round(
                        (self._supply_air_temperature - self._outside_air_temperature)
                        / (
                            self._extract_air_temperature
                            - self._outside_air_temperature
                        )
                        * 100,
                        2,
                    )
                )
            else:
                self._attr_native_value = 0

        self._attr_available = self._attr_native_value is not None
        self.schedule_update_ha_state(False)


class EasyControlFlagSensor(SensorEntity):
    """
    Represents a sensor which provides a text value
    for a variable which is a flag based representation
    of multiple binary states.
    """

    def __init__(
        self,
        coordinator: EasyControlsDataUpdateCoordinator,
        variable: IntModbusVariable,
        flags: dict[int, str],
        description: SensorEntityDescription,
    ):
        """
        Initialize a new instance of `EasyControlsFlagSensor` class.

        Args:
            coordinator:
                The coordinator instance.
            variable:
                The Modbus flag variable.
            flags:
                The dictionary which holds the flag value as the key and
                the related text as the value.
            description:
                The sensor entity description.
        """
        self.entity_description = description
        self._coordinator = coordinator
        self._variable = variable
        self._flags = flags
        self._attr_unique_id = self._coordinator.mac + self.name
        self._attr_device_info = DeviceInfo(
            connections={
                (device_registry.CONNECTION_NETWORK_MAC, self._coordinator.mac)
            }
        )

        # pylint: disable=unused-argument
        def update_listener(variable: IntModbusVariable, value: int):
            self._value_updated(value)

        self._update_listener = update_listener

    async def async_added_to_hass(self: Self) -> None:
        self._coordinator.add_listener(self._variable, self._update_listener)
        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.remove_listener(self._variable, self._update_listener)
        return await super().async_will_remove_from_hass()

    @property
    def should_poll(self: Self) -> bool:
        return False

    def _value_updated(self: Self, value: int):
        self._attr_native_value = self._get_string(value)
        self._attr_available = self._attr_native_value is not None
        self.schedule_update_ha_state(False)

    def _get_string(self, value: int) -> str:
        """
        Converts the specified integer to its
        text representation.
        """
        if value is None:
            return None
        string: str = ""
        if value != 0:
            for item in self._flags.items():
                has_flag = (item[0] & value) == item[0]
                if has_flag:
                    if string != "":
                        string += "\n"
                    string += item[1]
        else:
            string = "-"

        return string


# pylint: disable=invalid-name
T = TypeVar("T")


class EasyControlsSensor(SensorEntity, Generic[T]):
    """
    Represents a sensor which provides
    a ModBus variable value.
    """

    def __init__(
        self: Self,
        coordinator: EasyControlsDataUpdateCoordinator,
        variable: ModbusVariable[T],
        description: SensorEntityDescription,
    ):
        """
        Initialize a new instance of `EasyControlsSensor` class.

        Args:
            coordinator:
                The coordinator instance.
            variable:
                The Modbus variable.
            description:
                The sensor description.
        """
        self.entity_description = description
        self._coordinator = coordinator
        self._variable = variable
        self._attr_unique_id = self._coordinator.mac + self.name
        self._attr_device_info = DeviceInfo(
            connections={
                (device_registry.CONNECTION_NETWORK_MAC, self._coordinator.mac)
            }
        )

        # pylint: disable=unused-argument
        def update_listener(variable: ModbusVariable, value: T):
            self._value_updated(value)

        self._update_listener = update_listener

    async def async_added_to_hass(self: Self) -> None:
        self._coordinator.add_listener(self._variable, self._update_listener)
        return await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.remove_listener(self._variable, self._update_listener)
        return await super().async_will_remove_from_hass()

    @property
    def should_poll(self: Self) -> bool:
        return False

    def _value_updated(self: Self, value: T):
        self._attr_native_value = value
        self._attr_available = self._attr_native_value is not None
        self.schedule_update_ha_state(False)


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """
    Setup of Helios Easy Controls sensors for the specified config_entry.

    Args:
        hass: The Home Assistant instance.
        config_entry: The config entry which is used to create sensors.
        async_add_entities: The callback which can be used to add new entities to Home Assistant.

    Returns:
        The value indicates whether the setup succeeded.
    """
    _LOGGER.info("Setting up Helios EasyControls sensors.")

    coordinator = get_coordinator(hass, config_entry.data[CONF_MAC])

    async_add_entities(
        [
            EasyControlsSensor(
                coordinator,
                VARIABLE_SOFTWARE_VERSION,
                SensorEntityDescription(
                    key="version",
                    name=f"{coordinator.device_name} software version",
                    icon="mdi:new-box",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_PERCENTAGE_FAN_SPEED,
                SensorEntityDescription(
                    key="fan_speed",
                    name=f"{coordinator.device_name} fan speed percentage",
                    icon="mdi:air-conditioner",
                    native_unit_of_measurement="%",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_FAN_STAGE,
                SensorEntityDescription(
                    key="fan_stage",
                    name=f"{coordinator.device_name} fan stage",
                    icon="mdi:air-conditioner",
                    native_unit_of_measurement=" ",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_EXTRACT_AIR_FAN_STAGE,
                SensorEntityDescription(
                    key="extract_air_fan_stage",
                    name=f"{coordinator.device_name} extract air fan stage",
                    icon="mdi:air-conditioner",
                    native_unit_of_measurement=" ",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_SUPPLY_AIR_FAN_STAGE,
                SensorEntityDescription(
                    key="supply_air_fan_stage",
                    name=f"{coordinator.device_name} supply air fan stage",
                    icon="mdi:air-conditioner",
                    native_unit_of_measurement=" ",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_TEMPERATURE_OUTSIDE_AIR,
                SensorEntityDescription(
                    key="outside_air_temperature",
                    name=f"{coordinator.device_name} outside air temperature",
                    icon="mdi:thermometer",
                    native_unit_of_measurement="°C",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_TEMPERATURE_SUPPLY_AIR,
                SensorEntityDescription(
                    key="supply_air_temperature",
                    name=f"{coordinator.device_name} supply air temperature",
                    icon="mdi:thermometer",
                    native_unit_of_measurement="°C",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_TEMPERATURE_EXTRACT_AIR,
                SensorEntityDescription(
                    key="extract_air_temperature",
                    name=f"{coordinator.device_name} extract air temperature",
                    icon="mdi:thermometer",
                    native_unit_of_measurement="°C",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_TEMPERATURE_OUTGOING_AIR,
                SensorEntityDescription(
                    key="outgoing_air_temperature",
                    name=f"{coordinator.device_name} outgoing air temperature",
                    icon="mdi:thermometer",
                    native_unit_of_measurement="°C",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_EXTRACT_AIR_RPM,
                SensorEntityDescription(
                    key="extract_air_rpm",
                    name=f"{coordinator.device_name} extract air rpm",
                    icon="mdi:rotate-3d-variant",
                    native_unit_of_measurement="rpm",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_SUPPLY_AIR_RPM,
                SensorEntityDescription(
                    key="supply_air_rpm",
                    name=f"{coordinator.device_name} supply air rpm",
                    icon="mdi:rotate-3d-variant",
                    native_unit_of_measurement="rpm",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_HUMIDITY_EXTRACT_AIR,
                SensorEntityDescription(
                    key="extract_air_relative_humidity",
                    name=f"{coordinator.device_name} extract air relative humidity",
                    icon="mdi:water-percent",
                    native_unit_of_measurement="%",
                    device_class=SensorDeviceClass.HUMIDITY,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_PARTY_MODE_REMAINING_TIME,
                SensorEntityDescription(
                    key="party_mode_remaining_time",
                    name=f"{coordinator.device_name} party mode remaining time",
                    icon="mdi:clock",
                    native_unit_of_measurement="min",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
                SensorEntityDescription(
                    key="supply_air_fan_operation_hours",
                    name=f"{coordinator.device_name} supply air fan operation hours",
                    icon="mdi:history",
                    native_unit_of_measurement="h",
                    state_class=SensorStateClass.TOTAL_INCREASING,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
                SensorEntityDescription(
                    key="extract_air_fan_operation_hours",
                    name=f"{coordinator.device_name} extract air fan operation hours",
                    icon="mdi:history",
                    native_unit_of_measurement="h",
                    state_class=SensorStateClass.TOTAL_INCREASING,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_OPERATION_HOURS_PREHEATER,
                SensorEntityDescription(
                    key="preheater_operation_hours",
                    name=f"{coordinator.device_name} preheater operation hours",
                    icon="mdi:history",
                    native_unit_of_measurement="h",
                    state_class=SensorStateClass.TOTAL_INCREASING,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_PERCENTAGE_PREHEATER,
                SensorEntityDescription(
                    key="preheater_percentage",
                    name=f"{coordinator.device_name} preheater percentage",
                    icon="mdi:thermometer-lines",
                    native_unit_of_measurement="%",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_OPERATION_HOURS_AFTERHEATER,
                SensorEntityDescription(
                    key="after_heater_operation_hours",
                    name=f"{coordinator.device_name} afterheater operation hours",
                    icon="mdi:history",
                    native_unit_of_measurement="h",
                    state_class=SensorStateClass.TOTAL_INCREASING,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_PERCENTAGE_AFTERHEATER,
                SensorEntityDescription(
                    key="afterheater_percentage",
                    name=f"{coordinator.device_name} afterheater percentage",
                    icon="mdi:thermometer-lines",
                    native_unit_of_measurement="%",
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlFlagSensor(
                coordinator,
                VARIABLE_ERRORS,
                ERRORS,
                SensorEntityDescription(
                    key="ERRORS",
                    name=f"{coordinator.device_name} errors",
                    icon="mdi:alert-circle",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlFlagSensor(
                coordinator,
                VARIABLE_WARNINGS,
                WARNINGS,
                SensorEntityDescription(
                    key="WARNINGS",
                    name=f"{coordinator.device_name} warnings",
                    icon="mdi:alert-circle-outline",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlFlagSensor(
                coordinator,
                VARIABLE_INFOS,
                INFOS,
                SensorEntityDescription(
                    key="INFORMATION",
                    name=f"{coordinator.device_name} information",
                    icon="mdi:information-outline",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_TEMPERATURE_FTF1,
                SensorEntityDescription(
                    key='ftf1_temperature',
                    name=f'{coordinator.device_name} ftf1 temperature',
                    icon='mdi:thermometer',
                    native_unit_of_measurement='°C',
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_TEMPERATURE_FTF2,
                SensorEntityDescription(
                    key='ftf2_temperature',
                    name=f'{coordinator.device_name} ftf2 temperature',
                    icon='mdi:thermometer',
                    native_unit_of_measurement='°C',
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_HUMIDITY_FTF1,
                SensorEntityDescription(
                    key='ftf1_relative_humidity',
                    name=f'{coordinator.device_name} ftf1 relative humidity',
                    icon='mdi:water-percent',
                    native_unit_of_measurement='%',
                    device_class=SensorDeviceClass.HUMIDITY,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            ),
            EasyControlsSensor(
                coordinator,
                VARIABLE_HUMIDITY_FTF2,
                SensorEntityDescription(
                    key='ftf2_relative_humidity',
                    name=f'{coordinator.device_name} ftf2 relative humidity',
                    icon='mdi:water-percent',
                    native_unit_of_measurement='%',
                    device_class=SensorDeviceClass.HUMIDITY,
                    state_class=SensorStateClass.MEASUREMENT,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            EasyControlsAirFlowRateSensor(coordinator),
            EasyControlsEfficiencySensor(coordinator),
        ]
    )

    _LOGGER.info("Setting up Helios EasyControls sensors completed.")
    return True
