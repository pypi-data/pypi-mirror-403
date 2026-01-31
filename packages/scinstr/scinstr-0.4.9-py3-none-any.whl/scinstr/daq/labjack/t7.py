# -*- coding: utf-8 -*-

"""package scinstr.daq.labjack
author    Benoit Dubois
copyright FEMTO Engineering, 2020
licence   GPL 3.0+
brief     Handle Labjack T7(-Pro) device (DAQ board).
"""

import logging
from collections import namedtuple
import scinstr.daq.labjack.convert_data as cd


AIN_ADDR = [0 + addr for addr in range(0, 27, 2)]
AIN_BINARY_ADDR = [50000 + addr*2 for addr in range(0, 14)]
#
CURRENT_SOURCE_10UA_CAL_VALUE_ADDR = 1900
CURRENT_SOURCE_200UA_CAL_VALUE_ADDR = 1902
#
FIO_ADDR = [2000 + addr for addr in range(0, 8)]
EIO_ADDR = [2008 + addr for addr in range(0, 8)]
CIO_ADDR = [2016 + addr for addr in range(0, 8)]
MIO_ADDR = [2020 + addr for addr in range(0, 8)]
FIO_DIRECTION_ADDR = 2600  # 0=Input and 1=Output
EIO_DIRECTION_ADDR = 2601  # 0=Input and 1=Output
CIO_DIRECTION_ADDR = 2602  # 0=Input and 1=Output
MIO_DIRECTION_ADDR = 2603  # 0=Input and 1=Output
FIO_STATE_ADDR = 2500
EIO_STATE_ADDR = 2501
CIO_STATE_ADDR = 2502
MIO_STATE_ADDR = 2503
#
DIO_STATE_ADDR = 2800
DIO_DIRECTION_ADDR = 2850  # 0=Input and 1=Output
DIO_INHIBIT_ADDR = 2900  # 0=Affected (Default),1=Ignored
#
DIO_EF_READ_A_ADDR = [3000 + addr*2 for addr in range(0, 23)]
DIO_EF_READ_A_AND_RESET_ADDR = [3100 + addr*2 for addr in range(0, 23)]
DIO_EF_READ_A_F_ADDR = [3500 + addr*2 for addr in range(0, 23)]
DIO_EF_READ_A_F_AND_RESET_ADDR = [3600 + addr*2 for addr in range(0, 23)]
DIO_EF_ENABLE_ADDR = [44000 + addr*2 for addr in range(0, 23)]
DIO_EF_INDEX_ADDR = [44100 + addr*2 for addr in range(0, 23)]
DIO_EF_OPTIONS_ADDR = [44200 + addr*2 for addr in range(0, 23)]
#
DIO_EF_CLOCK_ENABLE_ADDR = [44900 + addr*10 for addr in range(0, 8)]
DIO_EF_CLOCK_DIVISOR_ADDR = [44901 + addr*10 for addr in range(0, 8)]
DIO_EF_CLOCK_OPTIONS_ADDR = [44902 + addr*10 for addr in range(0, 8)]
DIO_EF_CLOCK_ROLL_VALUE_ADDR = [44904 + addr*10 for addr in range(0, 8)]
DIO_EF_CLOCK_COUNT_ADDR = [44908 + addr*10 for addr in range(0, 8)]
#
STREAM_SCANRATE_HZ = 4002
STREAM_NUM_ADDRESSES = 4004
STREAM_SAMPLES_PER_PACKET = 4006
STREAM_SETTLING_US = 4008
STREAM_RESOLUTION_INDEX = 4010
STREAM_BUFFER_SIZE_BYTES = 4012
# STREAM_CLOCK_SOURCE = 4014
# STREAM_OPTIONS = 4014
STREAM_AUTO_TARGET = 4016
STREAM_DATATYPE = 4018
STREAM_NUM_SCANS = 4020
STREAM_ENABLE = 4990
STREAM_SCANLIST_ADDRESS = [4100 + addr for addr in range(0, 128, 2)]
#
AIN_RANGE_ADDR = [40000 + addr for addr in range(0, 27, 2)]
AIN_NEGATIVE_CH_ADDR = [41000 + addr for addr in range(0, 14)]
AIN_RESOLUTION_INDEX_ADDR = [41500 + addr for addr in range(0, 14)]
AIN_SETTLING_US_ADDR = [42000 + addr for addr in range(0, 27, 2)]
#
POWER_ETHERNET_ADDR = 48003
POWER_WIFI_ADDR = 48004
POWER_LED_ADDR = 48006
POWER_ETHERNET_DEFAULT_ADDR = 48053
POWER_WIFI_DEFAULT_ADDR = 48054
#
LED_COMM_ADDR =	2990
LED_STATUS_ADDR = 2991
#
IO_CONFIG_SET_DEFAULT_TO_CURRENT = 49002
#
TEST = 55100
TEST_RESULT = 1122867
TEST_UINT16 = 55110
TEST_UINT16_RESULT = 17
TEST_UINT32 = 55120
TEST_UINT32_RESULT = 1122867
TEST_INT32 = 55122
TEST_INT32_RESULT = -2003195205
TEST_FLOAT32 = 55124
TEST_FLOAT32_RESULT = -9999.0
#
PRODUCT_ID = 60000
#
WATCHDOG_ENABLE_DEFAULT = 61600
WATCHDOG_TIMEOUT_S_DEFAULT = 61604
WATCHDOG_RESET_ENABLE_DEFAULT = 61620
#
SYSTEM_REBOOT = 61998

# Define a new type used for storing device configurations
DTuple = namedtuple('DTuple', ['mnemo', 'caption', 'list'])


# T7(-Pro) device capabilities namespace
# =============================================================================
RESO_T7PRO = [DTuple("0", "Default 9 (19.6 bits, gain=1)", None),
              DTuple("1", "1 (16 bits, gain=1)", None),
              DTuple("2", "2", None),
              DTuple("3", "3", None),
              DTuple("4", "4", None),
              DTuple("5", "5", None),
              DTuple("6", "6", None),
              DTuple("7", "7", None),
              DTuple("8", "8", None),
              DTuple("9", "9 (19.6 bits, gain=1)", None),
              DTuple("10", "10", None),
              DTuple("11", "11", None),
              DTuple("12", "12 (21.8 bits, gain=1)", None)]

RESO_T7 = [DTuple("0", "Default 8 (19.1 bits, gain=1)", None),
           DTuple("1", "1 (16 bits, gain=1)", None),
           DTuple("2", "2", None),
           DTuple("3", "3", None),
           DTuple("4", "4", None),
           DTuple("5", "5", None),
           DTuple("6", "6", None),
           DTuple("7", "7", None),
           DTuple("8", "8 (19.1 bits, gain=1)", None)]

VOLT_RANGE = [DTuple("0.01", "10 mV", None),
              DTuple("0.1", "100 mV", None),
              DTuple("1", "1 V", None),
              DTuple("10", "10 V", None)]

SETTLING = [DTuple("0", "auto", None),
            DTuple("100", "100 us", None),
            DTuple("1000", "1 ms", None),
            DTuple("2000", "2 ms", None),
            DTuple("10000", "10 ms", None),
            DTuple("20000", "20 ms", None),
            DTuple("100000", "100 ms", None),
            DTuple("200000", "200 ms", None)]

CUR_SRC = [DTuple("0", "Disabled", None),
           DTuple("1", "10 uA", None),
           DTuple("2", "200 uA", None)]

FUNCTION = [DTuple("Voltage", "DC Voltage", VOLT_RANGE)]
# , DTuple("Pt100", "2-wire Pt100", None)] ##CUR_SRC[0])]


# =============================================================================
class T7():
    """Base class to handle T7(-Pro) board.
    """

    def __init__(self):
        """Constructor.
        :returns: None
        """
        self._client = None

    def connect(self):
        """ Connect to the remote host
        :returns: True if connection succeeded, False otherwise
        """
        raise NotImplementedError("Method not implemented by derived class")

    def close(self):
        """ Closes the underlying socket connection
        """
        raise NotImplementedError("Method not implemented by derived class")

    def reboot(self):
        """Reboot device.
        :returns: None
        """
        # Reboot after 50 ms
        self._client.write_registers(SYSTEM_REBOOT,
                                     cd.uint32_to_data(0x4C4A0001))

    def check_test_reg(self):
        """Use test registers to test device.
        :returns: True if test pass else False (bool)
        """
        rr = self._client.read_input_registers(TEST, 2)
        test = cd.data_to_uint32(rr.registers)
        if test != TEST_RESULT:
            return False
        return True

    def set_current_config_as_default(self):
        """Set current device configuration as new default (ie after
        reboot/power-up) values.
        :returns: None
        """
        self._client.write_registers(IO_CONFIG_SET_DEFAULT_TO_CURRENT,
                                     cd.uint32_to_data(1))

    def set_watchdog(self, timeout=60):
        """Configure watchdog to reset the device if it does not receive any
        communication for 'timeout' seconds. Usualy, the method is used in
        conjonction with 'set_current_config_as_default()' method.
        :param timeout: watchdog timer value (int)
        :returns: None
        """
        assert timeout > 1, \
            "Watchdog timeout value (%r s) too small." % timeout
        self._client.write_registers(WATCHDOG_ENABLE_DEFAULT,
                                     cd.uint32_to_data(0))
        self._client.write_registers(WATCHDOG_TIMEOUT_S_DEFAULT,
                                     cd.uint32_to_data(timeout))
        self._client.write_registers(WATCHDOG_RESET_ENABLE_DEFAULT,
                                     cd.uint32_to_data(1))
        self._client.write_registers(WATCHDOG_ENABLE_DEFAULT,
                                     cd.uint32_to_data(1))

    def read_float32_register(self, register):
        """Read a register of float 32 bits type.
        :returns: the register value (float)
        """
        rr = self._client.read_input_registers(register, 2)
        return cd.data_to_float32(rr.registers)

    def write_float32_register(self, register, value):
        """Write a register of float 32 bits type.
        :param register: address to write (int)
        :param value: value to write (float)
        :returns: None
        """
        self._client.write_registers(register,
                                     cd.float32_to_data(value))

    def read_uint16_register(self, register):
        """Read a register of unsigned integer 16 bits type.
        :returns: the register value (int)
        """
        rr = self._client.read_input_registers(register, 2)
        return cd.data_to_uint16(rr.registers)

    def write_uint16_register(self, register, value):
        """Write a register of unsigned integer 16 bits type.
        :param register: address to write (int)
        :param value: value to write (int)
        :returns: None
        """
        self._client.write_registers(register,
                                     cd.uint16_to_data(value))

    def read_uint32_register(self, register):
        """Read a register of unsigned integer 32 bits type.
        :returns: the register value (int)
        """
        rr = self._client.read_input_registers(register, 2)
        return cd.data_to_uint32(rr.registers)

    def write_uint32_register(self, register, value):
        """Write a register of unsigned integer 32 bits type.
        :param register: address to write (int)
        :param value: value to write (int)
        :returns: None
        """
        self._client.write_registers(register,
                                     cd.uint32_to_data(value))

    def read_int32_register(self, register):
        """Read a register of integer 32 bits type.
        :returns: the register value (int)
        """
        rr = self._client.read_input_registers(register, 2)
        return cd.data_to_int32(rr.registers)

    def write_int32_register(self, register, value):
        """Write a register of integer 32 bits type.
        :param register: address to write (int)
        :param value: value to write (int)
        :returns: None
        """
        self._client.write_registers(register,
                                     cd.int32_to_data(value))

    def get_id(self):
        """Return product id of device.
        :returns: product id of device (str)
        """
        rr = self._client.read_input_registers(PRODUCT_ID, 2)
        return cd.data_to_float32(rr.registers)

    def get_current_source_10ua_value(self, r_calibrate=None, v_ain=None):
        """Return the intensity value of the 10 uA current source.
        If a calibrate resistor is used, return the actual value computed from
        I/V value, else return the factory calibration value.
        :returns: 10 uA current source value (float)
        """
        if r_calibrate is None or v_ain is None:
            rr = self._client.read_input_registers(
                CURRENT_SOURCE_10UA_CAL_VALUE_ADDR, 2)
            current = cd.data_to_float32(rr.registers)
        else:
            current = v_ain / r_calibrate
        return current

    def get_current_source_200ua_value(self, r_calibrate=None, v_ain=None):
        """Return the intensity value of the 200 uA current source.
        If a calibrate resistor is used, return the actual value computed from
        I/V value, else return the factory calibration value.
        :returns: 200 uA current source value (float)
        """
        if r_calibrate is None or v_ain is None:
            rr = self._client.read_input_registers(
                CURRENT_SOURCE_200UA_CAL_VALUE_ADDR, 2)
            current = cd.data_to_float32(rr.registers)
        else:
            current = v_ain / r_calibrate
        return current

    def get_ains_voltage(self, ains):
        """Read analog input values.
        :param ains: list of analog inputs (list of int)
        :returns: list of analog input value(s) (list of float)
        """
        vains = []
        for ain in ains:
            assert 0 <= ain <= 13, "channel index out of range: %r" % ain
            rr = self._client.read_input_registers(AIN_ADDR[ain], 2)
            vains.append(cd.data_to_float32(rr.registers))
        return vains

    def set_ains_range(self, ains, ranges):
        """Set analog input range.
        :param ains: list of analog inputs (list of int)
        :param ranges: list of analog input range (list of float)
        :returns: None
        """
        assert len(ains) == len(ranges), \
            "parameters must have the same size"
        for ain, _range in zip(ains, ranges):
            self._client.write_registers(AIN_RANGE_ADDR[ain],
                                         cd.float32_to_data(_range))

    def set_ains_negative_ch(self, ains, negative_chs):
        """Set negative channel to be used for each positive channel.
        :param ains: list of analog positive channel (list of int)
        :param negative_chs: list of analog negative channel (list of int)
        :returns: None
        """
        assert len(ains) == len(negative_chs), \
            "parameters must have the same size"
        for ain, negative_ch in zip(ains, negative_chs):
            assert ain % 2 == 0, \
              "Even negative_ch registers must not be writed: %r" % ain
            self._client.write_register(AIN_NEGATIVE_CH_ADDR[ain],
                                        cd.uint16_to_data(negative_ch))

    def set_ains_resolution(self, ains, resolutions):
        """Set analog input resolution.
        :param ains: list of analog inputs (list of int)
        :param resolutions: list of analog input resolution (list of int)
        :returns: None
        """
        assert len(ains) == len(resolutions), \
            "parameters must have the same size"
        for ain, resolution in zip(ains, resolutions):
            assert 0 <= ain <= 13, "Analog input out of range: %r" % ain
            assert 0 <= resolution <= 12, \
                "Resolution out of range: %r" % resolution
            self._client.write_register(cd.uint16_to_data(resolution),
                                        AIN_RESOLUTION_INDEX_ADDR[ain])

    def set_ains_settling(self, ains, settlings):
        """Set analog input settling time.
        :param ains: list of analog inputs (list of int)
        :param settlings: list of analog input settling time (list of float)
        :returns: None
        """
        assert len(ains) == len(settlings), \
            "parameters must have the same size"
        for ain, settling in zip(ains, settlings):
            assert 0 <= ain <= 13, "Analog input out of range: %r" % ain
            assert 0 <= settling <= 3.402823 * 10**38, \
                "Settling out of range: %r" % settling
            self._client.write_registers(AIN_SETTLING_US_ADDR[ain],
                                         cd.float32_to_data(settling))

    def enable_high_speed_counter(self, num):
        """Enable high speed counter.
        :param num: number of counter (0 to 3) to enable (int)
        :returns: None
        """
        assert 0 <= num <= 3, "Counter index out of range: %r" % num
        if num == 0:
            self.write_uint16_register(DIO_EF_CLOCK_ENABLE_ADDR[0], 0)
            self.write_uint16_register(DIO_EF_CLOCK_ENABLE_ADDR[2], 0)
        if num == 1:
            self.write_uint16_register(DIO_EF_CLOCK_ENABLE_ADDR[0], 0)
            self.write_uint16_register(DIO_EF_CLOCK_ENABLE_ADDR[1], 0)
        if num == 3:
            # Disable stream mode (not implemented yet)
            logging.error("Configuration of High Speed counter 3 need to "
                          "disable stream mode before (not implemented).")
        self.write_uint32_register(DIO_EF_ENABLE_ADDR[num+16], 0)
        self.write_uint32_register(DIO_EF_INDEX_ADDR[num+16], 7)
        self.write_uint32_register(DIO_EF_ENABLE_ADDR[num+16], 1)

    def get_high_speed_counter_frequency(self, num):
        """Get frequency measured by high speed counter.
        :param num: number of counter (0 to 3) to enable (int)
        :returns: frequency measured by high speed counter (float)
        """
        assert 0 <= num <= 3, "Counter index out of range: %r" % num
        return self.read_uint32_register(DIO_EF_READ_A_AND_RESET_ADDR[num+16])

    def enable_fios(self, num, direction):
        """Enable FIO digital I/O and set direction.
        :param num: list of I/O to enable (list of int)
        :param direction: list of I/O direction (list of int)
        :returns: None
        """
        msg = 0
        for idx, n in enumerate(num):
            assert 0 <= n <= 7, "FIO index out of range: %r" % num
            msg += direction[idx] * 2**n
        self.write_uint16_register(FIO_DIRECTION_ADDR, msg)

    def set_fios_state(self, num, state):
        """Set state of FIO digital output.
        :param num: list of I/O to set state (list of int)
        :param state: list of state (list of int)
        :returns: None
        """
        msg = 0
        for idx, n in enumerate(num):
            assert 0 <= n <= 7, "FIO index out of range: %r" % num
            msg += state[idx] * 2**n
        self.write_uint16_register(FIO_STATE_ADDR, msg)

    def get_fios_state(self, num):
        """Get state of FIO digital output.
        :param num: list of I/O to get state (list of int)
        :returns: list of state (list of int)
        """
        fios_state = self.read_uint16_register(FIO_STATE_ADDR)
        state_list = []
        for idx, n in enumerate(num):
            assert 0 <= n <= 7, "FIO index out of range: %r" % num
            state_list.append((x >> n) & 1)
        return state_list
