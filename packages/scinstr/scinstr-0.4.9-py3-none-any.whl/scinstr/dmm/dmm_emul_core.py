# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2019-2025
license   GPL v3.0+
brief     Emulated DMM with state tuningable from webserver
"""

import logging
import time
import threading
import random
from enum import Enum
from remi import start, App, gui

# Only to mime real device import (detection of circular reference)
import socket
import usbtmc


ACQUISITION_TIMES = {
    "1": 0.02,
    "10": 0.2,
    "100": 2,
}

DEFAULT_PORT = 8090
DEFAULT_FREQUENCY = 10E3
DEFAULT_VOLTAGE = 0.0005
DEFAULT_RANDOM_RANGE = 0.0001
DEFAULT_RANDOM_STATE= True
DEFAULT_ENABLE_PERIOD = 15
DEFAULT_DISABLE_PERIOD = 5
DEFAULT_ACQUISITION_TIME = ACQUISITION_TIMES["10"]


DmmMode= Enum('Mode', [("VOLTMETER", 1), ("FREQUENCYMETER", 2)])
CommunicationState = Enum('State', [("OPENED", 1), ("CLOSED", 2), ("FAULTED", 3)])

DEFAULT_MODE = DmmMode.VOLTMETER


# =============================================================================
def mystart(class_, port, userdata):
    start(class_, port=port, userdata=userdata)


# =============================================================================
class RepeatTimer(threading.Timer):
    """From https://stackoverflow.com/questions/12435211/threading-timer-repeat-function-every-n-seconds
    """
    def run(self)-> None:
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


# =============================================================================
class DmmEmulator:
    """Emulate a basic DMM device behavior and problem:
    - select mode between frequencymeter and voltmeter
    - get (emulated) measured values (user defined or randomized)
    - emulate disconnection/reconnection with device
    """

    def __init__(self, *args, **kwargs)-> None:
        """The constructor.
        :returns: None
        """
        self._log = logging.getLogger('scinstr.dmm.emul')
        self._communication_state = CommunicationState.CLOSED
        self._com_fail_duration = {'enable':DEFAULT_ENABLE_PERIOD, 'disable': DEFAULT_DISABLE_PERIOD}
        self._com_period_timer = None
        self._mode = DEFAULT_MODE
        self._is_random_data = False
        self._random_range = DEFAULT_RANDOM_RANGE
        self._freq = DEFAULT_FREQUENCY
        self._volt = DEFAULT_VOLTAGE
        self._acquisition_time = DEFAULT_ACQUISITION_TIME
        for idx, value in enumerate(args):
            self._log.info('DMM emulator device non-keyworded argument %02d: %r',
                         idx, value)
        for key, value in kwargs.items():
            self._log.info('DMM emulator device named argument %r: %r', key, value)
        mythread = threading.Thread(target=mystart, args=(DmmEmulatorHandler, DEFAULT_PORT, (self,)))
        mythread.start()
        self._log.info("DMM emulator device %r initialization done", self)

    def set_frequency(self, value: float) -> None:
        self._freq = value
        self._log.info(f"set_frequency {value}")

    def set_voltage(self, value: float)-> None:
        self._volt = value
        self._log.info(f"set_voltage {value}")

    def set_random_range(self, value: float) -> None:
        self._random_range = value
        self._log.info(f"set_random_range {value}")

    def set_communication_state(self, value: CommunicationState)-> None:
        self._communication_state = value
        self._log.info(f"set_communication_state {value}")

    def _emul_timed_faulted_connection(self, duration: float)-> None:
        """Emulate a faulted connection with device of 'duration' second.
        """
        self._log.info("Begin connection fault test")
        self._communication_state = CommunicationState.FAULTED
        time.sleep(duration)
        self._communication_state = CommunicationState.OPENED
        self._log.info("End connection fault test")

    def set_communication_faillure_params(self, enable_period=DEFAULT_ENABLE_PERIOD, disable_period=DEFAULT_DISABLE_PERIOD)-> None:        
        self._com_fail_duration['enable'] = enable_period
        self._com_fail_duration['disable'] = disable_period

    def set_communication_faillure_state(self, value: bool)-> None:
        if value is False:
            if self._com_period_timer:
                self._com_period_timer.cancel()
            return
        self._com_period_timer = RepeatTimer(
            self._com_fail_duration['enable'], 
            self._emul_timed_faulted_connection, 
            args=(self._com_fail_duration['disable'],)
        )
        self._com_period_timer.start()

    def set_random_data_state(self, state)-> None:
        self._is_random_data = state

    @property
    def timeout(self)-> float:
        """Gets timeout on socket operations.
        :returns: timeout value in second (float)
        """
        self._log.info("Get DMM emulator device timeout: %r", self._timeout)
        return self._timeout

    @timeout.setter
    def timeout(self, timeout)-> None:
        """Sets timeout on socket operations.
        :param timeout: timeout value in second (float)
        :returns: None
        """
        self._timeout = timeout
        self._log.info("Set DMM emulator device timeout: %r", timeout)

    def connect(self)-> bool:
        """Overload connection process to DMM.
        :returns: True if connection success other False (Bool)
        """
        self._communication_state = CommunicationState.OPENED
        self._log.info("Connected to DMM emulator device: %r", self)
        return True

    def close(self)-> None:
        """Closing process with DMM.
        :returns: None
        """
        self._communication_state = CommunicationState.CLOSED
        self._log.info("Connection to DMM emulator device %r closed", self)

    def reset(self) -> bool:
        """Connection process to DMM.
        :returns: True if connection success other False (Bool)
        """
        self._log.info("Reset DMM test device: %r", self)
        return True

    def get_error(self)-> list[str]:
        """Subclass method to emulate response of device.
        """
        return ["+0,\"No error\""]

    @property
    def is_connected(self)-> bool:
        """Check connection property.
        :returns: True if device connected else False (bool)
        """
        match self._communication_state:
            case CommunicationState.OPENED:
                return True
            case CommunicationState.CLOSED:
                return False
            case _:  # i.e. CommunicationState.FAULTED
                raise ConnectionError("Connection with DMM emulator failed")

    def write(self, data)-> int:
        """Emulate write process
        :param data: data writes to device (str)
        :returns: None
        """
        if self._communication_state == CommunicationState.FAULTED:
            raise ConnectionError("Communication with (emulated) DMM failled")
        if "CONF:FREQ" in data:
            self._mode = DmmMode.FREQUENCYMETER
        elif "CONF:VOLT:DC" in data:
            self._mode = DmmMode.VOLTMETER
        elif ":NPLC" in data:
            nplc = data.split("NPLC")[-1].replace(' ', '')
            self._acquisition_time = float(ACQUISITION_TIMES[nplc])
        self._log.info("Write %r to DMM emulator device %r", data, self)
        return len(data)

    def ask(self, msg):
        if "READ?" in msg:
            return self.data_read()
        return msg
        
    def data_read(self)-> float:
        if self._communication_state == CommunicationState.FAULTED:
            raise ConnectionError("Communication with (emulated) DMM failled")
        time.sleep(self._acquisition_time)  # Acquisition time
        if self._mode == DmmMode.FREQUENCYMETER:
            data = self._freq
        else:
            data = self._volt
        if self._is_random_data is True:
            data += self._random_gen()
        return data

    def read(self, length)-> str:
        """Emulate read process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        if self._communication_state == CommunicationState.FAULTED:
            raise ConnectionError("Communication with (emulated) DMM failled")
        data = "emulated_dmm"
        self._log.info("Read %r from DMM emulator device %r", data, self)
        return data

    def _random_gen(self)-> float:
        """Return a random value: use to emulate data input acquisition.
        """
        return random.uniform(-self._random_range / 2.0, self._random_range / 2.0)


# =============================================================================
class DmmEmulatorHandler(App):
    """Handle emulated DMM state from a web app.
    """

    def main(self, dmm)-> gui.Widget:
        self._dmm = dmm
        #
        main_box = gui.VBox()
        title_box = gui.HBox()
        title_lbl = gui.Label('DMM emulator handler', width="80%", margin="5px")
        comm_fault_box = gui.HBox()
        comm_fault_lbl = gui.Label('Emulate communication fault', width="80%", margin="5px")
        self.comm_fault_cbox = gui.CheckBox(checked=False, width="20%", margin="5px")
        randomize_box = gui.HBox()
        randomize_lbl = gui.Label('Randomize value', width="80%", margin="5px")
        self.randomize_cbox = gui.CheckBox(checked=DEFAULT_RANDOM_STATE, width="20%", margin="5px")
        random_range_box = gui.HBox()
        random_range_lbl = gui.Label('Random range (Hz or V)', width="20%", margin="5px")
        self.random_range_input = gui.TextInput(width="40%", margin="5px")
        self.random_range_input.set_text(str(DEFAULT_RANDOM_RANGE))
        self.random_range_btn = gui.Button('Set', width="10%", margin="5px")
        freq_box = gui.HBox()
        freq_lbl = gui.Label('Frequency value (Hz)', width="20%", margin="5px")
        self.freq_input = gui.TextInput(width="40%", margin="5px")
        self.freq_input.set_text(str(DEFAULT_FREQUENCY))
        self.freq_btn = gui.Button('Set', width="10%", margin="5px")
        volt_box = gui.HBox()
        volt_lbl = gui.Label('Voltage value (V)', width="20%", margin="5px")
        self.volt_input = gui.TextInput(width="40%", margin="5px")
        self.volt_input.set_text(str(DEFAULT_VOLTAGE))
        self.volt_btn = gui.Button('Set', width="10%", margin="5px")
        #
        title_box.append(title_lbl)
        comm_fault_box.append(comm_fault_lbl)
        comm_fault_box.append(self.comm_fault_cbox)
        freq_box.append(freq_lbl)
        freq_box.append(self.freq_input)
        freq_box.append(self.freq_btn)
        volt_box.append(volt_lbl)
        volt_box.append(self.volt_input)
        volt_box.append(self.volt_btn)
        randomize_box.append(randomize_lbl)
        randomize_box.append(self.randomize_cbox)
        random_range_box.append(random_range_lbl)
        random_range_box.append(self.random_range_input)
        random_range_box.append(self.random_range_btn)
        main_box.append(title_box)
        main_box.append(comm_fault_box)
        main_box.append(freq_box)
        main_box.append(volt_box)
        main_box.append(randomize_box)
        main_box.append(random_range_box)
        #
        self.comm_fault_cbox.onclick.do(self.comm_fault_pressed)
        self.freq_btn.onclick.do(self.freq_btn_pressed)
        self.volt_btn.onclick.do(self.volt_btn_pressed)
        self.randomize_cbox.onclick.do(self.randomize_pressed)
        self.random_range_btn.onclick.do(self.random_range_pressed)
        #
        self._dmm.set_random_data_state(DEFAULT_RANDOM_STATE)
        #
        return main_box

    def comm_fault_pressed(self, widget) -> None:
        if self.comm_fault_cbox.get_value() is True:
            state = CommunicationState.FAULTED
        else:
            state = CommunicationState.OPENED
        self._dmm.set_communication_state(state)

    def freq_btn_pressed(self, widget) -> None:
        self._dmm.set_frequency(float(self.freq_input.text))

    def volt_btn_pressed(self, widget) -> None:
        self._dmm.set_voltage(float(self.volt_input.text))

    def randomize_pressed(self, widget) -> None:
        if self.randomize_cbox.get_value() is True:
            self._dmm.set_random_data_state(True)
        else:
            self._dmm.set_random_data_state(False)

    def random_range_pressed(self, widget) -> None:
        self._dmm.set_random_range(float(self.random_range_input.text))


# =============================================================================
def check_dmm_emulator()-> None:
    date_fmt = "%d/%m/%Y %H:%M:%S"
    log_format = "%(asctime)s %(levelname) -8s %(filename)s " + \
                 " %(funcName)s (%(lineno)d)-> None: %(message)s"
    self._log.basicConfig(level=self._log.INFO,
                        datefmt=date_fmt,
                        format=log_format)

    dmm = DmmEmulator(pid=0x2a8d, vid=0x1601, timeout=4.8)


if __name__ == '__main__':
    check_dmm_emulator()
