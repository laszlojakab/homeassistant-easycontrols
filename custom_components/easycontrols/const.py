"""Define Helios Easy Controls constants."""

from custom_components.easycontrols.modbus_variable import (
    BoolModbusVariable,
    FlagModbusVariable,
    FloatModbusVariable,
    IntModbusVariable,
    OperationHoursModbusVariable,
    StrModbusVariable,
)

DOMAIN = "easycontrols"

DATA_COORDINATOR = "coordinator"

INFO_FILTER_CHANGE_FLAG = 0x01

VARIABLE_ARTICLE_DESCRIPTION = StrModbusVariable("v00000", 31)
VARIABLE_MAC_ADDRESS = StrModbusVariable("v00002", 18)
VARIABLE_PREHEATER_STATUS = BoolModbusVariable("v00024")
VARIABLE_AFTERHEATER_STATUS = BoolModbusVariable("v00201")
VARIABLE_PARTY_MODE = BoolModbusVariable("v00094")
VARIABLE_PARTY_MODE_DURATION = IntModbusVariable("v00091", 3)
VARIABLE_PARTY_MODE_FAN_STAGE = IntModbusVariable("v00092", 3)                              #241019 CHAR[1] swapped to CHAR[3] - Analog to "Manual" from Helios
VARIABLE_PARTY_MODE_REMAINING_TIME = IntModbusVariable("v00093", 3)
VARIABLE_STANDBY_MODE_DURATION = IntModbusVariable("v00096", 3)
VARIABLE_STANDBY_MODE_FAN_STAGE = IntModbusVariable("v00097", 1)
VARIABLE_STANDBY_MODE_REMAINING_TIME = IntModbusVariable("v00098", 3)
VARIABLE_STANDBY_MODE = BoolModbusVariable("v00099")
VARIABLE_OPERATING_MODE = IntModbusVariable("v00101", 1)
VARIABLE_FAN_STAGE = IntModbusVariable("v00102", 1)
VARIABLE_PERCENTAGE_FAN_SPEED = IntModbusVariable("v00103", 3)
VARIABLE_TEMPERATURE_OUTSIDE_AIR = FloatModbusVariable("v00104", 7)
VARIABLE_TEMPERATURE_SUPPLY_AIR = FloatModbusVariable("v00105", 7)
VARIABLE_TEMPERATURE_OUTGOING_AIR = FloatModbusVariable("v00106", 7)
VARIABLE_TEMPERATURE_EXTRACT_AIR = FloatModbusVariable("v00107", 7)
VARIABLE_TEMPERATURE_DUCT_SENSOR_SUPPLY_AIR_T6 = FloatModbusVariable("v00110", 7)
VARIABLE_TEMPERATURE_RETURN_WW_REGISTER_T7 = FloatModbusVariable("v00146", 7)
VARIABLE_EXTERNAL_FTF_HUMIDITY_1 = FloatModbusVariable("v00111", 4)
VARIABLE_EXTERNAL_FTF_HUMIDITY_2 = FloatModbusVariable("v00112", 4)
VARIABLE_EXTERNAL_FTF_HUMIDITY_3 = FloatModbusVariable("v00113", 4)
VARIABLE_EXTERNAL_FTF_HUMIDITY_4 = FloatModbusVariable("v00114", 4)
VARIABLE_EXTERNAL_FTF_HUMIDITY_5 = FloatModbusVariable("v00115", 4)
VARIABLE_EXTERNAL_FTF_HUMIDITY_6 = FloatModbusVariable("v00116", 4)
VARIABLE_EXTERNAL_FTF_HUMIDITY_7 = FloatModbusVariable("v00117", 4)
VARIABLE_EXTERNAL_FTF_HUMIDITY_8 = FloatModbusVariable("v00118", 4)
VARIABLE_EXTERNAL_FTF_TEMPERATURE_1 = FloatModbusVariable("v00119", 7)
VARIABLE_EXTERNAL_FTF_TEMPERATURE_2 = FloatModbusVariable("v00120", 7)
VARIABLE_EXTERNAL_FTF_TEMPERATURE_3 = FloatModbusVariable("v00121", 7)
VARIABLE_EXTERNAL_FTF_TEMPERATURE_4 = FloatModbusVariable("v00122", 7)
VARIABLE_EXTERNAL_FTF_TEMPERATURE_5 = FloatModbusVariable("v00123", 7)
VARIABLE_EXTERNAL_FTF_TEMPERATURE_6 = FloatModbusVariable("v00124", 7)
VARIABLE_EXTERNAL_FTF_TEMPERATURE_7 = FloatModbusVariable("v00125", 7)
VARIABLE_EXTERNAL_FTF_TEMPERATURE_8 = FloatModbusVariable("v00126", 7)
VARIABLE_EXTERNAL_CO2_1 = IntModbusVariable("v00128", 4)
VARIABLE_EXTERNAL_CO2_2 = IntModbusVariable("v00129", 4)
VARIABLE_EXTERNAL_CO2_3 = IntModbusVariable("v00130", 4)
VARIABLE_EXTERNAL_CO2_4 = IntModbusVariable("v00131", 4)
VARIABLE_EXTERNAL_CO2_5 = IntModbusVariable("v00132", 4)
VARIABLE_EXTERNAL_CO2_6 = IntModbusVariable("v00133", 4)
VARIABLE_EXTERNAL_CO2_7 = IntModbusVariable("v00134", 4)
VARIABLE_EXTERNAL_CO2_8 = IntModbusVariable("v00135", 4)
VARIABLE_EXTERNAL_VOC_1 = IntModbusVariable("v00136", 4)
VARIABLE_EXTERNAL_VOC_2 = IntModbusVariable("v00137", 4)
VARIABLE_EXTERNAL_VOC_3 = IntModbusVariable("v00138", 4)
VARIABLE_EXTERNAL_VOC_4 = IntModbusVariable("v00139", 4)
VARIABLE_EXTERNAL_VOC_5 = IntModbusVariable("v00140", 4)
VARIABLE_EXTERNAL_VOC_6 = IntModbusVariable("v00141", 4)
VARIABLE_EXTERNAL_VOC_7 = IntModbusVariable("v00142", 4)
VARIABLE_EXTERNAL_VOC_8 = IntModbusVariable("v00143", 4)
VARIABLE_SERIAL_NUMBER = StrModbusVariable("v00303", 16)
VARIABLE_SUPPLY_AIR_RPM = IntModbusVariable("v00348", 4)
VARIABLE_EXTRACT_AIR_RPM = IntModbusVariable("v00349", 4)
VARIABLE_FILTER_CHANGE = BoolModbusVariable("v01031")
VARIABLE_SUPPLY_AIR_FAN_STAGE = IntModbusVariable("v01050", 1)
VARIABLE_EXTRACT_AIR_FAN_STAGE = IntModbusVariable("v01051", 1)
VARIABLE_SOFTWARE_VERSION = StrModbusVariable("v01101", 5)
VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN = OperationHoursModbusVariable("v01103", 10)
VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN = OperationHoursModbusVariable("v01104", 10)
VARIABLE_OPERATION_HOURS_PREHEATER = OperationHoursModbusVariable("v01105", 10)
VARIABLE_OPERATION_HOURS_AFTERHEATER = OperationHoursModbusVariable("v01106", 10)
VARIABLE_ERRORS = IntModbusVariable("v01123", 10)
VARIABLE_WARNINGS = IntModbusVariable("v01124", 3)                                          #241019 CHAR[10] swapped to CHAR[3] - Analog to "Manual" from Helios
VARIABLE_INFOS = IntModbusVariable("v01125", 3)                                             #241019 CHAR[10] swapped to CHAR[3] - Analog to "Manual" from Helios
VARIABLE_INFO_FILTER_CHANGE = FlagModbusVariable("v01125", 3, INFO_FILTER_CHANGE_FLAG)      #241019 CHAR[10] swapped to CHAR[3] - Analog to "Manual" from Helios
VARIABLE_PERCENTAGE_PREHEATER = IntModbusVariable("v02117", 3)
VARIABLE_PERCENTAGE_AFTERHEATER = IntModbusVariable("v02118", 3)
VARIABLE_BYPASS = BoolModbusVariable("v02119")
VARIABLE_HUMIDITY_EXTRACT_AIR = IntModbusVariable("v02136", 3)
VARIABLE_BYPASS_FROM_DAY = IntModbusVariable("v02120", 2)
VARIABLE_BYPASS_FROM_MONTH = IntModbusVariable("v02121", 2)
VARIABLE_BYPASS_TO_DAY = IntModbusVariable("v02128", 2)
VARIABLE_BYPASS_TO_MONTH = IntModbusVariable("v02129", 2)
VARIABLE_BYPASS_EXTRACT_AIR_TEMPERATURE = IntModbusVariable("v01035", 2)
VARIABLE_BYPASS_OUTDOOR_AIR_TEMPERATURE = IntModbusVariable("v01036", 2)
VARIABLE_BYPASS_OFFSET_SUPPLY_AIR_TEMPERATURE = IntModbusVariable("v01037", 2)

PRESET_PARTY = "party"
PRESET_STANDBY = "standby"
PRESET_AUTO = "auto"

SERVICE_START_PARTY_MODE = "start_party_mode"
SERVICE_STOP_PARTY_MODE = "stop_party_mode"
SERVICE_SET_FAN_STAGE = "set_fan_stage"

OPERATING_MODE_MANUAL = 1
OPERATING_MODE_AUTO = 0

ERRORS = {
    0x00000001: "Fan speed error «Supply air» (outside air)",
    0x00000002: "Fan speed error «Extract air» (outgoing air)",
    0x00000004: "?",  # free
    0x00000008: "SD card error when writing E-Eprom data with «FLASH ring buffer FULL»",
    0x00000010: "Bus overcurrent",
    0x00000020: "?",  # free
    0x00000040: "BASIS:  0-Xing error VHZ EH   (0-Xing = Zero-Crossing, Zero-crossing detection)",
    0x00000080: "Ext. module (VHZ):  0-Xing error VHZ EH",
    0x00000100: "Ext. module (NHZ):  0-Xing error NHZ EH",
    0x00000200: "BASIS: Internal temp. sensor error - (T1) -Outside air (missing or cable break)",
    0x00000400: "BASIS: Internal temp. sensor error - (T2) -Supply air- (missing or cable break)",
    0x00000800: "BASIS: Internal temp. sensor error - (T3) -Extract air- (missing or cable break)",
    0x00001000: "BASIS: Internal temp. sensor error - (T4) -Outgoing air- (missing or cable break)",
    0x00002000: "BASIS: Internal temp. sensor error - (T1) -Outside air- (short circuit)",
    0x00004000: "BASIS: Internal temp. sensor error - (T2) -Supply air- (short circuit)",
    0x00008000: "BASIS: Internal temp. sensor error - (T3) -Extract air- (short circuit)",
    0x00010000: "BASIS: Internal temp. sensor error - (T4) -Outgoing air- (short circuit)",
    0x00020000: "Ext. module configured as VHZ, but missing or malfunctioned",
    0x00040000: "Ext. module configured as NHZ, but missing or malfunctioned",
    0x00080000: "Ext. module (VHZ): Duct sensor (T5) -Outside air- (missing or cable break)",
    0x00100000: "Ext. module (NHZ): Duct sensor (T6) -Supply air- (missing or cable break)",
    0x00200000: "Ext. module (NHZ): Duct sensor (T7) -Return WW-Register- (missing or cable break)",
    0x00400000: "Ext. module (VHZ): Duct sensor (T5) -Outside air- (short circuit)",
    0x00800000: "Ext. module (NHZ): Duct sensor (T6) -Supply air- (short circuit)",
    0x01000000: "Ext. module (NHZ): Duct sensor (T7) -Return WW-Register- (short circuit)",
    0x02000000: "Ext. module (VHZ): Safety limiter automatic",
    0x04000000: "Ext. module (VHZ): Safety limiter manual",
    0x08000000: "Ext. module (NHZ): Safety limiter automatic",
    0x10000000: "Ext. module (NHZ): Safety limiter manual",
    0x20000000: "Ext. module (NHZ): Frost protection WW-Reg. "
    "Measured via WW-return (T7) (switching threshold "
    "adjustable per variable list  e.g. <  7°C)",
    0x40000000: "Ext. module (NHZ): Frost protection WW-Reg. "
    "Measured via supply air sensor (T6) (switching threshold "
    "adjustable per variable list  e.g. <  7°C)",
    0x80000000: "Frost protection external WW Reg.: ( fixed < 5°C only PHI), "
    "measured either via (1.) Ext. module (NHZ): "
    "Supply air duct sensor (T6) or (2.) BASIS: Supply air duct sensor (T2)",
}

WARNINGS = {
    0x01: "Internal humidity sensor provides no value",
    0x02: "?",  # free
    0x04: "?",  # free
    0x08: "?",  # free
    0x10: "?",  # free
    0x20: "?",  # free
    0x40: "?",  # free
    0x80: "?",  # free
}

INFOS = {
    INFO_FILTER_CHANGE_FLAG: "Filter change",
    0x02: "Frost protection WT",
    0x04: "SD card error",
    0x08: "Failure of external module (more info in LOG-File)",
    0x10: "?",  # free
    0x20: "?",  # free
    0x40: "?",  # free
    0x80: "?",  # free
}