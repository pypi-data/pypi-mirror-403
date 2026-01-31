# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2019-2025
license   GPL v3.0+
brief     API dedicated to handle the Keysight 532X0A counter serie.
"""

import logging
import socket
import usbtmc
from scinstr.cnt.constants import (
    CNT532X0A_PORT,
    CNT532X0A_TIMEOUT,
    CNT532X0A_VID,
    CNT532X0A_PID,
)


# =============================================================================
def isfloat(value):
    """Basic float test type function.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False
    except TypeError:
        return False


# =============================================================================
class Cnt532x0aAbstract:
    """Abstract class to handling Counter532x0a digital multimeter device.
    Derived classes need to re-implement specific-protocol methods: connect(),
    close(), _write(), _read()...
    """

    def __del__(self):
        if self.is_connected:
            self.local()

    def connect(self):
        """Abstract protocol connect process. Derived classes must implement
        the connect process dedicated to the specific protocol used.
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    @property
    def is_connected(self):
        """Abstract connection check property.
        :returns: True if device connected else False (bool)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def close(self):
        """Abstract protocol closing process. Derived classes must implement
        the closing process dedicated to the specific protocol used.
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _write(self, data) -> int:
        """Abstract protocol write process. Derived classes must implement
        the write process dedicated to the specific protocol used.
        :param data: data writes to device (str)
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _read(self) -> str | None:
        """Abstract protocol read process. Derived classes must implement
        the read process dedicated to the specific protocol used.
        :returns: Message reads from device (str)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def write(self, data: str) -> int:
        """A basic write method: writes "data" to device.
        :param data: data writes to device (str)
        :returns: number of writed byte, -1 in case of error
        """
        try:
            retval = self._write(data)
        except Exception as ex:
            logging.error("Write error: %r", ex)
            return -1
        logging.debug(f"write: {data}")
        return retval

    def read(self) -> str | None:
        """A basic read method: read a message from device.
        :param length: length of message to read (int)
        :returns: Message reads from device, None if error (str)
        """
        try:
            retval = self._read()
        except Exception as ex:
            logging.error("Read error: %r", ex)
            return None
        logging.debug(f"read: {retval}")
        return retval

    def query(self, msg) -> None | str:
        """Read after write method.
        :param data: data writes to device (str)
        :param length: length of message to read (int)
        :returns: Message returned by device (str)
        """
        if self.write(msg) < 0:
            return None
        return self.read()

    def reset(self) -> bool:
        """Resets meter to its power-on state, sets all bits to zero in
        status byte register and all event registers and clear error queue.
        :returns: None
        """
        try:
            self._write("*RST")
            self._write("*CLS")
        except Exception as ex:
            logging.error(ex)
            return False
        logging.info("Counter reseted")
        return True

    def get_error(self) -> list[str] | None:
        """Return list of current error.
        :returns: list of current error (list of str)
        """
        errors = []
        while True:
            error = self.query("SYST:ERR?")
            if error is None or error == "":
                logging.error(f"Get error from device failed.")
                return None
            if "No error" in error:
                break
            errors.append(error)
        return errors

    def local(self):
        self.write("SYST:LOCK:REL")

    def data_read(self) -> float | None:
        """Takes a measurement the next time the trigger condition is met.
        After the measurement is taken, the reading is placed in the output
        buffer. "data_read" will not cause readings to be stored in the Meter’s
        internal memory.
        :returns: data read in buffer (float)
        """
        data = self.query("READ?")
        if data is None:
            logging.error(f"READ? returns None")
            return None
        try:
            data = float(data)
        except ValueError:
            logging.error(f"Invalid data {data}")
            return None
        return data


# =============================================================================
class Cnt532x0aEth(Cnt532x0aAbstract):
    """Class handling the 532x0a device through ethernet protocol."""

    def __init__(self, ip="", port=CNT532X0A_PORT, timeout=CNT532X0A_TIMEOUT):
        """The constructor.
        :param ip: IP address of device (str)
        :param port: socket port of device (int)
        :param timeout: socket timeout value in s (float)
        :returns: None
        """
        super().__init__()
        self._sock = None
        self.ip = ip
        self.port = port
        self._timeout = timeout

    def connect(self):
        """Specific ethernet connection process to Counter532x0a.
        :returns: True if connection success other False (Bool)
        """
        self._sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
        )
        self._sock.settimeout(self._timeout)
        try:
            self._sock.connect((self.ip, self.port))
        except ValueError as ex:
            logging.error("Connection parameters out of range: %r", ex)
            return False
        except socket.timeout:
            logging.error("Timeout on connection")
            return False
        except Exception as ex:
            logging.critical("Connection problem: %r", ex)
            return False
        logging.info("Connected to Counter532x0a")
        return True

    @property
    def is_connected(self):
        if self._sock is None:
            return False
        return True

    def close(self):
        """Specific ethernet closing process with Counter532x0a.
        :returns: None
        """
        super().close()
        try:
            self._sock.close()
        except Exception as ex:
            logging.error("%r", ex)
        self._sock = None
        logging.info("Connection to Counter532x0a closed")

    def _write(self, data):
        """Specific ethernet writing process.
        :param data: data writes to device (str)
        :returns: number of byte sent (int)
        """
        return self._sock.send((data + "\n").encode("utf8"))

    def _read(self, length):
        """Specific ethernet reading process.
        :param length: length of message to read (int)
        :returns: message reads from device (str)
        """
        return self._sock.recv(length).decode("utf-8").strip("\n")

    @property
    def timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        return self._sock.gettimeout()

    @timeout.setter
    def timeout(self, value):
        """Sets timeout on socket operations.
        :param value: timeout value in second (float)
        :returns: None
        """
        self._sock.settimeout(value)
        self._timeout = value


# =============================================================================
class Cnt532x0aUsb(Cnt532x0aAbstract):
    """Handle counter device through USB connection."""

    def __init__(
        self,
        vendor_id=CNT532X0A_VID,
        product_id=CNT532X0A_PID,
        timeout=CNT532X0A_TIMEOUT,
    ):
        self._dev = None
        self.vid = vendor_id
        self.pid = product_id
        self._timeout = timeout

    def connect(self):
        """Connect to the remote host.
        :returns: True if connection succeeded, False otherwise
        """
        logging.info("Connecting to counter")
        try:
            self._dev = usbtmc.Instrument(self.vid, self.pid)
        except usbtmc.usbtmc.UsbtmcException as ex:
            logging.error("Connection problem: %r", ex)
            return False
        self._dev.timeout = self._timeout
        logging.info("Connection --> Ok")
        return True

    @property
    def is_connected(self):
        if self._dev is None:
            return False
        return True

    def close(self):
        """Closes the underlying serial connection"""
        if self._dev is not None:
            try:
                self._dev.close()
            except Exception as ex:
                logging.error("Error when closing USB connection: %r", ex)
        self._dev = None
        logging.info("Connection to counter closed")

    def _write(self, data):
        """Specific USB writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        if not self.is_connected:
            self.connect()
        self._dev.write(data)
        return len(data)

    def _read(self):
        """Specific USB reading process.
        :returns: Message reads from device (str)
        """
        if not self.is_connected:
            self.connect()
        return self._dev.read()

    @property
    def timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        if self._dev is not None:
            return self._dev.timeout
        return None

    @timeout.setter
    def timeout(self, timeout):
        """Sets timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        if self._dev is not None:
            self._dev.timeout = timeout
            self._timeout = timeout


# =============================================================================
def check_counter532x0a():
    """Checks the Counter532x0axx class: connect to the counter, configure
    a basic measurement then collects and print data to standard output.
    """
    from datetime import datetime

    date_fmt = "%d/%m/%Y %H:%M:%S"
    log_format = (
        "%(asctime)s %(levelname) -8s %(filename)s "
        + " %(funcName)s (%(lineno)d): %(message)s"
    )
    logging.basicConfig(level=logging.INFO, datefmt=date_fmt, format=log_format)

    counter = Cnt532x0aUsb(0x0957, 0x1707, timeout=2.8)
    # counter = Cnt532x0aEth(ip="192.168.0.20", port=5025, timeout=1.5)
    if counter.connect() is not True:
        print("Connection failed")
        return
    counter.reset()

    print("IDN:", counter.idn())
    counter.write("CONF:FREQ 100.0E6")
    counter.write("TRIG:SOUR IMM")
    counter.write("TRIG:SLOP POS")
    counter.write("SENS:FREQ:GATE:TIME 1.0")
    counter.write("SENS:FREQ:GATE:SOUR TIME")
    print("Error config?:", counter.get_error())

    try:
        while True:
            value = counter.data_read()
            now = datetime.utcnow()
            if value is None or value == "":
                print("# No data @", now)
            else:
                print(now, value)
    except KeyboardInterrupt:
        counter.write("ABORT")
    except Exception as er:
        logging.error("# Exception during acquisition: %r", er)

    counter.close()


# =============================================================================
if __name__ == "__main__":
    check_counter532x0a()
