'''
The module contains Modbus variables.
'''
from typing import Any, Callable


class ModbusVariable():
    '''
    Represents a Modbus variable.
    '''

    def __init__(
        self,
        name: str,
        size: int,
        get_converter: Callable[[str], Any] = None,
        set_converter: Callable[[Any], str] = None
    ):
        '''
        Initialize a new instance of ModbusVariable class.

        Parameters
        ----------
        name: str
            The Modbus variable name.
        size: int
            The length of the variable value.
        get_converter: Callable[[str], Any]
            The converter function to convert value received from device.
        set_converter: Callable[[Any], str]
            The converter function to convert value send to device.
        '''
        self.name = name
        self.size = size
        self.get_converter = get_converter
        self.set_converter = set_converter


class BoolModbusVariable(ModbusVariable):
    '''
    Represents a boolean type Modbus variable.
    '''

    def __init__(self, name: str):
        '''
        Initialize a new instance of BoolModbusVariable class.

        Parameters
        ----------
        name: str
            The Modbus variable name
        '''
        super().__init__(name, 1, lambda s: s == '1', lambda b: '1' if b else '0')


class StrModbusVariable(ModbusVariable):
    '''
    Represents a string type Modbus variable.
    '''

    def __init__(self, name: str, size: int):
        '''
        Initialize a new instance of StrModbusVariable class.


        Parameters
        ----------
        name: str
            The Modbus variable name.
        size: int
            The variable value length.
        '''
        super().__init__(name, size)


class IntModbusVariable(ModbusVariable):
    '''
    Represents an integer type Modbus variable.
    '''

    def __init__(self, name: str, size: int):
        '''
        Initialize a new instance of IntModbusVariable class.

        Parameters
        ----------
        name: str
            The Modbus variable name.
        size: int
            The variable value length.
        '''
        super().__init__(name, size, int, str)


class OperationHoursModbusVariable(ModbusVariable):
    '''
    Represents an operation hours type Modbus variable.

    Operation hours value is in minutes, it converts to hours.
    '''

    def __init__(self, name: str, size: int):
        '''
        Initialize a new instance of OperationHoursModbusVariable class.

        Parameters
        ----------
        name: str
            The Modbus variable name.
        size: int
            The variable value length.
        '''
        super().__init__(name, size, lambda x: round(int(x) / 60.0, 2), lambda x: str(x * 60))


class FloatModbusVariable(ModbusVariable):
    '''
    Represents a float type Modbus variable.
    '''

    def __init__(self, name: str, size: int):
        '''
        Initialize a new instance of FloatModbusVariable class.

        Parameters
        ----------
        name: str
            The Modbus variable name.
        size: int
            The variable value length.
        '''
        super().__init__(name, size, float, str)


class FlagModbusVariable(ModbusVariable):
    '''
    Represents a flag Modbus variable.
    '''

    def __init__(self, name: str, size: int, flag: int):
        '''
        Initialize a new instance of FlagModbusVariable.

        Parameters
        ----------
        name: str
            The Modbus variable name.
        size: int
            The variable value length.
        flag: int
            The flag value.
        '''
        super().__init__(name, size, lambda x: (int(x) & flag) == flag)
