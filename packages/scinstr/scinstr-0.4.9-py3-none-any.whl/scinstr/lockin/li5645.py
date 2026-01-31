# -*- coding: utf-8 -*-

"""package scinstr
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2026
license   LGPL v3.0+
brief     Base class for handling NF LI56[45|50] devices
"""

import time
from collections import OrderedDict
from scinstr.lockin.li5645_services import HwIntfService

SENSITIVITY = OrderedDict(
    [
        ("1 V", 0),
        ("500 mV", 1),
        ("200 mV", 2),
        ("100 mV", 3),
        ("50 mV", 4),
        ("20 mV", 5),
        ("10 mV", 6),
        ("5 mV", 7),
        ("2 mV", 8),
        ("1 mV", 9),
        ("500 uV", 10),
        ("200 uV", 11),
        ("100 uV", 12),
        ("50 uV", 13),
        ("20 uV", 14),
        ("10 uV", 15),
        ("5 uV", 16),
        ("2 uV", 17),
        ("1 uV", 18),
        ("500 nV", 19),
        ("200 nV", 20),
        ("100 nV", 21),
        ("50 nV", 22),
        ("20 nV", 23),
        ("10 nV", 24),
    ]
)

# TCONSTANTS = OrderedDict(
#     [
#         ("10 us", 0),
#         ("30 us", 1),
#         ("100 us", 2),
#         ("300 us", 3),
#         ("1 ms", 4),
#         ("3 ms", 5),
#         ("10 ms", 6),
#         ("30 ms", 7),
#         ("100 ms", 8),
#         ("300 ms", 9),
#         ("1 s", 10),
#         ("3 s", 11),
#         ("10 s", 12),
#         ("30 s", 13),
#         ("100 s", 14),
#         ("300 s", 15),
#         ("1 ks", 16),
#         ("3 ks", 17),
#         ("10 ks", 18),
#         ("30 ks", 19),
#     ]
# )

# SAMPLE_RATES = OrderedDict(
#     [
#         ("62.5 mHz", 0),
#         ("125 mHz", 1),
#         ("250 mHz", 2),
#         ("500 mHz", 3),
#         ("1 Hz", 4),
#         ("2 Hz", 5),
#         ("4 Hz", 6),
#         ("8 Hz", 7),
#         ("16 Hz", 8),
#         ("32 Hz", 9),
#         ("64 Hz", 10),
#         ("128 Hz", 11),
#         ("256 Hz", 12),
#         ("512 Hz", 13),
#         ("trigger", 14),
#     ]
# )

# REFERENCE_TRIGGER = OrderedDict(
#     [("zero_crossing", 0), ("rising_edge", 1), ("faling_edge", 2)]
# )

# INPUT_SHIELD = OrderedDict([("float", 0), ("ground", 1)])

# INPUT_COUPLING = OrderedDict([("AC", 0), ("DC", 1)])

# INPUT_FILTER = OrderedDict(
#     [((False, False), 0), ((True, False), 1), ((False, True), 2), ((True, True), 3)]
# )

# RESERVE_MODE = OrderedDict([("high", 0), ("normal", 1), ("low", 2)])

# FILTER_SLOPE = OrderedDict(
#     [("6 dB/oct", 0), ("12 dB/oct", 1), ("18 dB/oct", 2), ("24 dB/oct", 3)]
# )

# FRONT_OUTPUT = OrderedDict([("display", 0), ("X", 1)])

# AUTO_OFFSET_ASYNC_CH = OrderedDict([("x", 1), ("y", 2), ("r", 3)])

# FAST_MODE = OrderedDict([("Off", 0), ("On (Dos)", 1), ("On (Windows)", 2)])


# =============================================================================
class Li5645(object):
    """Base class for NF LI56[45|50] Lock-In Amplifier devices."""

    def __init__(self, hw_intf: HwIntfService) -> None:
        self.hw_intf = hw_intf

    def connect(self) -> bool:
        return self.hw_intf.connect()

    def close(self) -> None:
        return self.hw_intf.close()

    def write(self, msg: str) -> int:
        return self.hw_intf.write(msg)

    def read(self, length: int) -> str:
        return self.hw_intf.read(length)

    def query(self, msg: str) -> str:
        return self.hw_intf.query(msg)

    @property
    def idn(self):
        """Instrument identification."""
        return self.query("*IDN?")

    def reset(self):
        """Reset GPIB interface of Stanford device"""
        self.write("*RST")

    def status_byte(self, bit=None):
        """Serial poll status byte, a number between 0-255.
        User can request a specific bit value.
        """
        if bit is None:
            return int(self.query("*STB?"))
        else:
            return int(self.query("*STB? {:d}".format(bit)))

    def wait_bit0(self):
        """Check the scan in progress bit in the Serial Poll Status
        Byte (bit 0) to determine when a scan is finished.
        """
        bit0 = self.status_byte(0)
        while bit0 == 0:
            time.sleep(1.0)
            bit0 = self.status_byte(0)

    def wait_bit1(self):
        """Check the command execution in progress bit in the Serial Poll
        Status Byte (bit 1) to determine when the function is finished.
        """
        bit1 = self.status_byte(1)
        while bit1 == 0:
            time.sleep(0.5)
            bit1 = self.status_byte(1)

    @property
    def reference_phase_shift(self):
        """Getter of the phase shift of the reference."""
        return self.query("PHAS?")

    @reference_phase_shift.setter
    def reference_phase_shift(self, value):
        """Setter of the phase shift of the reference."""
        self.write("PHAS{:.2f}".format(value))

    @property
    def reference_frequency(self, outn: int = 1) -> str | None:
        """Getter of the reference source.
        :param outn: source output (int, 1 or 2)
        """
        if outn not in (1, 2):
            return
        return self.query(f":SOUR:FREQ{outn:d}?")

    @reference_frequency.setter
    def reference_frequency(self, value: float, outn: int = 1):
        """Setter of the reference source."""
        if outn not in (1, 2):
            return
        self.write(f":SOUR:FREQ{outn:d} {value:.5E}")

    @property
    def reference_amplitude(self) -> str:
        """Getter of the amplitude of the sine:SOURce:VOLTag output."""
        return self.query("SOUR:VOLT:AMPL?")

    @reference_amplitude.setter
    def reference_amplitude(self, value: float) -> None:
        """Setter of the amplitude of the sine output."""
        self.write(f"SOUR:VOLT:AMPL {value:.3E}")

    # --------------------------------
    # GAIN and TIME CONSTANT COMMANDS.
    # --------------------------------

    @property
    def sensitivity(self):
        """Getter of the sensitivity tuning."""
        return self.query("VOLT:AC:RANG?")

    @sensitivity.setter
    def sensitivity(self, value):
        """Setter of the sensitivity tuning."""
        self.write(f"VOLT:AC:RANG {value}")

    @property
    def time_constants(self):
        """Get time constant."""
        return self.query("FILT:TCON?")

    @time_constants.setter
    def time_constants(self, value):
        """Set time constant."""
        self.write(f"FILT:TCON {value}")

    @property
    def filter_db_per_oct(self):
        """Get the low pass filter slope."""
        return self.query("FILT:SLOP?")

    @filter_db_per_oct.setter
    def filter_db_per_oct(self, value):
        """Set the low pass filter slope."""
        self.write(f"FILT:SLOP {value:d}")

    @property
    def sync_filter(self):
        """Get synchronous filter status."""
        return self.query("FILT:TYPE?")

    @sync_filter.setter
    def sync_filter(self, value):
        """Set synchronous filter status."""
        self.write(f"FILT:TYPE {value}")

    # SETUP COMMANDS

    # @property
    # def remote(self):
    #     """Lock Front panel."""
    #     self.write("OVRM?")

    # @remote.setter
    # def remote(self, value):
    #     """Lock Front panel."""
    #     self.write("OVRM {:d}".format(value))

    # @property
    # def key_click_enabled(self):
    #     """Get key click status."""
    #     return self.query("KCLK?")

    # @key_click_enabled.setter
    # def key_click_enabled(self, value):
    #     """Set key click status."""
    #     self.write("KCLK {}".format(value))

    # @property
    # def alarm_enabled(self):
    #     """Get alarm status."""
    #     return self.query("ALRM?")

    # @alarm_enabled.setter
    # def alarm_enabled(self, value):
    #     """Set alarm status."""
    #     self.write("ALRM {}".format(value))

    # def recall_state(self, location):
    #     """Recalls instrument state in specified non-volatile location.
    #     :param location: non-volatile storage location.
    #     """
    #     self.write("RSET {}".format(location))

    # def save_state(self, location):
    #     """Saves instrument state in specified non-volatile location.
    #     Previously stored state in location is overwritten (no error
    #     is generated).
    #     :param location: non-volatile storage location.
    #     """
    #     self.write("SSET {}".format(location))

    # ---------------
    # AUTO FUNCTIONS.
    # ---------------

    # def auto_gain_async(self):
    #     """Equivalent to press the Auto Gain key in the front panel.
    #     Might take some time if the time constant is long.
    #     Does nothing if the constant is greater than 1 second.
    #     """
    #     self.write("AGAN")

    # def auto_gain(self):
    #     """Synced auto gain command."""
    #     self.auto_gain_async()
    #     self.wait_bit1()

    # def auto_reserve_async(self):
    #     """Equivalent to press the Auto Reserve key in the front panel.
    #     Might take some time if the time constant is long.
    #     """
    #     self.write("ARSV")

    # def auto_reserve(self):
    #     """Synced auto reserve command"""
    #     self.auto_reserve_async()
    #     self.wait_bit1()

    # def auto_phase_async(self):
    #     """Equivalent to press the Auto Phase key in the front panel.
    #     Might take some time if the time constant is long.
    #     Does nothing if the phase is unstable.
    #     """
    #     self.write("ARSV")

    # def auto_phase(self):
    #     """Synced auto phase command."""
    #     self.auto_phase_async()
    #     self.wait_bit1()

    # def auto_offset_async(self, channel):
    #     """Automatically offset a given channel to zero.
    #     Is equivalent to press the Auto Offset Key in the front panel.
    #     :param channel: the name of the channel.
    #     :returns: None
    #     """
    #     self.write("AOFF {}".format(channel))

    # ----------------------
    # DATA STORAGE COMMANDS.
    # ----------------------

    # @property
    # def sample_rate(self):
    #     """Queries the data sample rate."""
    #     return self.query("SRAT?")

    # @sample_rate.setter
    # def sample_rate(self, value):
    #     """Sets the data sample rate."""
    #     self.write("SRAT {}".format(value))

    # @property
    # def single_shot(self):
    #     """End of buffer mode getter:
    #     - if True (1 shot mode), at the end of the buffer, data storage stops
    #     and an audio alarm sounds.
    #     - if False (Loop mode), data storage continues continues at the end of
    #     the buffer.
    #     Note: If loop mode selected, make sure to pause data storage before
    #     reading the data to avoid confusion about which point is the most
    #     recent.
    #     """
    #     return self.query("SEND?")

    # @single_shot.setter
    # def single_shot(self, value):
    #     """End of buffer mode setter."""
    #     self.write("SEND {}".format(value))

    # def trigger(self):
    #     """Software trigger command. This command has the same effect as
    #     a trigger at the rear panel trigger input.
    #     """
    #     self.write("TRIG")

    # @property
    # def trigger_start_mode(self):
    #     """Getter of trigger start mode."""
    #     return self.query("TSTR?")

    # @trigger_start_mode.setter
    # def trigger_start_mode(self, value):
    #     """Setter of trigger start mode."""
    #     self.write("TSTR {}".format(value))

    # def start_data_storage(self):
    #     """Start or resume data storage. Command is ignored if
    #     storage is already in progress.
    #     """
    #     self.write("STRT")

    # def pause_data_storage(self):
    #     """Pause data storage.  If storage is already paused
    #     or reset then this command is ignored.
    #     """
    #     self.write("PAUS")

    # def reset_data_storage(self):
    #     """Reset data buffers. The command can be sent at any time, any storage
    #     in progress, paused or not, will be reset. The command will erase
    #     the data buffer.
    #     """
    #     self.write("REST")

    # ---------------
    # OAUX See above.
    # ---------------

    # def buffer_length(self):
    #     """Query the number of points stored in the buffer.
    #     :returns: the number of points stored in the buffer.
    #     """
    #     return int(self.query("SPTS?"))

    # @property
    # def fast_mode(self):
    #     """Query the data transfer mode value:
    #     - 0: Off
    #     - 1: On (DOS programs or other dedicated data collection computers)
    #     - 2: On (Windows Operating System Programs)
    #     """
    #     return self.query("FAST?")

    # @fast_mode.setter
    # def fast_mode(self, value):
    #     """Set the data transfer mode on and off."""
    #     self.write("FAST {:d}".format(value))

    # def start_fast_data_storage(self):
    #     """Start the datat storage after turning on fast data transfert."""
    #     self.write("STRD")

    # -----------------------
    # DATA TRANSFER COMMANDS.
    # -----------------------

    # def analog_value(self, key):
    #     """The command reads the value of X, Y, R, θ, CH1 or CH2 display.
    #     Available key = {'x', 'y', 'r', 't', '1', '2'}.
    #     """
    #     if key in "xyrt":
    #         return self.query("OUTP? {}".format(key))
    #     else:
    #         return self.query("OUTR? {}".format(key))

    def set_measure(self, measure: str, channel:int = 1) -> None:
        """From "REAL|MLIN|IMAG|PHAS|NOIS|AUX1|REAL2|MLIN2"
        """
        self.write(f"CALC{channel}:FORM {measure}")

    def measure(self, channel:int = 1) -> str:
        """The command return the value from X, Y, R, θ and input referred noise density.
        :returns: data value recorded (float)
        """
        return self.query(f"CALC{channel}:FORM?")

    # def read_buffer(self, start=0, length=None, _format="a"):
    #     """Queries points stored in the Channel buffer
    #     :param start: Index of the buffer to start.
    #     :param length: Number of points to read.
    #                    Defaults to the number of points in the buffer.
    #     :param _format: Transfer format
    #                   'a': ASCII (slow)
    #                   'b': IEEE Binary (fast) - NOT IMPLEMENTED
    #                   'c': Non-IEEE Binary (fastest) - NOT IMPLEMENTED
    #     """
    #     if _format == "c":
    #         cmd = "TRCL"
    #     elif _format == "b":
    #         cmd = "TRCB"
    #     else:
    #         cmd = "TRCA"
    #     if not length:
    #         length = self.buffer_length
    #     self.write("{}? {},{}".format(cmd, start, length))
    #     if cmd == "TRCA":
    #         data = self.read()
    #         return [float(x) for x in data.split(",")]
    #     elif cmd == "TRCB":
    #         return self.read()
    #     else:
    #         return self.read()

    # @property
    # def display(self, channel):
    #     """Query the display source.
    #     :param channel: 1 or 2 i.e. CH1 or CH2 (int)
    #     """
    #     return [int(var) for var in self.query("DDEF? {}".format(channel)).split(",")]

    # @display.setter
    # def display(self, channel, display, ratio):
    #     """Set the display source.
    #     :param channel: 1 or 2 i.e. CH1 or CH2 (int)
    #     :param display: 0, 1, 2, 3, 4 i.e. X, R, Xnoise,
    #                     AUxIn1 or AuxIn2 (int))
    #     :param ratio: 0, 1, 2 i.e. none, AuxIn1, AuxIn2 (int)
    #     """
    #     self.write("DDEF {},{},{}".format(channel, display, ratio))

    # @property
    # def front_output(self, channel):
    #     """Query the output source.
    #     :param channel: 1 or 2 i.e. CH1 or CH2 (int)
    #     """
    #     return self.query("FPOP? {}".format(channel))

    # @front_output.setter
    # def front_output(self, channel, output):
    #     """Set the output source.
    #     :param channel: 1 or 2 i.e. CH1 or CH2 (int)
    #     :param output: X, Y (output=1) or Display (output=0) (int)
    #     """
    #     self.write("FPOP {},{}".format(channel, output))
