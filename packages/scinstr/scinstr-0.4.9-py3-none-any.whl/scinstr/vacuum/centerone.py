# -*- coding: utf-8 -*-

import serial
from scinstr.vacuum.gauge import GaugeSerial, CR, LF

LINE_TERMINATION = CR + LF # CR, LF and CRLF are all possible

ERR_CODES = {
    0: 'No error',
    1: 'Watchdog has responded',
    2: 'Task fail error',
    5: 'EPROM error',
    6: 'RAM error',
    7: 'EEPROM error',
    9: 'DISPLAY error',
    10: 'A/D converter error',
    11: 'Gauge error (e.g. filament rupture, no supply)',
    12: 'Gauge identification error',
}

PRESSURE_READING_STATUS = {
    0: 'Measurement data okay',
    1: 'Underrange',
    2: 'Overrange',
    3: 'Sensor error',
    4: 'Sensor off',
    5: 'No sensor',
    6: 'Identification error',
    7: 'Error ITR'
}

GAUGE_TYPE = {
    'TTR': 'Pirani, all version',
    'TTR100': 'Pirani/Capacitive',
    'PTR': 'Cold Cathode',
    'PTR90': 'Cold Cathode/Pirani',
    'CTR': 'Capacitive',
    'ITR': 'Hot cathode',
    'ITR100': 'Hot cathode',
    'ITR200': 'Hot cathode/Pirani',
    'noSen': 'no Sensor',
    'noid': 'no identifier'
}

FSR = {
    0: '0.01 mbar',
    1: '0.01 Torr',
    2: '0.02 Torr',
    3: '0.05 Torr',
    4: '0.10 mbar',
    5: '0.10 Torr',
    6: '0.25 mbar',
    7: '0.25 Torr',
    8: '0.50 mbar',
    9: '0.50 Torr',
    10: '1 mbar',
    11: '1 Torr',
    12: '2 mbar',
    13: '2 Torr',
    14: '5 mbar',
    15: '5 Torr',
    16: '10 mbar',
    17: '10 Torr',
    18: '20 mbar',
    19: '20 Torr',
    20: '50 mbar',
    21: '50 Torr',
    22: '100 mbar',
    23: '100 Torr',
    24: '200 mbar',
    25: '200 Torr',
    26: '500 mbar',
    27: '500 Torr',
    28: '1000 mbar',
    29: '1100 mbar',
    30: '1000 Torr',
    31: '2 bar',
    32: '5 bar',
    33: '10 bar',
    34: '50 bar',
    35: 'DI200 mbar',
    36: 'DI200 bar',
    37: 'DI200 barRel'
}

SER_TIMEOUT = 0.2
ETH_TIMEOUT = 0.2


# =============================================================================
class CenteroneSerial(GaugeSerial):
    """Handle Centerone gauge device through serial interface.
    Serial interface configuration parameters:
    - Baud rate 9600, 19200, 38400
    - Start bits 1
    - Data bits 8
    - Parity None
    - Stop bits 1
    - Flow control None
    - Handshaking None
    """

    def __init__(self, port, timeout=SER_TIMEOUT):
        super().__init__(port,
                         baudrate=9600,
                         bytesize=8,
                         parity=serial.PARITY_NONE,
                         stopbits=1,
                         timeout=timeout)
