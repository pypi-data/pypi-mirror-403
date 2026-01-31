# -*- coding: utf-8 -*-

"""package scinstr.lockin
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2018
license   GPL v3.0+
brief     Class for handling SR8x0 device throuch serial connection.
details   Use FTDI USB to serial RS232 adapter (USB-RS232-WE-1800-BT_0.0).
          Lockin exhibits sub-D25 female connector.
          Connection between cable and DE25:
            orange (TXD) <-> 2
            yellow (RXD) <-> 3
            black  (GND) <-> 7
          Rear view (solder face) of DB25 connector:
            13 12 11 10 9 8 Black 6 5 Yellow Orange 1
              25 24 23 22 21 20 19 18 17 16 15 14
"""

import logging
import serial
import scinstr.lockin.sr8x0 as sr8x0


class Sr8x0Serial(sr8x0.Sr8x0):
    """Stanford Research System SR8x0 serial interface.
    """

    DEFAULT_TIMEOUT = 1.0

    def __init__(self, port=None, baudrate=9600, parity=serial.PARITY_NONE,
                 rtscts=False, dsrdtr=False, timeout=DEFAULT_TIMEOUT):
        """The constructor.
        """
        super().__init__()
        self.port = port
        self._baudrate = baudrate
        self._parity = parity
        self._rtscts = rtscts
        self._dsrdtr = dsrdtr
        self._timeout = timeout
        self._ser = None

    def connect(self):
        """Connect to the remote host
        :returns: True if connection succeeded, False otherwise
        """
        self._ser = serial.Serial(port=self.port,
                                  baudrate=self._baudrate,
                                  parity=self._parity,
                                  rtscts=self._rtscts,
                                  dsrdtr=self._dsrdtr,
                                  timeout=self._timeout)
        if self._ser.isOpen() is False:
            try:
                self._sock.connect()
            except ValueError as ex:
                logging.error("Wrong connection parameters: %r", ex)
                return False
            except serial.timeout:
                logging.error("Timeout on connection")
                return False
        logging.info("Connected to SR8x0")
        return True

    def close(self):
        """Closes the underlying serial connection
        """
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception as ex:
                logging.error("Error when closing USB connection: %r", ex)
        self._ser = None
        logging.info("Connection to SR8x0 closed")

    def write(self, data):
        """Specific serial writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        try:
            nb_bytes = self._ser.write((data + '\n').encode('utf-8'))
        except serial.SerialTimeoutException:
            logging.error("Device write timeout")
            return 0
        logging.debug("write %s", data)
        return nb_bytes

    def read(self, length):
        """Specific serial reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        try:
            retval = self._ser.read(length).decode('utf-8').strip('\n')
        except serial.SerialTimeoutException:
            logging.error("Device read timeout")
            return ''
        logging.debug("read %s", retval)
        return retval


# =============================================================================
if __name__ == '__main__':
    import sys
    import argparse

    # Handles log
    DATE_FMT = "%d/%m/%Y %H:%M:%S"
    LOG_FORMAT = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d): %(message)s"
    logging.basicConfig(level=logging.DEBUG,
                        datefmt=DATE_FMT,
                        format=LOG_FORMAT)

    PARSER = argparse.ArgumentParser(description='Lakeshore Monitoring')
    PARSER.add_argument('--port', dest='port', type=str,
                        help='If interface = \'usb\', serial port')
    ARGS = PARSER.parse_args()
    PORT = ARGS.port

    INST = Sr8x0Serial(port=PORT, baudrate=9600, timeout=1.0)
    RETVAL = INST.connect()
    if RETVAL is False:
        sys.exit("Connection error")

    print("IDN: %s" % INST.idn)

    print("Single shot acquisition")
    INST.reset_data_storage()
    INST.sample_rate = sr8x0.SAMPLE_RATES["256 Hz"]
    INST.single_shot = 1
    INST.start_data_storage()
    INST.wait_bit0()
    DATA = INST.read_buffer(_format='a')
    with open("sr810_data.dat", 'w') as fd:
        fd.write("# Sample rate: " + INST.sample_rate)
        for i in DATA:
            fd.write("%e\n" % i)
    INST.close()
