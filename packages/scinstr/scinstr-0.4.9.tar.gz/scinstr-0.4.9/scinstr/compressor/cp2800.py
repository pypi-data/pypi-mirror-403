"""package compressor
author  Benoit Dubois
brief   Basic API to handle CP2800 compressor part from Cryomech.
details CP2800 compressor provide  SMDP (Sycon Multi Drop Protocol) over
        RS232/485 interface. See manual for more information.

        Read data packet structure:
        - send:     <'c'><hashval-int><array index-byte>
        - returns:  <'c'><hashval-int><array index-byte><data-long>

        Example, read the dictionary variable COMP_MINUTES (hash 0x454C):
        - send :   0x63|0x45|0x4C|0x00
        - returns: 0x63|0x45|0x4C|0x00|0x00|0x01|0x36|0x23
        Value returned is 00013623(hex) (79395 decimal) minutes.

        Write data packet structure:
        - send:     <'a'><hashval-int><array index-byte><data-long>
        - returns:  None

        Example, start the compressor by writing 1 to EV_START_COMP_REM
        (hash 0xD501):
        - send:    0x61|0xD5|0x01|0x00|0x00|0x00|0x00|0x01
        - returns: None
"""

import serial
import logging
import binascii
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
import smdp


HASHCODE = {
    'CODE_SUM': '\x2B\x0D',
    'MEM_LOSS': '\x80\x1A',
    'CPU_TEMP': '\x35\x74',
    'BATT_OK': '\xA3\x7A',
    'BATT_LOW': '\x0B\x8B',
    'COMP_MINUTES': '\x45\x4C',
    'MOTOR_CURR_A': '\x63\x8B',
    'RI_RMT_COMP_START': '\xBA\xF7',
    'RI_RMT_COMP_STOP': '\x3D\x85',
    'RI_RMT_COMP_ILOK': '\xB1\x5A',
    'RI_SLVL': '\x95\xE3',
    'TEMP_TNTH_DEG': '\x0D\x8F',
    'TEMP_TNTH_DEG_MINS': '\x6E\x58',
    'TEMP_TNTH_DEG_MAXES': '\x8A\x1C',
    'CLR_TEMP_PRES_MMMARKERS': '\xD3\xDB',
    'TEMP_ERR_ANY': '\x6E\x2D',
    'PRES_TNTH_PSI': '\xAA\x50',
    'PRES_TNTH_PSI_MINS': '\x5E\x0B',
    'PRES_TNTH_PSI_MAXES': '\x7A\x62',
    'PRES_ERR_ANY': '\xF8\x2B',
    'H_ALP': '\xBB\x94',
    'H_AHP': '\x7E\x90',
    'H_ADP': '\x31\x9C',
    'H_DPAC': '\x66\xFA',
    'DIODES_UV': '\x8E\xEA',
    'DIODES_TEMP_CDK': '\x58\x13',
    'DIODES_ERR': '\xD6\x44',
    'DCAL_SEL': '\x99\x65',
    'EV_START_COMP_REM': '\xD5\x01',
    'EV_STOP_COMP_REM': '\xC5\x98',
    'COMP_ON': '\x5F\x95',
    'ERR_CODE_STATUS': '\x65\xA4'
    }


#==============================================================================
# CLASS Cp2800
#==============================================================================
class Cp2800(QObject):
    """Class dedicated to handle the CP2800 device.
    """

    COMP_ADDR = '\x10'  # Compressor address to be used to use RS232 interface
    PORT = 0            # Default serial port
    TIMEOUT = 0.5       # Default timeout (in s)
    BAUDRATE = 9600     # Default baudrate (baud/s)
    READ_SIZE = 128     # Number of bytes to read
    READ = '\x63'       # Read data byte 
    WRITE = '\x61'      # Write data byte 
    CMD_RSP = '\x80'    # Command/Response default character

    new_data = pyqtSignal(int)

    def __init__(self, port=PORT, baudrate=BAUDRATE, timeout=TIMEOUT, \
                 addr=COMP_ADDR):
        """Constructor
        :param port: device name or port number value (str or int)
        :param baudrate: baudrate (9600 or 115200) (int)
        :param timeout: timeout on serial interface (int)
        :param addr: address of device (str)
        :returns: None
        """
        super(Cp2800, self).__init__()
        self._addr = addr
        try:
            self._intf = smdp.Smdp(port=port, baudrate=baudrate, \
                                   timeout=timeout)
        except serial.SerialException as ex:
            logging.error("Connection to CP2800 failed: " + str(ex))
        except Exception as ex:
            raise ex

    @pyqtSlot()
    def close(self):
        """Call destructor.
        :returns: None
        """
        self._intf.close()

    @pyqtSlot()
    def open(self):
        """Open connection to device.
        :returns: None
        """
        if self._intf.is_open() is True:
            logging.warning("Port is already open")
            return
        try:
            self._intf.open()
        except serial.SerialException as ex:
            logging.error("Connection to CP2800 failed: " + str(ex))
        except Exception as ex:
            raise ex

    @pyqtSlot(str, str, str)
    def ask(self, keycode, index='\x00', writedata=''):
        """Combines a read after write request and return the result of the
        command.
        :param keycode: key code of data dictionnary of device (str)
        :param index: index of the data (for array) (str)
        :param writedata: data to write (if writing) (str)
        :returns: Results of query (str)
        """
        if keycode not in HASHCODE:
            raise KeyError
        if writedata == '':
            readwrite = self.READ
        else:
            readwrite = self.WRITE
        data = self._gen_data(readwrite, HASHCODE[keycode], index, writedata)
        self._intf.write(self._addr, self.CMD_RSP, data)
        data = self._intf.read(self.READ_SIZE)
        self.new_data.emit(data)
        return data

    def _gen_data(self, readwrite, hashcode, index, writedata):
        """Generate data field of message. More details in doc.
        :param readwrite: read or write data byte (str)
        :param hashcode: hash code of data dictionnary of device (str)
        :param index: index of the data (for array) (str)
        :param writedata: data to write (if writing) (str)
        :returns: the formated data field (str)
        """
        if readwrite == self.READ:
            outlen = 4
        elif readwrite == self.WRITE:
            outlen = 8
        else:
            raise KeyError("readwrite parameter is not valid")
        output = readwrite + hashcode + index + writedata
        if len(output) == outlen:
            return output
        else:
            logging.error("readwrite suggests length %d but gen_data input " \
                          "only %d: %s", outlen, len(output), \
                          binascii.hexlify(output))
