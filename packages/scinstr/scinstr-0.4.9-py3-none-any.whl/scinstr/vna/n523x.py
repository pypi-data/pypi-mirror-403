# -*- coding: utf-8 -*-

"""package scinstr.vna
author    Benoit Dubois
copyright FEMTO ENGINEERING
license   GPL v3.0+
brief     Handle PNA-X, N522xA or N523x device from Keysight.
          Tested on N5234 device.
"""

import time
import socket
import struct
import logging
import numpy as np

PORT = 5025

#==============================================================================
class N523x(object):
    """Handle PNA-X, N522xA or N523x device from Keysight.
    """

    IFBW = (1, 2, 3, 5, 7, 10, 15, 20, 30, 50, 70, 100, 150, 200, 300, 500, 700,
            1e3, 1.5e3, 2e3, 3e3, 5e3, 7e3, 10e3, 15e3, 20e3, 30e3, 50e3, 70e3,
            100e3, 150e3, 200e3, 280e3, 360e3, 600e3)

    def __init__(self, ip, port=PORT, timeout=1.0):
        """Constructor.
        :param ip: IP address of device (str)
        :param port: Ethernet port of device (int)
        :param timeout: Timeout on connection instance (float)
        :returns: None
        """
        self.ip = ip
        self.port = port
        self._timeout = timeout
        self._sock = None

    def connect(self):
        """Connect to device.
        """
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(self._timeout)
            self._sock.connect((self.ip, self.port))
        except ValueError as ex:
            logging.error("Connection parameters out of range: %s", str(ex))
            return False
        except socket.timeout:
            logging.error("Timeout on connection")
            return False
        except Exception as ex:
            logging.error("Unexpected exception during connection with " + \
                          "VNA: %s", str(ex))
            return False
        else:
            logging.debug("Connected to VNA")
            return True

    def close(self):
        self._sock.close()

    def write(self, data):
        """"Ethernet writing process.
        :param data: data writes to device (str)
        :returns: None
        """
        try:
            self._sock.send((data + "\n").encode('utf-8'))
        except socket.timeout:
            logging.error("Timeout")
        except Exception as ex:
            logging.error(str(ex))
        logging.debug("write " + data.strip('\n'))

    def read(self, length=100):
        """Read process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        try:
            retval = self._sock.recv(length).decode('utf-8').strip('\n')
        except socket.timeout:
            logging.error("Timeout")
            return ''
        except Exception as ex:
            logging.error(str(ex))
            raise ex
        logging.debug("read: " + retval)
        return retval

    def raw_read(self, length=512):
        """Raw read process.
        :param length: length of message to read (int)
        :returns: Message reads from device (bytes)
        """
        try:
            data = self._sock.recv(length)
        except socket.timeout:
            logging.error("Timeout")
            return bytes()
        except Exception as ex:
            logging.error(str(ex))
            raise ex
        return data

    def bin_read(self):
        """Read binary data then decode them to ascii.
        The reading process is specific to the transfert of binary data
        with these VNA devices: <header><data><EOT>, with:
        - <header>: #|lenght of bytes_count (one byte)|bytes_count
        - <data>: "REAL,64" (float64) binary data
        - <EOT>: '\n' character.
        Note: The data transfert format must be selected to "REAL,64"" before
        using this method
        """
        header_max_length = 11
        raw_data = self.raw_read(header_max_length)
        if raw_data.find(b'#') != 0:
            logging.error("Data header not valid")
            return
        byte_count_nb = int(raw_data[1:2])
        byte_count = int(raw_data[2:2+byte_count_nb])
        # Note : Read 'byte_count' bytes but only
        # 2 + byte_count_nb + byte_count - header_max_length
        # needs to be readen.
        # This tip can be used because EOF ('\n') is transmited at the end of
        # the message and thus stop reception of data.
        while len(raw_data) < byte_count:
            raw_data += self.raw_read(byte_count)
        nb_elem = int(byte_count / 8)
        data = np.asarray(struct.unpack(">{:d}d".format(nb_elem),
                                        raw_data[2+byte_count_nb:-1]))
        return data

    def query(self, msg, length=100):
        """Basic query process: write query then read response.
        """
        self.write(msg)
        return self.read(length)

    def reset(self):
        """Reset device.
        """
        self.write("*RST")

    @property
    def idn(self):
        """Return ID of device.
        """
        return self.query("*IDN?")

    def get_span(self, cnum=1):
        return self.query("SENS{}:FOM:RANG:SEGM:FREQ:SPAN?".format(cnum))

    def set_span(self, value, cnum=1):
        self.write("SENS{}:FREQ:SPAN {}".format(cnum, value))

    def get_start(self, cnum=1):
        return self.query("SENS{}:FREQ:START?".format(cnum))

    def set_start(self, value, cnum=1):
        self.write("SENS{}:FREQ:START {}".format(cnum, value))

    def get_stop(self, cnum=1):
        return self.query("SENS{}:FREQ:STOP?".format(cnum))

    def set_stop(self, value, cnum=1):
        self.write("SENS{}:FREQ:STOP {}".format(cnum, value))

    def get_center_freq(self, cnum=1):
        return self.query("SENS{}:FREQ:CENT?".format(cnum))

    def set_center_freq(self, value, cnum=1):
        self.write("SENS{}:FREQ:CENT {}".format(cnum, value))

    def get_points(self, cnum=1):
        return self.query("SENS{}:SWE:POINTS?".format(cnum))

    def set_points(self, value, cnum=1):
        self.write("SENS{}:SWE:POINTS {}".format(cnum, value))

    def get_sweep_type(self, cnum=1):
        return self.query("SENS{}:SWE:TYPE?".format(cnum))

    def set_sweep_type(self, value, cnum=1):
        self.write("SENS{}:SWE:TYPE {}".format(cnum, value))

    @staticmethod
    def read_s2p(filename):
        return np.loadtxt(filename, comments=['!', '#'])

    def get_window_numbers(self):
        """Return the number of existing windows.
        """
        data = self.query("DISP:CAT?")
        if data is None:
            return []
        return [int(x) for x in data.replace('\"', '').split(',')]

    def get_measurement_catalog(self, channel=''):
        """Returns ALL measurement numbers, or measurement numbers
        from a specified channel
        :param channel: Channel number to catalog. If not specified,
                        all measurement numbers are returned.
        :returns: ALL measurement numbers, or measurement numbers
                  from a specified channel
        """
        data = self.query("SYST:MEAS:CAT? {}".format(channel))
        if data is None:
            return []
        return [int(x) for x in data.replace('\"', '').split(',')]

    def measurement_number_to_trace(self, nb=None):
        """Returns the trace number of the specified measurement number.
        Trace numbers restart for each window while measurement numbers are
        always unique.
        :param n: Measurement number for which to return the trace number.
                  If unspecified, value is set to 1.
        """
        return self.query("SYST:MEAS{}:TRAC?".format(nb))

    def measurement_number_to_name(self, nb=None):
        """Returns the name of the specified measurement.
        :param n: Measurement number for which to return the measurement name.
        If unspecified, value is set to 1.
        """
        return self.query("SYST:MEAS{}:NAME?".format(nb)).replace('\"', '')

    def set_measurement(self, name, fast=True):
        """ Sets the selected measurement. Most CALC: commands require that
        this command be sent before a setting change is made. One measurement
        on each channel can be selected at the same time.
        :param name: Name of the measurement. CASE-SENSITIVE. Do NOT include
                      the parameter name that is returned with Calc:Par:Cat?
        :param fast: Optional. The PNA display is NOT updated. Therefore,
                     do not use this argument when an operator is using the
                     PNA display. Otherwise, sending this argument results
                     in much faster sweep speeds. There is NO other reason
                     to NOT send this argument.
        """
        if name is None:
            logging.error("Requiered name parameter")
            raise ValueError("Requiered name parameter")
        cnum = int(name[2])
        self.write("CALC{}:PAR:SEL {}{}"
                   .format(cnum, name, ",fast" if fast is True else None))

    def get_measurement(self, name):
        """Get a data measurement.
        Note that VNA must be configured to transfer data in float 64 format
        before using this method.
        :param name: Name of the measurement. CASE-SENSITIVE. Do NOT include
                     the parameter name that is returned with Calc:Par:Cat?
        :return: Array of measurement data.
        """
        cnum = int(name[2])
        self.set_measurement(name)
        if self.get_sweep_type() != "LIN":
            raise NotImplementedError
        datax = np.linspace(float(self.get_start(cnum)),
                            float(self.get_stop(cnum)),
                            int(self.get_points(cnum)))
        self.write("CALC{}:DATA? FDATA".format(cnum))
        datay = self.bin_read()
        retval = np.asarray([datax, datay])
        return retval

    def get_snp(self, cnum=1):
        """Get snp data.
        :param cnum: Channel number of the measurement. There must be a selected
        measurement on that channel. If unspecified, <cnum> is set to 1.
        :return: Array of data.
        """
        self.write("CALC{}:DATA:SNP:PORT? \"1,2\"".format(cnum))
        return np.asarray(self.bin_read()).reshape(9, -1)

    def get_measurements(self):
        """Find current measurements, get data then prepare a list of array
        [freq, data] for each measurement.
        :returns: list of measurements
        """
        datas = []
        meas_nb = self.get_measurement_catalog()
        for nb in meas_nb:
            name = self.measurement_number_to_name(nb)
            datas.append(self.get_measurement(name))
        return datas

    def get_snps(self):
        """Get all snp traces.
        """
        meas_nb = self.get_measurement_catalog()
        datas = []
        for measurement in meas_nb:
            datas.append(self.get_snp(measurement))
        return datas

    def write_snps(self, filename=None):
        """Write all snp traces.
        """
        if filename is None:
            filename = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        meas_nb = self.get_measurement_catalog()
        for measurement in meas_nb:
            data = np.asarray(self.get_snp(measurement)).reshape(9, -1)
            np.savetxt(filename + '_' + str(measurement) + '.s2p',
                       data,
                       delimiter='\t',
                       header="#f(Hz)\tReal(S11)\tImag(S11)" +
                       "\tReal(S21)\tImag(S21)" +
                       "\tReal(S12)\tImag(S12)" +
                       "\tReal(S22)\tImag(S22)")


#==============================================================================
def main():
    """Main of test program
    :returns: None
    """
    import matplotlib.pyplot as plt

    ip = "192.168.0.11"

    acp_type = 'data' # 'data' or 'snp'

    dev = N523x(ip, timeout=0.5)

    if dev.connect() is False:
        print("Connection error")
        return

    print("Connected to", dev.id)

    dev.write("FORMAT:DATA REAL,64")

    if acp_type == 'snp':
        dev.write("MMEM:STOR:TRAC:FORM:SNP MA")
        datas = dev.get_snp()
        plt.figure(1)
        nb_rows = datas.shape[0]
        for idx, data in enumerate(datas):
            plt.subplot(nb_rows*100+10+idx)
            plt.plot(datas[0], data, 'b')
        plt.show()

    else:
        datas = dev.get_measurements()
        plt.figure(1)
        nb_rows = len(datas)
        for idx, data in enumerate(datas):
            plt.subplot(nb_rows*100+10+idx+1)
            plt.ylabel(dev.measurement_number_to_name(idx+1))
            try:
                plt.plot(data[0], data[1], 'b', )
            except Exception:
                pass
        plt.show()


#==============================================================================
if __name__ == '__main__':
    CONSOLE_LOG_LEVEL = logging.DEBUG
    CONSOLE_FORMAT = '%(levelname) -8s %(filename)s (%(lineno)d): %(message)s'
    logging.basicConfig(format=CONSOLE_FORMAT, level=CONSOLE_LOG_LEVEL)

    main()
