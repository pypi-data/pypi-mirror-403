# -*- coding: utf-8 -*-

"""package stanford
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2018
license   GPL v3.0+
brief     Class for handling SR8x0 device through ethernet connection.
details   Ethernet connection is provided through Prologix GPIB-Ethernet
          adapter.
"""

from iopy.prologix import PrologixGpibEth
import scinstr.lockin.sr8x0 as sr8x0


class Sr8x0Ethernet(sr8x0.Sr8x0):
    """Stanford Research System SR8x0 ethernet (prologix GPIB-Ethernet adapter)
    interface.
    """

    PORT = 1234

    def __init__(self, ip='', port=PORT, gpib_addr=1):
        self._intf = None
        self.ip = ip
        self.port = port
        self.gpib_addr = gpib_addr

    def connect(self):
        """Open connection with device.
        :param ip: IP address of device (str)
        :param port: Device port in use (int)
        :param timeout: Timeout in second (float)
        :returns: True if connection succeed False elsewhere (bool)
        """
        self._dev = PrologixGpibEth(self.ip, self.port, self.gpib_addr)
        try:
            self._dev.connect((self.ip, self.port))
        except ValueError as ex:
            logging.error("Wrong connection parameters: %r", ex)
            return False
        except Exception as ex:
            logging.error("Exception during connection: %r", ex)
            return False
        logging.info("Connected to SR8x0")
        return True

    def close(self):
        """Close connection with device.
        :returns: None
        """
        if self._dev is None:
            return
        self._dev.close()
        self._dev = None
        logging.info("Connection to SR8x0 closed")

    def write(self, data):
        """Specific ethernet writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        try:
            nb_bytes = self._dev.write((data + '\n').encode('utf-8'))
        except Exception as ex:
            logging.error("Device write error %r", ex)
            return 0
        logging.debug("write %r", data)
        return nb_bytes

    def read(self, length):
        """Specific ethernet reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        try:
            retval = (self._dev.read(length).decode('utf-8')).strip('\n')
        except Exception as ex:
            logging.error("Device read error %r", ex)
            return ''
        logging.debug("read %r", retval)
        return retval


# =============================================================================
if __name__ == '__main__':
    import logging
    import argparse

    # Handles log
    DATE_FMT = "%d/%m/%Y %H:%M:%S"
    LOG_FORMAT = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d): %(message)s"
    logging.basicConfig(level=logging.DEBUG,
                        datefmt=DATE_FMT,
                        format=LOG_FORMAT)

    parser = argparse.ArgumentParser(description='Lakeshore Monitoring')
    parser.add_argument('--ip', dest='ip', type=str,
                        help='If interface = \'ethernet\', IP of device')

    # Parse command line
    args = parser.parse_args()
    ip = args.ip

    INST = Sr8x0Ethernet(ip=ip, timeout=1.0)
    INST.connect()

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
