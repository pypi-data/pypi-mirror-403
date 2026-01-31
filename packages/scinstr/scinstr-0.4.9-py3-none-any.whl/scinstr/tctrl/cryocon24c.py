# -*- coding: utf-8 -*-

"""package cryocon
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2018
brief     Basic API for Cryo-Con 24C gauge device.
details   The 24C model is a cryogenic temperature controller device from
          CRYOgenic CONtrol system. The 24C model has two remote interfaces:
          ethernet LAN and RS-232.
          Messages are transmitted to the Cryo-Con 24C as ASCII strings in
          the form of mnemonics and parameters:
              INPut { A | B }:ALARm:HIGH <value>;NAMe "name";
          Mnemonics:
          *IDN?, *CLS, *OPC?
          INPut, TEMPerature, UNITs, VARIance, SLOPe, ALARm, NAMe
          SYSTem, BEEP, ADRS, LOCKout, LOOP, SETPT, RANGe, RATe
          CONFig, SAVE, RESTore
"""

import socket
import logging
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot

from constants import CC24C_ID, CC24C_PORT, CC24C_DEFAULT_TIMEOUT


# =============================================================================
class CryoCon24cEth(QObject):
    """Class dedicated to handle Cryo-Con 24C from ethernet interface.
    """

    connected = pyqtSignal()
    closed = pyqtSignal()
    id_checked = pyqtSignal(bool)
    outUpdated = pyqtSignal(str)

    def __init__(self, ip, port=CC24C_PORT, timeout=CC24C_DEFAULT_TIMEOUT):
        """Constructor.
        :param ip: IP address of device (str)
        :param port: ethernet interface port value (int)
        :param timeout: socket timeout value in second (float)
        """
        super(CryoCon24cEth, self).__init__()
        self._ip = ip
        self._port = port
        self._timeout = timeout
        self._sock = None

    @pyqtSlot()
    def connect(self):
        """Specific ethernet connection process to device.
        :returns: True if connection success other False (Bool)
        """
        try:
            logging.info('Connecting to device @%s...', self._ip)
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(self._timeout)
        except socket.error as er:
            logging.error("Socket error: %r", er)
            raise
        except ValueError as ex:
            logging.error("Connection parameters out of range: %r", ex)
            raise
        except Exception as er:
            logging.error("Unexpected socket error: %r", er)
            raise
        try:
            self._sock.connect((self._ip, self._port))
        except socket.timeout:
            logging.warning("Socket timeout error during connection.")
            raise
        except socket.error as er:
            logging.error("Socket error during connection: %r", er)
            raise
        except Exception as er:
            logging.error("Unexpected error during connection: %r", er)
            raise
        else:
            self.connected.emit()
            logging.info("Connected to Cryo-Con 24C")
            return True
        return False

    @pyqtSlot()
    def close(self):
        """Specific ethernet closing process with Cryo-Con 24C.
        :returns: None
        """
        try:
            self._sock.close()
        except Exception as ex:
            logging.error("%r", ex)
        else:
            self._sock = None
            self.closed.emit()
            logging.info("Connection to Cryo-Con 24C closed")

    @pyqtSlot()
    def check_interface(self):
        """Basic interface connection test: check id of device.
        Return True if interface with device is OK.
        :returns: status of interface with device (bool)
        """
        try:
            self.connect()
            _id = str(self.get_id())
        except Exception:  # Catch connection and get_id problem
            _id = ""  # To avoid error with 'find()' if '_id' is not defined
        else:
            self.close()
        if _id.find(CC24C_ID) >= 0:
            self.id_checked.emit(True)
            return True
        self.id_checked.emit(False)
        return False

    @pyqtSlot()
    def get_id(self):
        """Return product id of device.
        :returns: product id of device (str)
        """
        self._write("*IDN?")
        _id = self._sock.recv(100)
        return _id

    @pyqtSlot(float)
    def set_timeout(self, timeout):
        """Sets timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        self._sock.settimeout(timeout)

    @pyqtSlot()
    def get_timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        return self._sock.gettimeout()

    @pyqtSlot(str)
    def set_ip(self, ip):
        """Sets IP address used to speak with device.
        :param ip: IP address (str)
        :return: None
        """
        self._ip = ip

    @pyqtSlot()
    def get_ip(self):
        """Gets IP used to speak with device.
        :returns: IP address (str)
        """
        return self._ip

    @pyqtSlot(int)
    def set_port(self, port):
        """Sets ethernet port used to speak with device.
        :param port: port used by 24C (int)
        :returns: None
        """
        self._port = port

    @pyqtSlot()
    def get_port(self):
        """Gets ethernet port used to speak with device.
        :returns: port used by 24C (int)
        """
        return self._port

    def read(self, size=128):
        """Basic read process.
        :param size: max number of bytes to read, None -> no limit (int)
        :returns: data received or False if communication error (str)
        """
        return self._read(size)

    def write(self, msg=""):
        """Write message to device.
        :param  msg: data wite to device (str)
        :returns: True if transmission OK else False (bool)
        """
        return self._write(msg)

    def ask(self, msg="", length=128):
        """Ask procedure ie read data after write.
        :param msg: data wite to device (str)
        :returns: data received (str)
        """
        write_ok = self._write(msg)
        if write_ok is False:
            return ""
        result = self._read(length)
        self.outUpdated.emit(result)
        return result

    def _write(self, msg=""):
        """Specific ethernet writing process.
        :param msg: data writes to device (str)
        :returns: True if transmission OK else False (bool)
        """
        try:
            self._sock.send(msg + '\n')
        except socket.timeout:
            logging.error("24C write timeout")
            return False
        except Exception as ex:
            logging.error(str(ex))
            return False
        logging.debug("_write %s", msg)
        return True

    def _read(self, length):
        """Specific ethernet reading process.
        :param length: length of message to read (int)
        :returns: Message read from device (str)
        """
        try:
            retval = self._sock.recv(length).rstrip('\n')
        except socket.timeout:
            logging.error("24C read timeout")
            return ""
        except Exception as ex:
            logging.error("Unexpected read error: %r", ex)
            return ""
        logging.debug("_read %s", retval)
        return retval
