# -*- coding: utf-8 -*-

"""scinstr.tctrl
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2018-2025
license   GPL v3.0+
brief     Base class to handle Lakeshore 350 device.
"""

import logging
import socket
import time
import serial

# Ethernet specific
PORT = 7777
ETH_TIMEOUT = 1.0  # in second

# USB specific
BAUDRATE = 57600
DATA_BITS = serial.SEVENBITS
STOP_BIT = serial.STOPBITS_ONE
ODD_PARITY = serial.PARITY_ODD
USB_TIMEOUT = 1.0  # 0 is non-blocking mode

CMD = ('CLS', '*ESE', '*ESE?', '*ESR?', '*IDN?', '*OPC', '*OPC?', '*RST',
       '*SRE', '*SRE?', '*STB?', '*TST?', '*WAI', 'ALARM', 'ALARM?',
       'ALARMST?', 'ALMRST', 'ANALOG', 'ANALOG?', 'AOUT?', 'ATUNE', 'BRIGT',
       'BRIGT?', 'CRDG?', 'CRVDEL', 'CRVHDR', 'CRVHDR?', 'CRVPT', 'CRVPT?',
       'DFLT', 'DIOCUR', 'DISPFLD', 'DISPFLD?', 'DISPLAY', 'DISPLAY?',
       'FILTER', 'FILTER?', 'HTR?', 'HTRSET', 'HTRSET?', 'HTRST?', 'IEEE',
       'IEEE?', 'INCRV', 'INCRV?', 'INNAME', 'INNAME?', 'INTSEL', 'INTSEL?',
       'INTYPE', 'INTYPE?', 'KRDG?', 'LEDS', 'LEDS?', 'LOCK', 'LOCK?',
       'MDAT?', 'MNMXRST', 'MODE', 'MODE?', 'MOUT', 'MOUT?', 'NET', 'NET?',
       'NETID?', 'OPST?', 'OPSTE', 'OPSTE?', 'OPSTR?', 'OUTMODE', 'OUTMODE?',
       'PID', 'PID?', 'RAMP', 'RAMP?', 'RAMPST?', 'RANGE', 'RANGE?', 'RDGST?',
       'RELAY', 'RELAY?', 'RELAYST?', 'SCAL', 'SETP', 'SETP?', 'SRDG?',
       'TEMP?', 'TLIMIT', 'TLIMIT?', 'TUNEST?', 'WARMUP', 'WARMUP?', 'WEBLOG',
       'WEBLOG?', 'ZONE', 'ZONE?')


# =============================================================================
class L350():
    """Base class to handle Lakeshore 350 device.
    """

    def connect(self):
        """Abstract protocol connect process. Derived classes must implement
        the connect process dedicated to the specific protocol used.
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    def close(self):
        """Abstract protocol closing process. Derived classes must implement
        the closing process dedicated to the specific protocol used.
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _write(self, data):
        """Abstract protocol write process. Derived classes must implement
        the write process dedicated to the specific protocol used.
        :param data: data writes to device (str)
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _read(self, length):
        """Abstract protocol read process. Derived classes must implement
        the read process dedicated to the specific protocol used.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def read(self, length=None):
        """A basic read method: read a message from device.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        try:
            retval = self._read(length)
        except Exception as ex:
            logging.error("Read error: %r", ex)
            return ''
        logging.debug("read: %r", retval)
        return retval

    def write(self, data):
        """A basic write method: writes "data" to device.
        :param data: data writes to device (str)
        :returns: None
        """
        try:
            nb_bytes = self._write(data)
        except Exception as ex:
            logging.error("Write error: %r", ex)
            return 0
        logging.debug("write: %r", data)
        return nb_bytes

    def query(self, data, length=1024):
        """Write than read procedure.
        :param data: data writes to device (str)
        :returns: Message returned by device (str)
        """
        self.write(data)
        return self.read(length)

    def local(self):
        """Set device in local mode.
        :returns: None
        """
        self.write("MODE 0")

    def remote(self, lock=False):
        """Set device in remote mode. If lock is True, device is in remote
        mode with local lockout.
        :param lock: if True, remote with local lockout (bool)
        :returns: None
        """
        if lock is True:
            self.write("MODE 2")
        else:
            self.write("MODE 1")

    @property
    def idn(self):
        """Return product id of device.
        :returns: product id of device (str)
        """
        _id = self.query("*IDN?")
        return _id

    def get_rc(self, key: int) -> float:
        """Return resistance value with respect to key:
        - 0 -> Channel A
        - 1 -> Channel B
        - 2 -> Channel C
        - 3 -> Channel D
        - 4 -> Heater 1
        - 5 -> Heater 2
        """
        if key == 0:
            return float(self.query('SRDG? A', 128))
        elif key == 1:
            return float(self.query('SRDG? B', 128))
        elif key == 2:
            return float(self.query('SRDG? C', 128))
        elif key == 3:
            return float(self.query('SRDG? D', 128))
        elif key == 4:
            return float(self.query('HTR? 1', 128))
        elif key == 5:
            return float(self.query('HTR? 2', 128))
        else:
            raise ValueError("Key value must be beetween 0 and 5.")

    def get_tc(self, key: int) -> float:
        """Return temperature value with respect to key:
        - 0 -> Channel A
        - 1 -> Channel B
        - 2 -> Channel C
        - 3 -> Channel D
        - 4 -> Heater
        """
        if key == 0:
            return float(self.query('KRDG? A', 128))
        elif key == 1:
            return float(self.query('KRDG? B', 128))
        elif key == 2:
            return float(self.query('KRDG? C', 128))
        elif key == 3:
            return float(self.query('KRDG? D', 128))
        elif key == 4:
            return float(self.query('HTR? 1', 128))
        elif key == 5:
            return float(self.query('HTR? 2', 128))
        else:
            raise ValueError("Key value must be beetween 0 and 5.")

    def get_rc_all(self) -> list[float]:
        """Return all resistances and all heater values.
        """
        retval = self.query("SRDG? A; SRDG? B;SRDG? C;SRDG? D;HTR? 1;HTR? 2", 512)
        return [float(value) for value in retval.split(';')]

    def get_tc_all(self) -> list[float]:
        """Return all temperatures and all heater values.
        """
        retval = self.query("KRDG? A; KRDG? B;KRDG? C;KRDG? D;HTR? 1;HTR? 2", 512)
        return [float(value) for value in retval.split(';')]


# =============================================================================
class L350Eth(L350):
    """Handle Lakeshore 350 device through ethernet interface.
    """

    def __init__(self, ip='', port=PORT, timeout=ETH_TIMEOUT):
        """'Constructor'.
        :param ip: IP address of device (str)
        :param port: Device port in use (int)
        :param timeout: Timeout in second (float)
        :returns: None
        """
        self._sock = None
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def connect(self):
        """Open connection with device.
        :returns: True if connection succeed False elsewhere (bool)
        """
        self._sock = socket.socket(socket.AF_INET,
                                   socket.SOCK_STREAM,
                                   socket.IPPROTO_TCP)
        self._sock.settimeout(self.timeout)
        try:
            self._sock.connect((self.ip, self.port))
        except ValueError as ex:
            logging.error("Wrong connection parameters: %r", ex)
            return False
        except socket.timeout:
            logging.error("Timeout on connection")
            return False
        logging.info("Connected to Lakeshore")
        return True

    def close(self):
        """Close connection with device.
        :returns: None
        """
        if self._sock is None:
            return
        self._sock.close()
        self._sock = None
        logging.info("Connection to Lakeshore closed")

    def _write(self, data):
        """Specific ethernet writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        time.sleep(0.01)  # Device seems temporisation between com
        return self._sock.send((data + '\n').encode('utf-8'))

    def _read(self, length=100):
        """Specific ethernet reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        time.sleep(0.01)  # Device seems temporisation between com
        return self._sock.recv(length).decode('utf-8').strip('\r\n')


# =============================================================================
class L350Usb(L350):
    """Handle Lakeshore 350 device through USB interface.
    The USB interface emulates an RS-232 serial port with the folowing
    configuration parameters (see manual p.116):
    - Baud rate 57,600
    - Data bits 7
    - Start bits 1
    - Stop bits 1
    - Parity Odd
    - Flow control None
    - Handshaking None
    """

    def __init__(self, port='', timeout=USB_TIMEOUT):
        self._ser = None
        self.port = port
        self._timeout = timeout

    def connect(self):
        """Connect to the remote host.
        :returns: True if connection succeeded, False otherwise (bool)
        """
        self._ser = serial.Serial(self.port,
                                  baudrate=BAUDRATE,
                                  bytesize=DATA_BITS,
                                  parity=ODD_PARITY,
                                  stopbits=STOP_BIT,
                                  timeout=self._timeout)
        if self._ser.isOpen() is False:
            try:
                self._ser.open()
            except ValueError as ex:
                logging.error("Wrong connection parameters: %r", ex)
                return False
        logging.info("Connected to Lakeshore")
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
        logging.info("Connection to Lakeshore closed")

    def _write(self, data):
        """Specific USB writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        time.sleep(0.05)  # 50 ms minimum between USB com (p.120-121 manual)
        return self._ser.write((data + '\n').encode('utf-8'))

    def _read(self, length=None):
        """Specific USB reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        time.sleep(0.05)  # 50 ms minimum between USB com (p.120-121 manual)
        return self._ser.read_until(size=length).decode('utf-8').strip('\r\n')

    def hard_flush(self):
        """Try to make a "hard" flush of output data.
        Needed because commands can cause inappropriate behavior (CRVDEL)
        :returns: None
        """
        self._ser.flush()
        self._ser.reset_output_buffer()
        time.sleep(1.0)

    @property
    def timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        if self._ser is None:
            return self._timeout
        return self._ser.timeout

    @timeout.setter
    def timeout(self, timeout):
        """Sets timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        self._timeout = timeout
        if self._ser is None:
            return
        self._ser.timeout = timeout
