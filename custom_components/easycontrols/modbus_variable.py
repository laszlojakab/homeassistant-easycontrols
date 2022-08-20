"""
The module contains Modbus variables.
"""
from typing import Any, Callable

# pylint: disable=too-few-public-methods
class ModbusVariable:
    """
    Represents a Modbus variable.
    """

    def __init__(
        self,
        name: str,
        size: int,
        get_converter: Callable[[str], Any] = None,
        set_converter: Callable[[Any], str] = None,
    ):
        """
        Initialize a new instance of `ModbusVariable` class.

        Args:
            name: The Modbus variable name.
            size: The length of the variable value.
            get_converter: The converter function to convert value received from device.
            set_converter:  The converter function to convert value send to device.
        """
        self.name = name
        self.size = size
        self.get_converter = get_converter
        self.set_converter = set_converter


# pylint: disable=too-few-public-methods
class BoolModbusVariable(ModbusVariable):
    """
    Represents a boolean type Modbus variable.
    """

    def __init__(self, name: str):
        """
        Initialize a new instance of `BoolModbusVariable` class.

        Args:
            name: The Modbus variable name
        """
        super().__init__(name, 1, lambda s: s == "1", lambda b: "1" if b else "0")


# pylint: disable=too-few-public-methods
class StrModbusVariable(ModbusVariable):
    """
    Represents a string type Modbus variable.
    """

    def __init__(self, name: str, size: int):
        """
        Initialize a new instance of `StrModbusVariable` class.

        Args
            name: The Modbus variable name.
            size: The variable value length.
        """
        super().__init__(name, size)


# pylint: disable=too-few-public-methods
class IntModbusVariable(ModbusVariable):
    """
    Represents an integer type Modbus variable.
    """

    def __init__(self, name: str, size: int):
        """
        Initialize a new instance of `IntModbusVariable` class.

        Args:
            name: The Modbus variable name.
            size: The variable value length.
        """
        super().__init__(name, size, int, str)


# pylint: disable=too-few-public-methods
class OperationHoursModbusVariable(ModbusVariable):
    """
    Represents an operation hours type Modbus variable.

    Operation hours value is in minutes, it converts to hours.
    """

    def __init__(self, name: str, size: int):
        """
        Initialize a new instance of `OperationHoursModbusVariable` class.

        Args:
            name: The Modbus variable name.
            size: The variable value length.
        """
        super().__init__(
            name, size, lambda x: round(int(x) / 60.0, 2), lambda x: str(x * 60)
        )


# pylint: disable=too-few-public-methods
class FloatModbusVariable(ModbusVariable):
    """
    Represents a float type Modbus variable.
    """

    def __init__(self, name: str, size: int):
        """
        Initialize a new instance of `FloatModbusVariable` class.

        Args:
            name: The Modbus variable name.
            size: The variable value length.
        """
        super().__init__(name, size, float, str)


# pylint: disable=too-few-public-methods
class FlagModbusVariable(ModbusVariable):
    """
    Represents a flag type Modbus variable.
    """

    def __init__(self, name: str, size: int, flag: int):
        """
        Initialize a new instance of `FlagModbusVariable`.

        Args:
            name: The Modbus variable name.
            size: The variable value length.
            flag: The flag value.
        """
        super().__init__(name, size, lambda x: (int(x) & flag) == flag)
