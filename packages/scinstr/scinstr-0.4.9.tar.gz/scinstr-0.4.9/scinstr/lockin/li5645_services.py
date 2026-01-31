# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2026
license   LGPL v3.0+
brief     Service class (hardware communication interface) for handling
          NF LI56[45|50] devices
"""

import socket
import serial
import pyvisa
from typing import Protocol


# ----------------------------------------------------------------------------
class HwIntfService(Protocol):

    def connect(self) -> bool:
        """Connect to the device
        :returns: True if connection succeeded, False otherwise
        """
        ...

    def close(self) -> None:
        """Closes the underlying connection"""
        ...

    def write(self, msg: str) -> int:
        """Writing process.
        :param msg: message writes to device (str)
        :returns: number of bytes sent (int)
        """
        ...

    def read(self, length: int) -> str:
        """Reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        ...

    def query(self, msg: str) -> str:
        """Basic query i.e. write then read.
        """
        ...


# ----------------------------------------------------------------------------
class Usb(HwIntfService):

    def __init__(
        self, vendor_id: int, product_id: int, serial_id: str = "", timeout: float = 0
    ) -> None:
        self.vid = vendor_id
        self.pid = product_id
        self.sid = serial_id
        self._timeout = timeout  # in second

    def connect(self) -> bool:
        rm = pyvisa.ResourceManager()
        # USB[board]::manufacturer ID::model code::serial number[::USB interface number][::INSTR]
        # USB::0x1234::125::A22-5::INSTR
        try:
            self._dev = rm.open_resource(
                f"USB::{self.vid}::{self.pid}::{self.sid}::INSTR"
            )
        except pyvisa.VisaIOError as e:
            print(f"Opening USB interface failed: {e}")
            return False
        self._dev.read_termination = "\n"
        self._dev.write_termination = "\n"
        self._dev.timeout = self._timeout * 1000  # in ms
        return True

    def close(self) -> None:
        self._dev.close()

    def write(self, msg: str) -> int:
        try:
            nb_byte = self._dev.write(msg)
        except AttributeError as ex:  # Exception raised after first write
            return 0
        return nb_byte

    def read(self, length: int) -> str:
        return self._dev.read()

    def query(self, msg: str) -> str:
        return self._dev.query(msg)


# ----------------------------------------------------------------------------
class Serial(HwIntfService):

    def __init__(
        self, port: str, baudrate: int = 9600, timeout: float = 0.5
    ) -> None:
        self.port = port
        self._timeout = timeout
        self._baudrate = baudrate
        self._dev = None

    def connect(self) -> bool:
        try:
            self._dev = serial.Serial(
                port=self.port, 
                baudrate=self._baudrate,
                timeout=self._timeout
                )
        except Exception as ex:
            print(f"Opening serial port failed: {ex}")
            return False
        return True

    def close(self) -> None:
        if self._dev:
            self._dev.close()

    def write(self, msg: str) -> int:
        return self._dev.write((msg + '\n').encode("utf-8"))

    def read(self, length: int) -> str:
        return self._dev.read(length).decode("utf-8")

    def query(self, msg: str) -> str:
        self._dev.write((msg + '\n').encode("utf-8"))
        return self._dev.readline().decode("utf-8")[:-1]


# ----------------------------------------------------------------------------
class Socket(HwIntfService):

    def __init__(self, ip: str, port: int, timeout: float = 0.1) -> None:
        """
        :param ip: IP address of device (str)
        :param port: Ethernet port of device (int)
        :param timeout: Socket timeout value in s (float)
        :returns: None
        """
        self._sock = None
        self._ip = ip
        self._port = port
        self._timeout = timeout

    def connect(self):
        self._sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
        )
        self._sock.settimeout(self._timeout)
        try:
            self._sock.connect((self._ip, self._port))
        except Exception as ex:
            print(f"Opening socket failed: {ex}")
            return False
        return True

    def close(self):
        self._sock.close()

    def write(self, msg):
        self._sock.send(msg.encode("utf8"))

    def read(self, length):
        return self._sock.recv(length).decode("utf-8")
