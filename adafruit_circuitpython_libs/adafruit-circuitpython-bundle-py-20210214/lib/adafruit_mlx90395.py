# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
# The MIT License (MIT)
#
# Copyright (c) 2020 Bryan Siepert for Adafruit Industries
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
`adafruit_mlx90395`
================================================================================
CircuitPython helper library for the Melexis MLX90395 3-axis Magnetometer
* Author(s): Bryan Siepert
Implementation Notes
--------------------
**Hardware:**
* Adafruit MLX90395 Breakout <https://www.adafruit.com/products/48XX>

**Software and Dependencies:**
Adafruit CircuitPython firmware for the supported boards:
* https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""
from time import sleep
from struct import unpack_from
from micropython import const
import adafruit_bus_device.i2c_device as i2c_device

# from adafruit_register.i2c_struct import ROUnaryStruct, Struct
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_struct import UnaryStruct

# from adafruit_register.i2c_bit import RWBit

__version__ = "1.0.0"
__repo__ = "https:#github.com/adafruit/Adafruit_CircuitPython_MLX90395.git"

_DEFAULT_ADDR = const(0x0C)  ## Can also be 0x18, depending on IC */

_STATUS_RESET = const(0x02)
_STATUS_SMMODE = const(0x20)
_STATUS_DRDY = const(0x01)
_REG_0 = const(0x0)
_REG_1 = const(0x2)
_REG_2 = const(0x4)
_REG_SM = const(0x30)
_REG_EX = const(0x80)
_REG_RT = const(0xF0)
GAIN_AMOUNT = [
    0.2,
    0.25,
    0.3333,
    0.4,
    0.5,
    0.6,
    0.75,
    1,
    0.1,
    0.125,
    0.1667,
    0.2,
    0.25,
    0.3,
    0.375,
    0.5,
]


class CV:
    """struct helper"""

    @classmethod
    def add_values(cls, value_tuples):
        "creates CV entires"
        cls.string = {}
        cls.lsb = {}

        for value_tuple in value_tuples:
            name, value, string, lsb = value_tuple
            setattr(cls, name, value)
            cls.string[value] = string
            cls.lsb[value] = lsb

    @classmethod
    def is_valid(cls, value):
        "Returns true if the given value is a member of the CV"
        return value in cls.string


class OSR(CV):
    """Options for ``oversample_rate``"""


OSR.add_values(
    (
        ("RATE_1X", 0, "1X", None),
        ("RATE_2X", 1, "2X", None),
        ("RATE_4X", 2, "4X", None),
        ("RATE_8X", 3, "8X", None),
    )
)


class Resolution(CV):
    """Options for :py:meth:`MLX90640.resolution`"""


Resolution.add_values(
    (
        ("BITS_16", 0, 16, None),
        ("BITS_17", 1, 17, None),
        ("BITS_18", 2, 18, None),
        ("BITS_19", 3, 19, None),
    )
)


class Gain(CV):
    """Options for :py:meth:`MLX90395.gain`"""


Gain.add_values(
    (
        ("GAIN_0_2", 0, "0.2", None),
        ("GAIN_0_25", 1, "0.25", None),
        ("GAIN_0_3333", 2, "0.3333", None),
        ("GAIN_0_4", 3, "0.4", None),
        ("GAIN_0_5", 4, "0.5", None),
        ("GAIN_0_6", 5, "0.6", None),
        ("GAIN_0_75", 6, "0.75", None),
        ("GAIN_1", 7, "1", None),
        ("GAIN_0_1", 8, "0.1", None),
        ("GAIN_0_125", 9, "0.125", None),
        ("GAIN_0_1667", 10, "0.1667", None),
        ("GAIN_0_2", 11, "0.2", None),
        ("GAIN_0_25", 12, "0.25", None),
        ("GAIN_0_3", 13, "0.3", None),
        ("GAIN_0_375", 14, "0.375", None),
        ("GAIN_0_5", 15, "0.5", None),
    )
)


class MLX90395:
    """Class for interfacing with the MLX90395 3-axis magnetometer"""

    _gain = RWBits(4, _REG_0, 4, 2, False)

    _resolution = RWBits(2, _REG_2, 5, 2, False)
    _filter = RWBits(3, _REG_2, 2, 2, False)
    _osr = RWBits(2, _REG_2, 0, 2, False)
    _reg0 = UnaryStruct(_REG_0, ">H",)
    _reg2 = UnaryStruct(_REG_2, ">H")

    def __init__(self, i2c_bus, address=_DEFAULT_ADDR):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._ut_lsb = None
        self._gain_val = 0
        self._buffer = bytearray(12)

        self.reset()
        self.initialize()

    def reset(self):
        """Reset the sensor to it's power-on state"""

        self._command(_REG_EX)
        self._command(_REG_EX)

        sleep(0.10)
        if self._command(_REG_RT) != _STATUS_RESET:
            raise RuntimeError("Unable to reset!")

        sleep(0.10)

    def initialize(self):
        """Configure the sensor for use"""
        self._gain_val = self.gain
        if self._gain_val == 8:  # default high field gain
            self._ut_lsb = 7.14
        else:
            self._ut_lsb = 2.5  # medium field gain

    @property
    def resolution(self):
        """The current resolution setting for the magnetometer"""
        return self._resolution

    @resolution.setter
    def resolution(self, value):
        if not Resolution.is_valid(value):
            raise AttributeError("resolution must be a Resolution")
        self._resolution = value

    @property
    def gain(self):
        """The gain applied to the magnetometer's ADC."""
        return self._gain

    @gain.setter
    def gain(self, value):
        if not Gain.is_valid(value):
            raise AttributeError("gain must be a valid value")
        self._gain = value
        self._gain_val = value

    def _command(self, command_id):

        buffer = bytearray([0x80, command_id])
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buffer, buffer, in_end=1)
        return buffer[0]

    @property
    def magnetic(self):
        """The processed magnetometer sensor values.
        A 3-tuple of X, Y, Z axis values in microteslas that are signed floats.
        """
        if self._command(_REG_SM | 0x0F) != _STATUS_SMMODE:
            raise RuntimeError("Unable to initiate a single reading")
        res = self._read_measurement()
        while res is None:
            sleep(0.001)
            res = self._read_measurement()

        return res

    def _read_measurement(self):

        # clear the buffer
        for i in range(len(self._buffer)):
            self._buffer[i] = 0
        self._buffer[0] = 0x80  # read memory command

        with self.i2c_device as i2c:
            i2c.write_then_readinto(self._buffer, self._buffer, out_end=1)

        if self._buffer[0] != _STATUS_DRDY:
            return None

        x_raw, y_raw, z_raw = unpack_from(">hhh", self._buffer, offset=2)

        scalar = GAIN_AMOUNT[self._gain_val] * self._ut_lsb
        return (x_raw * scalar, y_raw * scalar, z_raw * scalar)

    @property
    def oversample_rate(self):
        """The number of times that the measurements are re-sampled and averaged to reduce noise"""
        return self._osr

    @oversample_rate.setter
    def oversample_rate(self, value):
        if not OSR.is_valid(value):
            raise AttributeError("oversample_rate must be an OSR")
        self._osr = value
