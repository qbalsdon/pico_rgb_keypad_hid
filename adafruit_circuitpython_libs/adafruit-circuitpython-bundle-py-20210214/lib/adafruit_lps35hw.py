# SPDX-FileCopyrightText: Copyright (c) 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
# The MIT License (MIT)
#
# Copyright (c) 2019 Bryan Siepert for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_lps35hw`
================================================================================

A driver for the ST LPS35HW water resistant MEMS pressure sensor


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* `LPS35HW Breakout <https://www.adafruit.com/products/4258>`_

**Software and Dependencies:**
 * Adafruit CircuitPython firmware for the supported boards:
    https://github.com/adafruit/circuitpython/releases
 * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
 * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register

"""

# imports

__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LPS35HW.git"

from micropython import const
import adafruit_bus_device.i2c_device as i2cdevice
from adafruit_register.i2c_struct import UnaryStruct
from adafruit_register.i2c_bits import RWBits, ROBits
from adafruit_register.i2c_bit import RWBit

_INTERRUPT_CFG = const(0x0B)
_THS_P_L = const(0x0C)
_THS_P_H = const(0x0D)
_WHO_AM_I = const(0x0F)
_CTRL_REG1 = const(0x10)
_CTRL_REG2 = const(0x11)
_CTRL_REG3 = const(0x12)
_FIFO_CTRL = const(0x14)
_REF_P_XL = const(0x15)
_REF_P_L = const(0x16)
_REF_P_H = const(0x17)
_RPDS_L = const(0x18)
_RPDS_H = const(0x19)
_RES_CONF = const(0x1A)
_INT_SOURCE = const(0x25)
_FIFO_STATUS = const(0x26)
_STATUS = const(0x27)
_PRESS_OUT_XL = const(0x28)
_PRESS_OUT_L = const(0x29)
_PRESS_OUT_H = const(0x2A)
_TEMP_OUT_L = const(0x2B)
_TEMP_OUT_H = const(0x2C)
_LPFP_RES = const(0x33)


class DataRate:  # pylint: disable=too-few-public-methods
    """Options for ``data_rate``

    +---------------------------+-------------------------+
    | ``DataRate``              | Time                    |
    +===========================+=========================+
    | ``DataRate.ONE_SHOT``     | One shot mode           |
    +---------------------------+-------------------------+
    | ``DataRate.RATE_1_HZ``    | 1 hz                    |
    +---------------------------+-------------------------+
    | ``DataRate.RATE_10_HZ``   | 10 hz  (Default)        |
    +---------------------------+-------------------------+
    | ``DataRate.RATE_25_HZ``   | 25 hz                   |
    +---------------------------+-------------------------+
    | ``DataRate.RATE_50_HZ``   | 50 hz                   |
    +---------------------------+-------------------------+
    | ``DataRate.RATE_75_HZ``   | 75 hz                   |
    +---------------------------+-------------------------+

    """

    ONE_SHOT = const(0x00)
    RATE_1_HZ = const(0x01)
    RATE_10_HZ = const(0x02)
    RATE_25_HZ = const(0x03)
    RATE_50_HZ = const(0x04)
    RATE_75_HZ = const(0x05)


class LPS35HW:  # pylint: disable=too-many-instance-attributes
    """Driver for the ST LPS35HW MEMS pressure sensor

    :param ~busio.I2C i2c_bus: The I2C bus the LPS34HW is connected to.
    :param address: The I2C device address for the sensor. Default is ``0x5d`` but will accept
        ``0x5c`` when the ``SDO`` pin is connected to Ground.

    """

    data_rate = RWBits(3, _CTRL_REG1, 4)
    """The rate at which the sensor measures ``pressure`` and ``temperature``. ``data_rate`` should
    be set to one of the values of ``adafruit_lps35hw.DataRate``. Note that setting ``data_rate``
    to ``DataRate.ONE_SHOT`` places the sensor into a low-power shutdown mode where measurements to
    update ``pressure`` and ``temperature`` are only taken when ``take_measurement`` is called."""

    low_pass_enabled = RWBit(_CTRL_REG1, 3)
    """True if the low pass filter is enabled. Setting to `True` will reduce the sensor bandwidth
    from ``data_rate/2`` to ``data_rate/9``, filtering out high-frequency noise."""

    _raw_temperature = UnaryStruct(_TEMP_OUT_L, "<h")
    _raw_pressure = ROBits(24, _PRESS_OUT_XL, 0, 3)

    _block_updates = RWBit(_CTRL_REG1, 1)
    _reset = RWBit(_CTRL_REG2, 2)
    _one_shot = RWBit(_CTRL_REG2, 0)

    # INT status registers
    _pressure_low = RWBit(_INT_SOURCE, 1)
    _pressure_high = RWBit(_INT_SOURCE, 0)

    _auto_zero = RWBit(_INTERRUPT_CFG, 5)
    _reset_zero = RWBit(_INTERRUPT_CFG, 4)

    _interrupts_enabled = RWBit(_INTERRUPT_CFG, 3)
    _interrupt_latch = RWBit(_INTERRUPT_CFG, 2)
    _interrupt_low = RWBit(_INTERRUPT_CFG, 1)
    _interrupt_high = RWBit(_INTERRUPT_CFG, 0)

    _reset_filter = ROBits(8, _LPFP_RES, 0, 1)

    _chip_id = UnaryStruct(_WHO_AM_I, "<B")
    _pressure_threshold = UnaryStruct(_THS_P_L, "<H")

    def __init__(self, i2c_bus, address=0x5D):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)
        if self._chip_id != 0xB1:
            raise RuntimeError("Failed to find LPS35HW! Chip ID 0x%x" % self._chip_id)

        self.reset()

        # set data_rate to put the sensor in continuous mode
        self.data_rate = DataRate.RATE_10_HZ

        self._block_updates = True
        self._interrupt_latch = True

    @property
    def pressure(self):
        """The current pressure measurement in hPa"""
        # reset the filter to prevent spurious readings
        self._reset_filter  # pylint: disable=pointless-statement

        # check for negative and convert
        raw = self._raw_pressure
        if raw & (1 << 23) != 0:
            raw = raw - (1 << 24)
        return raw / 4096.0

    @property
    def temperature(self):
        """The current temperature measurement in degrees C"""
        return self._raw_temperature / 100.0

    def reset(self):
        """Reset the sensor, restoring all configuration registers to their defaults"""
        self._reset = True
        # wait for the reset to finish
        while self._reset:
            pass

    def take_measurement(self):
        """Update the value of ``pressure`` and ``temperature`` by taking a single measurement.
        Only meaningful if ``data_rate`` is set to ``ONE_SHOT``"""
        self._one_shot = True
        while self._one_shot:
            pass

    def zero_pressure(self):
        """Set the current pressure as zero and report the ``pressure`` relative to it"""
        self._auto_zero = True
        while self._auto_zero:
            pass

    def reset_pressure(self):
        """Reset ``pressure`` to be reported as the measured absolute value"""
        self._reset_zero = True

    @property
    def pressure_threshold(self):
        """The high presure threshold. Use ``high_threshold_enabled`` or  ``high_threshold_enabled``
        to use it"""
        return self._pressure_threshold / 16

    @pressure_threshold.setter
    def pressure_threshold(self, value):
        """The high value threshold"""
        self._pressure_threshold = value * 16

    @property
    def high_threshold_enabled(self):
        """Set to `True` or `False` to enable or disable the high pressure threshold"""
        return self._interrupts_enabled and self._interrupt_high

    @high_threshold_enabled.setter
    def high_threshold_enabled(self, value):
        self._interrupts_enabled = value
        self._interrupt_high = value

    @property
    def low_threshold_enabled(self):
        """Set to `True` or `False` to enable or disable the low pressure threshold. **Note the
        low pressure threshold only works in relative mode**"""
        return self._interrupts_enabled and self._interrupt_low

    @low_threshold_enabled.setter
    def low_threshold_enabled(self, value):
        self._interrupts_enabled = value
        self._interrupt_low = value

    @property
    def high_threshold_exceeded(self):
        """Returns `True` if the pressure high threshold has been exceeded. Must be enabled by
        setting ``high_threshold_enabled`` to `True` and setting a ``pressure_threshold``."""
        return self._pressure_high

    @property
    def low_threshold_exceeded(self):
        """Returns `True` if the pressure low threshold has been exceeded. Must be enabled by
        setting ``high_threshold_enabled`` to `True` and setting a ``pressure_threshold``."""
        return self._pressure_low
