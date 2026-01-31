# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2019-2025
license   GPL v3.0+
brief     API dedicated to handle the Keysight 532X0A counter serie with
          pure Python signal/slot capabilities.
"""

import logging
import signalslot as ss

from scinstr.cnt.cnt532x0a import Cnt532x0aEth, Cnt532x0aUsb


# =============================================================================
class SCnt532x0aUsb(Cnt532x0aUsb):
    """Class derived from Cnt532x0aUsb class to add signal/slot facilities.
    """

    connected = ss.Signal()
    closed = ss.Signal()
    id_checked = ss.Signal(['flag'])
    out_updated = ss.Signal(['value'])

    def connect(self, **kwargs):
        """Connection process.
        :returns: True if connection is ok else False (bool)
        """
        retval = super().connect(**kwargs)
        if retval is True:
            self.connected.emit()
        return retval

    def close(self, **kwargs):
        """Closing process.
        :returns: None
        """
        super().close(self)
        self.closed.emit()

    def check_interface(self, **kwargs):
        retval = super().check_interface()
        self.id_checked.emit(flag=retval)
        return retval

    def data_read(self, **kwargs):
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
class SCnt532x0aEth(Cnt532x0aEth):
    """Class derived from Cnt532x0aEth class to add signal/slot facilities.
    """

    connected = ss.Signal()
    closed = ss.Signal()
    id_checked = ss.Signal(['flag'])
    out_updated = ss.Signal(['value'])

    def connect(self, **kwargs):
        """Abstract protocol connect process. Derived classes must implement
        the connect process dedicated to the specific protocol used.
        :returns: None
        """
        retval = super().connect(**kwargs)
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

    def set_ip(self, ip):
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
def check_counter532x0a():
    """Checks the SCnt532x0a class: connect to the multimeter, configure a dc
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

    counter = SCnt532x0aUsb(0x0957, 0x1707, timeout=2.8)
    # counter = Counter532x0aEth(ip="192.168.0.20", port=5025, timeout=1.5)
    if counter.connect() is not True:
        print("Connection failed")
        return
    counter.reset()
    print("IDN:", counter.idn())
    counter.write("CONF:FREQ 100.0E6")
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
                # print(now, '{:0.14f}'.format(value.strip('\n')))
                print(now, value)
    except KeyboardInterrupt:
        pass
    except Exception as er:
        print("# Exception during acquisition: " + str(er))
    counter.reset()
    counter.close()


# =============================================================================
if __name__ == '__main__':
    check_counter532x0a()
