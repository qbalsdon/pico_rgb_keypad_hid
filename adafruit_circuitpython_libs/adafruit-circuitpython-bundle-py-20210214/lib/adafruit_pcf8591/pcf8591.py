# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`pcf8591`
================================================================================

ADC+DAC Combo

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* `Adafruit PCF8591 Breakout <https://www.adafruit.com/products/45XX>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

 * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
 * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

__version__ = "1.0.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PCF8591.git"
# from time import sleep
from struct import unpack_from
from micropython import const
import adafruit_bus_device.i2c_device as i2c_device

_PCF8591_DEFAULT_ADDR = const(0x48)  # PCF8591 Default Address
_PCF8591_ENABLE_DAC = const(0x40)  # control bit for having the DAC active

# Pin constants
A0 = const(0)
A1 = const(1)
A2 = const(2)
A3 = const(3)

OUT = const(0)


class PCF8591:
    """Driver for the PCF8591 DAC & ADC Combo breakout.

    :param ~busio.I2C i2c_bus: The I2C bus the PCF8591 is connected to.
    :param address: The I2C device address for the sensor. Default is ``0x28``.

    """

    def __init__(self, i2c_bus, address=_PCF8591_DEFAULT_ADDR, reference_voltage=3.3):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._dacval = 0
        self._dac_enabled = False
        # this is the range supported by the PCF8591
        if 2.5 <= reference_voltage <= 6.0:
            self._reference_voltage = reference_voltage
        else:
            raise ValueError("reference_voltage must be from 2.5 - 6.0")
        self._buffer = bytearray(2)
        # possibly measure each channel here to prep readings for
        # user calls to `read`

    @property
    def reference_voltage(self):
        """The voltage level that ADC signals are compared to.
        An ADC value of 65535 will equal `reference_voltage`"""
        return self._reference_voltage

    def _half_read(self, channel):
        if self._dac_enabled:
            self._buffer[0] = _PCF8591_ENABLE_DAC
            self._buffer[1] = self._dacval
        else:
            self._buffer[0] = 0
            self._buffer[1] = 0

        self._buffer[0] |= channel & 0x3

        with self.i2c_device as i2c:
            i2c.write_then_readinto(self._buffer, self._buffer)

    def read(self, channel):
        """Read an analog value from one of the four ADC inputs

          param: :channel The single-ended ADC channel to read from, 0 thru 3
        """
        if channel < 0 or channel > 3:
            raise ValueError("channel must be from 0-3")
        # reads are started on the ACK of the WRITE to the 'register' and
        # not returned until the read after the _next_ WRITE so we have to
        # do it twice to get the actual value
        self._half_read(channel)
        self._half_read(channel)

        return unpack_from(">B", self._buffer[1:])[0]

    @property
    def dac_enabled(self):
        """ Enables the DAC when True, or sets it to tri-state / high-Z when False"""
        return self._dac_enabled

    @dac_enabled.setter
    def dac_enabled(self, enable_dac):

        self._dac_enabled = enable_dac
        self.write(self._dacval)

    def write(self, value):
        """Writes a uint8_t value to the DAC output

      param: :output The value to write: 0 is GND and 65535 is VCC

      """

        self._buffer = bytearray(2)
        if self._dac_enabled:
            self._buffer[0] = _PCF8591_ENABLE_DAC
            self._buffer[1] = value
        self._dacval = value
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self._buffer, self._buffer)
