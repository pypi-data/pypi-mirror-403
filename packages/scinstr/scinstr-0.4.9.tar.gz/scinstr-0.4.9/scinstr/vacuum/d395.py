# -*- coding: utf-8 -*-

"""scinstr.vaccum
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2026
license   GPL v3.0+
brief     Class to handle Edwards D395 controller device.
details   All messages consist of ASCII coded characters. Messages to the ADC
start with either a "!" or a "?" character. All messages end with a carriage
return (cr). Characters not enclosed by start (!?) and end (cr) characters
will be ignored. Incomplete messages will be ignored if a new start character
is received. Responses from the ADC end with a carriage return (cr).
If the message cannot be understood or if the syntax is wrong, an error message
of the form "Err n" will be returned.
"""

import logging
import serial


TIMEOUT = 0.5

CR = '\x0D'

COMMANDS = [
    '!CH', # Set-point high threshold
    '!CL', # Set-point low threshold
    '!GA', # Accept gauge error
    '!GW', # Switch gauge on/off
    '!RC', # Relay controlling gauge
    '!TH', # Link high threshold
    '!TL', # Link low threshold
    '!US', # Units
]

QUERIES = [
    '?CH', # Set-point high threshold -> {pressure}
    '?CL', # Set-point low threshold -> {pressure}
    '?GA', # Gauge pressure -> {pressure}
    '?GV', # Gauge version -> {nn}
    '?RC', # Relay controlling gauge -> {1..2}
    '?TH', # Link high threshold -> {pressure}
    '?TL', # Link low threshold -> {pressure}
    '?US', # Units -> {0..3}
    '?VL', # Voltage -> {voltage}
]

ERROR_CODES = {
    # Controller errors
    '0': 'No error',
    '1': 'EEPROM error',
    '2': 'ID reference error',
    # Gauge errors
    '11': 'Gauge voltage too high',
    '12': 'Gauge voltage too low',
    '13': 'AIM Gauge not striking',
    '21': 'WRG Pirani failure',
    '22': 'WRG magnetron short',
    '23': 'WRG striker fail',
    '24': 'WRG magnetron not struck',
    '25': 'APGX filament failure',
    '26': 'APGX cal err',
    '27': 'APGXH tube not fitted',
    # RS232 errors
    '51': 'Not a valid query or command word',
    '52': 'Message incomplete',
    '53': 'Message too long',
    '54': 'Incorrect gauge number',
    '57': 'Incorrect number format',
    '58': 'Incorrect pressure format',
    #
    '81': 'No gauge connected',
    '82': 'Unknown gauge type',
    '83': 'Gauge not reading pressure',
    '84': 'AIM gauge striking',
    '90': 'Incorrect gauge type, query/commandnot appropriate',
    '91': 'Gauge turn-on is inhibited by link',
}


def errn_to_errmsg(errn):
    print("ERROR:", retval)
    print(retval[-1])
    error_message = ERROR_CODES[retval[-1]]
    print(error_message)


class CommunicationError(Exception):
    """Raised when device return error message"""
    def __init__(self, errn):
        msg = errn_to_errmsg(errn)
        super().__init__(msg)



# =============================================================================
class D395:
    """Handle vacuum controller device through RS232-serial/USB connection.
    The USB interface emulates a 'classic' serial interface.
    Default RS232 protocol: 9600 baud, 1 stop bit, 8 data bits, no parity.
    """

    def __init__(self, port=None, baudrate=9600, bytesize=8,
                 parity=serial.PARITY_NONE, stopbits=1, timeout=TIMEOUT):
        super().__init__()
        self._ser = serial.Serial()
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout

    def connect(self):
        """Connect to the remote host.
        :returns: True if connection succeeded, False otherwise.
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
        """Close the underlying serial connection.
        """
        if self._ser is not None:
            self._ser.close()
        self._ser = None
        logging.info("Connection to gauge closed")

    def _write(self, data):
        """Specific device writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        nb_bytes = self._ser.write(data.encode('utf-8'))
        return nb_bytes

    def _read(self, length):
        """Specific device reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        retval = self._ser.read(length).decode('utf-8')
        return retval

    def read(self, length=128):
        """Basic read process.
        :param length: max number of bytes to read, None -> no limit (int)
        :returns: data received or False if communication error (str)
        """
        retval = self._read(length)
        retval = retval.strip(CR)
        logging.debug("read %r", retval)
        return retval

    def command(self, mnemo, parameters=None):
        """Command message.
        :param mnemo: mnemonique (command mnemonique) (str)
        :param parameters: command parameters if needed (str)
        :returns: True if transmission OK else False (bool)
        """
        assert mnemo not in COMMANDS
        if parameters is not None:
            msg = mnemo + '=' + str(parameters) + CR
        else:
            msg = mnemo + CR
        self._write(msg)
        retval = self._read(8).strip(CR)
        if 'Err' in retval:
            logging.debug("Command %r error: %r", msg.strip(CR), retval)
            raise CommunicationError(retval)
        logging.debug("Command %r ok", msg.strip(CR))
        return True

    def query(self, mnemo, parameter=None, size=100):
        """Ask procedure ie read data after write.
        :param mnemo: mnemonique (command/response) (str)
        :param parameters: query parameters if needed (str)
        :param size: size of returned data (int)
        :returns: data received (str)
        """
        assert mnemo not in QUERIES
        if parameter is not None:
            msg = mnemo + str(parameter) + CR
        else:
            msg = mnemo + CR
        self._write(msg)
        retval = self._read(128).strip(CR)
        if 'Err' in retval:
            logging.debug("Querry %r error: %r", msg.strip(CR), retval)
            raise CommunicationError(retval)
        return retval

    def pressure(self, gauge_nb):
        """Ask pressure value of gauge 'gauge_nb'.
        :param gauge_nb: id number of the gauge (int)
        :returns: pressure value (float)
        """
        return self.query('?GA', gauge_nb)

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




# =============================================================================
if __name__ == '__main__':
    import logging
    import argparse

    PARSER = argparse.ArgumentParser(description='Test Edwards D395')
    PARSER.add_argument('-p', '--port', dest='port', type=str,
                        help='Serial port to connect to')

    ARGS = PARSER.parse_args()
    PORT = ARGS.port

    INST = D395(port=PORT)
    INST.connect()
    print("Pressure:", INST.pressure(1))
    INST.close()
