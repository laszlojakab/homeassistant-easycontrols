#!/usr/bin/env python3
###############################################################################
#
#  eazyctrl: library and command line tool for monitoring and controlling Easy
#  Controls KWL (air exchanger) devices via Modbus/TCP.
#
###############################################################################
#
#  Copyright (c) 2019-2020, Bálint Aradi
#
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#
###############################################################################

"""Library and command line tool for monitoring and controlling Eazy Controls
KWL (air exchanger) devices via Modbus/TCP.
"""

import time
import random
import socket
import struct
import asyncio
import logging

logger = logging.getLogger(__name__)

# Standard Modbus TCP port
_MODBUS_TCP_PORT = 502

# Size of the receive buffer when communicating the Modbus device
_RECV_BUFFER_SIZE = 1024

# Time-out for the socket communication
_SOCKET_TIMEOUT = 10.0

# Nr. of times communication should be tried in case of conflicts
_READ_VAR_NR_TRIALS = 3

# Minimal and maximal waiting time in seconds between trials
_READ_VAR_TIMEOUT_RANGE = 0.1, 0.5

# Dictionary of known air exchanger (KWL) features.
# Key: feature name (abbreviated version of the description in the manual)
# Value: Tuple consisting of following values:
#     - variable name,
#     - nr. of chars to trasmint
#     - function to use to convert received char into Python native type
#     - function to use to convert Python native type into chars to be sent
#       or None, if the property is read-only.
#
_KWL_FEATURES = {
    'party_mode': ("v00094", 1, int, str),
    'standby_mode': ("v00099", 1, int, str),
    'operating_mode': ("v00101", 1, int, str),
    'fan_stage': ("v00102", 1, int, str),
    'fan_stage_percentage': ("v00103", 3, int, None),
    'temp_outside_air': ("v00104", 7, float, None),
    'temp_supply_air': ("v00105", 7, float, None),
    'temp_outgoing_air': ("v00106", 7, float, None),
    'temp_extract_air': ("v00107", 7, float, None),
    'supply_air_rpm': ("v00348", 4, int, None),
    'extract_air_rpm': ("v00349", 4, int, None),
    'bypass': ("v02119", 1, int, None),
    'filter_change_remaining_time': ("v01033", 10, int, None),
}

# Modbus unit id used by the air exchanger devices.
_KWL_UNIT_ID = 180

# Various Modbus fields needed for the communication
_FIELDS_MODBUS_HEADER = {
    'transaction_identifier': ((0, 2), '>H'),
    'protocol_identifier': ((2, 4), '>H'),
    'length': ((4, 6), '>H'),
    'unit_identifier': ((6, 7), 'B'),
    'application_data': ((7, None), None),
}

_FIELDS_MODBUS_03_REQUEST = {
    'function_code': ((7, 8), 'B'),
    'starting_address': ((8, 10), '>H'),
    'quantity_of_registers': ((10, 12), '>H'),
}

_FIELDS_MODBUS_03_RESPONSE = {
    'function_code': ((7, 8), 'B'),
    'byte_count': ((8, 9), 'B'),
    'registers_value': ((9, None), None),
}

_FIELDS_MODBUS_16_REQUEST = {
    'function_code': ((7, 8), 'B'),
    'starting_address': ((8, 10), '>H'),
    'quantity_of_registers': ((10, 12), '>H'),
    'byte_count': ((12, 13), 'B'),
    'registers_value': ((13, None), None),
}

_FIELDS_MODBUS_16_RESPONSE = {
    'function_code': ((7, 8), 'B'),
    'starting_address': ((8, 10), '>H'),
    'quantity_of_registers': ((10, 12), '>H'),
}

_FIELDS_MODBUS_ERROR = {
    'error_code': ((7, 8), 'B'),
    'exception_code': ((8, 9), 'B'),
}


# Upper bound for transaction ids (maximal allowed value + 1)
_TRANSID_RANGE = 2**16

_read_lock = asyncio.Lock()

class NamedByteArray(bytearray):
    """Simple wrapper class to access byte arrays slices by name.

    Various parts of the byte array can be read or written in a dictionary like
    fashion using predefined field names. During read the bytearray slices are
    converted to a Python type using the ``struct.unpack()`` routine, while the
    Python type is converted using the ``struct.pack()`` routine when writing::

        fields = {'field1': ((0, 2), '>H'), 'field2': ((2, 4), '>H'),
            'remainder': ((4, None), None)}
        arr = ec.NamedByteArray(fields, 4)
        arr['field1'] = 1
        arr['field2'] = 2
        arr['remainder'] = bytearray('3456', encoding='ascii')
        print(arr['field1'], arr['field2'], arr['remainder'])

    """

    def __init__(self, fields, *args):
        """Initialises a NamedByteArray instance.

        Args:
            fields: Dictionary containing the named slice definitions. The key
                is the name under which a given slice should be accessed.  The
                value is a tuple ``((from, to), formatstr)`` containing the
                slice definition and the format string which is passed to the
                ``struct.pack()`` and ``struct.unpack()`` routines when
                converting a bytearray slice to a Python type or back.  Each
                format string should contain exactly one value. If the format
                string is None, the byte array slice is passed through without
                conversion.
            *args: Any arguments ``bytearray()`` accepts.
        """
        self._fields = fields
        arrslices = [slice(*arrslice) for arrslice, _ in fields.values()]
        self._minsize = max([arrslice.stop for arrslice in arrslices
                             if arrslice.stop is not None])
        if args:
            super().__init__(*args)
            self._ensure_minimal_size()
        else:
            super().__init__(self._minsize)


    def __setitem__(self, fieldname, fieldvalue):
        if not isinstance(fieldname, str):
            super().__setitem__(fieldname, fieldvalue)
        else:
            arrslice, formatstr = self._get_field_params(fieldname)
            if formatstr is not None:
                byterep = struct.pack(formatstr, fieldvalue)
            else:
                byterep = fieldvalue
            super().__setitem__(slice(*arrslice), byterep)
        self._ensure_minimal_size()


    def __getitem__(self, fieldname):
        if not isinstance(fieldname, str):
            return super().__getitem__(fieldname)
        arrslice, formatstr = self._get_field_params(fieldname)
        byterep = super().__getitem__(slice(*arrslice))
        if formatstr is not None:
            result = struct.unpack(formatstr, byterep)[0]
        else:
            result = byterep
        return result


    def _get_field_params(self, fieldname):
        fieldparams = self._fields.get(fieldname)
        if fieldparams is None:
            raise ValueError("Invalid bytearray slice name '" + fieldname + "'")
        return fieldparams


    def _ensure_minimal_size(self):
        if len(self) < self._minsize:
            raise ValueError(
                "With current field definition bytearray length may not be "\
                "shorter as {:d} bytes".format(self._minsize))


class ModbusMessage(NamedByteArray):
    """Represents a generic modbus message.

    It contains the standard modbus header message fields
    ('transaction_modifier', 'protocol_identifier', 'length', 'unit_identifier'
    and 'appilication_data') and any additional data fields defined at
    initialisation time.

    """

    def __init__(self, appdatafields, *args):
        """Initialises a modbus message.

        Args:
            appdatafields: Extra (application data) fields beyond the standard
                modbus header. The initialised object will contain the standar
                modbus headers ('transaction_identifier', 'protocol_identifier',
                'length', 'unit_identifier' and 'application_data'), and
                additionally the provided fields here. The field
                'application_data' allows to access everything beyond modbus
                header as one field.
        """
        allfields = dict(list(_FIELDS_MODBUS_HEADER.items())
                         + list(appdatafields.items()))
        super().__init__(allfields, *args)
        self._update_length()


    def __setitem__(self, fieldname, fieldvalue):
        super().__setitem__(fieldname, fieldvalue)
        self._update_length()


    def _update_length(self):
        super().__setitem__('length', len(self) - 6)



class Modbus03Request(ModbusMessage):
    """Represents a modbus 03 request as a named byte array."""

    def __init__(self, *args):
        super().__init__(_FIELDS_MODBUS_03_REQUEST, *args)
        self['function_code'] = 3


class Modbus03Response(ModbusMessage):
    """Represents a modbus 03 response as a named byte array."""

    def __init__(self, *args):
        super().__init__(_FIELDS_MODBUS_03_RESPONSE, *args)
        self['function_code'] = 3


class Modbus16Request(ModbusMessage):
    """Represents a modbus 16 request as a named byte array."""

    def __init__(self, *args):
        super().__init__(_FIELDS_MODBUS_16_REQUEST, *args)
        self['function_code'] = 16


class Modbus16Response(ModbusMessage):
    """Represents a modbus 03 response as a named byte array."""

    def __init__(self, *args):
        super().__init__(_FIELDS_MODBUS_16_RESPONSE, *args)
        self['function_code'] = 16


class ModbusErrorResponse(ModbusMessage):
    """Represents a modbus error message as a named byte array."""

    def __init__(self, *args):
        super().__init__(_FIELDS_MODBUS_ERROR, *args)


class UnexpectedModbusResponse(Exception):
    """Raised if the modbus response can not be interpreted"""

    def __init__(self, msg=None, sendmsg=None, response=None):
        super().__init__(msg)
        self.sendmsg = sendmsg
        self.response = response


class AsyncEazyCommunicator:
    def __init__(self, server, port=_MODBUS_TCP_PORT, timeout=_SOCKET_TIMEOUT):
        """Initializes an EasyCommunicator instance.

        Args:
            server: IP-address of the remote EasyControls device.
            port: Port of the remote device (default: standard modbus port)
            timeout: Time-out for the socket communication with the device.
        """
        self._transid = random.randrange(0, _TRANSID_RANGE)
        self._server = server
        self._port = port
        self._reader: asyncio.StreamReader = None
        self._writer: asyncio.StreamWriter = None
        self._timeout = timeout

    async def close(self):
        """Closes the communicator."""
        self._writer.close()
        await self._writer.wait_closed()

    async def __aenter__(self):
        self._reader, self._writer = await asyncio.wait_for(asyncio.open_connection(self._server, self._port), self._timeout)
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        await self.close()

    async def write_variable(self, vardef):
        """Writes a variable on the remote device.

        Args:
            vardef: Variable definition. It should have either the form
                ``varname=varvalue``, in order to set the corresponding variable
                on the remote device, or ``varname`` if the value of the given
                variable should be queried. In the latter case, the
                ``read_variable()`` method must be called immediately after this
                call to obtain the variable value.
        """

        # Transmitted data must be rounded up to even bytes
        vardeflen = len(vardef)
        datalen = (vardeflen + 2) // 2 * 2
        data = bytearray(datalen)
        data[:vardeflen] = bytearray(vardef, encoding='ascii')

        self._transid = (self._transid + 1) % _TRANSID_RANGE
        sendmsg = Modbus16Request()
        sendmsg['transaction_identifier'] = self._transid
        sendmsg['unit_identifier'] = _KWL_UNIT_ID
        sendmsg['starting_address'] = 1
        sendmsg['quantity_of_registers'] = datalen // 2
        sendmsg['byte_count'] = datalen
        sendmsg['registers_value'] = data
        self._writer.write(sendmsg)
        await self._writer.drain()
        response = await self._reader.read(_RECV_BUFFER_SIZE)
        exc = None
        try:
            respmsg = Modbus16Response(response)
        except ValueError:
            msg = "Unexpected modbus response (probably modbus error)"
            exc = UnexpectedModbusResponse(msg=msg, sendmsg=sendmsg,
                                           response=response)
        else:
            if respmsg['function_code'] != 16:
                msg = "Unexpected function code in modbus response"
                exc = UnexpectedModbusResponse(msg=msg, sendmsg=sendmsg,
                                               response=response)
        if exc is not None:
            raise exc

    async def read_variable(self, varnamelen, varlen):
        """Reads the value of a variable on the remote device.

        You typically call this function after having called the
        ``write_variable()`` method with a variable defintion of the type
        ``varname``.

        Args:
           varnamelen: Lenght of the variable name to be queried.
           varlen: Length (nr. of bytes) of the expected response.
        """

        answerlen = varnamelen + 1 + varlen
        datalen = (answerlen + 2) // 2 * 2

        sendmsg = Modbus03Request()
        self._transid = (self._transid + 1) % _TRANSID_RANGE
        sendmsg['transaction_identifier'] = self._transid
        sendmsg['unit_identifier'] = _KWL_UNIT_ID
        sendmsg['starting_address'] = 1
        sendmsg['quantity_of_registers'] = datalen // 2
        self._writer.write(sendmsg)
        await self._writer.drain()

        response = await self._reader.read(_RECV_BUFFER_SIZE)
        exc = None
        try:
            respmsg = Modbus03Response(response)
        except ValueError:
            msg = "Unexpected modbus response (probably modbus error)"
            exc = UnexpectedModbusResponse(msg=msg, sendmsg=sendmsg,
                                           response=response)

        else:
            if respmsg['function_code'] != 3:
                msg = "Unexpected function code in modbus response"
                exc = UnexpectedModbusResponse(msg=msg, sendmsg=sendmsg,
                                               response=response)
        if exc is not None:
            raise exc
        answer = respmsg['registers_value'].rstrip(b'\x00').decode('ascii')
        return answer[:varnamelen], answer[varnamelen + 1:]


class AsyncEazyController:
    """High-level controller to control and query a remote EasyControls device.

    You can either read or write variables directly  ::

        host = "mydevice.mynet"
        ctrl = EazyController(host)

        # Querying the outside air temperature
        temp_out = ctrl.get_variable("v00104", 7, conversion=float)

        # Setting the fan level to 1
        ctrl.set_variable("v00102", 1, conversion="{:d}")


    or access the various features via high-level feature calls and let
    EazyController make the data type conversion ::

        host = "mydevice.mynet"
        ctrl = EazyController(host)

        # Querying the outside air temperature
        temp_out = ctrl.get_feature("temperature_outside_air")

        # Setting the fan level to 1
        ctrl.set_feature("fan_stage", 1)

    Note: The routines of the controller are subject to potential coincidency
    conflicts due to the design of the protocol of the KWL-devices. In case of
    a conflict the routines retry the communication after a random
    delay. Nevertheless, the caller should make its best efforts, that for a
    given device only one ``get_variable()``, ``set_variable()``,
    ``get_feature()`` or ``set_feature()`` call is active at a given
    time. (E.g. using thread-locks in a threaded environment.)

    """

    def __init__(self, server, *args):
        self._server = server
        self._serverargs = args

    async def get_variable(self, varname, varlen, conversion=None):
        """Queries the value of a given variable on the remote device.

        Args:
            varname: name of the variable to query.
            varlen: length of the expected response (should be equal of longer
                as the response of the server)
            conversion: Function for converting the response into a Python
                type. Default: None -- no conversion is made, the string as
                obtained from the server is returned. The value of the argument
                can be either a formatting string or a function expecting one
                argument and returning the converted value.

        Returns:
            Value of the queried variable or None, if the query failed.

        """
        for itrial in range(_READ_VAR_NR_TRIALS):
            if itrial:
                await asyncio.sleep(random.uniform(*_READ_VAR_TIMEOUT_RANGE))
            async with AsyncEazyCommunicator(self._server, *self._serverargs) as comm:
                async with _read_lock:
                    try:
                        try:
                            await comm.write_variable(varname)
                        except UnexpectedModbusResponse:
                            continue
                        varnamelen = len(varname)
                        try:
                            recvvarname, varval = await comm.read_variable(varnamelen, varlen)                        
                        except UnexpectedModbusResponse:
                            continue
                    except Exception as e:
                        logger.exception("error in get_variable")
                        raise

            if recvvarname == varname:
                if conversion is None:
                    return varval
                return conversion(varval)

        return None

    async def set_variable(self, varname, varval, conversion=None):
        """Sets a variable on the remote device to a given value.

        Args:
            varname: Name of the variable to set.

            varval: Value to set. It should be either the proper string
                representation of the variable which can be directly sent
                to the server, or a Python type which is then converted
                using the optional conversion argument.
                as the response of the server)

            conversion: Function for converting the variable value into the
                proper string representation which can be sent to the server
                directly. Default: None -- no conversion is made, the variable
                value must be a string, which is sent directly to the server.
                The value of the argument can be either a formatting string or a
                function expecting one argument and returning the string
                representation which is then sent to the server.

        Returns:
            True if no error occured during setting the variable, False
            otherwise.
        """
        if conversion is None:
            varcontent = varval
        elif isinstance(conversion, str):
            varcontent = conversion.format(varval)
        else:
            varcontent = conversion(varval)
        vardef = "{}={}".format(varname, varcontent)
        for itrial in range(_READ_VAR_NR_TRIALS):
            if itrial:
                await asyncio.sleep(random.uniform(*_READ_VAR_TIMEOUT_RANGE))
            async with AsyncEazyCommunicator(self._server, *self._serverargs) as comm:
                try:
                    await comm.write_variable(vardef)
                except UnexpectedModbusResponse:
                    continue
            return True
        return False

    async def get_feature(self, feature):
        """Queries the value of a given feature of the remote device.

        Args:
            feature: Name of the feature to query.

        Returns:
            Value of the queried feature or None if the query was unsuccessful.
        """
        featureparams = _KWL_FEATURES.get(feature)
        if featureparams is None:
            raise ValueError("Unknown feature '" + feature + "'")
        varname, varlen, getconv, _ = featureparams
        return await self.get_variable(varname, varlen, getconv)

    async def set_feature(self, feature, featureval):
        """Sets the value of a given feature on the remote device.

        Args:
            feature: Name of the feature to query.
            featureval: Value for the given feature.
        """
        featureparams = _KWL_FEATURES.get(feature)
        if featureparams is None:
            raise ValueError("Unknown feature '" + feature + "'")
        varname, _, _, setconv = featureparams
        if setconv is None:
            raise ValueError("Feature '" + feature + "' is read-only")
        return await self.set_variable(varname, featureval, setconv)

    @staticmethod
    def get_feature_list():
        """Returns the list of the available features.

        Returns:
            List of tuples, each of them containing the feature name and a
            dictionary with the feature parameters.

        """
        feature_list = []
        for feature, featureparams in _KWL_FEATURES.items():
            rw = featureparams[-1] is not None
            features = {'varname': featureparams[0], 'rw': rw}
            feature_list.append((feature, features))
        return feature_list


class EazyCommunicator:
    """Low-level communicator for modbus/tcp data exchange with an EasyControls
    device.
    """

    def __init__(self, server, port=_MODBUS_TCP_PORT, timeout=_SOCKET_TIMEOUT):
        """Initializes an EasyCommunicator instance.

        Args:
            server: IP-address of the remote EasyControls device.
            port: Port of the remote device (default: standard modbus port)
            timeout: Time-out for the socket communication with the device.
        """
        self._transid = random.randrange(0, _TRANSID_RANGE)
        self._server = server
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((server, port))
        self._socket.settimeout(timeout)


    def close(self):
        """Closes the communicator."""
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()


    def __enter__(self):
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        self.close()


    def write_variable(self, vardef):
        """Writes a variable on the remote device.

        Args:
            vardef: Variable definition. It should have either the form
                ``varname=varvalue``, in order to set the corresponding variable
                on the remote device, or ``varname`` if the value of the given
                variable should be queried. In the latter case, the
                ``read_variable()`` method must be called immediately after this
                call to obtain the variable value.
        """

        # Transmitted data must be rounded up to even bytes
        vardeflen = len(vardef)
        datalen = (vardeflen + 2) // 2  * 2
        data = bytearray(datalen)
        data[:vardeflen] = bytearray(vardef, encoding='ascii')

        self._transid = (self._transid + 1) % _TRANSID_RANGE
        sendmsg = Modbus16Request()
        sendmsg['transaction_identifier'] = self._transid
        sendmsg['unit_identifier'] = _KWL_UNIT_ID
        sendmsg['starting_address'] = 1
        sendmsg['quantity_of_registers'] = datalen // 2
        sendmsg['byte_count'] = datalen
        sendmsg['registers_value'] = data
        self._socket.sendall(sendmsg)

        response = self._socket.recv(_RECV_BUFFER_SIZE)
        exc = None
        try:
            respmsg = Modbus16Response(response)
        except ValueError:
            msg = "Unexpected modbus response (probably modbus error)"
            exc = UnexpectedModbusResponse(msg=msg, sendmsg=sendmsg,
                                           response=response)
        else:
            if respmsg['function_code'] != 16:
                msg = "Unexpected function code in modbus response"
                exc = UnexpectedModbusResponse(msg=msg, sendmsg=sendmsg,
                                               response=response)
        if exc is not None:
            raise exc


    def read_variable(self, varnamelen, varlen):
        """Reads the value of a variable on the remote device.

        You typically call this function after having called the
        ``write_variable()`` method with a variable defintion of the type
        ``varname``.

        Args:
           varnamelen: Lenght of the variable name to be queried.
           varlen: Length (nr. of bytes) of the expected response.
        """

        answerlen = varnamelen + 1 + varlen
        datalen = (answerlen + 2) // 2 * 2

        sendmsg = Modbus03Request()
        self._transid = (self._transid + 1) % _TRANSID_RANGE
        sendmsg['transaction_identifier'] = self._transid
        sendmsg['unit_identifier'] = _KWL_UNIT_ID
        sendmsg['starting_address'] = 1
        sendmsg['quantity_of_registers'] = datalen // 2
        self._socket.sendall(sendmsg)

        response = self._socket.recv(_RECV_BUFFER_SIZE)
        exc = None
        try:
            respmsg = Modbus03Response(response)
        except ValueError:
            msg = "Unexpected modbus response (probably modbus error)"
            exc = UnexpectedModbusResponse(msg=msg, sendmsg=sendmsg,
                                           response=response)

        else:
            if respmsg['function_code'] != 3:
                msg = "Unexpected function code in modbus response"
                exc = UnexpectedModbusResponse(msg=msg, sendmsg=sendmsg,
                                               response=response)
        if exc is not None:
            raise exc
        answer = respmsg['registers_value'].rstrip(b'\x00').decode('ascii')
        return answer[:varnamelen], answer[varnamelen + 1 :]


class EazyController:
    """High-level controller to control and query a remote EasyControls device.

    You can either read or write variables directly  ::

        host = "mydevice.mynet"
        ctrl = EazyController(host)

        # Querying the outside air temperature
        temp_out = ctrl.get_variable("v00104", 7, conversion=float)

        # Setting the fan level to 1
        ctrl.set_variable("v00102", 1, conversion="{:d}")


    or access the various features via high-level feature calls and let
    EazyController make the data type conversion ::

        host = "mydevice.mynet"
        ctrl = EazyController(host)

        # Querying the outside air temperature
        temp_out = ctrl.get_feature("temperature_outside_air")

        # Setting the fan level to 1
        ctrl.set_feature("fan_stage", 1)

    Note: The routines of the controller are subject to potential coincidency
    conflicts due to the design of the protocol of the KWL-devices. In case of
    a conflict the routines retry the communication after a random
    delay. Nevertheless, the caller should make its best efforts, that for a
    given device only one ``get_variable()``, ``set_variable()``,
    ``get_feature()`` or ``set_feature()`` call is active at a given
    time. (E.g. using thread-locks in a threaded environment.)

    """

    def __init__(self, server, *args):
        self._server = server
        self._serverargs = args


    def get_variable(self, varname, varlen, conversion=None):
        """Queries the value of a given variable on the remote device.

        Args:
            varname: name of the variable to query.
            varlen: length of the expected response (should be equal of longer
                as the response of the server)
            conversion: Function for converting the response into a Python
                type. Default: None -- no conversion is made, the string as
                obtained from the server is returned. The value of the argument
                can be either a formatting string or a function expecting one
                argument and returning the converted value.

        Returns:
            Value of the queried variable or None, if the query failed.

        """
        for itrial in range(_READ_VAR_NR_TRIALS):
            if itrial:
                time.sleep(random.uniform(*_READ_VAR_TIMEOUT_RANGE))
            with EazyCommunicator(self._server, *self._serverargs) as comm:
                try:
                    comm.write_variable(varname)
                except UnexpectedModbusResponse:
                    continue
                varnamelen = len(varname)
                try:
                    recvvarname, varval = comm.read_variable(varnamelen, varlen)
                except UnexpectedModbusResponse:
                    continue
            if recvvarname == varname:
                if conversion is None:
                    return varval
                return conversion(varval)
        return None


    def set_variable(self, varname, varval, conversion=None):
        """Sets a variable on the remote device to a given value.

        Args:
            varname: Name of the variable to set.

            varval: Value to set. It should be either the proper string
                representation of the variable which can be directly sent
                to the server, or a Python type which is then converted
                using the optional conversion argument.
                as the response of the server)

            conversion: Function for converting the variable value into the
                proper string representation which can be sent to the server
                directly. Default: None -- no conversion is made, the variable
                value must be a string, which is sent directly to the server.
                The value of the argument can be either a formatting string or a
                function expecting one argument and returning the string
                representation which is then sent to the server.

        Returns:
            True if no error occured during setting the variable, False
            otherwise.
        """
        if conversion is None:
            varcontent = varval
        elif isinstance(conversion, str):
            varcontent = conversion.format(varval)
        else:
            varcontent = conversion(varval)
        vardef = "{}={}".format(varname, varcontent)
        for itrial in range(_READ_VAR_NR_TRIALS):
            if itrial:
                time.sleep(random.uniform(*_READ_VAR_TIMEOUT_RANGE))
            with EazyCommunicator(self._server, *self._serverargs) as comm:
                try:
                    comm.write_variable(vardef)
                except UnexpectedModbusResponse:
                    continue
            return True
        return False


    def get_feature(self, feature):
        """Queries the value of a given feature of the remote device.

        Args:
            feature: Name of the feature to query.

        Returns:
            Value of the queried feature or None if the query was unsuccessful.
        """
        featureparams = _KWL_FEATURES.get(feature)
        if featureparams is None:
            raise ValueError("Unknown feature '" + feature + "'")
        varname, varlen, getconv, _ = featureparams
        return self.get_variable(varname, varlen, getconv)


    def set_feature(self, feature, featureval):
        """Sets the value of a given feature on the remote device.

        Args:
            feature: Name of the feature to query.
            featureval: Value for the given feature.
        """
        featureparams = _KWL_FEATURES.get(feature)
        if featureparams is None:
            raise ValueError("Unknown feature '" + feature + "'")
        varname, _, _, setconv = featureparams
        if setconv is None:
            raise ValueError("Feature '" + feature + "' is read-only")
        return self.set_variable(varname, featureval, setconv)


    @staticmethod
    def get_feature_list():
        """Returns the list of the available features.

        Returns:
            List of tuples, each of them containing the feature name and a
            dictionary with the feature parameters.

        """
        feature_list = []
        for feature, featureparams in _KWL_FEATURES.items():
            rw = featureparams[-1] is not None
            features = {'varname': featureparams[0], 'rw': rw}
            feature_list.append((feature, features))
        return feature_list


#
# Command line script routines
#

def run_eazyctrl():
    """Runs the eazyctrl command line script."""
    _eazyctrl_parse_cmd_line_args()


def _eazyctrl_list(_):
    print("{:30s} {:6s} {:8s}".format('Feature name', 'Access', 'Variable'))
    print("-" * 46)
    for feature, featureparams in EazyController.get_feature_list():
        rw = 'rw' if featureparams['rw'] else 'r'
        print("{:30s} {:6s} {:8s}"\
              .format(feature, rw, featureparams['varname']))


def _eazyctrl_getvar(args):
    ctrl = EazyController(args.host)
    varvalue = ctrl.get_variable(args.varname, args.varlen)
    if varvalue is None:
        _eazyctrl_error("Could not get variable '{}'".format(args.varname))
    print(varvalue)


def _eazyctrl_setvar(args):
    ctrl = EazyController(args.host)
    success = ctrl.set_variable(args.varname, args.varval)
    if not success:
        _eazyctrl_error("Could not set variable '{}'".format(args.feature))


def _eazyctrl_getftr(args):
    ctrl = EazyController(args.host)
    try:
        varvalue = ctrl.get_feature(args.feature)
    except ValueError as exc:
        _eazyctrl_error(exc.args[0])
    if varvalue is None:
        _eazyctrl_error("Could not get feature '{}'".format(args.feature))
    print(varvalue)


def _eazyctrl_setftr(args):
    ctrl = EazyController(args.host)
    try:
        success = ctrl.set_feature(args.feature, args.value)
    except ValueError as exc:
        _eazyctrl_error(exc.args[0])
    if not success:
        _eazyctrl_error("Could not set feature '{}'".format(args.feature))


def _eazyctrl_parse_cmd_line_args():
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    msg = 'lists the available features with some relevant information'
    list_parser = subparsers.add_parser('list', help=msg)
    list_parser.set_defaults(func=_eazyctrl_list)

    msg = 'queries a given feature'
    getftr_parser = subparsers.add_parser('get', help=msg)
    msg = 'host name or ip-address of air exchanger'
    getftr_parser.add_argument('host', help=msg)
    msg = 'feature to query'
    getftr_parser.add_argument('feature', help=msg)
    getftr_parser.set_defaults(func=_eazyctrl_getftr)

    msg = 'sets a given feature'
    setftr_parser = subparsers.add_parser('set', help=msg)
    msg = 'host name or ip-address of air exchanger'
    setftr_parser.add_argument('host', help=msg)
    msg = 'feature to set'
    setftr_parser.add_argument('feature', help=msg)
    msg = 'desired new value'
    setftr_parser.add_argument('value', help=msg)
    setftr_parser.set_defaults(func=_eazyctrl_setftr)

    msg = 'retrieves the value of a variable'
    getvar_parser = subparsers.add_parser('getvar', help=msg)
    msg = 'host name or ip-address of air exchanger'
    getvar_parser.add_argument('host', help=msg)
    msg = 'name of the variable to be queried'
    getvar_parser.add_argument('varname', help=msg)
    msg = 'number of bytes to fetch from the host'
    getvar_parser.add_argument('varlen', type=int, help=msg)
    getvar_parser.set_defaults(func=_eazyctrl_getvar)

    msg = 'sets the value of a given variable'
    setvar_parser = subparsers.add_parser('setvar', help=msg)
    msg = 'host name or ip-address of air exchanger'
    setvar_parser.add_argument('host', help=msg)
    msg = 'name of the variable to be set'
    setvar_parser.add_argument('varname', help=msg)
    msg = 'desired new variable value'
    setvar_parser.add_argument('varval', help=msg)
    setvar_parser.set_defaults(func=_eazyctrl_setvar)
    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.error('You have to specify a subcommand')


def _eazyctrl_error(message):
    import sys
    sys.stderr.write("Error: " + message + "\n")
    sys.exit(1)

if __name__ == '__main__':
    run_eazyctrl()
