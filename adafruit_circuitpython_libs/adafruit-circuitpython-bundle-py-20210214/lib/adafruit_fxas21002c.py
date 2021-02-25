# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_fxas21002c`
====================================================

CircuitPython module for the NXP FXAS21002C gyroscope.  Based on the driver
from: https://github.com/adafruit/Adafruit_FXAS21002C

See examples/simpletest.py for a demo of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

*  Adafruit `Precision NXP 9-DOF Breakout Board - FXOS8700 + FXAS21002
   <https://www.adafruit.com/product/3463>`_ (Product ID: 3463)

**Software and Dependencies:**

* Adafruit CircuitPython firmware (2.2.0+) for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
import time

try:
    import ustruct as struct
except ImportError:
    import struct

__version__ = "2.1.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FXAS21002C.git"

import adafruit_bus_device.i2c_device as i2c_dev
from micropython import const


# Internal constants and register values:
_FXAS21002C_ADDRESS = const(0x21)  # 0100001
_FXAS21002C_ID = const(0xD7)  # 1101 0111
_GYRO_REGISTER_STATUS = const(0x00)
_GYRO_REGISTER_OUT_X_MSB = const(0x01)
_GYRO_REGISTER_OUT_X_LSB = const(0x02)
_GYRO_REGISTER_OUT_Y_MSB = const(0x03)
_GYRO_REGISTER_OUT_Y_LSB = const(0x04)
_GYRO_REGISTER_OUT_Z_MSB = const(0x05)
_GYRO_REGISTER_OUT_Z_LSB = const(0x06)
_GYRO_REGISTER_WHO_AM_I = const(0x0C)  # 11010111   r
_GYRO_REGISTER_CTRL_REG0 = const(0x0D)  # 00000000   r/w
_GYRO_REGISTER_CTRL_REG1 = const(0x13)  # 00000000   r/w
_GYRO_REGISTER_CTRL_REG2 = const(0x14)  # 00000000   r/w
_GYRO_SENSITIVITY_250DPS = 0.0078125  # Table 35 of datasheet
_GYRO_SENSITIVITY_500DPS = 0.015625  # ..
_GYRO_SENSITIVITY_1000DPS = 0.03125  # ..
_GYRO_SENSITIVITY_2000DPS = 0.0625  # ..

# User facing constants/module globals:
GYRO_RANGE_250DPS = 250
GYRO_RANGE_500DPS = 500
GYRO_RANGE_1000DPS = 1000
GYRO_RANGE_2000DPS = 2000

# Unit conversion:
DEGREE_TO_RAD = 3.141592653589793 / 180


class FXAS21002C:
    """Driver for the NXP FXAS21002C gyroscope."""

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!
    _BUFFER = bytearray(7)

    def __init__(self, i2c, address=_FXAS21002C_ADDRESS, gyro_range=GYRO_RANGE_250DPS):
        assert gyro_range in (
            GYRO_RANGE_250DPS,
            GYRO_RANGE_500DPS,
            GYRO_RANGE_1000DPS,
            GYRO_RANGE_2000DPS,
        )
        self._gyro_range = gyro_range
        self._device = i2c_dev.I2CDevice(i2c, address)
        # Check for chip ID value.
        if self._read_u8(_GYRO_REGISTER_WHO_AM_I) != _FXAS21002C_ID:
            raise RuntimeError("Failed to find FXAS21002C, check wiring!")
        ctrl_reg0 = 0x00
        if gyro_range == GYRO_RANGE_250DPS:
            ctrl_reg0 = 0x03
        elif gyro_range == GYRO_RANGE_500DPS:
            ctrl_reg0 = 0x02
        elif gyro_range == GYRO_RANGE_1000DPS:
            ctrl_reg0 = 0x01
        elif gyro_range == GYRO_RANGE_2000DPS:
            ctrl_reg0 = 0x00
        # Reset then switch to active mode with 100Hz output
        # Putting into standy doesn't work as the chip becomes instantly
        # unresponsive.  Perhaps CircuitPython is too slow to go into standby
        # and send reset?  Keep these two commented for now:
        # self._write_u8(_GYRO_REGISTER_CTRL_REG1, 0x00)     # Standby)
        # self._write_u8(_GYRO_REGISTER_CTRL_REG1, (1<<6))   # Reset
        self._write_u8(_GYRO_REGISTER_CTRL_REG0, ctrl_reg0)  # Set sensitivity
        self._write_u8(_GYRO_REGISTER_CTRL_REG1, 0x0E)  # Active
        time.sleep(0.1)  # 60 ms + 1/ODR

    def _read_u8(self, address):
        # Read an 8-bit unsigned value from the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_end=1)
        return self._BUFFER[0]

    def _write_u8(self, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)

    def read_raw(self):
        """Read the raw gyroscope readings.  Returns a 3-tuple of X, Y, Z axis
        16-bit signed values.  If you want the gyroscope values in friendly
        units consider using the gyroscope property!
        """
        # Read gyro data from the sensor.
        with self._device as i2c:
            self._BUFFER[0] = _GYRO_REGISTER_OUT_X_MSB
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1)
        # Parse out the gyroscope data as 16-bit signed data.
        raw_x = struct.unpack_from(">h", self._BUFFER[0:2])[0]
        raw_y = struct.unpack_from(">h", self._BUFFER[2:4])[0]
        raw_z = struct.unpack_from(">h", self._BUFFER[4:6])[0]
        return (raw_x, raw_y, raw_z)

    # pylint is confused and incorrectly marking this function as bad return
    # types.  Perhaps it doesn't understand map returns an iterable value.
    # Disable the warning.
    @property
    def gyroscope(self):
        """Read the gyroscope value and return its X, Y, Z axis values as a
        3-tuple in radians/second.
        """
        raw = self.read_raw()
        # Compensate values depending on the resolution
        factor = 0
        if self._gyro_range == GYRO_RANGE_250DPS:
            factor = _GYRO_SENSITIVITY_250DPS
        elif self._gyro_range == GYRO_RANGE_500DPS:
            factor = _GYRO_SENSITIVITY_500DPS
        elif self._gyro_range == GYRO_RANGE_1000DPS:
            factor = _GYRO_SENSITIVITY_1000DPS
        elif self._gyro_range == GYRO_RANGE_2000DPS:
            factor = _GYRO_SENSITIVITY_2000DPS
        factor *= DEGREE_TO_RAD
        return [x * factor for x in raw]
