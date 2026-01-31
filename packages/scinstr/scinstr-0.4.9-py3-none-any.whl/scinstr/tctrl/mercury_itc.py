# -*- coding: utf-8 -*-

"""package mercury
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2019
license   GPL v3.0+
brief     Class to handle Mercury Itc device through its different interfaces
          (USB, Ethernet, Serial).
"""

import time
import logging
import serial
import socket
import pysobus
from pysobus.parser import Parser
import usb.core
import usb.util
import usb.control


# =============================================================================
class MercuryItc(object):
    """Base class to handle Mercury Itc device.
    """

    def connect(self):
        """Abstract protocol connect process. Derived classes must implement
        the connect process dedicated to the specific protocol used.
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    def close(self):
        """Abstract protocol closing process. Derived classes must implement
        the closing process dedicated to the specific protocol used.
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _write(self, data):
        """Abstract protocol write process. Derived classes must implement
        the write process dedicated to the specific protocol used.
        :param data: data writes to device (str)
        :returns: None
        """
        raise NotImplementedError("Method not implemented by derived class")

    def _read(self, length):
        """Abstract protocol read process. Derived classes must implement
        the read process dedicated to the specific protocol used.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def read(self, length=100):
        """A basic read method: read a message from device.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        try:
            retval = self._read(length)
        except Exception as ex:
            logging.error("Read error: %r", ex)
            return ''
        logging.debug("read: %r", retval)
        return retval

    def write(self, data):
        """A basic write method: writes "data" to device.
        :param data: data writes to device (str)
        :returns: None
        """
        try:
            nb_bytes = self._write(data)
        except Exception as ex:
            logging.error("Write error: %r", ex)
            return 0
        logging.debug("write: %r", data)
        return nb_bytes

    def query(self, data, length=1024):
        """Write than read procedure.
        :param data: data writes to device (str)
        :returns: Message returned by device (str)
        """
        self.write(data)
        return self.read(length)

    @property
    def idn(self):
        """Return product id of device.
        :returns: product id of device (str)
        """
        self.write("*IDN?")
        _id = self.read(100)
        return _id


#==============================================================================
class MercuryItcEth(MercuryItc):
    """Handle Mercury iTC device through ethernet interface.
    """

    PORT = 7020
    TIMEOUT = 3.0  # Default timeout in second

    def __init__(self, ip='', port=PORT, timeout=TIMEOUT):
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
        logging.info("Connected to Lakeshore")
        return True

    def close(self):
        """Close connection with device.
        :returns: None
        """
        if self._sock is None:
            return
        self._sock.close()
        self._sock = None
        logging.info("Connection to Lakeshore closed")

    def _write(self, data):
        """Specific ethernet writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        return self._sock.send((data + '\n').encode('utf-8'))

    def _read(self, length):
        """Specific ethernet reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        return self._sock.recv(length).decode('utf-8').strip('\n')


#==============================================================================
class MercuryItcUsb(MercuryItc):

    VID = 0x0525
    PID = 0xa4a7
    TIMEOUT = 2.0

    _CONFIG_ID     = 2
    #
    _INTERFACE_ID0  = 0       # The interface we use to talk to the device
    _ALT_INTF_ID0   = 0       # The alternate interface use to talk to the device
    _IN_DAT_EP_ID  = 5       # EP8 @0x83 = 131    -> large endpoint
    #
    _INTERFACE_ID1  = 1       # The interface we use to talk to the device
    _ALT_INTF_ID1   = 0       # The alternate interface use to talk to the device
    _IN_EP_ID      = 0       # EP1_IN @0x81 = 129 -> small endpoint
    _OUT_EP_ID     = 1       # EP1_OUT @0x02 = 2  -> small endpoint


    def __init__(self, vendor_id=VID, product_id=PID, timeout=TIMEOUT):
        self._dev = None
        self.vid = vendor_id
        self.pid = product_id
        self._timeout = timeout

    def reset(self):
        if self._dev is not None:
            self._dev.reset()

    def close(self):
        """There is no "concept" of device connection either in USB spec or
        in PyUSB, you can just release resources allocated by the object.
        """
        if self._dev is not None:
            usb.util.dispose_resources(self._dev)

    def connect(self):
        """Set an object representing our device (usb.core.Device).
        :returns: True if connection is Ok else returns False (bool)
        """
        # Find our device
        self._dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        print("type(self._dev):", type(self._dev))
        # Was it found?
        if self._dev is None:
            logging.warning("Device not found")
            return False
        # Detach the kernel driver if it is active
        """if self._dev.is_kernel_driver_active(0):
            try:
                self._dev.detach_kernel_driver(0)
            except usb.core.USBError as ex:
                logging.critical("Could not detach kernel driver: %r", ex)
                return False
        self._dev.reset()"""
        self._config(self._CONFIG_ID, self._INTERFACE_ID1, self._ALT_INTF_ID1, self._OUT_EP_ID ,self._IN_EP_ID)
        return True

    def is_connected(self):
        if self._dev is None:
            return False
        return True

    def _config(self, config_id, interface_id, alt_interface_id, out_ep_id,
               in_ep_id) : ##, out_dat_ep_id, in_dat_ep_id):
        """Configure device and get endpoint instance.
        Endpoint Address description:
        - Bits 0..3 Endpoint Number.
        - Bits 4..6 Reserved. Set to Zero
        - Bits 7 Direction 0 = Out, 1 = In (Ignored for Control Endpoints)
        Example: address = 129 = (81)8 = (1000 0001)2
                 -> Direction: In, Number: 1
        :param config_id:
        ...
        :returns: None
        """
        try:
            self._dev.set_configuration(config_id)
        except usb.core.USBError as ex:
            logging.critical("USB error during dev configuration: %r", ex)
            raise
        except Exception as ex:
            logging.critical("Could not set interface configuration: %r", ex)
            raise
        self._dev.reset()
        # Set interface
        try:
            self._dev.set_interface_altsetting(interface=interface_id,
                                               alternate_setting=alt_interface_id)
        except usb.core.USBError as ex:
            logging.critical("USB error during interface altsetting: %r", ex)
            raise
        except Exception as ex:
            logging.critical("Error during interface altsetting: %r", ex)
            raise
        # Get endpoint instances
        try:
            self._ep_out = self._dev[config_id-1] \
                [(interface_id, alt_interface_id)][out_ep_id]
            self._ep_in = self._dev[config_id-1] \
                [(interface_id, alt_interface_id)][in_ep_id]
            """self._ep_dat_out = self._dev[config_id-1][(interface_id, \
                                            alt_interface_id)][out_dat_ep_id]
            self._ep_dat_in = self._dev[config_id-1][(interface_id, \
                                        alt_interface_id)][in_dat_ep_id]"""
        except usb.core.USBError as ex:
            logging.critical("Could not set endpoint setting: %r", ex)
        logging.debug("USB interface succefuly configured")

    def write_ctrl(self, msg):
        """Write raw data on control endpoint.
        The method don't take care about meaning of msg.
        :param msg: message to write to device (sequence like type convertible
                    to array type of int cf usb.core.device.write()).
        :returns: number of bytes sent (int).
        """
        try:
            nb = self._ep_out.write(msg)
        except usb.core.USBError as ex:
            logging.error("Could not write data: %r", ex)
            return 0
        return nb

    def read_ctrl(self):
        """Read raw dat on control endpointa.
        :returns: Received bytes (list of ?).
        """
        # Collect data
        try:
            data = self._ep_in.read(self._ep_dat_in.wMaxPacketSize)
        except usb.core.USBError as ex:
            logging.error("Could not read data: %r", ex)
        return data

    def _write(self, msg):
        """Write raw data.
        The method don't take care about meaning of msg.
        Write on the DDS board is handled by a FX2 device (USB interface).
        A write cycle on the FX2 device is divided in two parts:
        - init message writed to main endpoint (EP0),
        - real message writed to 'data' endpoint (EP4).
        Writing on the USB bus is transparent: you transmit each bit in order.
        Writing on the USB bus consists in filling the write function (usb.core)
        with a list of binary values.
        :param msg: message to write to device (sequence like type convertible
                    to array type of int cf usb.core.device.write()).
        :returns: number of bytes sent (int).
        """
        try:
            nb = self._ep_dat_out.write(msg)
        except usb.core.USBError as ex:
            logging.error("Could not write data: %r", ex)
            return 0
        return nb

    def _read(self):
        """Read raw data.
        The method don't take care about meaning of data.
        :returns: Received bytes (list of ?).
        """
        # Collect data
        try:
            data = self._ep_dat_in.read(self._ep_dat_in.wMaxPacketSize)
        except usb.core.USBError as ex:
            logging.error("Could not read data: %r", ex)
        return data

    @property
    def timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        if self._dev is None:
            logging.debug("Can't get timeout value, device not connected")
            return None
        return self._dev.timeout

    @timeout.setter
    def timeout(self, timeout):
        """Sets timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        if self._dev is None:
            logging.debug("Can't set timeout valule, device not connected")
            return
        self._dev.timeout = timeout
        self._timeout = timeout


#==============================================================================
class MercuryItcRs232(MercuryItc):

    """ISOBUS_ADDRESS = 1
    """

    BAUD = 9600
    DATA_SIZE = serial.EIGHTBITS
    PARITY = serial.PARITY_NONE
    STOP_BITS = serial.STOPBITS_ONE
    FLOW_CONTROL = False
    TIMEOUT = 2.0

    def __init__(self, port="", baudrate=BAUD, bytesize=DATA_SIZE,
                 parity=PARITY, stopbits=STOP_BITS, flowctrl=FLOW_CONTROL,
                 timeout=TIMEOUT):
        super().__init__()
        self._ser = None
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
        self._ser = serial.Serial(self.port,
                                  baudrate=self.baudrate,
                                  bytesize=self.bytesize,
                                  parity=self.parity,
                                  stopbits=self.stopbits,
                                  timeout=self.timeout)
        if self._ser.isOpen() is False:
            try:
                self._ser.open()
            except ValueError as ex:
                logging.error("Wrong connection parameters: %r", ex)
                return False
            except serial.SerialTimeoutException:
                logging.error("Timeout on connection")
                return False
        logging.info("Connected to device")
        self._ser.timeout = self.timeout
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
        logging.info("Connection to device closed")

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
        except Exception as ex:
            logging.error("Device write error %r", ex)
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
        except Exception as ex:
            logging.error("Device read error %r", ex)
            return ''
        return retval


#==============================================================================
if __name__ == "__main__":
    # Setup logger
    LOG_FORMAT = '%(asctime)s %(levelname)s %(filename)s (%(lineno)d): ' \
        +'%(message)s'
    logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)

    DEV = MercuryItcEth("192.168.0.22", timeout=5.0)
    #DEV = MercuryItcUsb()
    #DEV = MercuryItcRs232("/dev/ttyACM0")

    if DEV.connect() is False:
        exit()
    print("Connected to ", DEV.idn)

