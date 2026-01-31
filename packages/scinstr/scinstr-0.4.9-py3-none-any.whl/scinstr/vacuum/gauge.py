# -*- coding: utf-8 -*-

"""package scinstr.vacuum
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2018-2024
license   GPL v3.0+
brief     Base class to handle vacuum gauge device.
"""

import logging
import socket
import serial


# Control Symbols
ACK = '\x06' # AcKnowledge
NAK = '\x15' # Not AcKnowledge
ENQ = '\x05' # Enquiry (Request for data transmission)
ETX = '\x03' # End of text (Ctrl-C)
CR = '\x0D'
LF = '\x0A'

LINE_TERMINATION = CR + LF  # CR, LF and CRLF

# Generic mnemonics
MNEMONIQUE = [
    'BAU', # Baud rate
    'CAx', # Calibration factor Sensor x
    'CID', # Measurement point names
    'DCB', # Display control Bargraph
    'DCC', # Display control Contrast
    'DCD', # Display control Digits
    'DCS', # Display control Screensave
    'DGS', # Degas
    'ERR', # Error Status
    'FIL', # Filter time constant
    'FSR', # Full scale range of linear sensors
    'LOC', # Parameter setup lock
    'NAD', # Node (device) address for RS485
    'OFC', # Offset correction
    'OFC', # Offset correction
    'PNR', # Program number
    'PRx', # Status, Pressure sensor x (1 ... 6)
    'PUC', # Underrange Ctrl
    'RSX', # Interface
    'SAV', # Save default
    'SCx', # Sensor control
    'SEN', # Sensor on/off
    'SPx', # Set Point Control Source for Relay x
    'SPS', # Set Point Status A,B,C,D,E,F
    'TAI', # Test program A/D Identify
    'TAS', # Test program A/D Sensor
    'TDI', # Display test
    'TEE', # EEPROM test
    'TEP', # EPROM test
    'TID', # Sensor identification
    'TKB', # Keyboard test
    'TRA', # RAM test
    'UNI', # Unit of measurement (Display)
    'WDT' # Watchdog and System Error Control
]

ES = {
    "0000": "No error",
    "1000": "Error", # Controller error (See display on front panel)
    "0100": "NO HWR", # No hardware
    "0010": "PAR", # Inadmissible parameter
    "0001": "SYN" # Syntax error
}


# =============================================================================
class Gauge():
    """Base class to handle vacuum controller device.
    """

    def __init__(self, termination=LINE_TERMINATION):
        self._termination = termination

    def connect(self):
        """Connect to the remote host
        :returns: True if connection succeeded, False otherwise
        """
        raise NotImplementedError("Method not implemented by derived class")

    def close(self):
        """ Closes the underlying connection
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _write(self, data):
        """Writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _read(self, length):
        """Reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def read(self, length=128):
        """Basic read process.
        :param length: max number of bytes to read, None -> no limit (int)
        :returns: data received or False if communication error (str)
        """
        result = self._read(length).strip(self._termination)
        logging.debug("read %r", result)
        return result

    def write(self, mnemo, parameters=None):
        """Write message to device.
        :param mnemo: mnemonique (command/response) (str)
        :param parameters: parameters if needed (str)
        :returns: True if transmission OK else False (bool)
        """
        if parameters is not None:
            msg = mnemo + ',' + parameters + CR
        else:
            msg = mnemo + CR
        self._write(msg)
        is_ack = self._read(3)
        if is_ack == (ACK + CR + LF):
            logging.debug("write %r acknoledged", msg.strip(CR))
            return True
        logging.debug("write %r non acknoledged", msg.strip(CR))
        return False

    def query(self, mnemo, parameters=None, size=100):
        """Ask procedure ie read data after write.
        :param mnemo: mnemonique (command/response) (str)
        :param parameters: parameters if needed (str)
        :returns: data received (str)
        """
        write_ok = self.write(mnemo, parameters)
        if write_ok is False:
            logging.error("Write to device failed")
            return ''
        self._write(ENQ)
        result = self.read(size).strip(LINE_TERMINATION)
        return result

    def reset(self, cancel_error=False):
        """Set the instrument functions to the factory default power up state.
        Return all present error.
        'No error': 0,
        'Watchdog has responded': 1,
        'Task fail error': 2,
        'EPROM error': 3,
        'RAM error': 4,
        'EEPROM error': 5,
        'DISPLAY error': 6,
        'A/D converter error': 6,
        'Gauge 1 error (e.g. filament rupture, no supply)': 7,
        'Gauge 1 identification error': 8,
        'Gauge 2 error (e.g. filament rupture, no supply)': 8,
        'Gauge 2 identification error': 9
        """
        if cancel_error is True:
            param = '1'
        else:
            param = None
        return self.query('RES', param)

    @property
    def idn(self):
        """Gauge identification.
        """
        return self.query('TID')

    @property
    def degas(self):
        """Return degas gauges status.
        """
        degas_status = self.query("DGS").split(',')
        return degas_status

    @degas.setter
    def degas(self, channel, value=1):
        """Degas gauge. Return degas gauge status.
        """
        if channel == 1:
            param = str(value)
        elif channel == 2:
            param = ',' + str(value)
        else:
            logging.error(f"Bad channel number selection for degas: {channel}")
            return
        degas_status = self.query("DGS", param).split(',')[channel-1]
        return degas_status

    @property
    def display_channel(self):
        """Set measurement channel to be displayed.
        Return displayed channel.
        """
        return self.query('SCT')

    @display_channel.setter
    def display_channel(self, channel):
        """Set measurement channel to be displayed.
        Return displayed channel.
        """
        return self.query('SCT', channel-1)

    @property
    def error(self):
        """Return error status.
        """
        return self.query('ERR')

    @property
    def gauge_enabled(self):
        """Return gauge status.
        """
        gauges_status = self.query('SEN').split(',')
        return gauges_status

    @gauge_enabled.setter
    def gauge_enabled(self, channel, value):
        """Set gauge on/off. Return gauge status.
        """
        if channel == 1:
            param = str(value)
        else:
            param = ',' + str(value)
        gauge_status = self.query('SEN', param).split(',')[channel-1]
        return gauge_status

    def pressure(self, channel):
        """Pressure measurement gauge 1 or 2.
        Return status of measurement and measurement data.
        """
        ans = self.query('PR{:d}'.format(channel)).split(',')
        pressure = float(ans[1])
        status = ans[0]
        return status, pressure

    def get_filter_cst(self, channel):
        """Get time constant of measurement filters.
        :returns: current filters time constant (int or list of int)
        """
        time_cst = self.query("FIL").split(',')[channel-1]
        return time_cst

    def set_filter_cst(self, channel, value):
        """Set time constant of measurement filters.
        0 –> fast
        1 –> medium (default)
        2 –> slow
        Return current filter time constant.
        """
        if channel == 1:
            param = str(value)
        else:
            param = ',' + str(value)
        time_cst = self.query("FIL", param).split(',')[channel-1]
        return time_cst

    @property
    def unit(self):
        """Get control unit.
        """
        return self.query('UNI')

    @unit.setter
    def unit(self, value):
        """Set control unit.
        0 –> mbar/bar (default)
        1 –> Torr
        2 –> Pascal
        """
        return self.query('UNI', value)

    @property
    def baud(self):
        """Transmission rate.
        """
        return self.query('BAU')

    @baud.setter
    def baud(self, value):
        """Transmission rate.
        """
        return self.query('BAU', value)

    @property
    def digit_display(self):
        """Display resolution.
        """
        return self.query('DCD')

    @digit_display.setter
    def digit_display(self, value):
        """Display resolution.
        """
        return self.query('DCD', value)

    def get_full_scale_range(self, channel):
        """Return full scale range value of the measurement range of
        linear gauges (int or list of int).
        """
        scale_range = self.query('FSR').split(',')[channel-1]
        return scale_range

    def set_full_scale_range(self, channel, value):
        """Set full scale value of the measurement range of linear gauges.
        """
        if channel == 1:
            param = str(value)
        else:
            param = ',' + str(value)
        scale_range = self.query("FSR", param).split(',')[channel-1]
        return scale_range

    def get_calibration(self, channel):
        """Return calibration factor of specified gauge.
        """
        calibration_factor = self.query('CAL').split(',')[channel-1]
        return calibration_factor

    def set_calibration(self, channel, value):
        """Set calibration factor.
        """
        if channel == 1:
            param = str(value)
        else:
            param = ',' + str(value)
        calibration_factor = self.query("CAL", param).split(',')[channel-1]
        return calibration_factor

    def get_offset_correction(self, channel):
        """Return offset correction factor of specified gauge.
        """
        ofc = self.query('OFC').split(',')[channel-1]
        return ofc

    def set_offset_correction(self, channel, value):
        """Set offset correction for linear gauge.
        """
        if channel == 1:
            param = str(value)
        else:
            param = ',' + str(value)
        ofc = self.query("OFC", param).split(',')[channel-1]
        return ofc

    def get_offset_display(self, channel):
        """Return offset display factor of specified gauge.
        """
        ofd = self.query('OFD').split(',')[channel-1]
        return ofd

    def set_offset_display(self, channel, value):
        """Set offset display for linear gauge.
        """
        if channel == 1:
            param = str(value)
        else:
            param = ',' + str(value)
        ofd = self.query("OFD", param).split(',')[channel-1]
        return ofd

    def get_switching_threshold(self, key):
        """Get threshold value setting allocation.
        Return lower and upper threshold value.
        """
        pass

    def set_switching_threshold(self, channel, function,
                            lower_threshold, upper_threshold):
        """Set threshold value setting allocation.
        Return lower and upper threshold value.
        """
        param = str(channel-1) + ',' \
                + str(lower_threshold) + ',' \
                + str(upper_threshold)
        func, lth, uth = self.query("SP{:d}".format(function), param).split(',')
        return func, lth, uth

    def get_switching_function_status(self):
        """Return switching function status
        """
        function_status = self.query('SPS').split(',')
        return function_status


# =============================================================================
class GaugeEth(Gauge):
    """Handle vacuum controller device through ethernet interface.
    """

    def __init__(self, ip, port, timeout):
        super().__init__()
        self._sock = None
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def connect(self):
        """Open connection with device.
        :param ip: IP address of device (str)
        :param port: Device port in use (int)
        :param timeout: Timeout in second (float)
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
        logging.info("Connected to gauge")
        return True

    def close(self):
        """Close connection with device.
        :returns: None
        """
        if self._sock is None:
            return
        self._sock.close()
        self._sock = None
        logging.info("Connection to gauge closed")

    def _write(self, data):
        """Specific ethernet writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        try:
            nb_bytes = self._sock.send(data.encode('utf-8'))
        except socket.timeout:
            logging.error("Device write timeout")
            return 0
        return nb_bytes

    def _read(self, length):
        """Specific ethernet reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        try:
            retval = self._sock.recv(length).decode('utf-8')
        except socket.timeout:
            logging.error("Device read timeout")
            return ''
        return retval


# =============================================================================
class GaugeSerial(Gauge):
    """Handle vacuum controller device through USB connection.
    The USB interface emulates a 'classic' serial interface.
    """

    def __init__(self, port=None, baudrate=None, bytesize=None,
                 parity=None, stopbits=None, timeout=1.0):
        super().__init__()
        self._ser = serial.Serial()
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout

    def connect(self):
        """Connect to the remote host
        :returns: True if connection succeeded, False otherwise
        """
        if self._ser.isOpen() is False:
            try:
                self._ser.open()
            except ValueError as ex:
                logging.error("Wrong connection parameters: %r", ex)
                return False
            except serial.SerialTimeoutException:
                logging.error("Timeout on connection")
                return False
            except serial.serialutil.SerialException as ex:
                logging.error("Serial error: %r", ex)
                return False
        logging.info("Connected to gauge")
        self._ser.flush()
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
        logging.info("Connection to gauge closed")

    def _write(self, data):
        """Specific USB writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        try:
            nb_bytes = self._ser.write(data.encode('utf-8'))
        except serial.SerialTimeoutException:
            logging.error("Device write timeout")
            return 0
        return nb_bytes

    def _read(self, length):
        """Specific USB reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        try:
            retval = self._ser.read(length).decode('utf-8')
        except serial.SerialTimeoutException:
            logging.error("Device read timeout")
            return ''
        return retval

    @property
    def port(self):
        return self._ser.port

    @port.setter
    def port(self, value):
        self._ser.port = value

    @property
    def baudrate(self):
        return self._ser.baudrate

    @baudrate.setter
    def baudrate(self, value):
        self._ser.baudrate = value

    @property
    def bytesize(self):
        return self._ser.bytesize

    @bytesize.setter
    def bytesize(self, value):
        self._ser.bytesize = value

    @property
    def parity(self):
        return self._ser.parity

    @parity.setter
    def parity(self, value):
        self._ser.parity = value

    @property
    def stopbits(self):
        return self._ser.stopbits

    @stopbits.setter
    def stopbits(self, value):
        self._ser.stopbits = value

    @property
    def timeout(self):
        return self._ser.timeout

    @timeout.setter
    def timeout(self, value):
        self._ser.timeout = value
