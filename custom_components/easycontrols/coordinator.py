"""Module of `EasyControlsDataUpdateCoordinator` class."""

import asyncio
import logging
import re
from asyncio import Lock
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import datetime, timedelta
from queue import PriorityQueue
from typing import Any, Final, Self, overload

import async_timeout
from eazyctrl import AsyncEazyController
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from custom_components.easycontrols.const import (
    VARIABLE_ARTICLE_DESCRIPTION,
    VARIABLE_BYPASS,
    VARIABLE_BYPASS_EXTRACT_AIR_TEMPERATURE,
    VARIABLE_BYPASS_FROM_DAY,
    VARIABLE_BYPASS_FROM_MONTH,
    VARIABLE_BYPASS_OUTDOOR_AIR_TEMPERATURE,
    VARIABLE_BYPASS_TO_DAY,
    VARIABLE_BYPASS_TO_MONTH,
    VARIABLE_ERRORS,
    VARIABLE_EXTERNAL_CO2_1,
    VARIABLE_EXTERNAL_CO2_2,
    VARIABLE_EXTERNAL_CO2_3,
    VARIABLE_EXTERNAL_CO2_4,
    VARIABLE_EXTERNAL_CO2_5,
    VARIABLE_EXTERNAL_CO2_6,
    VARIABLE_EXTERNAL_CO2_7,
    VARIABLE_EXTERNAL_CO2_8,
    VARIABLE_EXTERNAL_FTF_HUMIDITY_1,
    VARIABLE_EXTERNAL_FTF_HUMIDITY_2,
    VARIABLE_EXTERNAL_FTF_HUMIDITY_3,
    VARIABLE_EXTERNAL_FTF_HUMIDITY_4,
    VARIABLE_EXTERNAL_FTF_HUMIDITY_5,
    VARIABLE_EXTERNAL_FTF_HUMIDITY_6,
    VARIABLE_EXTERNAL_FTF_HUMIDITY_7,
    VARIABLE_EXTERNAL_FTF_HUMIDITY_8,
    VARIABLE_EXTERNAL_FTF_TEMPERATURE_1,
    VARIABLE_EXTERNAL_FTF_TEMPERATURE_2,
    VARIABLE_EXTERNAL_FTF_TEMPERATURE_3,
    VARIABLE_EXTERNAL_FTF_TEMPERATURE_4,
    VARIABLE_EXTERNAL_FTF_TEMPERATURE_5,
    VARIABLE_EXTERNAL_FTF_TEMPERATURE_6,
    VARIABLE_EXTERNAL_FTF_TEMPERATURE_7,
    VARIABLE_EXTERNAL_FTF_TEMPERATURE_8,
    VARIABLE_EXTERNAL_VOC_1,
    VARIABLE_EXTERNAL_VOC_2,
    VARIABLE_EXTERNAL_VOC_3,
    VARIABLE_EXTERNAL_VOC_4,
    VARIABLE_EXTERNAL_VOC_5,
    VARIABLE_EXTERNAL_VOC_6,
    VARIABLE_EXTERNAL_VOC_7,
    VARIABLE_EXTERNAL_VOC_8,
    VARIABLE_EXTRACT_AIR_FAN_STAGE,
    VARIABLE_EXTRACT_AIR_RPM,
    VARIABLE_FAN_STAGE,
    VARIABLE_FILTER_CHANGE,
    VARIABLE_HUMIDITY_EXTRACT_AIR,
    VARIABLE_INFO_FILTER_CHANGE,
    VARIABLE_INFOS,
    VARIABLE_MAC_ADDRESS,
    VARIABLE_OPERATING_MODE,
    VARIABLE_OPERATION_HOURS_AFTERHEATER,
    VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
    VARIABLE_OPERATION_HOURS_PREHEATER,
    VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
    VARIABLE_PARTY_MODE,
    VARIABLE_PARTY_MODE_DURATION,
    VARIABLE_PARTY_MODE_FAN_STAGE,
    VARIABLE_PARTY_MODE_REMAINING_TIME,
    VARIABLE_PERCENTAGE_AFTERHEATER,
    VARIABLE_PERCENTAGE_FAN_SPEED,
    VARIABLE_PERCENTAGE_PREHEATER,
    VARIABLE_SERIAL_NUMBER,
    VARIABLE_SOFTWARE_VERSION,
    VARIABLE_STANDBY_MODE,
    VARIABLE_STANDBY_MODE_FAN_STAGE,
    VARIABLE_STANDBY_MODE_REMAINING_TIME,
    VARIABLE_SUPPLY_AIR_FAN_STAGE,
    VARIABLE_SUPPLY_AIR_RPM,
    VARIABLE_TEMPERATURE_EXTRACT_AIR,
    VARIABLE_TEMPERATURE_OUTGOING_AIR,
    VARIABLE_TEMPERATURE_OUTSIDE_AIR,
    VARIABLE_TEMPERATURE_SUPPLY_AIR,
    VARIABLE_WARNINGS,
)
from custom_components.easycontrols.modbus_variable import (
    BoolModbusVariable,
    FlagModbusVariable,
    FloatModbusVariable,
    IntModbusVariable,
    ModbusVariable,
    OperationHoursModbusVariable,
    StrModbusVariable,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class QueueItem:
    """Represents a queue item of the coordinator."""

    variable: Final[ModbusVariable]
    """The modbus variable in the queue."""
    refresh_interval: Final[timedelta]
    """The refresh interval of the variable."""

    def __lt__(self: Self, other: object) -> bool:
        """Less than operator, to be able to use QueueItem in PriorityQueue."""
        if isinstance(other, QueueItem):
            return self.variable.name < other.variable.name

        raise NotImplementedError(f"`<` not implemented for {type(other)}")


class EasyControlsDataUpdateCoordinator:
    """
    Responsible to handle querying data from Helios device.

    Helios device can only be queried in a single thread and takes some time
    (some hundred milliseconds) to get a ModBus variable value.

    This class builds an internal queue to get ModBus variable values
    without collision (querying multiple variables same time) and also supports to add
    the updating of a variable to start of the queue to make the update of variable
    as soon as possible.
    """

    def __init__(self: Self, hass: HomeAssistant, device_name: str, host: str):
        """
        Initialize a new instance of `EasyControlsDataUpdaterCoordinator` class.

        Args:
            hass:
                The Home Assistant instance.
            device_name:
                The name of the device.
            host:
                The host name of the device.

        """
        self.host: Final[str] = host
        """ The host name of the device. """
        self._eazyctrl = AsyncEazyController(host)
        """ The eazy controller to communicate with the device. """
        self._lock = Lock()
        """ The lock to prevent race condition. """
        self._hass = hass
        """ The Home Assistant instance. """
        self._variable_queue = PriorityQueue()
        """
        The variable queue which contains the variables need to be queried for any given moment.
        """
        self._mac: str
        """ The MAC address of the device. """
        self._serial_number: str
        """ The serial number of the device. """
        self._article_description: str
        """ The software version of the device. """
        self._version: str
        """ The article description of the device. """
        self._device_name: str = device_name
        """ The name of the device. """
        self._maximum_air_flow: float
        """ The maximum air flow rate of the device. """

        self._dispose_schedule_items: CALLBACK_TYPE | None = None
        self._disposed: bool = False

        self._variable_listeners: dict[str, list[Callable[[ModbusVariable, Any], None]]] = {}
        """
        The dictionary of variable listeners. The key is the variable name,
        the value is the functions to call when the given variable value updated
        (not necessarily changed)
        """

        for queue_item in [
            # Variables updated at most every 5 seconds.
            QueueItem(variable, timedelta(seconds=5))
            for variable in [
                VARIABLE_FAN_STAGE,
                VARIABLE_WARNINGS,
                VARIABLE_TEMPERATURE_SUPPLY_AIR,
                VARIABLE_TEMPERATURE_OUTSIDE_AIR,
                VARIABLE_TEMPERATURE_OUTGOING_AIR,
                VARIABLE_TEMPERATURE_EXTRACT_AIR,
                VARIABLE_SUPPLY_AIR_RPM,
                VARIABLE_SUPPLY_AIR_FAN_STAGE,
                VARIABLE_STANDBY_MODE,
                VARIABLE_STANDBY_MODE_FAN_STAGE,
                VARIABLE_STANDBY_MODE_REMAINING_TIME,
                VARIABLE_SOFTWARE_VERSION,
                VARIABLE_PERCENTAGE_PREHEATER,
                VARIABLE_PERCENTAGE_FAN_SPEED,
                VARIABLE_PERCENTAGE_AFTERHEATER,
                VARIABLE_PARTY_MODE_REMAINING_TIME,
                VARIABLE_PARTY_MODE_FAN_STAGE,
                VARIABLE_PARTY_MODE_DURATION,
                VARIABLE_PARTY_MODE,
                VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN,
                VARIABLE_OPERATION_HOURS_PREHEATER,
                VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN,
                VARIABLE_OPERATION_HOURS_AFTERHEATER,
                VARIABLE_OPERATING_MODE,
                VARIABLE_INFOS,
                VARIABLE_INFO_FILTER_CHANGE,
                VARIABLE_HUMIDITY_EXTRACT_AIR,
                VARIABLE_FILTER_CHANGE,
                VARIABLE_EXTRACT_AIR_RPM,
                VARIABLE_EXTRACT_AIR_FAN_STAGE,
                VARIABLE_ERRORS,
                VARIABLE_BYPASS,
                VARIABLE_STANDBY_MODE_REMAINING_TIME,
                VARIABLE_BYPASS_EXTRACT_AIR_TEMPERATURE,
                VARIABLE_BYPASS_OUTDOOR_AIR_TEMPERATURE,
                VARIABLE_BYPASS_FROM_DAY,
                VARIABLE_BYPASS_FROM_MONTH,
                VARIABLE_BYPASS_TO_DAY,
                VARIABLE_BYPASS_TO_MONTH,
                VARIABLE_EXTERNAL_FTF_HUMIDITY_1,
                VARIABLE_EXTERNAL_FTF_HUMIDITY_2,
                VARIABLE_EXTERNAL_FTF_HUMIDITY_3,
                VARIABLE_EXTERNAL_FTF_HUMIDITY_4,
                VARIABLE_EXTERNAL_FTF_HUMIDITY_5,
                VARIABLE_EXTERNAL_FTF_HUMIDITY_6,
                VARIABLE_EXTERNAL_FTF_HUMIDITY_7,
                VARIABLE_EXTERNAL_FTF_HUMIDITY_8,
                VARIABLE_EXTERNAL_FTF_TEMPERATURE_1,
                VARIABLE_EXTERNAL_FTF_TEMPERATURE_2,
                VARIABLE_EXTERNAL_FTF_TEMPERATURE_3,
                VARIABLE_EXTERNAL_FTF_TEMPERATURE_4,
                VARIABLE_EXTERNAL_FTF_TEMPERATURE_5,
                VARIABLE_EXTERNAL_FTF_TEMPERATURE_6,
                VARIABLE_EXTERNAL_FTF_TEMPERATURE_7,
                VARIABLE_EXTERNAL_FTF_TEMPERATURE_8,
                VARIABLE_EXTERNAL_CO2_1,
                VARIABLE_EXTERNAL_CO2_2,
                VARIABLE_EXTERNAL_CO2_3,
                VARIABLE_EXTERNAL_CO2_4,
                VARIABLE_EXTERNAL_CO2_5,
                VARIABLE_EXTERNAL_CO2_6,
                VARIABLE_EXTERNAL_CO2_7,
                VARIABLE_EXTERNAL_CO2_8,
                VARIABLE_EXTERNAL_VOC_1,
                VARIABLE_EXTERNAL_VOC_2,
                VARIABLE_EXTERNAL_VOC_3,
                VARIABLE_EXTERNAL_VOC_4,
                VARIABLE_EXTERNAL_VOC_5,
                VARIABLE_EXTERNAL_VOC_6,
                VARIABLE_EXTERNAL_VOC_7,
                VARIABLE_EXTERNAL_VOC_8,
            ]
        ]:
            # We put the queue item with priority 1 (high) to the queue.
            self._variable_queue.put((1, queue_item))

    async def init(self: Self) -> Self:
        """
        Initializes the coordinator and starts polling the variables
        based on the content of the queue.
        """
        self._mac = await self.get_variable(VARIABLE_MAC_ADDRESS)
        self._serial_number = await self.get_variable(VARIABLE_SERIAL_NUMBER)
        self._article_description = await self.get_variable(VARIABLE_ARTICLE_DESCRIPTION)
        self._version = await self.get_variable(VARIABLE_SOFTWARE_VERSION)
        self._maximum_air_flow = float(re.findall(r"\d+", self._article_description)[0])

        await self._process_queue()

        return self

    @property
    def device_name(self) -> str:
        """Gets the name of the device."""
        return self._device_name

    @property
    def mac(self) -> str:
        """Gets the MAC address of the device."""
        return self._mac

    @property
    def serial_number(self) -> str:
        """Gets the serial number of the device."""
        return self._serial_number

    @property
    def article_description(self) -> str:
        """Gets the article description of the device."""
        return self._article_description

    @property
    def version(self) -> str:
        """Gets the software version of the device."""
        return self._version

    @property
    def maximum_air_flow(self) -> float:
        """Gets the maximum air flow rate of the device."""
        return self._maximum_air_flow

    def schedule_update(self: Self, variable: ModbusVariable) -> None:
        """
        Schedules the specified variable for update.
        This means that the variable is put to the start of the queue and
        updated as soon as possible.

        Args:
            variable:
                The variable to update.

        """
        # We put the item to queue with priority 1 (high) to update as soon as possible.
        self._variable_queue.put((1, QueueItem(variable, timedelta())))

    def add_listener[TModBusVariableValue](
        self: Self,
        variable: ModbusVariable[TModBusVariableValue],
        listener: Callable[[ModbusVariable, TModBusVariableValue], None],
    ) -> None:
        """
        Adds a listener which will be called when the specified variable value has been updated.

        Args:
            variable:
                The variable to listen for value update.
            listener:
                The callback which will be called when the variable updated.

        """
        listeners_of_variable = self._variable_listeners.get(variable.name)
        if not listeners_of_variable:
            self._variable_listeners[variable.name] = listeners_of_variable = []

        listeners_of_variable.append(listener)

    def remove_listener[TModBusVariableValue](
        self: Self,
        variable: ModbusVariable[TModBusVariableValue],
        listener: Callable[[ModbusVariable, TModBusVariableValue], None],
    ) -> None:
        """
        Removes a listener which was called when the specified variable value had been updated.

        Args:
            variable:
                The variable to listen for value update.
            listener:
                The callback to listen no more.

        """
        listeners_of_variable = self._variable_listeners.get(variable.name)
        if not listeners_of_variable:
            return

        listeners_of_variable.remove(listener)

    def unload(self: Self) -> None:
        """
        Stops the processing of queue and removes all
        listeners.

        **NOTE**: the started callbacks of putting variables
        back to queue can still run but they won't
        have any effect because we set in a private
        flag to prevent putting them back to queue.

        So the actual full cleanup occurs at maximum
        5 minutes.
        """
        self._disposed = True
        if self._dispose_schedule_items is not None:
            self._dispose_schedule_items()
            self._variable_listeners.clear()

    async def _process_queue(self) -> None:  # noqa: C901
        """
        Processes the items in the update queue. Queries the device for the given
        variables and calls the listeners whenever a value for a variable received.F
        """
        queue_items_to_update_later: list[QueueItem] = []

        while not self._variable_queue.empty():
            queue_item: QueueItem = self._variable_queue.get_nowait()[1]
            try:
                # We allow maximum 5 seconds to update a single variable
                async with async_timeout.timeout(5):
                    listeners_of_variable = self._variable_listeners.get(queue_item.variable.name)
                    # If there is a listener for the variable we get the value from the device.
                    if listeners_of_variable and len(listeners_of_variable) > 0:
                        _LOGGER.debug("Updating variable %s.", queue_item.variable)
                        try:
                            value = await self.get_variable(queue_item.variable)
                        except Exception:
                            _LOGGER.exception("Failed to get variable value")
                            value = None

                        # After receiving the value we send the value to the listeners.
                        for listener in listeners_of_variable:
                            listener(queue_item.variable, value)
                    else:
                        # If no listener for a variable we won't get the value of it.
                        _LOGGER.debug(
                            "No listener for variable %s, skipping.",
                            queue_item.variable,
                        )
            except asyncio.exceptions.TimeoutError:
                _LOGGER.warning("Timeout while updating variable: %s", queue_item.variable)

            # If the queue item refresh interval is not zero
            # we have to update again so we collect it into
            # the `queue_items_to_update_later` list.
            if queue_item.refresh_interval != timedelta():
                queue_items_to_update_later.append(queue_item)

        # After we processed all the items from the queue we execute schedule
        # an update for every queue item defined in the `queue_items_to_update_later` list.
        # To do so we put the items back to the queue after the given `refresh_interval` timedelta.
        for queue_item in queue_items_to_update_later:

            def get_put_queue_item_back_callback(
                queue_item: QueueItem,
            ) -> Callable[[datetime], Coroutine[Any, Any, None] | None]:
                @callback
                def put_queue_item_back(exec_time: datetime) -> None:  # noqa: ARG001
                    if not self._disposed:
                        self._variable_queue.put((10, queue_item))

                return put_queue_item_back

            # We won't collect these callbacks, the actual cleanup
            # will be done in 5 minutes when this callback fired.
            async_call_later(
                self._hass,
                queue_item.refresh_interval,
                get_put_queue_item_back_callback(queue_item),
            )

        # Finally we process the queue again after 1 seconds.
        # It won't do anything if nothing in the queue after a seconds.
        @callback
        async def process_queue_again(exec_time: datetime) -> None:  # noqa: ARG001
            await self._process_queue()

        self._dispose_schedule_items = async_call_later(
            self._hass,
            timedelta(seconds=1),
            process_queue_again,
        )

    @overload
    async def get_variable(self: Self, variable: BoolModbusVariable) -> bool: ...

    @overload
    async def get_variable(self: Self, variable: FlagModbusVariable) -> int: ...

    @overload
    async def get_variable(self: Self, variable: FloatModbusVariable) -> float: ...

    @overload
    async def get_variable(self: Self, variable: IntModbusVariable) -> int: ...

    @overload
    async def get_variable(self: Self, variable: OperationHoursModbusVariable) -> int: ...

    @overload
    async def get_variable(self: Self, variable: StrModbusVariable) -> str: ...

    async def get_variable[T](self: Self, variable: ModbusVariable) -> T:
        """
        Gets the specified variable value from the Helios device.

        Args:
            variable:
                The variable value to get.

        Returns:
            The requested variable value.

        """
        async with self._lock:
            _LOGGER.debug("Getting %s.", variable.name)
            value = await self._eazyctrl.get_variable(
                variable.name, variable.size, variable.get_converter
            )
            _LOGGER.debug("%s value: %s", variable.name, value)
            return value

    @overload
    async def set_variable(self: Self, variable: BoolModbusVariable, value: bool) -> bool: ...

    @overload
    async def set_variable(self: Self, variable: FlagModbusVariable, value: int) -> bool: ...

    @overload
    async def set_variable(self: Self, variable: FloatModbusVariable, value: float) -> bool: ...

    @overload
    async def set_variable(self: Self, variable: IntModbusVariable, value: int) -> bool: ...

    @overload
    async def set_variable(
        self: Self, variable: OperationHoursModbusVariable, value: int
    ) -> bool: ...

    @overload
    async def set_variable(self: Self, variable: StrModbusVariable, value: str) -> bool: ...

    async def set_variable[T](self: Self, variable: ModbusVariable, value: T) -> bool:
        """
        Sets the specified variable value on the Helios device.

        Args:
            variable: The variable to set on Helios device.
            value: The value to set on Helios device.

        Returns:
            True if setting of variable succeeded otherwise False.

        """
        async with self._lock:
            _LOGGER.debug("Setting %s to %s.", variable.name, value)
            return await self._eazyctrl.set_variable(variable.name, value, variable.set_converter)


async def create_coordinator(
    hass: HomeAssistant, device_name: str, host: str
) -> EasyControlsDataUpdateCoordinator:
    """Creates and initializes a coordinator instance."""
    coordinator = EasyControlsDataUpdateCoordinator(hass, device_name, host)
    return await coordinator.init()
