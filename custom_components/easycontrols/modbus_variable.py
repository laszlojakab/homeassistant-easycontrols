"""The module contains Modbus variables."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final, Self


@dataclass
class ModbusVariable[TModBusVariableValue]:
    """Represents a Modbus variable."""

    name: Final[str]
    """ The Modbus variable name. """

    size: Final[int]
    """ The length of the variable value. """

    get_converter: Final[Callable[[str], TModBusVariableValue] | None] = None
    """ The converter function to convert value received from device. """

    set_converter: Final[Callable[[TModBusVariableValue], str] | None] = None
    """ The converter function to convert value send to device. """

    def __repr__(self) -> str:
        """
        Returns a string representation of the ModbusVariable object.

        The string representation includes the name and size of the variable.

        Returns
          The string representation of the ModbusVariable object.

        """
        return f"{self.name} [{self.size}]"

    def __lt__(self: Self, other: Self) -> bool:
        """Implements the less than operator for the ModbusVariable class."""
        return self.name < other.name


class BoolModbusVariable(ModbusVariable[bool]):
    """Represents a boolean type Modbus variable."""

    def __init__(self: Self, name: str):
        """
        Initialize a new instance of `BoolModbusVariable` class.

        Args:
            name: The Modbus variable name

        """
        super().__init__(name, 1, lambda s: s == "1", lambda b: "1" if b else "0")


class StrModbusVariable(ModbusVariable[str]):
    """Represents a string type Modbus variable."""

    def __init__(self: Self, name: str, size: int):
        """
        Initialize a new instance of `StrModbusVariable` class.

        Args:
            name: The Modbus variable name.
            size: The variable value length.

        """
        super().__init__(name, size)


class IntModbusVariable(ModbusVariable[int]):
    """Represents an integer type Modbus variable."""

    def __init__(self: Self, name: str, size: int):
        """
        Initialize a new instance of `IntModbusVariable` class.

        Args:
            name: The Modbus variable name.
            size: The variable value length.

        """
        super().__init__(name, size, int, str)


class OperationHoursModbusVariable(ModbusVariable[float]):
    """
    Represents an operation hours type Modbus variable.

    Operation hours value is in minutes, it converts to hours.
    """

    def __init__(self: Self, name: str, size: int):
        """
        Initialize a new instance of `OperationHoursModbusVariable` class.

        Args:
            name: The Modbus variable name.
            size: The variable value length.

        """
        super().__init__(name, size, lambda x: round(int(x) / 60.0, 2), lambda x: str(x * 60))


class FloatModbusVariable(ModbusVariable[float]):
    """Represents a float type Modbus variable."""

    def __init__(self: Self, name: str, size: int):
        """
        Initialize a new instance of `FloatModbusVariable` class.

        Args:
            name: The Modbus variable name.
            size: The variable value length.

        """
        super().__init__(name, size, float, str)


class FlagModbusVariable(ModbusVariable[bool]):
    """Represents a flag type Modbus variable."""

    def __init__(self: Self, name: str, size: int, flag: int):
        """
        Initialize a new instance of `FlagModbusVariable`.

        Args:
            name: The Modbus variable name.
            size: The variable value length.
            flag: The flag value.

        """
        super().__init__(name, size, lambda x: (int(x) & flag) == flag)
