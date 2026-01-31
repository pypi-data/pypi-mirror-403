# -*- coding: utf-8 -*-

"""package scinstr.daq.labjacq
author    Benoit Dubois
copyright FEMTO Engineering, 2020-2024
licence   GPL 3.0+
brief     Handle Labjack T7(-Pro) device (DAQ board) through USB interface.
details   The USB interface consists of the normal bidirectional control
          endpoint (0 OUT & IN), 3 used bulk endpoints (1 OUT, 2 IN, 3 IN),
          and 1 dummy endpoint (3 OUT). Endpoint 1 consists of a 64 byte OUT
          endpoint (address = 0x01). Endpoint 2 consists of a 64 byte IN
          endpoint (address = 0x82). Endpoint 3 consists of a dummy OUT
          endpoint (address = 0x03) and a 64 byte IN endpoint (address = 0x83).
          Endpoint 3 OUT is not supported, and should never be used.

          All commands should always be sent on Endpoint 1, and the responses
          to commands will always be on Endpoint 2. Endpoint 3 is only used
          to send stream data from the T-series device to the host.
"""

import logging
import time
import usb.core
import usb.util
import pymodbus.exceptions as mdex

# from pymodbus.factory import ClientDecoder
from pymodbus.pdu import DecodePDU as ClientDecoder
from pymodbus.exceptions import ConnectionException

#  pymodbus.framer.FramerSocket module
from pymodbus.framer import FramerSocket as ModbusSocketFramer

# from pymodbus.client.sync import BaseModbusClient
from pymodbus.client.base import ModbusBaseClient
from scinstr.daq.labjack.constants import T7_VID, T7_PID, T7_USB_TIMEOUT
from scinstr.daq.labjack.t7 import T7


DEFAULT_RETRIES_NB = 3

# USB interface parameters
_CONFIG_ID = 1
_INTERFACE_ID = 0  # The interface we use to talk to the device
_ALT_INTF_ID = 0  # The alternate interface use to talk to the device
_OUT_EP_ID = 0  # EP1_OUT @0x01 = 1    -> send command endpoint
_IN_EP_ID = 1  # EP2_IN  @0x82 = 130  -> response endpoint
_OUT_DAT_EP_ID = 2  # EP3_OUT @0x03 = 3    -> !! do not use !!
_IN_DAT_EP_ID = 3  # EP3_IN  @0x83 = 131  -> stream data from T7 to host


# =============================================================================
def get_interfaces():
    """Get available interface of T7 devices.
    Return a list of Usb Device, a named tuple with the following attributes:
    bLength, bDescriptorType, bcdUSB, bDeviceClass, bDeviceSubClass,
    bDeviceProtocol, bMaxPacketSize0, idVendor, idProduct, bcdDevice,
    iManufacturer, iProduct, iSerialNumber, bNumConfigurations, address, bus,
    port_number, port_numbers, speed.
    :returns: list of (usb.core.)Device (list of object)
    """
    interfaces = usb.core.find(idVendor=T7_VID, idProduct=T7_PID, find_all=True)
    return [interface for interface in interfaces]


# =============================================================================
class UsbModbusTcpClient(ModbusBaseClient):
    """'TCP' modbus client through USB connection."""

    def __init__(self, **kwargs):
        self._ep_in = None
        self._ep_out = None
        self._ep_din = None
        self._ep_dout = None
        self._socket = None
        self._vendor_id = kwargs.get("vendor_id", None)
        self._product_id = kwargs.get("product_id", None)
        self.bus = kwargs.get("bus", None)
        self.address = kwargs.get("address", None)
        self.timeout = kwargs.get("timeout", None)
        super().__init__(ModbusSocketFramer(ClientDecoder(is_server=False)))

    def __str__(self):
        """Builds a string representation of the connection.
        Function is used by pymodbus lib.
        !!!!!!
        Seems that usb driver needs to be recognize as UDP client (?Hack?).
        !!!!!!
        :returns: The string representation (str)
        """
        return "UsbModbusUdpClient(%s:%s)" % (self._vendor_id, self._product_id)

    def is_socket_open(self):
        """Check whether the underlying socket is open or not.
        :returns: True if socket/serial is open, False otherwise (bool)
        """
        if self._socket is None:
            return False
        return True

    def close(self):
        """Closes the underlying socket connection"""
        # Use of explicit release because it seems communication with t7 needs
        # deterministic interface release
        usb.util.release_interface(self._socket, _INTERFACE_ID)
        super().close()
        if self._socket is not None:
            del self._socket
            self._socket = None

    def connect(self):
        """Set an object representing our device (usb.core.Device).
        :param vendor_id: identification number of vendor (int)
        :param product_id: identification number of product (int)
        :returns: True if connection is Ok else returns False (bool)
        """
        if self._socket:
            return True
        # Find our device
        if self.bus is not None and self.address is not None:
            self._socket = usb.core.find(
                idVendor=self._vendor_id,
                idProduct=self._product_id,
                bus=self.bus,
                address=self.address,
            )
        else:
            self._socket = usb.core.find(
                idVendor=self._vendor_id, idProduct=self._product_id
            )
        # Was it found?
        if self._socket is None:
            logging.error("Device not found")
            return False
        # Detach the kernel driver if it is active
        if self._socket.is_kernel_driver_active(0):
            try:
                self._socket.detach_kernel_driver(0)
            except usb.core.USBError as ex:
                logging.critical("Could not detach kernel driver: %r", ex)
                return False
        #
        self._config(
            config_id=_CONFIG_ID,
            interface_id=_INTERFACE_ID,
            alt_interface_id=_ALT_INTF_ID,
            in_ep_id=_IN_EP_ID,
            out_ep_id=_OUT_EP_ID,
            in_dat_ep_id=_IN_DAT_EP_ID,
            out_dat_ep_id=_OUT_DAT_EP_ID,
        )
        logging.debug("UsbModbusClient connection OK ")
        return self._socket is not None

    def _config(
        self,
        config_id,
        interface_id,
        alt_interface_id,
        out_ep_id,
        in_ep_id,
        out_dat_ep_id,
        in_dat_ep_id,
    ):
        """Configure T7(-Pro) device and get endpoint instance.
        Endpoint Address description:
        - Bits 0..3 Endpoint Number.
        - Bits 4..6 Reserved. Set to Zero
        - Bits 7 Direction 0 = Out, 1 = In (Ignored for Control Endpoints)
        Example: address = 129 = (81)8 = (1000 0001)2
                 -> Direction: In, Number: 1
        :param config_id: ...
        ...
        :returns: None
        """
        try:
            self._socket.set_configuration(config_id)
        except usb.core.USBError as ex:
            logging.critical("USB error during dev configuration: %r", ex)
            raise
        except Exception as ex:
            logging.critical("Could not set interface configuration: %r", ex)
            raise
        # Set interface
        try:
            self._socket.set_interface_altsetting(
                interface=interface_id, alternate_setting=alt_interface_id
            )
        except usb.core.USBError as ex:
            logging.critical("USB error during interface altsetting: %r", ex)
            raise
        except Exception as ex:
            logging.critical("Error during interface altsetting: %r", ex)
            raise
        # Use of explicit release because it seems communication with t7 needs
        # deterministic interface claiming
        usb.util.claim_interface(self._socket, interface_id)
        # Get endpoint instances
        try:
            self._ep_out = self._socket[config_id - 1][
                (interface_id, alt_interface_id)
            ][out_ep_id]
            self._ep_in = self._socket[config_id - 1][(interface_id, alt_interface_id)][
                in_ep_id
            ]
            self._ep_dout = self._socket[config_id - 1][
                (interface_id, alt_interface_id)
            ][out_dat_ep_id]
            self._ep_din = self._socket[config_id - 1][
                (interface_id, alt_interface_id)
            ][in_dat_ep_id]
        except usb.core.USBError as ex:
            logging.critical("Could not set endpoint setting: %r", ex)
        logging.debug("USB interface succefuly configured")

    def send(self, request, _):
        """Sends data on the underlying socket
        :param request: The encoded request to send
        :return: The number of bytes written
        """
        if not self._socket:
            raise ConnectionException(self.__str__())
        if request:
            try:
                nb = self._ep_out.write(request, self.timeout)
            except usb.core.USBError as ex:
                logging.error("Could not write data: %r", ex)
                return 0
        return nb

    def recv(self, size):
        """Reads data from the underlying descriptor
        :param size: The number of bytes to read
        :return: The bytes read
        """
        if not self._socket:
            raise ConnectionException(self.__str__())

        begin = time.time()
        data = b""

        if size is not None:
            if size < self._ep_din.wMaxPacketSize:
                data = self._ep_in.read(self._ep_din.wMaxPacketSize)
            else:
                while len(data) < size:
                    try:
                        data += self._ep_in.read(self._ep_din.wMaxPacketSize)
                    except usb.core.USBError:
                        pass
                    if not self.timeout or (time.time() - begin > self.timeout):
                        break
        else:
            while True:
                try:
                    data += self._ep_in.read(self._ep_din.wMaxPacketSize)
                except usb.core.USBError:
                    pass
                if not self.timeout or (time.time() - begin > self.timeout):
                    break

        return data


# =============================================================================
class T7Usb(T7):
    """T7Usb class, provide command/response handling of LabJack T7(-Pro)
    board through USB interface.
    """

    def __init__(self, bus=None, address=None):
        super().__init__()
        self.bus = bus
        self.address = address

    def connect(self):
        """Connect to device.
        :returns: None
        """
        logging.info("Connecting to T7")
        try:
            self._client = UsbModbusTcpClient(
                retries=DEFAULT_RETRIES_NB,
                vendor_id=T7_VID,
                product_id=T7_PID,
                bus=self.bus,
                address=self.address,
                timeout=T7_USB_TIMEOUT,
            )
            is_connected = self._client.connect()
        except mdex.ConnectionException as ex:
            logging.error("Modbus connection error: %r", ex)
            return False
        except Exception as ex:
            logging.error("Unexpected exception: %r", ex)
            return False
        if is_connected is False:
            logging.error("Connection failed")
            return False
        logging.info("Connection --> Ok")
        return True

    def close(self):
        """Close connection with device.
        :returns: None
        """
        try:
            self._client.close()
        except Exception as ex:
            logging.error("Unexpected error %r", ex)
        else:
            logging.info("Connection to T7 closed")


# =============================================================================
if __name__ == "__main__":
    # For "Ctrl+C" works
    import signal

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Setup logger
    LOG_FORMAT = "%(asctime)s %(levelname)s %(filename)s (%(lineno)d): " + "%(message)s"
    logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

    I0 = 200e-6

    def pt100_v2t(volt, i0=I0):
        """Temperature from voltage of a Pt100 sensor."""
        return (2.604 * volt / i0) - 260.4

    print("Find T7 device(s) with following bus and address:")
    interfaces = get_interfaces()
    for interface in interfaces:
        print("bus: {}, address: {}".format(interface.bus, interface.address))

    _FILE = "t7.dat"

    T7 = T7Usb()
    if not (T7.connect()):
        print("Connection to T7 failed.")
        exit()

    # AINS_LIST = [0, 1, 2, 3]
    # T7.set_ains_resolution(AINS_LIST, [8, 8, 8, 8])

    T7.enable_high_speed_counter(2)

    with open(_FILE, "a") as fd:
        while True:
            # V_LIST = T7.get_ains_voltage(AINS_LIST)
            # V_STRING = ''
            # for V in V_LIST:
            #    V_STRING += str(V) + ';'
            # print(V_STRING)
            # v0 = v_list[1]-v_list[0]
            # v1 = v_list[2]-v_list[3]
            # t0 = pt100_v2t(v0)
            # t1 = pt100_v2t(v1)
            # print(v0, v1,t0, t1)
            # fd.write(v_string + '\n')
            # fd.flush()

            print("Frequency:", T7.get_high_speed_counter_frequency(2))
            time.sleep(1.0)

    T7.close()
    exit()
