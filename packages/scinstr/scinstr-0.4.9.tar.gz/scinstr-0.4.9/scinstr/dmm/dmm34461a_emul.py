# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2019
license   GPL v3.0+
brief     Emulation of basic SCPI DMM
"""

import logging
import time
import threading
import random
import signalslot as ss
from remi import start, Server
import scinstr.dmm.dmm34461a as dmm34461a
import scinstr.dmm.dmm_emul_server as dmm_server
from enum import Enum

# Only to mime real device import (detection of circular reference)
import socket
import usbtmc

DEFAULT_ENABLE_PERIOD = 15
DEFAULT_DISABLE_PERIOD = 5

DmmMode= Enum('Mode', [("VOLTMETER", 1), ("FREQUENCYMETER", 2)])


class RepeatTimer(threading.Timer):
    """From https://stackoverflow.com/questions/12435211/threading-timer-repeat-function-every-n-seconds
    """
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


# =============================================================================
class Dmm34461aEmul(dmm34461a.Dmm34461aAbstract):
    """Emulate DMM device connected.
    """

    def __init__(self, *args, **kwargs):
        """The constructor.
        :returns: None
        """
        logging.info("Init DMM test device: %r", self)
        super().__init__()
        self._is_communication_faillure = False
        self._communication_state = True
        self._com_fail_duration = {'enable':DEFAULT_ENABLE_PERIOD, 'disable': DEFAULT_DISABLE_PERIOD}
        self._com_period_timer = None
        self._is_random_data = True
        self._ofreq = 99e6
        self._volt = 4.0
        self._mode = DmmMode.VOLTMETER
        for idx, value in enumerate(args):
            logging.info('DMM test device non-keyworded argument %02d: %r',
                         idx, value)
        for key, value in kwargs.items():
            logging.info('DMM test device named argument %r: %r', key, value)
        logging.info("DMM test device %r initialization done", self)
        start(dmm_server.SDmm34461aServer, userdata=(self,))

    def _disable_device_connection(self, duration):
        self._communication_state = False
        print("Enter sleep")
        time.sleep(duration)
        print("exit sleep")
        self._communication_state = True


    def set_frequency(self, value):
        self._ofreq = value
        print(f"set_ofreq {value}")

    def set_voltage(self, value):
        self._volt = value
        print(f"set_volt {value}")

    def set_communication_faillure_params(self, enable_period=DEFAULT_ENABLE_PERIOD, disable_period=DEFAULT_DISABLE_PERIOD):        
        self._com_fail_duration['enable'] = enable_period
        self._com_fail_duration['disable'] = disable_period

    def set_communication_faillure_state(self, value):
        if value is False:
            if self._com_period_timer:
                self._com_period_timer.cancel()
            return
        self._is_communication_faillure = True
        self._com_period_timer = RepeatTimer(
            self._com_fail_duration['enable'], 
            self._disable_device_connection, 
            args=(self._com_fail_duration['disable'],)
        )
        print("Start TIMER")
        self._com_period_timer.start()

    def set_random_data(self, state=False, value=0.0):
        self._is_random_data = state

    def connect(self):
        """Connection process to DMM.
        :returns: True if connection success other False (Bool)
        """
        logging.info("Connected to DMM test device: %r", self)
        return True

    @property
    def is_connected(self):
        """Check connection property.
        :returns: True if device connected else False (bool)
        """
        logging.info("Test connection to DMM test device: %r", self)
        return True

    def close(self):
        """Closing process with DMM.
        :returns: None
        """
        logging.info("Connection to DMM test device %r closed", self)

    def get_error(self):
        """Subclass method to emulate response of device.
        """
        return ["+0,\"No error\""]

    @property
    def timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        logging.info("Get DMM test device timeout: %r", self._timeout)
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        """Sets timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        self._timeout = timeout
        logging.info("Set DMM test device timeout: %r", timeout)

    def _write(self, data):
        """Emulate write process
        :param data: data writes to device (str)
        :returns: None
        """
        if self._communication_state is False:
            raise ConnectionError("Communication with (emulated) DMM failled")
        if data == "CONF:FREQ":
            # self.set_random_data(False, 0.1)
            self._mode = DmmMode.FREQUENCYMETER
        elif data == "CONF:VOLT:DC":
            # self.set_random_data(True)
            self._mode = DmmMode.VOLTMETER
        logging.info("Write %r to DMM test device %r", data, self)

    def data_read(self):
        time.sleep(1.0)
        if self._mode == DmmMode.FREQUENCYMETER:
            return self._ofreq
        else:
            return self._volt

    def _read(self, length):
        """Emulate read process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        if self._communication_state is False:
            raise ConnectionError("Communication with (emulated) DMM failled")
        if self._is_random_data is True:
            data = self._random_gen()
        else:
            data = 0.0  #self._static_data
        logging.info("Read %r from DMM test device %r", data, self)
        return data

    def _random_gen(self):
        """Return a random value: use to emulate data input acquisition.
        """
        time.sleep(1.0)
        return "{:+E}".format(random.uniform(-1.0, 1.0))


# =============================================================================
class SDmm34461aEmul(Dmm34461aEmul):
    """Class derived from Dmm34461aEmul class to add signal/slot facilities.
    """

    connected = ss.Signal()
    closed = ss.Signal()
    id_checked = ss.Signal(['flag'])
    out_updated = ss.Signal(['value'])

    def connect(self):
        """Abstract protocol connect process. Derived classes must implement
        the connect process dedicated to the specific protocol used.
        :returns: None
        """
        retval = super().connect()
        if retval is True:
            self.connected.emit()
        return retval

    def close(self):
        """Abstract protocol closing process. Derived classes must implement
        the closing process dedicated to the specific protocol used.
        :returns: None
        """
        super().close()
        self.closed.emit()

    def check_interface(self):
        retval = super().check_interface()
        self.id_checked.emit(flag=retval)
        return retval

    def data_read(self):
        retval = super().data_read()
        if retval is not None:
            self.out_updated.emit(value=retval)
            return retval

    def set_timeout(self, timeout, **kwargs):
        """Sets timeout on operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        self.timeout = timeout
        logging.info("Set DMM test device timeout: %r", timeout)

    def get_timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        logging.info("Get DMM test device timeout: %r", self.timeout)
        return self.timeout

    def set_pid(self, pid, **kwargs):
        """Set PID used to speak with device through USB.
        :param pid:
        :returns: None
        """
        self.pid = pid
        logging.info("Set DMM test device PID: %r", pid)

    def get_pid(self):
        """Get PID.
        :returns: pid
        """
        logging.info("Get DMM test device PID: %r", self.pid)
        return self.pid

    def set_vid(self, vid, **kwargs):
        """Set VID used to speak with device through USB.
        :param vid:
        :returns: None
        """
        self.vid = vid
        logging.info("Set DMM test device vid: %r", vid)

    def get_vid(self):
        """Get VID.
        :returns: vid
        """
        logging.info("Get DMM test device vid: %r", self.vid)
        return self.vid

    def set_ip(self, ip, **kwargs):
        """Sets IP address used to speak with device.
        :param ip: IP address (str)
        :return: None
        """
        self._ip = ip
        logging.info("Set DMM test device ip: %r", ip)

    def get_ip(self):
        """Gets IP used to speak with device.
        :returns: IP address (str)
        """
        logging.info("Get DMM test device ip: %r", self._ip)
        return self._ip

    def set_port(self, port, **kwargs):
        """Sets internet port used to speak with device.
        :param port: port used by DMM (int)
        :returns: None
        """
        self._port = port
        logging.info("Set DMM test device port: %r", port)

    def get_port(self):
        """Gets internet port used to speak with device.
        :returns: port used by DMM (int)
        """
        logging.info("Get DMM test device port: %r", self._port)
        return self._port


# =============================================================================
def check_dmm():
    """Check the Dmm34461axx class: connect to the multimeter, configures a dc
    voltage measurement then collect and print data to standard output.
    """
    import datetime

    date_fmt = "%d/%m/%Y %H:%M:%S"
    log_format = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d): %(message)s"
    logging.basicConfig(level=logging.INFO,
                        datefmt=date_fmt,
                        format=log_format)

    dmm = Dmm34461aEmul(0x2a8d, 0x1601, timeout=4.8)
    # dmm = Dmm34461aEmul(ip="192.168.0.61", port=5025, timeout=2.8)
    if dmm.connect() is not True:
        print("Connection failed")
        return
    dmm.reset()


    print("IDN:", dmm.query("*IDN?"))
    dmm.write("CONF:VOLT:DC AUTO")  # Autorange
    dmm.write("VOLT:DC:NPLC 100")
    dmm.write("VOLT:DC:ZERO:AUTO ON")  # Autozero off
    print("Error config?:", dmm.get_error())

    dmm.set_communication_faillure_params(4, 4)
    dmm.set_communication_faillure_state(True)

    try:
        while True:
            value = dmm.data_read()
            now = datetime.datetime.now(datetime.UTC)
            if value is None or value == "":
                print("# No data @", now)
                time.sleep(1.0)
            else:
                print(now, value)
    except KeyboardInterrupt:
        dmm.write("ABORT")
    except Exception as er:
        logging.error("# Exception during acquisition: %r", er)

    print("Final error?:", dmm.get_error())

    dmm.close()


# =============================================================================
if __name__ == '__main__':
    check_dmm()
