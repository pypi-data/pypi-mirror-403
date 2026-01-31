# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2019
license   GPL v3.0+
brief     API dedicated to handle the Keysight 34461A digital multimeter
          with signal/slot capabilities.
"""

import logging
import signalslot as ss

from scinstr.dmm.dmm34461a import Dmm34461aUsb, Dmm34461aEth


# =============================================================================
class SDmm34461aUsb(Dmm34461aUsb):
    """Class derived from Dmm34461aEth class to add signal/slot facilities.
    """

    connected = ss.Signal()
    closed = ss.Signal()
    id_checked = ss.Signal(['flag'])
    out_updated = ss.Signal(['value'])

    def connect(self):
        """Connection process.
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

    def get_timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        return self.timeout

    def set_pid(self, pid, **kwargs):
        """
        :param pid:
        :returns: None
        """
        self.pid = pid

    def get_pid(self):
        """
        :returns: pid
        """
        return self.pid

    def set_vid(self, vid, **kwargs):
        """
        :param vid:
        :returns: None
        """
        self.vid = vid

    def get_vid(self):
        """
        :returns: vid
        """
        return self.vid


# =============================================================================
class SDmm34461aEth(Dmm34461aEth):
    """Class derived from Dmm34461aEth class to add signal/slot facilities.
    """

    connected = ss.Signal()
    closed = ss.Signal()
    id_checked = ss.Signal(['flag'])
    out_updated = ss.Signal(['value'])

    def connect(self):
        """Connection process.
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
        """Sets timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        self._sock.settimeout(timeout)

    def get_timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        return self._sock.gettimeout()

    def set_ip(self, ip, **kwargs):
        """Sets IP address used to speak with device.
        :param ip: IP address (str)
        :return: None
        """
        self._ip = ip

    def get_ip(self):
        """Gets IP used to speak with device.
        :returns: IP address (str)
        """
        return self._ip

    def set_port(self, port, **kwargs):
        """Sets internet port used to speak with device.
        :param port: port used by counter532x0a (int)
        :returns: None
        """
        self._port = port

    def get_port(self):
        """Gets internet port used to speak with device.
        :returns: port used by counter532x0a (int)
        """
        return self._port


# =============================================================================
def check_sdmm34461a():
    """Check the SDmm34461axx class: connect to the multimeter, configure a dc
    voltage measurement then collect and print data to standard output.
    Values that work:
    - 1PLC with 0.5 de rtimeout
    - 10PLC with 0.8 de rtimeout
    """
    from datetime import datetime
    # from mjdutil import datetime_to_mjd

    date_fmt = "%d/%m/%Y %H:%M:%S"
    log_format = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d): %(message)s"
    logging.basicConfig(level=logging.INFO,
                        datefmt=date_fmt,
                        format=log_format)

    # dmm34461a = Dmm34461aSerial(serport="/dev/ttyUSB0", timeout=0.8)
    dmm34461a = SDmm34461aUsb(0x2a8d, 0x1601, timeout=4.8)
    # dmm34461a = Dmm34461aEth(ip="192.168.0.61", port=5025, timeout=2.8)
    if dmm34461a.connect() is not True:
        print("Connection failed")
        return
    dmm34461a.reset()
    dmm34461a.write("CONF:VOLT:DC AUTO")  # Autorange
    dmm34461a.write("VOLT:ZERO:AUTO ON")  # Autozero off
    dmm34461a.write("VOLT:DC:NPLC 100")
    # dmm34461a.write("TRIG:SOUR IMM")  # Immediate trigger source
    # dmm34461a.write("TRIG:DEL 0")   # No trigger delay
    # dmm34461a.write("TRIG:COUN 1")  # 1 measurement per trigger
    # dmm34461a.write("SAMP:COUN 1")  # 1 sample per trigger
    try:
        while True:
            value = dmm34461a.data_read()
            now = datetime.utcnow()
            if value is None or value == "":
                print("# No data @", now)
            else:
                # print(now, '{:0.14f}'.format(value.strip('\n')))
                print(now, value)
    except KeyboardInterrupt:
        pass
    except Exception as er:
        print("# Exception during acquisition: " + str(er))
    dmm34461a.reset()
    dmm34461a.write("SYST:LOC\n")
    dmm34461a.close()


# =============================================================================
if __name__ == '__main__':
    check_sdmm34461a()
