'''Define Helios Easy Controls constants.'''

DOMAIN = 'easycontrols'

DATA_CONTROLLER = 'controller'

CONF_MAC_ADDRESS = 'mac'

MODE_MANUAL = 'manual'
MODE_AUTO = 'auto'

VARIABLE_ARTICLE_DESCRIPTION = 'v00000'
VARIABLE_MAC_ADDRESS = 'v00002'
VARIABLE_PREHEATER_STATUS = 'v00024'
VARIABLE_AFTERHEATER_STATUS = 'v00201'
VARIABLE_PARTY_MODE = 'v00094'
VARIABLE_PARTY_MODE_DURATION = 'v00091'
VARIABLE_PARTY_MODE_FAN_STAGE = 'v00092'
VARIABLE_PARTY_MODE_REMAINING_TIME = 'v00093'
VARIABLE_STANDBY_MODE = 'v00099'
VARIABLE_OPERATING_MODE = 'v00101'
VARIABLE_FAN_STAGE = 'v00102'
VARIABLE_PERCENTAGE_FAN_SPEED = 'v00103'
VARIABLE_TEMPERATURE_OUTSIDE_AIR = 'v00104'
VARIABLE_TEMPERATURE_SUPPLY_AIR = 'v00105'
VARIABLE_TEMPERATURE_OUTGOING_AIR = 'v00106'
VARIABLE_TEMPERATURE_EXTRACT_AIR = 'v00107'
VARIABLE_SERIAL_NUMBER = 'v00303'
VARIABLE_SUPPLY_AIR_RPM = 'v00348'
VARIABLE_EXTRACT_AIR_RPM = 'v00349'
VARIABLE_HOLIDAY_MODE = 'v00601'
VARIABLE_FILTER_CHANGE = 'v01031'
VARIABLE_SUPPLY_AIR_FAN_STAGE = 'v01050'
VARIABLE_EXTRACT_AIR_FAN_STAGE = 'v01051'
VARIABLE_SOFTWARE_VERSION = 'v01101'
VARIABLE_OPERATION_HOURS_SUPPLY_AIR_FAN = 'v01103'
VARIABLE_OPERATION_HOURS_EXTRACT_AIR_FAN = 'v01104'
VARIABLE_OPERATION_HOURS_PREHEATER = 'v01105'
VARIABLE_OPERATION_HOURS_AFTERHEATER = 'v01106'
VARIABLE_ERRORS = 'v01123'
VARIABLE_WARNINGS = 'v01124'
VARIABLE_INFOS = 'v01125'
VARIABLE_PERCENTAGE_PREHEATER = 'v02117'
VARIABLE_PERCENTAGE_AFTERHEATER = 'v02118'
VARIABLE_BYPASS = 'v02119'
VARIABLE_HUMIDITY_EXTRACT_AIR = 'v02136'

PRESET_NOT_SET = 'not set'
PRESET_PARTY = 'party'
PRESET_STANDBY = 'standby'
PRESET_HOLIDAY_INTERVAL = 'holiday interval'
PRESET_HOLIDAY_CONSTANT = 'holiday constant'

ERRORS = {
    0x00000001: 'Fan speed error «Supply air» (outside air)',
    0x00000002: 'Fan speed error «Extract air» (outgoing air)',
    0x00000004: '?',  # free
    0x00000008: 'SD card error when writing E-Eprom data with «FLASH ring buffer FULL»',
    0x00000010: 'Bus overcurrent',
    0x00000020: '?',  # free
    0x00000040: 'BASIS:  0-Xing error VHZ EH   (0-Xing = Zero-Crossing, Zero-crossing detection)',
    0x00000080: 'Ext. module (VHZ):  0-Xing error VHZ EH',
    0x00000100: 'Ext. module (NHZ):  0-Xing error NHZ EH',
    0x00000200: 'BASIS: Internal temp. sensor error - (T1) -Outside air (missing or cable break)',
    0x00000400: 'BASIS: Internal temp. sensor error - (T2) -Supply air- (missing or cable break)',
    0x00000800: 'BASIS: Internal temp. sensor error - (T3) -Extract air- (missing or cable break)',
    0x00001000: 'BASIS: Internal temp. sensor error - (T4) -Outgoing air- (missing or cable break)',
    0x00002000: 'BASIS: Internal temp. sensor error - (T1) -Outside air- (short circuit)',
    0x00004000: 'BASIS: Internal temp. sensor error - (T2) -Supply air- (short circuit)',
    0x00008000: 'BASIS: Internal temp. sensor error - (T3) -Extract air- (short circuit)',
    0x00010000: 'BASIS: Internal temp. sensor error - (T4) -Outgoing air- (short circuit)',
    0x00020000: 'Ext. module configured as VHZ, but missing or malfunctioned',
    0x00040000: 'Ext. module configured as NHZ, but missing or malfunctioned',
    0x00080000: 'Ext. module (VHZ): Duct sensor (T5) -Outside air- (missing or cable break)',
    0x00100000: 'Ext. module (NHZ): Duct sensor (T6) -Supply air- (missing or cable break)',
    0x00200000: 'Ext. module (NHZ): Duct sensor (T7) -Return WW-Register- (missing or cable break)',
    0x00400000: 'Ext. module (VHZ): Duct sensor (T5) -Outside air- (short circuit)',
    0x00800000: 'Ext. module (NHZ): Duct sensor (T6) -Supply air- (short circuit)',
    0x01000000: 'Ext. module (NHZ): Duct sensor (T7) -Return WW-Register- (short circuit)',
    0x02000000: 'Ext. module (VHZ): Safety limiter automatic',
    0x04000000: 'Ext. module (VHZ): Safety limiter manual',
    0x08000000: 'Ext. module (NHZ): Safety limiter automatic',
    0x10000000: 'Ext. module (NHZ): Safety limiter manual',
    0x20000000: 'Ext. module (NHZ): Frost protection WW-Reg. ' +
                'Measured via WW-return (T7) (switching threshold ' +
                'adjustable per variable list  e.g. <  7°C)',
    0x40000000: 'Ext. module (NHZ): Frost protection WW-Reg. ' +
                'Measured via supply air sensor (T6) (switching threshold ' +
                'adjustable per variable list  e.g. <  7°C)',
    0x80000000: 'Frost protection external WW Reg.: ( fixed < 5°C only PHI), ' +
                'measured either via (1.) Ext. module (NHZ): ' +
                'Supply air duct sensor (T6) or (2.) BASIS: Supply air duct sensor (T2)',
}

WARNINGS = {
    0x01: 'Internal humidity sensor provides no value',
    0x02: '?',  # free
    0x04: '?',  # free
    0x08: '?',  # free
    0x10: '?',  # free
    0x20: '?',  # free
    0x40: '?',  # free
    0x80: '?',  # free
}

INFO_FILTER_CHANGE_FLAG = 0x01

INFOS = {
    INFO_FILTER_CHANGE_FLAG: 'Filter change',
    0x02: 'Frost protection WT',
    0x04: 'SD card error',
    0x08: 'Failure of external module (more info in LOG-File)',
    0x10: '?',  # free
    0x20: '?',  # free
    0x40: '?',  # free
    0x80: '?',  # free
}
