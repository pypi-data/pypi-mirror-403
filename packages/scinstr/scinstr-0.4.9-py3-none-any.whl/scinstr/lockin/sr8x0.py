# -*- coding: utf-8 -*-

"""package stanford
author    Benoit Dubois
copyright FEMTO ENGINEERING, 2018
license   GPL v3.0+
brief     Base class for handling SR8x0 device
"""

import time
from collections import OrderedDict


SENSITIVITY = OrderedDict([
    ('2 nV/fA', 0),
    ('5 nV/fA', 1),
    ('10 nV/fA', 2),
    ('20 nV/fA', 3),
    ('50 nV/fA', 4),
    ('100 nV/fA', 5),
    ('200 nV/fA', 6),
    ('500 nV/fA', 7),
    ('1 uV/pA', 8),
    ('2 uV/pA', 9),
    ('5 uV/pA', 10),
    ('10 uV/pA', 11),
    ('20 uV/pA', 12),
    ('50 uV/pA', 13),
    ('100 uV/pA', 14),
    ('200 uV/pA', 15),
    ('500 uV/pA', 16),
    ('1 mV/nA', 17),
    ('2 mV/nA', 18),
    ('5 mV/nA', 19),
    ('10 mV/nA', 20),
    ('20 mV/nA', 21),
    ('50 mV/nA', 22),
    ('100 mV/nA', 23),
    ('200 mV/nA', 24),
    ('500 mV/nA', 25),
    ('1 V/uA', 26)
])

TCONSTANTS = OrderedDict([
    ('10 us', 0),
    ('30 us', 1),
    ('100 us', 2),
    ('300 us', 3),
    ('1 ms', 4),
    ('3 ms', 5),
    ('10 ms', 6),
    ('30 ms', 7),
    ('100 ms', 8),
    ('300 ms', 9),
    ('1 s', 10),
    ('3 s', 11),
    ('10 s', 12),
    ('30 s', 13),
    ('100 s', 14),
    ('300 s', 15),
    ('1 ks', 16),
    ('3 ks', 17),
    ('10 ks', 18),
    ('30 ks', 19)
])

SAMPLE_RATES = OrderedDict([
    ('62.5 mHz', 0),
    ('125 mHz', 1),
    ('250 mHz', 2),
    ('500 mHz', 3),
    ('1 Hz', 4),
    ('2 Hz', 5),
    ('4 Hz', 6),
    ('8 Hz', 7),
    ('16 Hz', 8),
    ('32 Hz', 9),
    ('64 Hz', 10),
    ('128 Hz', 11),
    ('256 Hz', 12),
    ('512 Hz', 13),
    ('trigger', 14)
])

REFERENCE_TRIGGER = OrderedDict([
    ('zero_crossing', 0),
    ('rising_edge', 1),
    ('faling_edge', 2)
])

INPUT_SHIELD = OrderedDict([
    ('float', 0),
    ('ground', 1)
])

INPUT_COUPLING = OrderedDict([
    ('AC', 0),
    ('DC', 1)
])

INPUT_FILTER = OrderedDict([
    ((False, False), 0),
    ((True, False), 1),
    ((False, True), 2),
    ((True, True), 3)
])

RESERVE_MODE = OrderedDict([
    ('high', 0),
    ('normal', 1),
    ('low', 2)
])

FILTER_SLOPE = OrderedDict([
    ('6 dB/oct', 0),
    ('12 dB/oct', 1),
    ('18 dB/oct', 2),
    ('24 dB/oct', 3)
])

FRONT_OUTPUT = OrderedDict([
    ('display', 0),
    ('X', 1)
])

AUTO_OFFSET_ASYNC_CH = OrderedDict([
    ('x', 1),
    ('y', 2),
    ('r', 3)
])

FAST_MODE = OrderedDict([
    ('Off', 0),
    ('On (Dos)', 1),
    ('On (Windows)', 2)
])


# =============================================================================
class Sr8x0(object):
    """Base class for Stanford Research System DSP Lock-In Amplifier
    model SR8(3|1)0.
    """

    def connect(self):
        """Connect to the remote host
        :returns: True if connection succeeded, False otherwise
        """
        raise NotImplementedError("Method not implemented by derived class")

    def close(self):
        """ Closes the underlying socket connection
        """
        raise NotImplementedError("Method not implemented by derived class")

    def write(self, data):
        """Writing process.
        :param data: data writes to device (str)
        :returns: number of bytes sent (int)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def read(self, length):
        """Reading process.
        :param length: length of message to read (int)
        :returns: Message reads from device (str)
        """
        raise NotImplementedError("Method not implemented by derived class")

    def query(self, data, length=100):
        """Basic query i.e. write then read.
        """
        self.write(data)
        return self.read(length).strip('\n')

    @property
    def idn(self):
        """Instrument identification.
        """
        return self.query('*IDN?')

    def reset(self):
        """Reset GPIB interface of Stanford device
        """
        self.write("*RST")

    def status_byte(self, bit=None):
        """Serial poll status byte, a number between 0-255.
        User can request a specific bit value.
        """
        if bit is None:
            return int(self.query('*STB?'))
        else:
            return int(self.query('*STB? {:d}'.format(bit)))

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
        """Getter of the phase shift of the reference.
        """
        return self.query('PHAS?')

    @reference_phase_shift.setter
    def reference_phase_shift(self, value):
        """Setter of the phase shift of the reference.
        """
        self.write('PHAS{:.2f}'.format(value))

    @property
    def reference_internal(self):
        """Getter of the reference source.
        """
        return self.query('FMOD?')

    @reference_internal.setter
    def reference_internal(self, value):
        """Setter of the reference source.
        """
        self.write('FMOD {}'.format(value))

    @property
    def frequency(self):
        """Getter of the reference frequency.
        """
        return self.query('FREQ?')

    @frequency.setter
    def frequency(self, value):
        """Setter of the reference frequency.
        """
        self.write('FREQ {:.5f}'.format(value))

    @property
    def reference_trigger(self):
        """Getter of the reference trigger when using the external
        reference mode.
        """
        return self.query('RSLP?')

    @reference_trigger.setter
    def reference_trigger(self, value):
        """Setter of the reference trigger when using the external
        reference mode.
        """
        self.write('RSLP {:d}'.format(value))

    @property
    def harmonic(self):
        """Getter of the detection harmonic.
        """
        return self.query('HARM?')

    @harmonic.setter
    def harmonic(self, value):
        """Setter of the detection harmonic.
        """
        self.write('HARM {:d}'.format(value))

    @property
    def sine_output_amplitude(self):
        """Getter of the amplitude of the sine output.
        """
        return self.query('SLVL?')

    @sine_output_amplitude.setter
    def sine_output_amplitude(self, value):
        """Setter of the amplitude of the sine output.
        """
        self.write('SLVL{:.3f}'.format(value))

    @property
    def input_configuration(self):
        """Getter of the configuration of the Input.
        """
        return self.query('ISRC?')

    @input_configuration.setter
    def input_configuration(self, value):
        """Setter of the configuration of the Input.
        """
        self.write('ISRC {}'.format(value))

    @property
    def input_shield(self):
        """Getter of the input shield grounding.
        """
        return self.query('IGND?')

    @input_shield.setter
    def input_shield(self, value):
        """Setter of the input shield grounding.
        """
        self.write('IGND {}'.format(value))

    @property
    def input_coupling(self):
        """Getter of the iput coupling.
        """
        return self.query('ICPL?')

    @input_coupling.setter
    def input_coupling(self, value):
        """Setter of the iput coupling.
        """
        self.write('ICPL {}'.format(value))

    @property
    def input_filter(self):
        """Getter of the input line notch filters (1x, 2x).
        """
        return self.query('ILIN?')

    @input_filter.setter
    def input_filter(self, value):
        """Setter of the input line notch filters (1x, 2x).
        """
        self.write('ILIN {}'.format(value))

    # GAIN and TIME CONSTANT COMMANDS.

    @property
    def sensitivity(self):
        """Getter of the sensitivity tuning.
        """
        return self.query('SENS?')

    @sensitivity.setter
    def sensitivity(self, value):
        """Setter of the sensitivity tuning.
        """
        self.write('SENS {}'.format(value))

    @property
    def reserve_mode(self):
        """Getter of the reserve mode tuning.
        """
        return self.query('RMOD?')

    @reserve_mode.setter
    def reserve_mode(self, value):
        """Setter of the reserve mode tuning.
        """
        self.write('RMOD {}'.format(value))

    @property
    def time_constants(self):
        """Get time constant.
        """
        return self.query('OFLT?')

    @time_constants.setter
    def time_constants(self, value):
        """Set time constant.
        """
        self.write('OFLT {}'.format(value))

    @property
    def filter_db_per_oct(self):
        """Get the low pass filter slope.
        """
        return self.query('OFSL?')

    @filter_db_per_oct.setter
    def filter_db_per_oct(self, value):
        """Set the low pass filter slope.
        """
        self.write('OFSL {:d}'.format(value))

    @property
    def sync_filter(self):
        """Get synchronous filter status.
        """
        return self.query('SYNC?')

    @sync_filter.setter
    def sync_filter(self, value):
        """Set synchronous filter status.
        """
        self.write('SYNC {}'.format(value))

    # SETUP COMMANDS

    @property
    def remote(self):
        """Lock Front panel.
        """
        self.write('OVRM?')

    @remote.setter
    def remote(self, value):
        """Lock Front panel.
        """
        self.write('OVRM {:d}'.format(value))

    @property
    def key_click_enabled(self):
        """Get key click status.
        """
        return self.query('KCLK?')

    @key_click_enabled.setter
    def key_click_enabled(self, value):
        """Set key click status.
        """
        self.write('KCLK {}'.format(value))

    @property
    def alarm_enabled(self):
        """Get alarm status.
        """
        return self.query('ALRM?')

    @alarm_enabled.setter
    def alarm_enabled(self, value):
        """Set alarm status.
        """
        self.write('ALRM {}'.format(value))

    def recall_state(self, location):
        """Recalls instrument state in specified non-volatile location.
        :param location: non-volatile storage location.
        """
        self.write('RSET {}'.format(location))

    def save_state(self, location):
        """Saves instrument state in specified non-volatile location.
        Previously stored state in location is overwritten (no error
        is generated).
        :param location: non-volatile storage location.
        """
        self.write('SSET {}'.format(location))

    # AUTO FUNCTIONS

    def auto_gain_async(self):
        """Equivalent to press the Auto Gain key in the front panel.
        Might take some time if the time constant is long.
        Does nothing if the constant is greater than 1 second.
        """
        self.write('AGAN')

    def auto_gain(self):
        """Synced auto gain command.
        """
        self.auto_gain_async()
        self.wait_bit1()

    def auto_reserve_async(self):
        """Equivalent to press the Auto Reserve key in the front panel.
        Might take some time if the time constant is long.
        """
        self.write('ARSV')

    def auto_reserve(self):
        """Synced auto reserve command
        """
        self.auto_reserve_async()
        self.wait_bit1()

    def auto_phase_async(self):
        """Equivalent to press the Auto Phase key in the front panel.
        Might take some time if the time constant is long.
        Does nothing if the phase is unstable.
        """
        self.write('ARSV')

    def auto_phase(self):
        """Synced auto phase command.
        """
        self.auto_phase_async()
        self.wait_bit1()

    def auto_offset_async(self, channel):
        """Automatically offset a given channel to zero.
        Is equivalent to press the Auto Offset Key in the front panel.
        :param channel: the name of the channel.
        :returns: None
        """
        self.write('AOFF {}'.format(channel))

    # DATA STORAGE COMMANDS

    @property
    def sample_rate(self):
        """Queries the data sample rate.
        """
        return self.query('SRAT?')

    @sample_rate.setter
    def sample_rate(self, value):
        """Sets the data sample rate.
        """
        self.write('SRAT {}'.format(value))

    @property
    def single_shot(self):
        """End of buffer mode getter:
        - if True (1 shot mode), at the end of the buffer, data storage stops
        and an audio alarm sounds.
        - if False (Loop mode), data storage continues continues at the end of
        the buffer.
        Note: If loop mode selected, make sure to pause data storage before
        reading the data to avoid confusion about which point is the most
        recent.
        """
        return self.query('SEND?')

    @single_shot.setter
    def single_shot(self, value):
        """End of buffer mode setter.
        """
        self.write('SEND {}'.format(value))

    def trigger(self):
        """Software trigger command. This command has the same effect as
        a trigger at the rear panel trigger input.
        """
        self.write('TRIG')

    @property
    def trigger_start_mode(self):
        """Getter of trigger start mode.
        """
        return self.query('TSTR?')

    @trigger_start_mode.setter
    def trigger_start_mode(self, value):
        """Setter of trigger start mode.
        """
        self.write('TSTR {}'.format(value))

    def start_data_storage(self):
        """Start or resume data storage. Command is ignored if
        storage is already in progress.
        """
        self.write('STRT')

    def pause_data_storage(self):
        """Pause data storage.  If storage is already paused
        or reset then this command is ignored.
        """
        self.write('PAUS')

    def reset_data_storage(self):
        """Reset data buffers. The command can be sent at any time, any storage
        in progress, paused or not, will be reset. The command will erase
        the data buffer.
        """
        self.write('REST')

    # OAUX See above

    def buffer_length(self):
        """Query the number of points stored in the buffer.
        :returns: the number of points stored in the buffer.
        """
        return int(self.query('SPTS?'))

    @property
    def fast_mode(self):
        """Query the data transfer mode value:
        - 0: Off
        - 1: On (DOS programs or other dedicated data collection computers)
        - 2: On (Windows Operating System Programs)
        """
        return self.query('FAST?')

    @fast_mode.setter
    def fast_mode(self, value):
        """Set the data transfer mode on and off.
        """
        self.write('FAST {:d}'.format(value))

    def start_fast_data_storage(self):
        """Start the datat storage after turning on fast data transfert.
        """
        self.write('STRD')

    # DATA TRANSFER COMMANDS

    def analog_value(self, key):
        """The command reads the value of X, Y, R, θ, CH1 or CH2 display.
        Available key = {'x', 'y', 'r', 't', '1', '2'}.
        """
        if key in 'xyrt':
            return self.query('OUTP? {}'.format(key))
        else:
            return self.query('OUTR? {}'.format(key))

    def measure(self, channels):
        """The command records the values of either 2, 3, 4, 5 or 6 parameters
        at a single instant. For example, the command is a way to query values
        of X and Y (or R and θ) which are taken at the same time.
        :param channels: list of data requested
        :returns: list of data values recorded
        """
        channel = {'x': 1, 'y': 2, 'r': 3, 't': 4,
                   '1': 5, '2': 6, '3': 7, '4': 8,
                   'f': 9, '10': 10}
        channels = ','.join(str(channel[ch]) for ch in channels)
        return [float(value) for value in
                (self.query('SNAP? {}'.format(channels))).split(',')]

    def read_buffer(self, start=0, length=None, _format='a'):
        """Queries points stored in the Channel buffer
        :param start: Index of the buffer to start.
        :param length: Number of points to read.
                       Defaults to the number of points in the buffer.
        :param _format: Transfer format
                      'a': ASCII (slow)
                      'b': IEEE Binary (fast) - NOT IMPLEMENTED
                      'c': Non-IEEE Binary (fastest) - NOT IMPLEMENTED
        """
        if _format == 'c':
            cmd = 'TRCL'
        elif _format == 'b':
            cmd = 'TRCB'
        else:
            cmd = 'TRCA'
        if not length:
            length = self.buffer_length
        self.write('{}? {},{}'.format(cmd, start, length))
        if cmd == 'TRCA':
            data = self.read()
            return [float(x) for x in data.split(',')]
        elif cmd == 'TRCB':
            return self.read()
        else:
            return self.read()

    @property
    def display(self, channel):
        """Query the display source.
        :param channel: 1 or 2 i.e. CH1 or CH2 (int)
        """
        return [int(var) for var in
                self.query('DDEF? {}'.format(channel)).split(',')]

    @display.setter
    def display(self, channel, display, ratio):
        """Set the display source.
        :param channel: 1 or 2 i.e. CH1 or CH2 (int)
        :param display: 0, 1, 2, 3, 4 i.e. X, R, Xnoise,
                        AUxIn1 or AuxIn2 (int))
        :param ratio: 0, 1, 2 i.e. none, AuxIn1, AuxIn2 (int)
        """
        self.write('DDEF {},{},{}'.format(channel, display, ratio))

    @property
    def front_output(self, channel):
        """Query the output source.
        :param channel: 1 or 2 i.e. CH1 or CH2 (int)
        """
        return self.query('FPOP? {}'.format(channel))

    @front_output.setter
    def front_output(self, channel, output):
        """Set the output source.
        :param channel: 1 or 2 i.e. CH1 or CH2 (int)
        :param output: X, Y (output=1) or Display (output=0) (int)
        """
        self.write('FPOP {},{}'.format(channel, output))
