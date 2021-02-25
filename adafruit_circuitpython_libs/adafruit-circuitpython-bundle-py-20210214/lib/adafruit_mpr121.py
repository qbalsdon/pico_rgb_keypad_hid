# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_mpr121`
====================================================

CircuitPython driver for the MPR121 capacitive touch breakout board.

See usage in the examples/simpletest.py file.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `12-Key Capacitive Touch Sensor Breakout - MPR121
  <https://www.adafruit.com/product/1982>`_ (Product ID: 1982)

* Adafruit `12 x Capacitive Touch Shield for Arduino - MPR121
  <https://www.adafruit.com/product/2024>`_ (Product ID: 2024)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

import time

import adafruit_bus_device.i2c_device as i2c_device
from micropython import const

__version__ = "2.1.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MPR121.git"

# Register addresses.  Unused registers commented out to save memory.
MPR121_I2CADDR_DEFAULT = const(0x5A)
MPR121_TOUCHSTATUS_L = const(0x00)
# MPR121_TOUCHSTATUS_H   = const(0x01)
MPR121_FILTDATA_0L = const(0x04)
# MPR121_FILTDATA_0H     = const(0x05)
MPR121_BASELINE_0 = const(0x1E)
MPR121_MHDR = const(0x2B)
MPR121_NHDR = const(0x2C)
MPR121_NCLR = const(0x2D)
MPR121_FDLR = const(0x2E)
MPR121_MHDF = const(0x2F)
MPR121_NHDF = const(0x30)
MPR121_NCLF = const(0x31)
MPR121_FDLF = const(0x32)
MPR121_NHDT = const(0x33)
MPR121_NCLT = const(0x34)
MPR121_FDLT = const(0x35)
MPR121_TOUCHTH_0 = const(0x41)
MPR121_RELEASETH_0 = const(0x42)
MPR121_DEBOUNCE = const(0x5B)
MPR121_CONFIG1 = const(0x5C)
MPR121_CONFIG2 = const(0x5D)
# MPR121_CHARGECURR_0    = const(0x5F)
# MPR121_CHARGETIME_1    = const(0x6C)
MPR121_ECR = const(0x5E)
# MPR121_AUTOCONFIG0     = const(0x7B)
# MPR121_AUTOCONFIG1     = const(0x7C)
# MPR121_UPLIMIT         = const(0x7D)
# MPR121_LOWLIMIT        = const(0x7E)
# MPR121_TARGETLIMIT     = const(0x7F)
# MPR121_GPIODIR         = const(0x76)
# MPR121_GPIOEN          = const(0x77)
# MPR121_GPIOSET         = const(0x78)
# MPR121_GPIOCLR         = const(0x79)
# MPR121_GPIOTOGGLE      = const(0x7A)
MPR121_SOFTRESET = const(0x80)


class MPR121_Channel:
    # pylint: disable=protected-access
    """Helper class to represent a touch channel on the MPR121. Not meant to
    be used directly."""

    def __init__(self, mpr121, channel):
        self._mpr121 = mpr121
        self._channel = channel

    @property
    def value(self):
        """Whether the touch pad is being touched or not."""
        return self._mpr121.touched() & (1 << self._channel) != 0

    @property
    def raw_value(self):
        """The raw touch measurement."""
        return self._mpr121.filtered_data(self._channel)

    @property
    def threshold(self):
        """The touch threshold."""
        buf = bytearray(1)
        self._mpr121._read_register_bytes(MPR121_TOUCHTH_0 + 2 * self._channel, buf, 1)
        return buf[0]

    @threshold.setter
    def threshold(self, value):
        self._mpr121._write_register_byte(MPR121_TOUCHTH_0 + 2 * self._channel, value)

    @property
    def release_threshold(self):
        """The release threshold."""
        buf = bytearray(1)
        self._mpr121._read_register_bytes(
            MPR121_RELEASETH_0 + 2 * self._channel, buf, 1
        )
        return buf[0]

    @release_threshold.setter
    def release_threshold(self, value):
        self._mpr121._write_register_byte(MPR121_RELEASETH_0 + 2 * self._channel, value)


class MPR121:
    """Driver for the MPR121 capacitive touch breakout board."""

    def __init__(self, i2c, address=MPR121_I2CADDR_DEFAULT):
        self._i2c = i2c_device.I2CDevice(i2c, address)
        self._buffer = bytearray(2)
        self._channels = [None] * 12
        self.reset()

    def __getitem__(self, key):
        if key < 0 or key > 11:
            raise IndexError("Pin must be a value 0-11.")
        if self._channels[key] is None:
            self._channels[key] = MPR121_Channel(self, key)
        return self._channels[key]

    @property
    def touched_pins(self):
        """A tuple of touched state for all pins."""
        touched = self.touched()
        return tuple([bool(touched >> i & 0x01) for i in range(12)])

    def _write_register_byte(self, register, value):
        # Write a byte value to the specifier register address.
        # MPR121 must be put in Stop Mode to write to most registers
        stop_required = True
        if register == MPR121_ECR or 0x73 <= register <= 0x7A:
            stop_required = False
        with self._i2c:
            if stop_required:
                self._i2c.write(bytes([MPR121_ECR, 0x00]))
            self._i2c.write(bytes([register, value]))
            if stop_required:
                self._i2c.write(bytes([MPR121_ECR, 0x8F]))

    def _read_register_bytes(self, register, result, length=None):
        # Read the specified register address and fill the specified result byte
        # array with result bytes.  Make sure result buffer is the desired size
        # of data to read.
        if length is None:
            length = len(result)
        with self._i2c:
            self._i2c.write_then_readinto(bytes([register]), result, in_end=length)

    def reset(self):
        """Reset the MPR121 into a default state ready to detect touch inputs."""
        # Write to the reset register.
        self._write_register_byte(MPR121_SOFTRESET, 0x63)
        time.sleep(
            0.001
        )  # This 1ms delay here probably isn't necessary but can't hurt.
        # Set electrode configuration to default values.
        self._write_register_byte(MPR121_ECR, 0x00)
        # Check CDT, SFI, ESI configuration is at default values.
        self._read_register_bytes(MPR121_CONFIG2, self._buffer, 1)
        if self._buffer[0] != 0x24:
            raise RuntimeError("Failed to find MPR121 in expected config state!")
        # Default touch and release thresholds
        for i in range(12):
            self._write_register_byte(MPR121_TOUCHTH_0 + 2 * i, 12)
            self._write_register_byte(MPR121_RELEASETH_0 + 2 * i, 6)
        # Configure baseline filtering control registers.
        self._write_register_byte(MPR121_MHDR, 0x01)
        self._write_register_byte(MPR121_NHDR, 0x01)
        self._write_register_byte(MPR121_NCLR, 0x0E)
        self._write_register_byte(MPR121_FDLR, 0x00)
        self._write_register_byte(MPR121_MHDF, 0x01)
        self._write_register_byte(MPR121_NHDF, 0x05)
        self._write_register_byte(MPR121_NCLF, 0x01)
        self._write_register_byte(MPR121_FDLF, 0x00)
        self._write_register_byte(MPR121_NHDT, 0x00)
        self._write_register_byte(MPR121_NCLT, 0x00)
        self._write_register_byte(MPR121_FDLT, 0x00)
        # Set other configuration registers.
        self._write_register_byte(MPR121_DEBOUNCE, 0)
        self._write_register_byte(MPR121_CONFIG1, 0x10)  # default, 16uA charge current
        self._write_register_byte(MPR121_CONFIG2, 0x20)  # 0.5uS encoding, 1ms period
        # Enable all electrodes.
        self._write_register_byte(
            MPR121_ECR, 0x8F
        )  # start with first 5 bits of baseline tracking

    def filtered_data(self, pin):
        """Return filtered data register value for the provided pin (0-11).
        Useful for debugging.
        """
        if pin < 0 or pin > 11:
            raise ValueError("Pin must be a value 0-11.")
        self._read_register_bytes(MPR121_FILTDATA_0L + pin * 2, self._buffer)
        return ((self._buffer[1] << 8) | (self._buffer[0])) & 0xFFFF

    def baseline_data(self, pin):
        """Return baseline data register value for the provided pin (0-11).
        Useful for debugging.
        """
        if pin < 0 or pin > 11:
            raise ValueError("Pin must be a value 0-11.")
        self._read_register_bytes(MPR121_BASELINE_0 + pin, self._buffer, 1)
        return self._buffer[0] << 2

    def touched(self):
        """Return touch state of all pins as a 12-bit value where each bit
        represents a pin, with a value of 1 being touched and 0 not being touched.
        """
        self._read_register_bytes(MPR121_TOUCHSTATUS_L, self._buffer)
        return ((self._buffer[1] << 8) | (self._buffer[0])) & 0xFFFF

    def is_touched(self, pin):
        """Return True if the specified pin is being touched, otherwise returns
        False.
        """
        if pin < 0 or pin > 11:
            raise ValueError("Pin must be a value 0-11.")
        touches = self.touched()
        return (touches & (1 << pin)) > 0
