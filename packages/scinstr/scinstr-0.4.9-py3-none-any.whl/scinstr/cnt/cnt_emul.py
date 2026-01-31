# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2019-2025
license   GPL v3.0+
brief     Emulate basic SCPI counter with state tuningable from webserver
"""

import logging
import threading
import time
import random
from enum import Enum
from remi import start, App, gui

# Only to mime real device import (detection of circular reference)
import socket
import usbtmc


DEFAULT_PORT = 8091
DEFAULT_FREQUENCY = 99999999.925  #100E6  # + 1.0


CommunicationState = Enum('State', [("OPENED", 1), ("CLOSED", 2), ("FAULTED", 3)])


# =============================================================================
def mystart(class_, port, userdata):
    start(class_, port=port, userdata=userdata)


# =============================================================================
class CntEmulator:
    """Emulate a basic Counter device behavior and problem:
    - get (emulated) measured values (user defined or randomized)
    - emulate disconnection/reconnection with device
    """

    def __init__(self, *args, **kwargs):
        """The constructor.
        :returns: None
        """
        self._log = logging.getLogger('scinstr.cnt.emul')
        self._communication_state = CommunicationState.CLOSED
        self._is_random_data = False
        if 'f_mean' in kwargs.keys():
            self._freq = kwargs['f_mean']
        else:
            self._freq = DEFAULT_FREQUENCY
        for idx, value in enumerate(args):
            self._log.info('Counter test device non-keyworded argument %02d: %r',
                         idx, value)
        for key, value in kwargs.items():
            self._log.info('Counter test device named argument %r: %r', key, value)
        mythread = threading.Thread(target=mystart, args=(CntEmulatorHandler, DEFAULT_PORT, (self,)))
        mythread.start()
        self._log.info("Counter test device %r initialization done", self)

    def set_frequency(self, value: float) -> None:
        self._freq = value
        self._log.info(f"set_frequency {value}")

    def set_communication_state(self, value: CommunicationState)-> None:
        self._communication_state = value
        self._log.info(f"set_communication_state {value}")

    def set_random_data_state(self, state)-> None:
        self._is_random_data = state

    @property
    def timeout(self):
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        self._log.info("Get Counter test device timeout: %r", self._timeout)
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        """Sets timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        self._timeout = timeout
        self._log.info("Set Counter test device timeout: %r", timeout)

    def connect(self) -> bool:
        """Connection process to Counter.
        :returns: True if connection success other False (Bool)
        """
        self._communication_state = CommunicationState.OPENED
        self._log.info("Connected to Counter test device: %r", self)
        return True

    def close(self)-> None:
        """Closing process with DMM.
        :returns: None
        """
        self._communication_state = CommunicationState.CLOSED
        self._log.info("Connection to DMM emulator device %r closed", self)

    def read(self, length):
        """Emulate read process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        if self._communication_state == CommunicationState.FAULTED:
            raise ConnectionError("Communication with (emulated) DMM failled")
        data = "emulated_counter"
        self._log.info("Read %r from DMM emulator device %r", data, self)
        return data

    def write(self, data):
        """Emulate write process
        :param data: data writes to device (str)
        :returns: None
        """
        if self._communication_state == CommunicationState.FAULTED:
            raise ConnectionError("Communication with (emulated) DMM failled")
        self._log.debug("Write %r to Counter test device %r", data, self)

    def query(self, msg):
        self._log.info(f"query({msg})")
        if msg == "SYST:ERR?":
            return "No error"
        return msg

    def reset(self) -> bool:
        """Connection process to Counter.
        :returns: True if connection success other False (Bool)
        """
        self._log.info("Reset Counter test device: %r", self)
        return True

    def get_error(self)-> list[str]:
        """Subclass method to emulate response of device.
        """
        return ["+0,\"No error\""]

    @property
    def is_connected(self):
        match self._communication_state:
            case CommunicationState.OPENED:
                return True
            case CommunicationState.CLOSED:
                return False
            case _:  # i.e. CommunicationState.FAULTED
                raise ConnectionError("Connection with Counter emulator failed")

    def data_read(self):
        if self._communication_state == CommunicationState.FAULTED:
            raise ConnectionError("Communication with (emulated) Counter failled")
        time.sleep(1.0)  # Acquisition time
        data = self._freq
        if self._is_random_data is True:
            data += self._random_gen()
        self._log.debug("Counter test data_read(%r) %r", data, self)
        return data

    def _random_gen(self) -> float:
        """Return a random value: use to emulate data input acquisition.
        """
        return random.uniform(-1.0, 1.0)


# =============================================================================
class CntEmulatorHandler(App):
    """Handle emulated Counter state from a web app.
    """

    def main(self, counter)-> gui.Widget:
        self._cnt = counter
        #
        main_box = gui.VBox()
        title_box = gui.HBox()
        title_lbl = gui.Label('Counter emulator handler', width="80%", margin="5px")
        comm_fault_box = gui.HBox()
        comm_fault_lbl = gui.Label('Emulate communication fault', width="80%", margin="5px")
        self.comm_fault_cbox = gui.CheckBox(False, width="20%", margin="5px")
        freq_box = gui.HBox()
        freq_lbl = gui.Label('Frequency value (Hz)', width="20%", margin="5px")
        self.freq_input = gui.TextInput(width="40%", margin="5px")
        self.freq_input.set_text(str(DEFAULT_FREQUENCY))
        self.freq_btn = gui.Button('Set', width="10%", margin="5px")
        #
        title_box.append(title_lbl)
        comm_fault_box.append(comm_fault_lbl)
        comm_fault_box.append(self.comm_fault_cbox)
        freq_box.append(freq_lbl)
        freq_box.append(self.freq_input)
        freq_box.append(self.freq_btn)
        main_box.append(title_box)
        main_box.append(comm_fault_box)
        main_box.append(freq_box)
        #
        self.comm_fault_cbox.onclick.do(self.comm_fault_pressed)
        self.freq_btn.onclick.do(self.freq_btn_pressed)
        #
        return main_box

    def comm_fault_pressed(self, widget)-> None:
        if self.comm_fault_cbox.get_value() is True:
            state = CommunicationState.FAULTED
        else:
            state = CommunicationState.OPENED
        self._cnt.set_communication_state(state)

    def freq_btn_pressed(self, widget)-> None:
        self._log.critical(f"set frequency: {self.freq_input.text}")
        self._cnt.set_frequency(self.freq_input.text)


# =============================================================================
def check_cnt_emulator():
    """Check the Cnt532x0aEmul class: connect to the counter, configure
    frequency measurement then collect and print data to standard output.
    """
    from datetime import datetime

    date_fmt = "%d/%m/%Y %H:%M:%S"
    log_format = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d): %(message)s"
    self._log.basicConfig(level=self._log.INFO,
                        datefmt=date_fmt,
                        format=log_format)

    f_mean = 10E7

    cnt = CntEmulator(0x2a8d, 0x1601, timeout=4.8, f_mean=f_mean)



if __name__ == '__main__':
    check_cnt_emulator()
