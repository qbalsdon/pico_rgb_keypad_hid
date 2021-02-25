# SPDX-FileCopyrightText: 2017 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_amg88xx` - AMG88xx GRID-Eye IR 8x8 IR sensor
======================================================
This library supports the use of the AMG88xx in CircuitPython.

Author(s): Dean Miller, Scott Shawcroft for Adafruit Industries.
Date: June 2017
Affiliation: Adafruit Industries

Implementation Notes
--------------------
**Hardware:**

**Software and Dependencies:**
* Adafruit CircuitPython: https://github.com/adafruit/circuitpython/releases
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

**Notes:**
"""

__version__ = "1.2.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AMG88xx"

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register import i2c_bit, i2c_bits
from micropython import const


# Registers are defined below in the class. These are possible register values.

# Operating Modes
_NORMAL_MODE = const(0x00)
_SLEEP_MODE = const(0x10)
_STAND_BY_60 = const(0x20)
_STAND_BY_10 = const(0x21)

# sw resets
_FLAG_RESET = const(0x30)
_INITIAL_RESET = const(0x3F)

# frame rates
_FPS_10 = const(0x00)
_FPS_1 = const(0x01)

# int enables
_INT_DISABLED = const(0x00)
_INT_ENABLED = const(0x01)

# int modes
_DIFFERENCE = const(0x00)
_ABSOLUTE_VALUE = const(0x01)

_INT_OFFSET = const(0x010)
_PIXEL_OFFSET = const(0x80)

_PIXEL_ARRAY_WIDTH = const(8)
_PIXEL_ARRAY_HEIGHT = const(8)
_PIXEL_TEMP_CONVERSION = 0.25
_THERMISTOR_CONVERSION = 0.0625


def _signed_12bit_to_float(val):
    # take first 11 bits as absolute val
    abs_val = val & 0x7FF
    if val & 0x800:
        return 0 - float(abs_val)
    return float(abs_val)


def _twos_comp_to_float(val):
    val &= 0xFFF
    if val & 0x800:
        val -= 0x1000
    return float(val)


class AMG88XX:
    """Driver for the AMG88xx GRID-Eye IR 8x8 thermal camera."""

    # Set up the registers
    _pctl = i2c_bits.RWBits(8, 0x00, 0)
    _rst = i2c_bits.RWBits(8, 0x01, 0)
    _fps = i2c_bit.RWBit(0x02, 0)
    _inten = i2c_bit.RWBit(0x03, 0)
    _intmod = i2c_bit.RWBit(0x03, 1)

    _intf = i2c_bit.RWBit(0x04, 1)
    _ovf_irs = i2c_bit.RWBit(0x04, 2)
    _ovf_ths = i2c_bit.RWBit(0x04, 3)

    _intclr = i2c_bit.RWBit(0x05, 1)
    _ovs_clr = i2c_bit.RWBit(0x05, 2)
    _ovt_clr = i2c_bit.RWBit(0x05, 3)

    _mamod = i2c_bit.RWBit(0x07, 5)

    _inthl = i2c_bits.RWBits(8, 0x08, 0)
    _inthh = i2c_bits.RWBits(4, 0x09, 0)
    _intll = i2c_bits.RWBits(8, 0x0A, 0)
    _intlh = i2c_bits.RWBits(4, 0x0B, 0)
    _ihysl = i2c_bits.RWBits(8, 0x0C, 0)
    _ihysh = i2c_bits.RWBits(4, 0x0D, 0)

    _tthl = i2c_bits.RWBits(8, 0x0E, 0)

    _tthh = i2c_bits.RWBits(4, 0x0F, 0)

    def __init__(self, i2c, addr=0x69):
        self.i2c_device = I2CDevice(i2c, addr)

        # enter normal mode
        self._pctl = _NORMAL_MODE

        # software reset
        self._rst = _INITIAL_RESET

        # disable interrupts by default
        self._inten = False

        # set to 10 FPS
        self._fps = _FPS_10

    @property
    def temperature(self):
        """Temperature of the sensor in Celsius"""
        raw = (self._tthh << 8) | self._tthl
        return _signed_12bit_to_float(raw) * _THERMISTOR_CONVERSION

    @property
    def pixels(self):
        """Temperature of each pixel across the sensor in Celsius.

        Temperatures are stored in a two dimensional list where the first index is the row and
        the second is the column. The first row is on the side closest to the writing on the
        sensor."""
        retbuf = [[0] * _PIXEL_ARRAY_WIDTH for _ in range(_PIXEL_ARRAY_HEIGHT)]
        buf = bytearray(3)

        with self.i2c_device as i2c:
            for row in range(0, _PIXEL_ARRAY_HEIGHT):
                for col in range(0, _PIXEL_ARRAY_WIDTH):
                    i = row * _PIXEL_ARRAY_HEIGHT + col
                    buf[0] = _PIXEL_OFFSET + (i << 1)
                    i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)

                    raw = (buf[2] << 8) | buf[1]
                    retbuf[row][col] = _twos_comp_to_float(raw) * _PIXEL_TEMP_CONVERSION

        return retbuf
