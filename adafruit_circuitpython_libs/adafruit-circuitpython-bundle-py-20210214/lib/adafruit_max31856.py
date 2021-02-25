# SPDX-FileCopyrightText: 2018 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`MAX31856`
====================================================

CircuitPython module for the MAX31856 Universal Thermocouple Amplifier. See
examples/simpletest.py for an example of the usage.

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Universal Thermocouple Amplifier MAX31856 Breakout
  <https://www.adafruit.com/product/3263>`_ (Product ID: 3263)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

from time import sleep
from micropython import const
from adafruit_bus_device.spi_device import SPIDevice

try:
    from struct import unpack
except ImportError:
    from ustruct import unpack

__version__ = "0.9.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MAX31856.git"

# Register constants
_MAX31856_CR0_REG = const(0x00)
_MAX31856_CR0_AUTOCONVERT = const(0x80)
_MAX31856_CR0_1SHOT = const(0x40)
_MAX31856_CR0_OCFAULT1 = const(0x20)
_MAX31856_CR0_OCFAULT0 = const(0x10)
_MAX31856_CR0_CJ = const(0x08)
_MAX31856_CR0_FAULT = const(0x04)
_MAX31856_CR0_FAULTCLR = const(0x02)

_MAX31856_CR1_REG = const(0x01)
_MAX31856_MASK_REG = const(0x02)
_MAX31856_CJHF_REG = const(0x03)
_MAX31856_CJLF_REG = const(0x04)
_MAX31856_LTHFTH_REG = const(0x05)
_MAX31856_LTHFTL_REG = const(0x06)
_MAX31856_LTLFTH_REG = const(0x07)
_MAX31856_LTLFTL_REG = const(0x08)
_MAX31856_CJTO_REG = const(0x09)
_MAX31856_CJTH_REG = const(0x0A)
_MAX31856_CJTL_REG = const(0x0B)
_MAX31856_LTCBH_REG = const(0x0C)
_MAX31856_LTCBM_REG = const(0x0D)
_MAX31856_LTCBL_REG = const(0x0E)
_MAX31856_SR_REG = const(0x0F)

# fault types
_MAX31856_FAULT_CJRANGE = const(0x80)
_MAX31856_FAULT_TCRANGE = const(0x40)
_MAX31856_FAULT_CJHIGH = const(0x20)
_MAX31856_FAULT_CJLOW = const(0x10)
_MAX31856_FAULT_TCHIGH = const(0x08)
_MAX31856_FAULT_TCLOW = const(0x04)
_MAX31856_FAULT_OVUV = const(0x02)
_MAX31856_FAULT_OPEN = const(0x01)


class ThermocoupleType:  # pylint: disable=too-few-public-methods
    """An enum-like class representing the different types of thermocouples that the MAX31856 can
    use. The values can be referenced like ``ThermocoupleType.K`` or ``ThermocoupleType.S``
    Possible values are

    - ``ThermocoupleType.B``
    - ``ThermocoupleType.E``
    - ``ThermocoupleType.J``
    - ``ThermocoupleType.K``
    - ``ThermocoupleType.N``
    - ``ThermocoupleType.R``
    - ``ThermocoupleType.S``
    - ``ThermocoupleType.T``

    """

    # pylint: disable=invalid-name
    B = 0b0000
    E = 0b0001
    J = 0b0010
    K = 0b0011
    N = 0b0100
    R = 0b0101
    S = 0b0110
    T = 0b0111
    G8 = 0b1000
    G32 = 0b1100


class MAX31856:
    """Driver for the MAX31856 Universal Thermocouple Amplifier

      :param ~busio.SPI spi_bus: The SPI bus the MAX31856 is connected to.
      :param ~microcontroller.Pin cs: The pin used for the CS signal.
      :param ~adafruit_max31856.ThermocoupleType thermocouple_type: The type of thermocouple.\
      Default is Type K.

    """

    # A class level buffer to reduce allocations for reading and writing.
    # Tony says this isn't re-entrant or thread safe!
    _BUFFER = bytearray(4)

    def __init__(self, spi, cs, thermocouple_type=ThermocoupleType.K):
        self._device = SPIDevice(spi, cs, baudrate=500000, polarity=0, phase=1)

        # assert on any fault
        self._write_u8(_MAX31856_MASK_REG, 0x0)
        # configure open circuit faults
        self._write_u8(_MAX31856_CR0_REG, _MAX31856_CR0_OCFAULT0)

        # set thermocouple type
        # get current value of CR1 Reg
        conf_reg_1 = self._read_register(_MAX31856_CR1_REG, 1)[0]
        conf_reg_1 &= 0xF0  # mask off bottom 4 bits
        # add the new value for the TC type
        conf_reg_1 |= int(thermocouple_type) & 0x0F
        self._write_u8(_MAX31856_CR1_REG, conf_reg_1)

    @property
    def temperature(self):
        """The temperature of the sensor and return its value in degrees celsius. (read-only)"""
        self._perform_one_shot_measurement()

        # unpack the 3-byte temperature as 4 bytes
        raw_temp = unpack(
            ">i", self._read_register(_MAX31856_LTCBH_REG, 3) + bytes([0])
        )[0]

        # shift to remove extra byte from unpack needing 4 bytes
        raw_temp >>= 8

        # effectively shift raw_read >> 12 to convert pseudo-float
        temp_float = raw_temp / 4096.0

        return temp_float

    @property
    def reference_temperature(self):
        """The temperature of the cold junction in degrees celsius. (read-only)"""
        self._perform_one_shot_measurement()

        raw_read = unpack(">h", self._read_register(_MAX31856_CJTH_REG, 2))[0]

        # effectively shift raw_read >> 8 to convert pseudo-float
        cold_junction_temp = raw_read / 256.0

        return cold_junction_temp

    @property
    def temperature_thresholds(self):
        """The thermocouple's low and high temperature thresholds
        as a ``(low_temp, high_temp)`` tuple
        """

        raw_low = unpack(">h", self._read_register(_MAX31856_LTLFTH_REG, 2))
        raw_high = unpack(">h", self._read_register(_MAX31856_LTHFTH_REG, 2))

        return (round(raw_low[0] / 16.0, 1), round(raw_high[0] / 16.0, 1))

    @temperature_thresholds.setter
    def temperature_thresholds(self, val):

        int_low = int(val[0] * 16)
        int_high = int(val[1] * 16)

        self._write_u8(_MAX31856_LTHFTH_REG, int_high >> 8)
        self._write_u8(_MAX31856_LTHFTL_REG, int_high)

        self._write_u8(_MAX31856_LTLFTH_REG, int_low >> 8)
        self._write_u8(_MAX31856_LTLFTL_REG, int_low)

    @property
    def reference_temperature_thresholds(self):  # pylint: disable=invalid-name
        """The cold junction's low and high temperature thresholds
        as a ``(low_temp, high_temp)`` tuple
        """
        return (
            float(unpack("b", self._read_register(_MAX31856_CJLF_REG, 1))[0]),
            float(unpack("b", self._read_register(_MAX31856_CJHF_REG, 1))[0]),
        )

    @reference_temperature_thresholds.setter
    def reference_temperature_thresholds(self, val):  # pylint: disable=invalid-name

        self._write_u8(_MAX31856_CJLF_REG, int(val[0]))
        self._write_u8(_MAX31856_CJHF_REG, int(val[1]))

    @property
    def fault(self):
        """A dictionary with the status of each fault type where the key is the fault type and the
        value is a bool if the fault is currently active

        ===================   =================================
        Key                   Fault type
        ===================   =================================
        "cj_range"            Cold junction range fault
        "tc_range"            Thermocouple range fault
        "cj_high"             Cold junction high threshold fault
        "cj_low"              Cold junction low threshold fault
        "tc_high"             Thermocouple high threshold fault
        "tc_low"              Thermocouple low threshold fault
        "voltage"             Over/under voltage fault
        "open_tc"             Thermocouple open circuit fault
        ===================   =================================

        """
        faults = self._read_register(_MAX31856_SR_REG, 1)[0]

        return {
            "cj_range": bool(faults & _MAX31856_FAULT_CJRANGE),
            "tc_range": bool(faults & _MAX31856_FAULT_TCRANGE),
            "cj_high": bool(faults & _MAX31856_FAULT_CJHIGH),
            "cj_low": bool(faults & _MAX31856_FAULT_CJLOW),
            "tc_high": bool(faults & _MAX31856_FAULT_TCHIGH),
            "tc_low": bool(faults & _MAX31856_FAULT_TCLOW),
            "voltage": bool(faults & _MAX31856_FAULT_OVUV),
            "open_tc": bool(faults & _MAX31856_FAULT_OPEN),
        }

    def _perform_one_shot_measurement(self):

        self._write_u8(_MAX31856_CJTO_REG, 0x0)
        # read the current value of the first config register
        conf_reg_0 = self._read_register(_MAX31856_CR0_REG, 1)[0]

        # and the complement to guarantee the autoconvert bit is unset
        conf_reg_0 &= ~_MAX31856_CR0_AUTOCONVERT
        # or the oneshot bit to ensure it is set
        conf_reg_0 |= _MAX31856_CR0_1SHOT

        # write it back with the new values, prompting the sensor to perform a measurement
        self._write_u8(_MAX31856_CR0_REG, conf_reg_0)

        sleep(0.250)

    def _read_register(self, address, length):
        # pylint: disable=no-member
        # Read a 16-bit BE unsigned value from the specified 8-bit address.
        with self._device as device:
            self._BUFFER[0] = address & 0x7F
            device.write(self._BUFFER, end=1)
            device.readinto(self._BUFFER, end=length)
        return self._BUFFER[:length]

    def _write_u8(self, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        with self._device as device:
            self._BUFFER[0] = (address | 0x80) & 0xFF
            self._BUFFER[1] = val & 0xFF
            device.write(self._BUFFER, end=2)  # pylint: disable=no-member
