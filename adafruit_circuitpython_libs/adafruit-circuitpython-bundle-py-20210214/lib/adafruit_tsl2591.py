# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_tsl2591`
====================================================

CircuitPython module for the TSL2591 precision light sensor.  See
examples/simpletest.py for a demo of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `TSL2591 High Dynamic Range Digital Light Sensor
  <https://www.adafruit.com/product/1980>`_ (Product ID: 1980)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
from micropython import const

import adafruit_bus_device.i2c_device as i2c_device


__version__ = "1.2.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TSL2591.git"


# Internal constants:
_TSL2591_ADDR = const(0x29)
_TSL2591_COMMAND_BIT = const(0xA0)
_TSL2591_ENABLE_POWEROFF = const(0x00)
_TSL2591_ENABLE_POWERON = const(0x01)
_TSL2591_ENABLE_AEN = const(0x02)
_TSL2591_ENABLE_AIEN = const(0x10)
_TSL2591_ENABLE_NPIEN = const(0x80)
_TSL2591_REGISTER_ENABLE = const(0x00)
_TSL2591_REGISTER_CONTROL = const(0x01)
_TSL2591_REGISTER_DEVICE_ID = const(0x12)
_TSL2591_REGISTER_CHAN0_LOW = const(0x14)
_TSL2591_REGISTER_CHAN1_LOW = const(0x16)
_TSL2591_LUX_DF = 408.0
_TSL2591_LUX_COEFB = 1.64
_TSL2591_LUX_COEFC = 0.59
_TSL2591_LUX_COEFD = 0.86
_TSL2591_MAX_COUNT_100MS = const(36863)  # 0x8FFF
_TSL2591_MAX_COUNT = const(65535)  # 0xFFFF

# User-facing constants:
GAIN_LOW = 0x00  # low gain (1x)
"""Low gain (1x)"""
GAIN_MED = 0x10  # medium gain (25x)
"""Medium gain (25x)"""
GAIN_HIGH = 0x20  # medium gain (428x)
"""High gain (428x)"""
GAIN_MAX = 0x30  # max gain (9876x)
"""Max gain (9876x)"""
INTEGRATIONTIME_100MS = 0x00  # 100 millis
"""100 millis"""
INTEGRATIONTIME_200MS = 0x01  # 200 millis
"""200 millis"""
INTEGRATIONTIME_300MS = 0x02  # 300 millis
"""300 millis"""
INTEGRATIONTIME_400MS = 0x03  # 400 millis
"""400 millis"""
INTEGRATIONTIME_500MS = 0x04  # 500 millis
"""500 millis"""
INTEGRATIONTIME_600MS = 0x05  # 600 millis
"""600 millis"""


class TSL2591:
    """TSL2591 high precision light sensor.
    :param busio.I2C i2c: The I2C bus connected to the sensor
    :param int address: The I2C address of the sensor.  If not specified
    the sensor default will be used.
    """

    # Class-level buffer to reduce memory usage and allocations.
    # Note this is NOT thread-safe or re-entrant by design.
    _BUFFER = bytearray(2)

    def __init__(self, i2c, address=_TSL2591_ADDR):
        self._integration_time = 0
        self._gain = 0
        self._device = i2c_device.I2CDevice(i2c, address)
        # Verify the chip ID.
        if self._read_u8(_TSL2591_REGISTER_DEVICE_ID) != 0x50:
            raise RuntimeError("Failed to find TSL2591, check wiring!")
        # Set default gain and integration times.
        self.gain = GAIN_MED
        self.integration_time = INTEGRATIONTIME_100MS
        # Put the device in a powered on state after initialization.
        self.enable()

    def _read_u8(self, address):
        # Read an 8-bit unsigned value from the specified 8-bit address.
        with self._device as i2c:
            # Make sure to add command bit to read request.
            self._BUFFER[0] = (_TSL2591_COMMAND_BIT | address) & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_end=1)
        return self._BUFFER[0]

    # Disable invalid name check since pylint isn't smart enough to know LE
    # is an abbreviation for little-endian.
    # pylint: disable=invalid-name
    def _read_u16LE(self, address):
        # Read a 16-bit little-endian unsigned value from the specified 8-bit
        # address.
        with self._device as i2c:
            # Make sure to add command bit to read request.
            self._BUFFER[0] = (_TSL2591_COMMAND_BIT | address) & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_end=2)
        return (self._BUFFER[1] << 8) | self._BUFFER[0]

    # pylint: enable=invalid-name

    def _write_u8(self, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        with self._device as i2c:
            # Make sure to add command bit to write request.
            self._BUFFER[0] = (_TSL2591_COMMAND_BIT | address) & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)

    def enable(self):
        """Put the device in a fully powered enabled mode."""
        self._write_u8(
            _TSL2591_REGISTER_ENABLE,
            _TSL2591_ENABLE_POWERON
            | _TSL2591_ENABLE_AEN
            | _TSL2591_ENABLE_AIEN
            | _TSL2591_ENABLE_NPIEN,
        )

    def disable(self):
        """Disable the device and go into low power mode."""
        self._write_u8(_TSL2591_REGISTER_ENABLE, _TSL2591_ENABLE_POWEROFF)

    @property
    def gain(self):
        """Get and set the gain of the sensor.  Can be a value of:

        - ``GAIN_LOW`` (1x)
        - ``GAIN_MED`` (25x)
        - ``GAIN_HIGH`` (428x)
        - ``GAIN_MAX`` (9876x)
        """
        control = self._read_u8(_TSL2591_REGISTER_CONTROL)
        return control & 0b00110000

    @gain.setter
    def gain(self, val):
        assert val in (GAIN_LOW, GAIN_MED, GAIN_HIGH, GAIN_MAX)
        # Set appropriate gain value.
        control = self._read_u8(_TSL2591_REGISTER_CONTROL)
        control &= 0b11001111
        control |= val
        self._write_u8(_TSL2591_REGISTER_CONTROL, control)
        # Keep track of gain for future lux calculations.
        self._gain = val

    @property
    def integration_time(self):
        """Get and set the integration time of the sensor.  Can be a value of:

        - ``INTEGRATIONTIME_100MS`` (100 millis)
        - ``INTEGRATIONTIME_200MS`` (200 millis)
        - ``INTEGRATIONTIME_300MS`` (300 millis)
        - ``INTEGRATIONTIME_400MS`` (400 millis)
        - ``INTEGRATIONTIME_500MS`` (500 millis)
        - ``INTEGRATIONTIME_600MS`` (600 millis)
        """
        control = self._read_u8(_TSL2591_REGISTER_CONTROL)
        return control & 0b00000111

    @integration_time.setter
    def integration_time(self, val):
        assert 0 <= val <= 5
        # Set control bits appropriately.
        control = self._read_u8(_TSL2591_REGISTER_CONTROL)
        control &= 0b11111000
        control |= val
        self._write_u8(_TSL2591_REGISTER_CONTROL, control)
        # Keep track of integration time for future reading delay times.
        self._integration_time = val

    @property
    def raw_luminosity(self):
        """Read the raw luminosity from the sensor (both IR + visible and IR
        only channels) and return a 2-tuple of those values.  The first value
        is IR + visible luminosity (channel 0) and the second is the IR only
        (channel 1).  Both values are 16-bit unsigned numbers (0-65535).
        """
        # Read both the luminosity channels.
        channel_0 = self._read_u16LE(_TSL2591_REGISTER_CHAN0_LOW)
        channel_1 = self._read_u16LE(_TSL2591_REGISTER_CHAN1_LOW)
        return (channel_0, channel_1)

    @property
    def full_spectrum(self):
        """Read the full spectrum (IR + visible) light and return its value
        as a 32-bit unsigned number.
        """
        channel_0, channel_1 = self.raw_luminosity
        return (channel_1 << 16) | channel_0

    @property
    def infrared(self):
        """Read the infrared light and return its value as a 16-bit unsigned number."""
        _, channel_1 = self.raw_luminosity
        return channel_1

    @property
    def visible(self):
        """Read the visible light and return its value as a 32-bit unsigned number."""
        channel_0, channel_1 = self.raw_luminosity
        full = (channel_1 << 16) | channel_0
        return full - channel_1

    @property
    def lux(self):
        """Read the sensor and calculate a lux value from both its infrared
        and visible light channels. Note: ``lux`` is not calibrated!
        """
        channel_0, channel_1 = self.raw_luminosity

        # Compute the atime in milliseconds
        atime = 100.0 * self._integration_time + 100.0

        # Set the maximum sensor counts based on the integration time (atime) setting
        if self._integration_time == INTEGRATIONTIME_100MS:
            max_counts = _TSL2591_MAX_COUNT_100MS
        else:
            max_counts = _TSL2591_MAX_COUNT

        # Handle overflow.
        if channel_0 >= max_counts or channel_1 >= max_counts:
            raise RuntimeError("Overflow reading light channels!")
        # Calculate lux using same equation as Arduino library:
        #  https://github.com/adafruit/Adafruit_TSL2591_Library/blob/master/Adafruit_TSL2591.cpp
        again = 1.0
        if self._gain == GAIN_MED:
            again = 25.0
        elif self._gain == GAIN_HIGH:
            again = 428.0
        elif self._gain == GAIN_MAX:
            again = 9876.0
        cpl = (atime * again) / _TSL2591_LUX_DF
        lux1 = (channel_0 - (_TSL2591_LUX_COEFB * channel_1)) / cpl
        lux2 = (
            (_TSL2591_LUX_COEFC * channel_0) - (_TSL2591_LUX_COEFD * channel_1)
        ) / cpl
        return max(lux1, lux2)
