# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2019-2025
license   GPL v3.0+
brief     API dedicated to handle Siglent SDM3065x and derivative digital
          multimeters.
"""

import logging
import time
import struct
import usb
import pyvisa

from scinstr.dmm.constants import (
    SDM3065X_TIMEOUT,
    SDM3065X_ID,
    SDM3065X_VID,
    SDM3065X_PID,
)

pyvisa.ResourceManager('@py')


MAX_REQUEST_RETRIES = 5
MAX_READ_FLUSH_ATTEMPT = 10

# Multimeter functions
(
    CAP,
    CURR,
    CURRDC,
    VOLTAC,
    VOLTDC,
    VOLTDCRAT,
    RES,
    FRES,
    FRE,
    PER,
    TEMPRTD,
    TEMPFRTD,
    DIOD,
    CONT,
) = (
    "CAP",
    "CURR",
    "CURR:DC",
    "VOLT:AC",
    "VOLT:DC",
    "VOLT:DC:RAT",
    "RES",
    "FRES",
    "FRE",
    "PER",
    "TEMP:RTD",
    "TEMP:FRTD",
    "DIOD",
    "CONT",
)

# Integration time
(PLC002, PLC02, PLC1, PLC10, PLC100) = ("0.02", "0.2", "1", "10", "100")

# Voltage input range
(RANGE10MV, RANGE1V, RANGE10V, RANGE100V, RANGE1000V) = (
    "0.1",
    "1",
    "10",
    "100",
    "1000",
)

# Trigger source
(IMM, EXT, BUS) = ("IMM", "EXT", "BUS")


# =============================================================================
class Sdm3065xAbstract:
    """Abstract class to handling Sdm3065x digital multimeter device. Derived
    classes need to re-implement specific-protocol methods: connect(), close(),
    _write(), _read()...
    """

    def _write(self, data: str) -> int:
        """Abstract protocol write process. Derived classes must implement
        the write process dedicated to the specific protocol used.
        :param data: data writes to device (str)
        :returns: number of writed byte
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _read(self) -> str:
        """Abstract protocol read process. Derived classes must implement
        the read process dedicated to the specific protocol used.
        :returns: Message reads from device (str)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def query(self, msg) -> str:
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
            logging.error(f"Write message:{data}, error: {ex}")
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
            logging.error(f"Read error: {ex}")
            return None
        logging.debug(f"read: {retval}")
        return retval

    def flush(self) -> bool:
        """Flush DMM HW buffer"""
        read_flush_attempt = MAX_READ_FLUSH_ATTEMPT
        while read_flush_attempt >= 0:
            try:
                _ = self._read()
            except usb.core.USBTimeoutError:
                return True
            read_flush_attempt -= 1

            logging.critical(f"flush({read_flush_attempt})")

        logging.error("DMM flush failed")
        return False

    def reset(self) -> bool:
        """Resets meter to its power-on state, sets all bits to zero in
        status byte register and all event registers and clear error queue.
        :returns: None
        """
        try:
            self.write("ABOR")
            self.write("*RST")
            self.write("*CLS")
        except Exception as ex:
            logging.error("reset failed %r", ex)
            return False
        time.sleep(2.0)
        logging.info("DMM reseted")
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

    def check_interface(self) -> bool:
        """Basic interface connection test: check id of device.
        Return True if interface with device is OK.
        :returns: status of interface with device (bool)
        """
        id_ = self.query("*IDN?")
        if id_ is None:
            return False
        if SDM3065X_ID in id_:
            return True
        return False

    def data_read(self) -> float | None:
        """Takes a measurement the next time the trigger condition is met.
        After the measurement is taken, the reading is placed in the output
        buffer. "data_read" will not cause readings to be stored in the Meter’s
        internal memory.
        Read method convenient for slow measurement.
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
class Sdm3065xUsb(Sdm3065xAbstract):
    """Handle DMM device through USB connection."""

    def __init__(
        self, vendor_id=SDM3065X_VID, product_id=SDM3065X_PID, timeout=SDM3065X_TIMEOUT, serial_id=None
    ):
        rm = pyvisa.ResourceManager()
        # USB[board]::manufacturer ID::model code::serial number[::USB interface number][::INSTR]
        # USB::0x1234::125::A22-5::INSTR
        self._dev = rm.open_resource(f"USB::{vendor_id}::{product_id}::{serial_id}::INSTR")
        self._dev.read_termination = '\n'
        self._dev.write_termination = '\n'
        self._dev.timeout = timeout * 1000

    def _write(self, data: str):
        """Specific USB writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        self._dev.write(data)
        return len(data)

    def _read(self) -> str:
        """Specific USB reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        request_retry = MAX_REQUEST_RETRIES
        while True:
            try:
                msg = self._dev.read()
            except struct.error:
                print(f"request_retry: {request_retry}")
                request_retry -= 1
                if request_retry < 0:
                    raise ConnectionError("_read() failed")
                continue
            break
        return msg

    def query(self, msg):
        return self._dev.query(msg)

    def ask(self, msg):
        return self.query(msg)

    @property
    def timeout(self):
        """Get timeout on socket operations.
        :returns: timeout value in second (float)
        """
        return self._dev.timeout / 1000

    @timeout.setter
    def timeout(self, timeout):
        """Set timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        self._dev.timeout = timeout * 1000


# =============================================================================
def check_dmm():
    """Check the Dmm34461axx class: connect to the multimeter, configure a dc
    voltage measurement then collect and print data to standard output.
    """
    import datetime

    date_fmt = "%d/%m/%Y %H:%M:%S"
    log_format = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d): %(message)s"
    logging.basicConfig(level=logging.INFO,
                        datefmt=date_fmt,
                        format=log_format)

    from scinstr.dmm.constants import SDM3055_VID as VID
    from scinstr.dmm.constants import SDM3055_PID as PID

    SERIAL_ID = "SDM35HBQ802983"

    # rm = pyvisa.ResourceManager()
    # print(f"list_devices(): {rm.list_resources()}")

    dmm = Sdm3065xUsb(VID, PID, 2.1, SERIAL_ID)
    print("IDN:", dmm.query("*IDN?"))

    dmm.write("CONF:VOLT:DC")
    dmm.write("CONF:VOLT:DC auto")  # Range
    dmm.write("VOLT:DC:NPLC 10")
    dmm.write("VOLT:DC:AZ:STATE ON")  # Autozero state
    dmm.write("SAMP:COUN 1")
    dmm.write("TRIG:COUN 10")
    dmm.write("TRIG:SOUR IMM")
    dmm.write("INIT")
    # print("Error config?:", dmm.get_error())

    try:
        while True:
            try:
                # value = dmm.data_read()
                values = dmm.query("READ?")
                value = sum([float(x) for x in values.split(',')]) / len(values)
                # value = dmm.query("MEAS:VOLT:DC? auto")
                now = datetime.datetime.now(datetime.UTC)
                if value is None or value == "":
                    print("# No data @", now)
                else:
                    print(now, value)
            except KeyboardInterrupt:
                break
            except Exception as er:
                logging.error("# Exception during acquisition: %r", er)
    except KeyboardInterrupt:
        dmm.write("ABORT")

    print("Final error?:", dmm.get_error())


# =============================================================================
if __name__ == '__main__':
    check_dmm()