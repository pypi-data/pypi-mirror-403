# -*- coding: utf-8 -*-

"""scinstr.vaccum
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2018-2024
license   GPL v3.0+
brief     Class to Pfeiffer TPG261 controller device.
"""

import serial
import scinstr.vacuum.gauge as gauge

ERR_CODES = {
    0: 'No error',
    1: 'Watchdog has responded',
    2: 'Task fail error',
    3: 'EPROM error',
    4: 'RAM error',
    5: 'EEPROM error',
    7: 'Display error',
    8: 'A/D converter error',
    9: 'Gauge 1 error (e.g. filament rupture, no supply)',
    10: 'Gauge 1 identification error',
    11: 'Gauge 2 error (e.g. filament rupture, no supply)',
    12: 'Gauge 2 identification error'
}

PRESSURE_READING_STATUS = {
    0: 'Measurement data okay',
    1: 'Underrange',
    2: 'Overrange',
    3: 'Sensor error',
    4: 'Sensor off',
    5: 'No sensor',
    6: 'Identification error'
}

GAUGE_TYPE = {
    'TPR': 'Pirani Gauge (all)',
    'IKR9': 'Cold Cathode Gauge 10-9',
    'IKR11': 'Cold Cathode Gauge 10-11',
    'PKR': 'FullRange CC Gauge',
    'PBR': 'FullRange BA Gauge',
    'IMR': 'Pirani / High Pressure Gauge',
    'CMR': 'Linear gauge',
    'noSEn': 'no SEnsor',
    'noid': 'no identifier'
}

FSR = {
    0: '0.01 mbar',
    1: '0.1 mbar',
    2: '1 mbar',
    3: '10 mbar',
    4: '100 mbar',
    5: '1000 mbar default',
    6: '2 bar',
    7: '5 bar',
    8: '10 bar',
    9: '50 bar'
}

SER_TIMEOUT = 0.2
ETH_TIMEOUT = 0.2


# =============================================================================
class Tpg261Serial(gauge.GaugeSerial):
    """Handle TPG261 vacuum gauge device through USB connection.
    The USB interface emulates an RS-232 serial port with the folowing
    configuration parameters:
    - Baud rate 9600
    - Start bits 1
    - Data bits 8
    - Parity None
    - Stop bits 1
    - Flow control None
    - Handshaking None
    """

    def __init__(self, port='', timeout=SER_TIMEOUT):
        super().__init__(port=port,
                         baudrate=9600,
                         bytesize=8,
                         parity=serial.PARITY_NONE,
                         stopbits=1,
                         timeout=timeout)


# =============================================================================
class Tpg261Eth(gauge.GaugeEth):
    """Handle TPG261 vacuum gauge device through ethernet interface.
    """

    PORT = 7777

    def __init__(self, ip='', port=PORT, timeout=ETH_TIMEOUT):
        super().__init__(ip, port, timeout)


# =============================================================================
if __name__ == '__main__':
    import logging
    import argparse

    DATE_FMT = "%d/%m/%Y %H:%M:%S"
    LOG_FORMAT = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d): %(message)s"
    logging.basicConfig(level=logging.DEBUG,
                        datefmt=DATE_FMT,
                        format=LOG_FORMAT)

    PARSER = argparse.ArgumentParser(description='Test Pfeiffer tpg261')
    PARSER.add_argument('-p', '--port', dest='port', type=str,
                        help='Serial port to connect to')

    ARGS = PARSER.parse_args()
    PORT = ARGS.port
    INST = Tpg261Serial(port=PORT)
    INST.connect()

    RETVAL = INST.reset()
    if RETVAL != '0':
        INST.close()
        exit()

    print("GID: %s" % (INST.gauge_id))
    print("Error: %s" % (INST.error))

    INST.close()
